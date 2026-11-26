from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from store.models import Product
from .models import Order, OrderItem


@require_POST
def confirm_order(request):
    cart = request.session.get('cart', {})
    if not isinstance(cart, dict) or not cart:
        messages.error(request, 'Your cart is empty.')
        return redirect('marketplace')

    customer_name = request.POST.get('customer_name', '').strip()
    customer_phone = request.POST.get('customer_phone', '').strip()
    delivery_address = request.POST.get('delivery_address', '').strip()
    customer_email = request.session.get('customer_email', '')

    if not customer_name or not customer_phone or not delivery_address:
        messages.error(request, 'Please fill in your Name, Phone Number, and Delivery Address.')
        return redirect('view_cart')

    valid_items = []
    subtotal = Decimal('0.00')

    for pid_str, qty in cart.items():
        try:
            product = Product.objects.get(id=int(pid_str), in_stock=True)
            quantity = int(qty)
            if quantity > 0:
                subtotal += product.price * quantity
                valid_items.append((product, quantity))
        except (Product.DoesNotExist, ValueError):
            continue

    if not valid_items:
        messages.error(request, 'Selected items are no longer available in stock.')
        return redirect('view_cart')

    delivery_fee = Decimal('60.00')
    total_amount = subtotal + delivery_fee

    # Reuse existing unpaid pending order in this session instead of creating duplicates
    pending_id = request.session.get('pending_order_id')
    order = None
    if pending_id:
        order = Order.objects.filter(id=pending_id, is_paid=False, order_status='pending_payment').first()

    if order:
        order.customer_name = customer_name
        order.customer_email = customer_email
        order.customer_phone = customer_phone
        order.delivery_address = delivery_address
        order.total_amount = total_amount
        order.save()
        order.items.all().delete()
    else:
        order = Order.objects.create(
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            delivery_address=delivery_address,
            total_amount=total_amount,
            is_paid=False,
            order_status='pending_payment',
        )
        request.session['pending_order_id'] = order.id
        request.session.modified = True

    for product, quantity in valid_items:
        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            price=product.price,
            quantity=quantity
        )

    return redirect('process_payment', order_id=order.id)


def process_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if order.order_status in ('verifying_payment', 'confirmed') or order.is_paid:
        return redirect('order_success', order_id=order.id)

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')

        if payment_method == 'bkash':
            bkash_number = request.POST.get('bkash_number', '').strip()
            bkash_trx_id = request.POST.get('bkash_trx_id', '').strip()

            if len(bkash_number) != 11 or not bkash_number.isdigit() or not bkash_trx_id:
                messages.error(request, 'Please enter a valid 11-digit bKash number and Transaction ID.')
                return render(request, 'payment.html', {
                    'order': order,
                    'customer_wallet': request.session.get('customer_wallet', '')
                })

            order.payment_method = 'bkash'
            order.bkash_number = bkash_number
            order.bkash_trx_id = bkash_trx_id
            order.order_status = 'verifying_payment'
            order.save()

        elif payment_method == 'credit_card':
            card_holder = request.POST.get('card_holder', '').strip()
            card_number = request.POST.get('card_number', '').replace(' ', '').strip()
            card_expiry = request.POST.get('card_expiry', '').strip()
            card_cvv = request.POST.get('card_cvv', '').strip()

            if not card_holder or len(card_number) < 12 or not card_number.isdigit() or not card_expiry or len(card_cvv) < 3:
                messages.error(request, 'Please enter valid Credit/Debit Card details.')
                return render(request, 'payment.html', {
                    'order': order,
                    'customer_wallet': request.session.get('customer_wallet', '')
                })

            order.payment_method = 'credit_card'
            order.card_holder = card_holder
            order.card_number = card_number
            order.card_expiry = card_expiry
            order.order_status = 'verifying_payment'
            order.save()

        else:
            messages.error(request, 'Please choose bKash or Credit Card.')
            return render(request, 'payment.html', {'order': order})

        # Clear cart after submitting payment details to Admin
        request.session['cart'] = {}
        request.session.pop('pending_order_id', None) 
        request.session.modified = True

        return redirect('order_success', order_id=order.id)

    return render(request, 'payment.html', {
        'order': order,
        'customer_wallet': request.session.get('customer_wallet', '')
    })


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'order_success.html', {'order': order})


def check_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return JsonResponse({
        'is_paid': order.is_paid,
        'order_status': order.order_status,
    })
