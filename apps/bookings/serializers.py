"""
Serializers for bookings app.
"""
from rest_framework import serializers

from kiro.serializers import PropertySerializer, UserSerializer

from .models import Booking


class BookingSerializer(serializers.ModelSerializer):
    """Serializer for Booking model."""

    property = PropertySerializer(read_only=True)
    guest = UserSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = "__all__"
