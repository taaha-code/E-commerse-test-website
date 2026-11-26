from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('register/check-status/', views.check_verification_status, name='check_verification_status'),
    path('register/activate/', views.activate_seller, name='activate_seller'),
]
