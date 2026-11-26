from django.urls import path
from . import views

urlpatterns = [
    path('confirm/', views.confirm_order, name='confirm_order'),
    path('payment/<int:order_id>/', views.process_payment, name='process_payment'),
    path('success/<int:order_id>/', views.order_success, name='order_success'),
    path('check-status/<int:order_id>/', views.check_order_status, name='check_order_status'),
]
