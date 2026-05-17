"""
DRF views for notification management.
"""
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.notifications.models import Notification, NotificationPreference
from apps.notifications.serializers import (
    NotificationSerializer,
    NotificationListSerializer,
    NotificationPreferenceSerializer,
    MarkAsReadSerializer,
    BulkDeleteSerializer,
)
from apps.notifications.services.notifications import NotificationService


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing notification preferences.
    """
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return notification preferences for the current user.
        """
        return NotificationPreference.objects.filter(user=self.request.user)

    def get_object(self):
        """
        Get or create notification preferences for the current user.
        """
        obj, created = NotificationPreference.objects.get_or_create(
            user=self.request.user,
            defaults={
                'email_notifications': True,
                'sms_notifications': False,
                'push_notifications': True,
                'in_app_notifications': True,
                'notification_frequency': 'instant',
            }
        )
        return obj

    def list(self, request, *args, **kwargs):
        """
        Get notification preferences for the current user.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Create notification preferences (should not be called directly).
        """
        return Response(
            {"detail": _("Use PUT or PATCH to update preferences.")},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def update(self, request, *args, **kwargs):
        """
        Update notification preferences for the current user.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    def perform_update(self, serializer):
        """
        Update preferences and log the change.
        """
        instance = serializer.save()
        NotificationService.update_user_preferences(
            user=self.request.user,
            **serializer.validated_data
        )


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing notifications.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_read', 'channel', 'notification_type', 'priority']
    search_fields = ['title', 'message']

    def get_queryset(self):
        """
        Return notifications for the current user.
        """
        return Notification.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """
        Use different serializers for list and detail views.
        """
        if self.action == 'list':
            return NotificationListSerializer
        return NotificationSerializer

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """
        Mark a single notification as read.
        """
        notification = self.get_object()
        if not notification.is_read:
            notification.mark_as_read()
            serializer = self.get_serializer(notification)
            return Response(serializer.data)
        return Response(
            {"detail": _("Notification is already marked as read.")},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['post'])
    def mark_bulk_as_read(self, request):
        """
        Mark multiple notifications as read.
        """
        serializer = MarkAsReadSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        updated_count = NotificationService.mark_notifications_as_read(
            user=request.user,
            notification_ids=serializer.validated_data['notification_ids']
        )

        return Response({
            "detail": _("Marked %(count)d notifications as read.") % {'count': updated_count}
        })

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """
        Mark all unread notifications as read for the current user.
        """
        updated_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())

        return Response({
            "detail": _("Marked %(count)d notifications as read.") % {'count': updated_count}
        })

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """
        Get the count of unread notifications.
        """
        count = NotificationService.get_unread_count(request.user)
        return Response({"unread_count": count})

    @action(detail=False, methods=['delete'])
    def bulk_delete(self, request):
        """
        Delete multiple notifications.
        """
        serializer = BulkDeleteSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        deleted_count = NotificationService.bulk_delete_notifications(
            user=request.user,
            notification_ids=serializer.validated_data['notification_ids']
        )

        return Response({
            "detail": _("Deleted %(count)d notifications.") % {'count': deleted_count}
        }, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['delete'])
    def delete_read(self, request):
        """
        Delete all read notifications for the current user.
        """
        deleted_count, _ = Notification.objects.filter(
            user=request.user,
            is_read=True
        ).delete()

        return Response({
            "detail": _("Deleted %(count)d read notifications.") % {'count': deleted_count}
        }, status=status.HTTP_204_NO_CONTENT)