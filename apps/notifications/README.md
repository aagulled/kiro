# Kirokiro Notification System

A scalable and production-ready notification preference system for the Kirokiro property rental platform.

## Overview

This notification system provides comprehensive user notification management with support for multiple channels (Email, SMS, Push, In-App, WhatsApp), user preferences, and automated notifications triggered by platform events.

## Architecture

### Components

1. **Models**: `NotificationPreference` and `Notification` for data persistence
2. **Service Layer**: `NotificationService` for business logic and channel routing
3. **Signals**: Automatic notification triggers for platform events
4. **Celery Tasks**: Asynchronous notification delivery
5. **DRF API**: RESTful endpoints for preference management and notification access
6. **Admin Interface**: Django admin integration for system management

### Key Features

- **Multi-Channel Support**: Email, SMS, Push, In-App, and WhatsApp notifications
- **User Preferences**: Granular control over notification channels and frequency
- **Asynchronous Delivery**: Celery-based background processing for reliability
- **Extensible Design**: Easy addition of new notification types and channels
- **Admin Management**: Comprehensive Django admin interface
- **REST API**: Full CRUD operations via DRF
- **Automated Triggers**: Signal-based notifications for platform events

## Models

### NotificationPreference

Stores user notification preferences with the following fields:
- `user`: OneToOneField to User
- `email_notifications`: Boolean
- `sms_notifications`: Boolean
- `push_notifications`: Boolean
- `in_app_notifications`: Boolean
- `notification_frequency`: Choice field ('instant', 'daily', 'weekly')

### Notification

Stores individual notifications with the following fields:
- `user`: ForeignKey to User
- `title`: CharField
- `message`: TextField
- `notification_type`: Choice field
- `channel`: Choice field
- `is_read`: Boolean
- `delivered`: Boolean
- `priority`: Choice field
- Timestamps and delivery tracking

## API Endpoints

### Preferences Management
- `GET /api/v1/notifications/preferences/` - Get user preferences
- `PUT /api/v1/notifications/preferences/` - Update user preferences

### Notification Management
- `GET /api/v1/notifications/` - List user notifications
- `POST /api/v1/notifications/{id}/mark_as_read/` - Mark single notification as read
- `POST /api/v1/notifications/mark_bulk_as_read/` - Mark multiple notifications as read
- `POST /api/v1/notifications/mark_all_as_read/` - Mark all notifications as read
- `GET /api/v1/notifications/unread_count/` - Get unread count
- `DELETE /api/v1/notifications/bulk_delete/` - Delete multiple notifications
- `DELETE /api/v1/notifications/delete_read/` - Delete all read notifications

## Usage Examples

### Sending Notifications

```python
from apps.notifications.services.notifications import NotificationService

# Send a simple notification
notifications = NotificationService.send_notification(
    user=user,
    title="Welcome!",
    message="Welcome to Kirokiro!",
    notification_type="system",
    channels=["email", "in_app"],
    priority="medium"
)

# Send notification with custom metadata
notifications = NotificationService.send_notification(
    user=user,
    title="Booking Confirmed",
    message="Your booking has been confirmed.",
    notification_type="booking",
    channels=["email", "sms", "push"],
    priority="high",
    metadata={"booking_id": booking.id},
    content_object=booking
)
```

### Managing User Preferences

```python
from apps.notifications.services.notifications import NotificationService

# Get user preferences
preferences = NotificationService.get_user_preferences(user)

# Update preferences
NotificationService.update_user_preferences(
    user=user,
    email_notifications=True,
    sms_notifications=False,
    push_notifications=True,
    notification_frequency="daily"
)
```

### API Usage

```python
import requests

# Update notification preferences
response = requests.put('/api/v1/notifications/preferences/', {
    "email_notifications": True,
    "sms_notifications": False,
    "push_notifications": True,
    "in_app_notifications": True,
    "notification_frequency": "instant"
}, headers={'Authorization': 'Bearer <token>'})

# Get notifications
response = requests.get('/api/v1/notifications/', headers={'Authorization': 'Bearer <token>'})

# Mark notifications as read
response = requests.post('/api/v1/notifications/mark_bulk_as_read/', {
    "notification_ids": ["uuid1", "uuid2"]
}, headers={'Authorization': 'Bearer <token>'})
```

## Automated Notifications

The system automatically sends notifications for the following events:

- **User Registration**: Welcome notification
- **Account Verification**: Verification confirmation
- **Password Changes**: Security notification
- **Property Approvals**: Listing approval notifications
- **Booking Creation**: Booking requests and confirmations
- **Payment Success**: Payment confirmations

## Celery Tasks

### Available Tasks

- `send_notification_task`: Deliver individual notifications
- `send_bulk_notifications_task`: Deliver multiple notifications
- `send_digest_notifications_task`: Send daily/weekly digests
- `cleanup_old_notifications_task`: Remove old read notifications
- `retry_failed_notifications_task`: Retry failed deliveries

### Example Task Usage

```python
from apps.notifications.tasks import send_notification_task

# Send notification asynchronously
send_notification_task.delay(notification_id)

# Send bulk notifications
from apps.notifications.tasks import send_bulk_notifications_task
send_bulk_notifications_task.delay([id1, id2, id3])
```

## Extending the System

### Adding New Channels

1. Add channel choice to `Notification.CHANNEL_CHOICES`
2. Implement delivery method in `NotificationService`
3. Add channel preference field to `NotificationPreference` model
4. Create database migration

### Adding New Notification Types

1. Add type choice to `Notification.TYPE_CHOICES`
2. Update signal handlers or service calls as needed

### Custom Email Templates

Create templates in `templates/notifications/email/`:
- `notification.html`: HTML email template
- `notification.txt`: Plain text email template

## Configuration

### Settings Integration

The app is integrated in `settings.py` under `LOCAL_APPS`. Celery settings are already configured for the project.

### Email Configuration

Configure email settings in environment variables:
- `EMAIL_BACKEND`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_USE_TLS`
- `DEFAULT_FROM_EMAIL`

### SMS/Push/WhatsApp Integration

Implement the placeholder methods in `NotificationService`:
- `_send_sms_notification()`: Integrate with SMS provider (Twilio, etc.)
- `_send_push_notification()`: Integrate with push service (Firebase, etc.)
- `_send_whatsapp_notification()`: Integrate with WhatsApp Business API

## Best Practices

1. **Always use the service layer** for notification operations
2. **Prefer async delivery** for better performance
3. **Handle delivery failures** gracefully with retries
4. **Use appropriate priorities** for different notification types
5. **Keep notification content concise** and actionable
6. **Test all notification channels** in staging environment
7. **Monitor delivery rates** and failure patterns

## Security Considerations

- Users can only access their own notifications and preferences
- All API endpoints require authentication
- Sensitive data is not included in notification content
- Rate limiting is configured at the DRF level

## Performance Optimization

- Database indexes on frequently queried fields
- Asynchronous delivery prevents blocking
- Bulk operations for multiple notifications
- Efficient queryset filtering in API views
- Cached user preference lookups

## Monitoring and Logging

- Comprehensive logging in service methods
- Delivery attempt tracking
- Admin interface for monitoring
- Celery task monitoring
- Error tracking for failed deliveries

## Future Enhancements

- **Notification Templates**: Dynamic content generation
- **Scheduled Notifications**: Time-based delivery
- **Notification Analytics**: Delivery and engagement metrics
- **Multi-language Support**: Localized notifications
- **Notification Categories**: User-defined grouping
- **Advanced Preferences**: Time-based and location-based rules