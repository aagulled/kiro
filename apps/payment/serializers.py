"""
Serializers for payments app.
"""
from rest_framework import serializers

from kiro.models import Booking, User
from kiro.serializers import BookingSerializer, UserSerializer


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for Payment model.
    """

    booking = BookingSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    total_amount = serializers.SerializerMethodField()

    def get_total_amount(self, obj):
        return obj.amount + obj.commission_amount

    class Meta:
        model = 'apps.payment.Payment'
        fields = "__all__"