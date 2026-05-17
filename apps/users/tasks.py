"""
Celery tasks for users app.
"""
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from apps.core.celery import app


@app.task
def send_welcome_email(user_id):
    """
    Send welcome email to new user.
    """
    from .models import User

    try:
        user = User.objects.get(id=user_id)
        subject = "Welcome to Kirokiro!"
        message = render_to_string('emails/welcome.html', {'user': user})
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=message,
        )
    except User.DoesNotExist:
        pass


@app.task
def send_password_reset_email(user_id, reset_token):
    """
    Send password reset email.
    """
    from .models import User

    try:
        user = User.objects.get(id=user_id)
        subject = "Password Reset Request"
        message = render_to_string('emails/password_reset.html', {
            'user': user,
            'reset_token': reset_token
        })
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=message,
        )
    except User.DoesNotExist:
        pass