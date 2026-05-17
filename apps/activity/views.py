"""
Activity logging API views and serializers.
"""
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import datetime, timedelta

from apps.activity.models import ActivityLog, AuditLog, SecurityEvent
from apps.activity.services.activity import ActivityService


class ActivityLogSerializer(serializers.ModelSerializer):
    """Serializer for activity logs."""

    actor_name = serializers.CharField(source='actor.full_name', read_only=True)
    changes_summary = serializers.ReadOnlyField()

    class Meta:
        model = ActivityLog
        fields = [
            'id', 'action_type', 'severity', 'actor', 'actor_name',
            'target_type', 'target_id', 'target_name', 'description',
            'old_values', 'new_values', 'changes_summary', 'metadata',
            'status', 'error_message', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'changes_summary']


class ActivityFeedSerializer(serializers.Serializer):
    """Serializer for activity feed parameters."""

    user_id = serializers.IntegerField(required=False)
    target_type = serializers.CharField(required=False, allow_blank=True)
    target_id = serializers.CharField(required=False, allow_blank=True)
    action_types = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )
    severity_levels = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=100, default=50)


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for audit logs."""

    actor_name = serializers.CharField(source='actor.full_name', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.full_name', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.full_name', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'action', 'actor', 'actor_name', 'actor_role',
            'target_type', 'target_id', 'target_details',
            'justification', 'evidence', 'compliance_notes',
            'verified_by', 'verified_by_name', 'verified_at', 'verification_notes',
            'requires_review', 'reviewed_at', 'reviewed_by', 'reviewed_by_name',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class SecurityEventSerializer(serializers.ModelSerializer):
    """Serializer for security events."""

    affected_user_name = serializers.CharField(source='affected_user.full_name', read_only=True)

    class Meta:
        model = SecurityEvent
        fields = [
            'id', 'event_type', 'risk_level', 'affected_user', 'affected_user_name',
            'ip_address', 'user_agent', 'location', 'device_info',
            'url', 'http_method', 'request_data', 'response_status',
            'threat_score', 'is_false_positive', 'analysis_notes',
            'blocked', 'alerted', 'alert_level', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'threat_score']


class ActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing activity logs.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ActivityLogSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['action_type', 'severity', 'status', 'actor', 'target_type']

    def get_queryset(self):
        """Return activity logs based on user permissions."""
        if self.request.user.is_staff:
            return ActivityLog.objects.all()
        return ActivityLog.objects.filter(actor=self.request.user)

    @action(detail=False, methods=['get'])
    def feed(self, request):
        """Get filtered activity feed."""
        serializer = ActivityFeedSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        params = serializer.validated_data

        # Permission check - only staff can see other users' activities
        if params.get('user_id') and not request.user.is_staff:
            if params['user_id'] != request.user.id:
                return Response(
                    {'error': _('You can only view your own activities.')},
                    status=status.HTTP_403_FORBIDDEN
                )

        activities = ActivityService.get_activity_feed(**params)

        # Serialize activities
        activity_serializer = ActivityLogSerializer(activities, many=True)
        return Response({
            'activities': activity_serializer.data,
            'count': len(activities)
        })

    @action(detail=False, methods=['get'])
    def user_summary(self, request):
        """Get activity summary for current user."""
        days = int(request.query_params.get('days', 30))
        summary = ActivityService.get_user_activity_summary(request.user, days)
        return Response(summary)

    @action(detail=True, methods=['get'])
    def audit_trail(self, request, pk=None):
        """Get complete audit trail for an activity."""
        try:
            activity = self.get_object()
        except ActivityLog.DoesNotExist:
            return Response(
                {'error': _('Activity not found.')},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get audit trail
        audit_trail = ActivityService.get_audit_trail(
            activity.target_type,
            activity.target_id
        )

        # Serialize audit trail
        serializer = ActivityLogSerializer(audit_trail, many=True)
        return Response({
            'original_activity': ActivityLogSerializer(activity).data,
            'audit_trail': serializer.data,
            'count': len(audit_trail)
        })


class AuditViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing audit logs.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = AuditLogSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['action', 'actor', 'requires_review', 'verified_by']

    def get_queryset(self):
        """Only staff can view audit logs."""
        if not self.request.user.is_staff:
            return AuditLog.objects.none()
        return AuditLog.objects.all()

    @action(detail=True, methods=['post'])
    def mark_reviewed(self, request, pk=None):
        """Mark audit log as reviewed."""
        if not request.user.is_staff:
            return Response(
                {'error': _('Only staff can review audit logs.')},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            audit_log = self.get_object()
        except AuditLog.DoesNotExist:
            return Response(
                {'error': _('Audit log not found.')},
                status=status.HTTP_404_NOT_FOUND
            )

        notes = request.data.get('notes', '')
        audit_log.mark_as_reviewed(request.user, notes)

        serializer = self.get_serializer(audit_log)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify audit log action."""
        if not request.user.is_staff:
            return Response(
                {'error': _('Only staff can verify audit logs.')},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            audit_log = self.get_object()
        except AuditLog.DoesNotExist:
            return Response(
                {'error': _('Audit log not found.')},
                status=status.HTTP_404_NOT_FOUND
            )

        notes = request.data.get('notes', '')
        audit_log.verify_action(request.user, notes)

        serializer = self.get_serializer(audit_log)
        return Response(serializer.data)


class SecurityEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing security events.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SecurityEventSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['event_type', 'risk_level', 'affected_user', 'blocked']

    def get_queryset(self):
        """Only staff can view security events."""
        if not self.request.user.is_staff:
            return SecurityEvent.objects.none()
        return SecurityEvent.objects.all()

    @action(detail=True, methods=['post'])
    def mark_false_positive(self, request, pk=None):
        """Mark security event as false positive."""
        if not request.user.is_staff:
            return Response(
                {'error': _('Only staff can modify security events.')},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            security_event = self.get_object()
        except SecurityEvent.DoesNotExist:
            return Response(
                {'error': _('Security event not found.')},
                status=status.HTTP_404_NOT_FOUND
            )

        notes = request.data.get('notes', '')
        security_event.is_false_positive = True
        security_event.analysis_notes = notes
        security_event.save()

        serializer = self.get_serializer(security_event)
        return Response(serializer.data)