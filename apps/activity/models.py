"""
Activity logging models for Kirokiro property platform.
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from apps.core.mixins import TimestampMixin


class ActivityLog(TimestampMixin, models.Model):
    """
    Immutable log of user/system actions with rich metadata.

    Stores action_type, actor, target, diffs and severity.
    Used for audit trail and analytics.
    """

    ACTION_TYPES = [
        # User actions
        ('login', _('User Login')),
        ('logout', _('User Logout')),
        ('register', _('User Registration')),
        ('password_change', _('Password Change')),
        ('profile_update', _('Profile Update')),

        # Property actions
        ('property_create', _('Property Created')),
        ('property_update', _('Property Updated')),
        ('property_delete', _('Property Deleted')),
        ('property_publish', _('Property Published')),
        ('property_unpublish', _('Property Unpublished')),
        ('property_view', _('Property Viewed')),
        ('property_inquiry', _('Property Inquiry')),
        ('property_favorite', _('Property Favorited')),
        ('property_review', _('Property Reviewed')),

        # Booking actions
        ('booking_create', _('Booking Created')),
        ('booking_update', _('Booking Updated')),
        ('booking_cancel', _('Booking Cancelled')),
        ('booking_confirm', _('Booking Confirmed')),
        ('booking_check_in', _('Check In')),
        ('booking_check_out', _('Check Out')),
        ('payment_process', _('Payment Processed')),
        ('payment_refund', _('Payment Refunded')),

        # Admin actions
        ('admin_login', _('Admin Login')),
        ('admin_action', _('Admin Action')),
        ('moderation_action', _('Moderation Action')),
        ('system_maintenance', _('System Maintenance')),

        # System events
        ('system_error', _('System Error')),
        ('system_warning', _('System Warning')),
        ('api_call', _('API Call')),
        ('file_upload', _('File Upload')),
        ('email_sent', _('Email Sent')),
        ('notification_sent', _('Notification Sent')),
    ]

    SEVERITY_LEVELS = [
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('critical', _('Critical')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_LEVELS,
        default='low'
    )

    # Actor information
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities'
    )
    actor_ip = models.GenericIPAddressField(null=True, blank=True)
    actor_user_agent = models.TextField(blank=True)
    session_id = models.CharField(max_length=255, blank=True)

    # Target information (what was acted upon)
    target_type = models.CharField(max_length=100, blank=True)  # e.g., 'property', 'booking', 'user'
    target_id = models.CharField(max_length=255, blank=True)  # ID of the target
    target_name = models.CharField(max_length=255, blank=True)  # Human-readable name

    # Related objects (generic relations)
    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)

    # Action details
    description = models.TextField(blank=True)
    old_values = models.JSONField(default=dict, blank=True)  # Previous state
    new_values = models.JSONField(default=dict, blank=True)  # New state
    metadata = models.JSONField(default=dict, blank=True)  # Additional context

    # Status and outcome
    status = models.CharField(
        max_length=20,
        choices=[
            ('success', _('Success')),
            ('failure', _('Failure')),
            ('pending', _('Pending')),
            ('cancelled', _('Cancelled')),
        ],
        default='success'
    )
    error_message = models.TextField(blank=True)

    # Audit trail
    audit_trail = models.JSONField(default=list, blank=True)  # Chain of related actions

    class Meta:
        verbose_name = _("Activity Log")
        verbose_name_plural = _("Activity Logs")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['action_type', 'created_at']),
            models.Index(fields=['actor', 'created_at']),
            models.Index(fields=['target_type', 'target_id']),
            models.Index(fields=['severity']),
            models.Index(fields=['status']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        """Return concise activity representation: actor-action-target."""
        actor_name = self.actor.email if self.actor else 'System'
        return f"{actor_name} - {self.action_type} - {self.target_name or self.target_id}"

    def add_to_audit_trail(self, activity_log):
        """Append related ActivityLog entry to this instance's trail JSON."""
        if isinstance(activity_log, ActivityLog):
            trail_entry = {
                'id': str(activity_log.id),
                'action_type': activity_log.action_type,
                'timestamp': activity_log.created_at.isoformat(),
                'actor': activity_log.actor.email if activity_log.actor else 'System',
            }
            self.audit_trail.append(trail_entry)
            self.save(update_fields=['audit_trail'])

    @property
    def changes_summary(self):
        """Get a summary of changes made."""
        changes = {}
        for key in set(self.old_values.keys()) | set(self.new_values.keys()):
            old_val = self.old_values.get(key)
            new_val = self.new_values.get(key)
            if old_val != new_val:
                changes[key] = {
                    'from': old_val,
                    'to': new_val
                }
        return changes


