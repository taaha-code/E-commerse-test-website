from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'price', 'quantity')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'customer_name',
        'customer_phone',
        'total_amount',
        'payment_method',
        'bkash_number',
        'bkash_trx_id',
        'card_number',
        'is_paid',
        'order_status',
    )
    list_filter = ('is_paid', 'order_status', 'payment_method', 'created_at')
    search_fields = ('id', 'customer_name', 'customer_phone', 'bkash_number', 'bkash_trx_id')
    inlines = [OrderItemInline]

    def save_model(self, request, obj, form, change):
        if obj.is_paid and obj.order_status != 'confirmed':
            obj.order_status = 'confirmed'
        elif not obj.is_paid and obj.order_status == 'confirmed':
            obj.order_status = 'verifying_payment'
        super().save_model(request, obj, form, change)
