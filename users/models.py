
from django.db import models


class CustomerProfile(models.Model):
    full_name = models.CharField(max_length=150)
    address = models.TextField()
    email = models.EmailField(unique=True)
    wallet_number = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.email})"


class SellerApplication(models.Model):
    full_name = models.CharField(max_length=150)
    address = models.TextField()
    phone_number = models.CharField(max_length=20)
    nid_pdf = models.FileField(upload_to='seller_docs/nid/')
    trade_license = models.FileField(upload_to='seller_docs/licenses/')
    gmail = models.EmailField(unique=True)
    stockhouse_address = models.TextField()

    # Admin manual approval & assigned keys
    is_verified = models.BooleanField(default=False)
    user_id = models.CharField(max_length=100, unique=True, blank=True, null=True, help_text="Assign User ID & send to seller's Gmail")
    business_key = models.CharField(max_length=100, blank=True, null=True, help_text="Assign Business Key & send to seller's Gmail")

    # Seller sets their own passkey after admin verifies
    passkey = models.CharField(max_length=255, blank=True, null=True)
    is_activated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "Verified" if self.is_verified else "Pending"
        return f"{self.full_name} ({self.gmail}) - {status}"
