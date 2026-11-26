def cart_counter(request):
    cart = request.session.get('cart', {})
    if not isinstance(cart, dict):
        return {'cart_count': 0}
    total_items = 0
    for qty in cart.values():
        try:
            quantity = int(qty)
            if quantity > 0:
                total_items += quantity
        except (TypeError, ValueError):
            continue
    return {'cart_count': total_items}
