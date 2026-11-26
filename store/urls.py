from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('marketplace/', views.marketplace, name='marketplace'),
    path('mydokaan/', views.mydokaan, name='mydokaan'),
    path('mydokaan/add/', views.add_product, name='add_product'),
    path('mydokaan/toggle-stock/<int:product_id>/', views.toggle_stock, name='toggle_stock'),
    path('mydokaan/delete/<int:product_id>/', views.delete_product, name='delete_product'),
]
