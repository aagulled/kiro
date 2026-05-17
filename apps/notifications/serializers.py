"""
DRF serializers for notification models.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.notifications.models import Notification, NotificationPreference


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for NotificationPreference model.
    """
    class Meta:
        model = NotificationPreference
        fields = [
            'id',
            'email_notifications',
            'sms_notifications',
            'push_notifications',
            'in_app_notifications',
            'notification_frequency',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_notification_frequency(self, value):
        """
        Validate notification frequency choices.
        """
        valid_choices = [choice[0] for choice in NotificationPreference.FREQUENCY_CHOICES]
        if value not in valid_choices:
            raise serializers.ValidationError(_("Invalid notification frequency."))
        return value


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Notification model.
    """
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id',
            'title',
            'message',
            'notification_type',
            'notification_type_display',
            'channel',
            'channel_display',
            'is_read',
            'read_at',
            'sent_at',
            'delivered',
            'delivery_attempts',
            'last_delivery_attempt',
            'delivery_error',
            'priority',
            'priority_display',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'sent_at', 'delivered', 'delivery_attempts',
            'last_delivery_attempt', 'delivery_error', 'created_at', 'updated_at'
        ]


class NotificationListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for notification lists.
    """
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id',
            'title',
            'notification_type',
            'notification_type_display',
            'channel',
            'channel_display',
            'is_read',
            'priority',
            'created_at',
        ]
        read_only_fields = fields


class MarkAsReadSerializer(serializers.Serializer):
    """
    Serializer for marking notifications as read.
    """
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
        help_text=_("List of notification IDs to mark as read")
    )

    def validate_notification_ids(self, value):
        """
        Validate that notification IDs belong to the current user.
        """
        request = self.context.get('request')
        if request and request.user:
            user_notifications = set(
                str(nid) for nid in Notification.objects.filter(
                    user=request.user
                ).values_list('id', flat=True)
            )
            invalid_ids = [str(nid) for nid in value if str(nid) not in user_notifications]
            if invalid_ids:
                raise serializers.ValidationError(
                    _("You don't have permission to modify notifications: %(ids)s") % {
                        'ids': ', '.join(invalid_ids)
                    }
                )
        return value


class BulkDeleteSerializer(serializers.Serializer):
    """
    Serializer for bulk deleting notifications.
    """
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
        help_text=_("List of notification IDs to delete")
    )

    def validate_notification_ids(self, value):
        """
        Validate that notification IDs belong to the current user.
        """
        request = self.context.get('request')
        if request and request.user:
            user_notifications = set(
                str(nid) for nid in Notification.objects.filter(
                    user=request.user
                ).values_list('id', flat=True)
            )
            invalid_ids = [str(nid) for nid in value if str(nid) not in user_notifications]
            if invalid_ids:
                raise serializers.ValidationError(
                    _("You don't have permission to delete notifications: %(ids)s") % {
                        'ids': ', '.join(invalid_ids)
                    }
                )
        return value