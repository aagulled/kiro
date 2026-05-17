"""
Django admin configuration for notifications.
"""
from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _, ngettext
from django.db.models import Q

from apps.notifications.models import Notification, NotificationPreference


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """
    Admin interface for NotificationPreference model.
    """
    list_display = [
        'user',
        'email_notifications',
        'sms_notifications',
        'push_notifications',
        'in_app_notifications',
        'notification_frequency',
        'created_at',
        'updated_at',
    ]
    list_filter = [
        'email_notifications',
        'sms_notifications',
        'push_notifications',
        'in_app_notifications',
        'notification_frequency',
        'created_at',
        'updated_at',
    ]
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        (_('User'), {
            'fields': ('user',)
        }),
        (_('Channel Preferences'), {
            'fields': (
                'email_notifications',
                'sms_notifications',
                'push_notifications',
                'in_app_notifications',
            )
        }),
        (_('Settings'), {
            'fields': ('notification_frequency',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin interface for Notification model.
    """
    list_display = [
        'id',
        'user',
        'title',
        'notification_type',
        'channel',
        'is_read',
        'priority',
        'delivered',
        'created_at',
    ]
    list_filter = [
        'notification_type',
        'channel',
        'is_read',
        'priority',
        'delivered',
        'created_at',
        'sent_at',
    ]
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'title', 'message']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'read_at', 'sent_at',
        'delivered', 'delivery_attempts', 'last_delivery_attempt', 'delivery_error'
    ]
    ordering = ['-created_at']
    actions = ['mark_as_read', 'mark_as_unread', 'resend_notifications']

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('id', 'user', 'title', 'message')
        }),
        (_('Notification Details'), {
            'fields': ('notification_type', 'channel', 'priority', 'metadata')
        }),
        (_('Status'), {
            'fields': ('is_read', 'read_at', 'delivered', 'sent_at')
        }),
        (_('Delivery Information'), {
            'fields': ('delivery_attempts', 'last_delivery_attempt', 'delivery_error'),
            'classes': ('collapse',)
        }),
        (_('Related Object'), {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """
        Optimize queryset for admin list view.
        """
        return super().get_queryset(request).select_related('user')

    @admin.action(description=_('Mark selected notifications as read'))
    def mark_as_read(self, request, queryset):
        """
        Bulk action to mark notifications as read.
        """
        updated = queryset.filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        self.message_user(
            request,
            ngettext(
                '%d notification was successfully marked as read.',
                '%d notifications were successfully marked as read.',
                updated,
            ) % updated,
        )

    @admin.action(description=_('Mark selected notifications as unread'))
    def mark_as_unread(self, request, queryset):
        """
        Bulk action to mark notifications as unread.
        """
        updated = queryset.filter(is_read=True).update(
            is_read=False,
            read_at=None
        )
        self.message_user(
            request,
            ngettext(
                '%d notification was successfully marked as unread.',
                '%d notifications were successfully marked as unread.',
                updated,
            ) % updated,
        )

    @admin.action(description=_('Resend selected notifications'))
    def resend_notifications(self, request, queryset):
        """
        Bulk action to resend notifications.
        """
        from apps.notifications.tasks import send_bulk_notifications_task

        notification_ids = list(queryset.values_list('id', flat=True))
        if notification_ids:
            send_bulk_notifications_task.delay(notification_ids)
            self.message_user(
                request,
                ngettext(
                    'Resending %d notification.',
                    'Resending %d notifications.',
                    len(notification_ids),
                ) % len(notification_ids),
            )
        else:
            self.message_user(request, _('No notifications selected.'))