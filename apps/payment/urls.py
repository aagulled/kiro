"""
URL configuration for payments app.
"""
from django.urls import path

from . import views

urlpatterns = [
    # Payments
    path("", views.PaymentListView.as_view(), name="payment-list"),
    path("<uuid:id>/", views.PaymentDetailView.as_view(), name="payment-detail"),
]