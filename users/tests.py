import tempfile
from unittest.mock import patch

from django.core import mail
from django.core.mail.message import BadHeaderError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import SellerApplication


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    EMAIL_HOST_USER='sender@example.com',
    EMAIL_HOST_PASSWORD='test-password',
    DEFAULT_FROM_EMAIL='sender@example.com',
    SELLER_APPLICATION_NOTIFICATION_EMAIL='arfantaahakuet@gmail.com',
)
class SellerRegistrationEmailTests(TestCase):
    def setUp(self):
        self.media_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.media_directory.cleanup)
        media_settings = override_settings(MEDIA_ROOT=self.media_directory.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)

    def _registration_data(self):
        return {
            'full_name': 'Test Seller',
            'phone_number': '01712345678',
            'gmail': 'seller@example.com',
            'address': '12 Test Road',
            'stockhouse_address': 'Warehouse Road',
            'nid_pdf': SimpleUploadedFile(
                'nid.pdf',
                b'test nid document',
                content_type='application/pdf',
            ),
            'trade_license': SimpleUploadedFile(
                'license.pdf',
                b'test trade license',
                content_type='application/pdf',
            ),
        }

    def test_registration_emails_application_details_and_documents(self):
        response = self.client.post(reverse('register'), self._registration_data())

        self.assertEqual(response.status_code, 302)
        self.assertEqual(SellerApplication.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

        notification = mail.outbox[0]
        self.assertEqual(notification.to, ['arfantaahakuet@gmail.com'])
        self.assertIn('Test Seller', notification.body)
        self.assertIn('seller@example.com', notification.body)
        self.assertIn('Warehouse Road', notification.body)
        self.assertEqual(
            {filename: content for filename, content, _ in notification.attachments},
            {
                'nid.pdf': b'test nid document',
                'license.pdf': b'test trade license',
            },
        )

    @patch('users.views._send_seller_application_notification', side_effect=BadHeaderError)
    def test_application_is_saved_and_email_failure_is_reported(self, send_email):
        response = self.client.post(
            reverse('register'),
            self._registration_data(),
            follow=True,
        )

        self.assertEqual(SellerApplication.objects.count(), 1)
        self.assertTrue(
            any('notification email could not be sent' in str(message) for message in response.context['messages'])
        )
