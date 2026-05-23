"""
ViewSets for the bookings app.
"""
from django.db import models
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated

from kiro.permissions import IsBookingParticipant

from .models import Booking
from .serializers import BookingSerializer


class BookingViewSet(viewsets.ModelViewSet):
    """ViewSet for Booking model."""

    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated, IsBookingParticipant]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["status", "payment_status"]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Booking.objects.all()
        return Booking.objects.filter(
            models.Q(guest=user) | models.Q(property__owner=user)
        )
