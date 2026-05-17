"""
Django admin configuration for activity app.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.activity.models import ActivityLog, ActivitySummary, AuditLog, SecurityEvent


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """
    Admin interface for ActivityLog model.
    """
    list_display = [
        'id', 'action_type', 'actor', 'target_type', 'target_name',
        'severity', 'status', 'created_at'
    ]
    list_filter = [
        'action_type', 'severity', 'status', 'target_type', 'created_at'
    ]
    search_fields = [
        'actor__email', 'target_name', 'description', 'target_id'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'changes_summary'
    ]
    ordering = ['-created_at']

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('id', 'action_type', 'severity', 'description')
        }),
        (_('Actor & Target'), {
            'fields': ('actor', 'target_type', 'target_id', 'target_name')
        }),
        (_('Details'), {
            'fields': ('old_values', 'new_values', 'metadata', 'status', 'error_message'),
            'classes': ('collapse',)
        }),
        (_('Audit Trail'), {
            'fields': ('audit_trail',),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        """Prevent manual creation of activity logs."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow staff to delete old activity logs."""
        if request.user.is_staff:
            return True
        return False


@admin.register(ActivitySummary)
class ActivitySummaryAdmin(admin.ModelAdmin):
    """
    Admin interface for ActivitySummary model.
    """
    list_display = [
        'date', 'period', 'total_activities', 'successful_activities',
        'failed_activities', 'admin_activities'
    ]
    list_filter = ['period', 'date']
    search_fields = ['date']
    readonly_fields = ['date', 'period']
    ordering = ['-date']

    fieldsets = (
        (_('Summary Period'), {
            'fields': ('date', 'period')
        }),
        (_('Activity Counts'), {
            'fields': (
                'total_activities', 'user_activities', 'admin_activities', 'system_activities',
                'successful_activities', 'failed_activities'
            )
        }),
        (_('Action Breakdown'), {
            'fields': ('property_actions', 'booking_actions', 'payment_actions', 'user_actions')
        }),
        (_('Severity Breakdown'), {
            'fields': ('low_severity', 'medium_severity', 'high_severity', 'critical_severity')
        }),
        (_('Analytics'), {
            'fields': ('top_actors', 'top_targets'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        """Prevent manual creation of activity summaries."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow staff to manage summaries."""
        return request.user.is_staff


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Admin interface for AuditLog model.
    """
    list_display = [
        'id', 'action', 'actor', 'target_type', 'target_id',
        'requires_review', 'verified_at', 'created_at'
    ]
    list_filter = [
        'action', 'requires_review', 'verified_at', 'reviewed_at', 'created_at'
    ]
    search_fields = [
        'actor__email', 'target_id', 'justification', 'compliance_notes'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        (_('Audit Information'), {
            'fields': ('id', 'action', 'actor', 'actor_role')
        }),
        (_('Target Details'), {
            'fields': ('target_type', 'target_id', 'target_details')
        }),
        (_('Justification & Evidence'), {
            'fields': ('justification', 'evidence', 'compliance_notes'),
            'classes': ('collapse',)
        }),
        (_('Review & Verification'), {
            'fields': (
                'requires_review', 'reviewed_at', 'reviewed_by',
                'verified_at', 'verified_by', 'verification_notes'
            )
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_reviewed', 'mark_as_verified']

    def has_add_permission(self, request):
        """Prevent manual creation of audit logs."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete audit logs."""
        return request.user.is_superuser

    @admin.action(description=_('Mark selected audit logs as reviewed'))
    def mark_as_reviewed(self, request, queryset):
        """Bulk action to mark audit logs as reviewed."""
        updated = 0
        for audit_log in queryset.filter(reviewed_at__isnull=True):
            audit_log.mark_as_reviewed(request.user, "Bulk reviewed via admin")
            updated += 1

        self.message_user(
            request,
            ngettext(
                '%d audit log was successfully marked as reviewed.',
                '%d audit logs were successfully marked as reviewed.',
                updated,
            ) % updated,
        )

    @admin.action(description=_('Mark selected audit logs as verified'))
    def mark_as_verified(self, request, queryset):
        """Bulk action to mark audit logs as verified."""
        updated = 0
        for audit_log in queryset.filter(verified_at__isnull=True):
            audit_log.verify_action(request.user, "Bulk verified via admin")
            updated += 1

        self.message_user(
            request,
            ngettext(
                '%d audit log was successfully marked as verified.',
                '%d audit logs were successfully marked as verified.',
                updated,
            ) % updated,
        )


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    """
    Admin interface for SecurityEvent model.
    """
    list_display = [
        'id', 'event_type', 'risk_level', 'affected_user',
        'ip_address', 'threat_score', 'blocked', 'created_at'
    ]
    list_filter = [
        'event_type', 'risk_level', 'blocked', 'alerted', 'created_at'
    ]
    search_fields = [
        'affected_user__email', 'ip_address', 'location', 'url'
    ]
    readonly_fields = [
        'id', 'threat_score', 'created_at', 'updated_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        (_('Event Information'), {
            'fields': ('id', 'event_type', 'risk_level', 'threat_score')
        }),
        (_('User & Context'), {
            'fields': ('affected_user', 'ip_address', 'user_agent', 'location', 'device_info')
        }),
        (_('Request Details'), {
            'fields': ('url', 'http_method', 'request_data', 'response_status'),
            'classes': ('collapse',)
        }),
        (_('Response & Analysis'), {
            'fields': ('blocked', 'alerted', 'alert_level', 'is_false_positive', 'analysis_notes')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_false_positive', 'block_ip']

    def has_add_permission(self, request):
        """Prevent manual creation of security events."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Only staff can delete security events."""
        return request.user.is_staff

    @admin.action(description=_('Mark selected events as false positives'))
    def mark_as_false_positive(self, request, queryset):
        """Bulk action to mark security events as false positives."""
        updated = queryset.update(
            is_false_positive=True,
            analysis_notes="Marked as false positive via admin bulk action"
        )

        self.message_user(
            request,
            ngettext(
                '%d security event was marked as false positive.',
                '%d security events were marked as false positives.',
                updated,
            ) % updated,
        )

    @admin.action(description=_('Block selected IPs'))
    def block_ip(self, request, queryset):
        """Bulk action to block IPs (would integrate with firewall)."""
        ips = list(queryset.values_list('ip_address', flat=True).distinct())

        # TODO: Integrate with firewall/blocking system
        # For now, just mark as blocked in our system
        updated = queryset.filter(blocked=False).update(
            blocked=True,
            analysis_notes="IP blocked via admin bulk action"
        )

        self.message_user(
            request,
            ngettext(
                '%d IP was blocked.',
                '%d IPs were blocked.',
                len(ips),
            ) % len(ips),
        )