from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from store.models import Product


def _get_cart(request):
    cart = request.session.get('cart')
    if not isinstance(cart, dict):
        cart = {}
        request.session['cart'] = cart
    return cart


def view_cart(request):
    cart = _get_cart(request)
    cart_items = []
    subtotal_amount = Decimal('0.00')
    invalid_ids = []

    for product_id_str, quantity in cart.items():
        try:
            product = Product.objects.get(id=int(product_id_str))
            qty = int(quantity)
            if qty <= 0 or not product.in_stock:
                invalid_ids.append(product_id_str)
                continue

            item_subtotal = product.price * qty
            subtotal_amount += item_subtotal
            cart_items.append({
                'product': product,
                'quantity': qty,
                'subtotal': item_subtotal,
            })
        except (Product.DoesNotExist, ValueError):
            invalid_ids.append(product_id_str)

    if invalid_ids:
        for pid in invalid_ids:
            cart.pop(pid, None)
        request.session['cart'] = cart
        request.session.modified = True

    delivery_fee = Decimal('60.00') if cart_items else Decimal('0.00')
    total_amount = subtotal_amount + delivery_fee

    context = {
        'cart_items': cart_items,
        'subtotal_amount': subtotal_amount,
        'delivery_fee': delivery_fee,
        'total_amount': total_amount,
        'customer_name': request.session.get('customer_name', ''),
        'customer_phone': request.session.get('customer_wallet', ''),
        'customer_email': request.session.get('customer_email', ''),
        'customer_address': request.session.get('customer_address', ''),
    }
    return render(request, 'cart.html', context)


@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if not product.in_stock:
        messages.error(request, f'"{product.name}" is currently out of stock.')
        return redirect('marketplace')

    cart = _get_cart(request)
    pid_str = str(product.id)
    cart[pid_str] = int(cart.get(pid_str, 0)) + 1

    request.session['cart'] = cart
    request.session.modified = True
    messages.success(request, f'"{product.name}" added to your cart.')
    return redirect('marketplace')


@require_POST
def update_cart(request, product_id, action):
    cart = _get_cart(request)
    pid_str = str(product_id)

    if pid_str in cart:
        current_qty = int(cart[pid_str])
        if action == 'increase':
            cart[pid_str] = current_qty + 1
        elif action == 'decrease':
            if current_qty > 1:
                cart[pid_str] = current_qty - 1
            else:
                cart.pop(pid_str, None)

        request.session['cart'] = cart
        request.session.modified = True

    return redirect('view_cart')


@require_POST
def remove_from_cart(request, product_id):
    cart = _get_cart(request)
    pid_str = str(product_id)

    if pid_str in cart:
        cart.pop(pid_str, None)
        request.session['cart'] = cart
        request.session.modified = True
        messages.success(request, 'Item removed from your cart.')

    return redirect('view_cart')
