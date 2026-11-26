from django.contrib import admin
from .models import CustomerProfile, SellerApplication


@admin.register(SellerApplication)
class SellerApplicationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'gmail', 'phone_number', 'is_verified', 'user_id', 'business_key', 'is_activated')
    list_filter = ('is_verified', 'is_activated')
    search_fields = ('full_name', 'gmail', 'user_id', 'phone_number')


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'wallet_number', 'created_at')
    search_fields = ('full_name', 'email')
