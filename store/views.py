from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Product
from users.models import SellerApplication


def _get_logged_in_seller(request):
    if request.session.get('role') != 'seller':
        return None
    seller_db_id = request.session.get('seller_db_id')
    if not seller_db_id:
        return None
    return SellerApplication.objects.filter(
        id=seller_db_id,
        is_verified=True,
        is_activated=True
    ).first()


# 1. DEFAULT ENTERING VIEW: HOME PAGE
def home(request):
    featured_products = Product.objects.filter(in_stock=True).order_by('-created_at')[:5]
    return render(request, 'home.html', {'featured_products': featured_products})


# 2. PUBLIC MARKETPLACE (REAL-TIME SEARCH & STOCK UPDATES)
def marketplace(request):
    query = request.GET.get('q', '').strip()
    products = Product.objects.all().order_by('-created_at')

    if query:
        products = products.filter(name__icontains=query)

    return render(request, 'marketplace.html', {'products': products})


# 3. SECRET SELLER PORTAL: MYDOKAAN
def mydokaan(request):
    seller = _get_logged_in_seller(request)
    if not seller:
        messages.error(request, 'Access denied. Please log in with your verified Seller credentials.')
        return redirect('login')

    query = request.GET.get('q', '').strip()
    all_my_products = Product.objects.filter(seller_user_id=seller.user_id).order_by('-created_at')

    total_products = all_my_products.count()
    in_stock_count = all_my_products.filter(in_stock=True).count()
    out_of_stock_count = all_my_products.filter(in_stock=False).count()

    displayed_products = all_my_products
    if query:
        displayed_products = all_my_products.filter(name__icontains=query)

    context = {
        'seller': seller,
        'my_products': displayed_products,
        'total_products': total_products,
        'in_stock_count': in_stock_count,
        'out_of_stock_count': out_of_stock_count,
    }
    return render(request, 'mydokaan.html', context)


# 4. SECRET SELLER: ADD NEW ITEM TO MARKETPLACE
def add_product(request):
    seller = _get_logged_in_seller(request)
    if not seller:
        messages.error(request, 'Access denied. Seller login required.')
        return redirect('login')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        price_raw = request.POST.get('price', '').strip()
        in_stock_choice = request.POST.get('in_stock', 'yes')
        photo = request.FILES.get('photo')

        if not name or not price_raw or not photo:
            messages.error(request, 'Product photo, name, and price are all required.')
            return render(request, 'add_product.html')

        try:
            price = Decimal(price_raw)
            if price <= 0:
                raise InvalidOperation
        except InvalidOperation:
            messages.error(request, 'Please enter a valid positive price in BDT.')
            return render(request, 'add_product.html')

        Product.objects.create(
            seller_user_id=seller.user_id,
            seller_name=seller.full_name,
            name=name,
            photo=photo,
            price=price,
            in_stock=(in_stock_choice == 'yes')
        )

        messages.success(request, f'"{name}" has been published to the Marketplace!')
        return redirect('mydokaan')

    return render(request, 'add_product.html')


# 5. SECRET SELLER: ONE-CLICK STOCK TOGGLE (YES <-> NO)
@require_POST
def toggle_stock(request, product_id):
    seller = _get_logged_in_seller(request)
    if not seller:
        return redirect('login')

    product = get_object_or_404(Product, id=product_id, seller_user_id=seller.user_id)
    product.in_stock = not product.in_stock
    product.save()

    status_label = "Yes" if product.in_stock else "No"
    messages.success(request, f'Stock for "{product.name}" updated to: {status_label}.')
    return redirect('mydokaan')


# 6. SECRET SELLER: DELETE PRODUCT
@require_POST
def delete_product(request, product_id):
    seller = _get_logged_in_seller(request)
    if not seller:
        return redirect('login')

    product = get_object_or_404(Product, id=product_id, seller_user_id=seller.user_id)
    product_name = product.name
    product.delete()

    messages.success(request, f'"{product_name}" was removed from the Marketplace.')
    return redirect('mydokaan')
