import logging
import mimetypes
from smtplib import SMTPException

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import EmailMessage
from django.core.mail.message import BadHeaderError
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password, check_password
from .models import CustomerProfile, SellerApplication


logger = logging.getLogger(__name__)


def _send_seller_application_notification(seller):
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        raise ImproperlyConfigured(
            'Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD to enable email notifications.'
        )

    email = EmailMessage(
        subject=f'MyDokaan seller application: {seller.full_name}',
        body=(
            'A new seller application was submitted.\n\n'
            f'Application ID: {seller.pk}\n'
            f'Full name: {seller.full_name}\n'
            f'Email: {seller.gmail}\n'
            f'Phone number: {seller.phone_number}\n'
            f'Address: {seller.address}\n'
            f'Stockhouse address: {seller.stockhouse_address}\n'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.SELLER_APPLICATION_NOTIFICATION_EMAIL],
    )

    for document in (seller.nid_pdf, seller.trade_license):
        document.open('rb')
        try:
            content = document.read()
        finally:
            document.close()
        content_type = mimetypes.guess_type(document.name)[0] or 'application/octet-stream'
        filename = document.name.rsplit('/', 1)[-1]
        email.attach(filename, content, content_type)

    return email.send(fail_silently=False) == 1


def login_view(request):
    if request.method == 'POST':
        login_type = request.POST.get('login_type')

        # 1. CUSTOMER AUTO-VERIFICATION & REDIRECT TO MARKETPLACE
        if login_type == 'customer':
            full_name = request.POST.get('full_name', '').strip()
            address = request.POST.get('address', '').strip()
            email = request.POST.get('email', '').strip().lower()
            wallet_number = request.POST.get('wallet_number', '').strip()

            if not full_name or not address or not email:
                messages.error(request, 'Please fill in all required customer fields.')
                return render(request, 'login.html')

            customer, _ = CustomerProfile.objects.update_or_create(
                email=email,
                defaults={
                    'full_name': full_name,
                    'address': address,
                    'wallet_number': wallet_number,
                }
            )

            request.session['role'] = 'customer'
            request.session['customer_id'] = customer.id
            request.session['customer_name'] = customer.full_name
            request.session['customer_email'] = customer.email
            request.session['customer_address'] = customer.address
            request.session['customer_wallet'] = customer.wallet_number or ''

            messages.success(request, f'Welcome, {customer.full_name}! You are verified.')
            return redirect('marketplace')

        # 2. SELLER VERIFICATION & REDIRECT TO SECRET MYDOKAAN
        elif login_type == 'seller':
            user_id = request.POST.get('mydokaan_user_id', '').strip()
            passkey = request.POST.get('passkey', '').strip()
            business_key = request.POST.get('business_key', '').strip()

            seller = SellerApplication.objects.filter(user_id=user_id).first()

            if not seller:
                messages.error(request, 'No seller account found with that User ID.')
                return render(request, 'login.html')

            if not seller.is_verified:
                messages.error(request, 'Your seller account is not verified by Admin yet.')
                return render(request, 'login.html')

            if not seller.is_activated:
                messages.error(request, 'Account not activated yet. Please complete activation on the Register page first.')
                return render(request, 'login.html')

            if business_key and seller.business_key != business_key:
                messages.error(request, 'Incorrect Business Key.')
                return render(request, 'login.html')

            if not seller.passkey:
                messages.error(request, 'No Passkey set for this account yet.')
                return render(request, 'login.html')

            # Verify hashed passkey (and auto-upgrade if plain text was entered in Admin)
            if check_password(passkey, seller.passkey):
                pass
            elif seller.passkey == passkey:
                seller.passkey = make_password(passkey)
                seller.save()
            else:
                messages.error(request, 'Incorrect Passkey. Please try again.')
                return render(request, 'login.html')

            request.session['role'] = 'seller'
            request.session['seller_db_id'] = seller.id
            request.session['seller_user_id'] = seller.user_id

            return redirect('mydokaan')

    return render(request, 'login.html')


def logout_view(request):
    request.session.flush()
    messages.success(request, 'You have been logged out safely.')
    return redirect('home')


def register_view(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        gmail = request.POST.get('gmail', '').strip().lower()
        address = request.POST.get('address', '').strip()
        stockhouse_address = request.POST.get('stockhouse_address', '').strip()
        nid_pdf = request.FILES.get('nid_pdf')
        trade_license = request.FILES.get('trade_license')

        if not all([full_name, phone_number, gmail, address, stockhouse_address, nid_pdf, trade_license]):
            messages.error(request, 'All fields and documents (NID PDF & Trade License) are required.')
            return render(request, 'register.html', {'status': 'form'})

        if SellerApplication.objects.filter(gmail=gmail).exists():
            existing = SellerApplication.objects.get(gmail=gmail)
            if existing.is_verified:
                return redirect(f'/register/?stage=verified&gmail={gmail}')
            return redirect(f'/register/?stage=pending&gmail={gmail}')

        seller = SellerApplication.objects.create(
            full_name=full_name,
            phone_number=phone_number,
            gmail=gmail,
            address=address,
            stockhouse_address=stockhouse_address,
            nid_pdf=nid_pdf,
            trade_license=trade_license,
        )

        try:
            email_sent = _send_seller_application_notification(seller)
        except (BadHeaderError, ImproperlyConfigured, OSError, SMTPException):
            logger.exception('Could not send seller application notification email.')
            email_sent = False

        if email_sent:
            messages.success(
                request,
                'Your application was submitted and the administrator was notified by email.',
            )
        else:
            messages.warning(
                request,
                'Your application was saved! Please wait for Admin approval.',
            )

        return redirect(f'/register/?stage=pending&gmail={gmail}')

    stage = request.GET.get('stage', 'form')
    gmail = request.GET.get('gmail', '')
    return render(request, 'register.html', {'status': stage, 'seller_gmail': gmail})


def check_verification_status(request):
    gmail = request.GET.get('gmail', '').strip().lower()
    if not gmail:
        return JsonResponse({'is_verified': False})

    try:
        seller = SellerApplication.objects.get(gmail=gmail)
        return JsonResponse({'is_verified': seller.is_verified})
    except SellerApplication.DoesNotExist:
        return JsonResponse({'is_verified': False})


def activate_seller(request):
    if request.method == 'POST':
        gmail = request.POST.get('gmail', '').strip().lower()
        user_id = request.POST.get('user_id', '').strip()
        business_key = request.POST.get('business_key', '').strip()
        new_passkey = request.POST.get('new_passkey', '').strip()

        seller_qs = SellerApplication.objects.filter(
            user_id=user_id,
            business_key=business_key,
            is_verified=True
        )
        if gmail:
            seller_qs = seller_qs.filter(gmail=gmail)

        seller = seller_qs.first()

        if not seller:
            messages.error(request, 'Verification failed: User ID and Business Key do not match our verified records.')
            return render(request, 'register.html', {'status': 'verified', 'seller_gmail': gmail})

        if len(new_passkey) < 4:
            messages.error(request, 'Please choose a passkey with at least 4 characters.')
            return render(request, 'register.html', {'status': 'verified', 'seller_gmail': gmail})

        seller.passkey = make_password(new_passkey)
        seller.is_activated = True
        seller.save()

        messages.success(request, 'Account activated! Log in using your User ID and Passkey.')
        return redirect('login')

    return redirect('register')
