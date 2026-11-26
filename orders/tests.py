from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from store.models import Product
from users.models import CustomerProfile
from .models import Order


class CheckoutCustomerProfileTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name='Test product',
            price=Decimal('12.50'),
            in_stock=True,
        )
        session = self.client.session
        session['cart'] = {str(self.product.pk): 2}
        session.save()

    def test_checkout_saves_and_updates_customer_profile_by_email(self):
        existing_profile = CustomerProfile.objects.create(
            full_name='Old Name',
            address='Old Address',
            email='buyer@example.com',
            wallet_number='01000000000',
        )

        response = self.client.post(
            reverse('confirm_order'),
            {
                'customer_name': 'Updated Name',
                'customer_email': 'BUYER@example.com',
                'customer_phone': '01711111111',
                'delivery_address': 'New Address',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(CustomerProfile.objects.count(), 1)
        existing_profile.refresh_from_db()
        self.assertEqual(existing_profile.full_name, 'Updated Name')
        self.assertEqual(existing_profile.address, 'New Address')
        self.assertEqual(existing_profile.wallet_number, '01711111111')

        order = Order.objects.get()
        self.assertEqual(order.customer_email, 'buyer@example.com')
        self.assertEqual(order.customer_name, 'Updated Name')
        self.assertEqual(self.client.session['customer_email'], 'buyer@example.com')
