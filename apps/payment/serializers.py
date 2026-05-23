"""
Serializers for payments app.
"""
from rest_framework import serializers

<<<<<<< HEAD
from kiro.models import Booking, User
from kiro.serializers import BookingSerializer, UserSerializer
=======
from apps.bookings.models import Booking
from kiro.models import User
from apps.bookings.serializers import BookingSerializer
from kiro.serializers import UserSerializer
>>>>>>> e13cee5 (update)


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for Payment model.
    """

    booking = BookingSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    total_amount = serializers.SerializerMethodField()

    def get_total_amount(self, obj):
        """Compute total payment amount including commission."""
        return obj.amount + obj.commission_amount

    class Meta:
        model = 'apps.payment.Payment'
        fields = "__all__"