from django.db import models
from store.models import Product


class Order(models.Model):
    PAYMENT_CHOICES = [
        ('bkash', 'bKash'),
        ('credit_card', 'Credit Card'),
    ]

    STATUS_CHOICES = [
        ('pending_payment', 'Pending Payment'),
        ('verifying_payment', 'Waiting for Admin Verification'),
        ('confirmed', 'Order Confirmed'),
        ('rejected', 'Payment Rejected'),
    ]

    customer_name = models.CharField(max_length=150)
    customer_email = models.EmailField(blank=True, default='')
    customer_phone = models.CharField(max_length=25)
    delivery_address = models.TextField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Payment Details Submitted by Customer for Admin Review
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, blank=True, null=True)
    bkash_number = models.CharField(max_length=20, blank=True, null=True)
    bkash_trx_id = models.CharField(max_length=50, blank=True, null=True)
    card_holder = models.CharField(max_length=150, blank=True, null=True)
    card_number = models.CharField(max_length=30, blank=True, null=True)
    card_expiry = models.CharField(max_length=10, blank=True, null=True)

    # Admin Confirmation Flags
    is_paid = models.BooleanField(default=False, help_text="Tick this after verifying bKash/Card payment to confirm order")
    order_status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='pending_payment')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name} ({self.get_order_status_display()})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity}x {self.product_name} (Order #{self.order.id})"
