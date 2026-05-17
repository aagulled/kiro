"""
Tests for notifications app.
"""
import uuid
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from apps.notifications.models import Notification, NotificationPreference
from apps.notifications.services.notifications import NotificationService

User = get_user_model()


class NotificationPreferenceModelTest(TestCase):
    """
    Test NotificationPreference model.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_preference_creation(self):
        """Test that preferences are created for new users."""
        preference = NotificationPreference.objects.create(user=self.user)
        self.assertEqual(preference.user, self.user)
        self.assertTrue(preference.email_notifications)
        self.assertFalse(preference.sms_notifications)
        self.assertTrue(preference.push_notifications)
        self.assertTrue(preference.in_app_notifications)
        self.assertEqual(preference.notification_frequency, 'instant')

    def test_enabled_channels(self):
        """Test getting enabled channels."""
        preference = NotificationPreference.objects.create(
            user=self.user,
            email_notifications=True,
            sms_notifications=False,
            push_notifications=True,
            in_app_notifications=False
        )
        enabled = preference.get_enabled_channels()
        self.assertEqual(enabled, ['email', 'push'])

    def test_channel_enabled_check(self):
        """Test checking if specific channels are enabled."""
        preference = NotificationPreference.objects.create(
            user=self.user,
            email_notifications=True,
            sms_notifications=False
        )
        self.assertTrue(preference.is_channel_enabled('email'))
        self.assertFalse(preference.is_channel_enabled('sms'))
        self.assertFalse(preference.is_channel_enabled('invalid'))


class NotificationModelTest(TestCase):
    """
    Test Notification model.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    def test_notification_creation(self):
        """Test creating a notification."""
        notification = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='This is a test message',
            notification_type='system',
            channel='in_app'
        )
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, 'Test Notification')
        self.assertFalse(notification.is_read)
        self.assertFalse(notification.delivered)

    def test_mark_as_read(self):
        """Test marking notification as read."""
        notification = Notification.objects.create(
            user=self.user,
            title='Test',
            message='Test message'
        )
        self.assertFalse(notification.is_read)
        notification.mark_as_read()
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)

    def test_mark_as_delivered(self):
        """Test marking notification as delivered."""
        notification = Notification.objects.create(
            user=self.user,
            title='Test',
            message='Test message'
        )
        self.assertFalse(notification.delivered)
        notification.mark_as_delivered()
        self.assertTrue(notification.delivered)
        self.assertIsNotNone(notification.sent_at)


class NotificationServiceTest(TestCase):
    """
    Test NotificationService.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    def test_get_user_preferences(self):
        """Test getting user preferences."""
        preferences = NotificationService.get_user_preferences(self.user)
        self.assertEqual(preferences.user, self.user)
        self.assertTrue(preferences.email_notifications)

    def test_send_notification(self):
        """Test sending a notification."""
        notifications = NotificationService.send_notification(
            user=self.user,
            title='Test Notification',
            message='Test message',
            notification_type='system',
            channels=['in_app'],
            async_delivery=False
        )
        self.assertEqual(len(notifications), 1)
        notification = notifications[0]
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, 'Test Notification')
        self.assertTrue(notification.delivered)  # In-app notifications are always delivered

    def test_update_preferences(self):
        """Test updating user preferences."""
        preferences = NotificationService.update_user_preferences(
            user=self.user,
            email_notifications=False,
            sms_notifications=True
        )
        self.assertFalse(preferences.email_notifications)
        self.assertTrue(preferences.sms_notifications)


class NotificationAPITest(APITestCase):
    """
    Test notification API endpoints.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_get_preferences(self):
        """Test getting notification preferences."""
        response = self.client.get('/api/v1/notifications/preferences/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('email_notifications', response.data)

    def test_update_preferences(self):
        """Test updating notification preferences."""
        data = {
            'email_notifications': False,
            'sms_notifications': True
        }
        response = self.client.put('/api/v1/notifications/preferences/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['email_notifications'])
        self.assertTrue(response.data['sms_notifications'])

    def test_list_notifications(self):
        """Test listing notifications."""
        Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='Test message'
        )
        response = self.client.get('/api/v1/notifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_unread_count(self):
        """Test getting unread notification count."""
        Notification.objects.create(
            user=self.user,
            title='Unread',
            message='Test'
        )
        Notification.objects.create(
            user=self.user,
            title='Read',
            message='Test',
            is_read=True
        )
        response = self.client.get('/api/v1/notifications/unread_count/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unread_count'], 1)