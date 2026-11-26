from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'seller_name', 'seller_user_id', 'price', 'in_stock', 'created_at')
    list_filter = ('in_stock', 'created_at')
    search_fields = ('name', 'seller_name', 'seller_user_id')