class ActivitySummary(models.Model):
    """
    Daily/weekly summary of activities for reporting.
    """

    date = models.DateField(unique=True)
    period = models.CharField(max_length=20, default='daily')  # daily, weekly, monthly

    # Activity counts by type
    total_activities = models.PositiveIntegerField(default=0)
    user_activities = models.PositiveIntegerField(default=0)
    admin_activities = models.PositiveIntegerField(default=0)
    system_activities = models.PositiveIntegerField(default=0)

    # Breakdown by action type
    property_actions = models.PositiveIntegerField(default=0)
    booking_actions = models.PositiveIntegerField(default=0)
    payment_actions = models.PositiveIntegerField(default=0)
    user_actions = models.PositiveIntegerField(default=0)

    # Status breakdown
    successful_activities = models.PositiveIntegerField(default=0)
    failed_activities = models.PositiveIntegerField(default=0)

    # Severity breakdown
    low_severity = models.PositiveIntegerField(default=0)
    medium_severity = models.PositiveIntegerField(default=0)
    high_severity = models.PositiveIntegerField(default=0)
    critical_severity = models.PositiveIntegerField(default=0)

    # Top actors and targets
    top_actors = models.JSONField(default=dict, blank=True)
    top_targets = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("Activity Summary")
        verbose_name_plural = _("Activity Summaries")
        ordering = ['-date']
        unique_together = ['date', 'period']

    def __str__(self):
        return f"Activity Summary - {self.date} ({self.period})"


class AuditLog(TimestampMixin, models.Model):
    """
    Critical audit log for compliance and security.
    """

    CRITICAL_ACTIONS = [
        ('data_export', _('Data Export')),
        ('bulk_delete', _('Bulk Delete')),
        ('permission_change', _('Permission Change')),
        ('system_config_change', _('System Configuration Change')),
        ('sensitive_data_access', _('Sensitive Data Access')),
        ('account_deactivation', _('Account Deactivation')),
        ('payment_manipulation', _('Payment Manipulation')),
        ('content_moderation', _('Content Moderation')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.CharField(max_length=50, choices=CRITICAL_ACTIONS)

    # Actor information (required for audit)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,  # Don't allow deletion of users with audit logs
        related_name='audit_logs'
    )
    actor_role = models.CharField(max_length=50)  # Store role at time of action

    # Target information
    target_type = models.CharField(max_length=100)
    target_id = models.CharField(max_length=255)
    target_details = models.JSONField(default=dict, blank=True)

    # Action details
    justification = models.TextField(blank=True)  # Why was this action taken?
    evidence = models.JSONField(default=dict, blank=True)  # Supporting evidence
    compliance_notes = models.TextField(blank=True)  # Compliance-related notes

    # Verification
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verifications'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True)

    # Compliance flags
    requires_review = models.BooleanField(default=False)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_reviews'
    )

    class Meta:
        verbose_name = _("Audit Log")
        verbose_name_plural = _("Audit Logs")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['actor', 'created_at']),
            models.Index(fields=['requires_review']),
            models.Index(fields=['verified_at']),
        ]

    def __str__(self):
        return f"AUDIT: {self.actor.email} - {self.action} - {self.target_type}:{self.target_id}"

    def mark_as_reviewed(self, reviewer, notes=''):
        """Mark audit log as reviewed."""
        from django.utils import timezone
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewer
        self.requires_review = False
        if notes:
            self.verification_notes = notes
        self.save()

    def verify_action(self, verifier, notes=''):
        """Verify the audit log action."""
        from django.utils import timezone
        self.verified_at = timezone.now()
        self.verified_by = verifier
        if notes:
            self.verification_notes = notes
        self.save()


class SecurityEvent(TimestampMixin, models.Model):
    """
    Security-related events that require monitoring.
    """

    EVENT_TYPES = [
        ('failed_login', _('Failed Login')),
        ('suspicious_activity', _('Suspicious Activity')),
        ('unauthorized_access', _('Unauthorized Access')),
        ('data_breach_attempt', _('Data Breach Attempt')),
        ('rate_limit_exceeded', _('Rate Limit Exceeded')),
        ('sql_injection_attempt', _('SQL Injection Attempt')),
        ('xss_attempt', _('XSS Attempt')),
        ('brute_force_attempt', _('Brute Force Attempt')),
        ('unusual_login_location', _('Unusual Login Location')),
        ('account_lockout', _('Account Lockout')),
        ('password_reset', _('Password Reset')),
        ('api_key_compromised', _('API Key Compromised')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)

    # Risk level
    risk_level = models.CharField(
        max_length=20,
        choices=[
            ('low', _('Low')),
            ('medium', _('Medium')),
            ('high', _('High')),
            ('critical', _('Critical')),
        ],
        default='medium'
    )

    # User information
    affected_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='security_events'
    )

    # Event details
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)  # Geolocation info
    device_info = models.JSONField(default=dict, blank=True)

    # Event context
    url = models.URLField(blank=True)
    http_method = models.CharField(max_length=10, blank=True)
    request_data = models.JSONField(default=dict, blank=True)
    response_status = models.IntegerField(null=True, blank=True)

    # Analysis
    threat_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="AI-calculated threat score (0-100)"
    )
    is_false_positive = models.BooleanField(default=False)
    analysis_notes = models.TextField(blank=True)

    # Response
    blocked = models.BooleanField(default=False)
    alerted = models.BooleanField(default=False)
    alert_level = models.CharField(
        max_length=20,
        choices=[
            ('none', _('None')),
            ('email', _('Email')),
            ('sms', _('SMS')),
            ('immediate', _('Immediate Action')),
        ],
        default='none'
    )

    class Meta:
        verbose_name = _("Security Event")
        verbose_name_plural = _("Security Events")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['risk_level']),
            models.Index(fields=['threat_score']),
            models.Index(fields=['blocked']),
            models.Index(fields=['ip_address']),
        ]

    def __str__(self):
        return f"SECURITY: {self.event_type} - {self.ip_address} - Risk: {self.risk_level}"