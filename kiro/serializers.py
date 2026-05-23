"""
Serializers for Kiro API.
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from django.contrib.auth.models import Group

from .models import (
    Amenity,
<<<<<<< HEAD
    Booking,
=======
>>>>>>> e13cee5 (update)
    Favorite,
    Inquiry,
    Message,
    Notification,
<<<<<<< HEAD
    Payment,
=======
>>>>>>> e13cee5 (update)
    Property,
    PropertyDocument,
    PropertyImage,
    Review,
    UserProfile,
)

User = get_user_model()


class GroupSerializer(serializers.ModelSerializer):
    """Serializer for Group model."""

    class Meta:
        model = Group
        fields = ["id", "name", "permissions"]


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""

    groups = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "avatar",
            "bio",
            "role",
            "groups",
            "is_verified",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""

    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = "__all__"


class AmenitySerializer(serializers.ModelSerializer):
    """Serializer for Amenity model."""

    class Meta:
        model = Amenity
        fields = "__all__"


class PropertyImageSerializer(serializers.ModelSerializer):
    """Serializer for PropertyImage model."""

    class Meta:
        model = PropertyImage
        fields = "__all__"


class PropertyDocumentSerializer(serializers.ModelSerializer):
    """Serializer for PropertyDocument model."""

    class Meta:
        model = PropertyDocument
        fields = "__all__"


<<<<<<< HEAD
class PropertySerializer(serializers.ModelSerializer):
    """Serializer for Property model."""

    owner = UserSerializer(read_only=True)
    amenities = AmenitySerializer(many=True, read_only=True)
    images = PropertyImageSerializer(many=True, read_only=True)
    documents = PropertyDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = Property
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "category",
            "listing_type",
            "status",
            "address",
            "city",
            "state",
            "postal_code",
            "country",
            "bedrooms",
            "bathrooms",
            "total_area",
            "built_area",
            "lot_size",
            "year_built",
            "sale_price",
            "rent_price",
            "currency",
            "furnished",
            "parking_spaces",
            "pets_allowed",
            "featured_image",
            "video_url",
            "virtual_tour_url",
            "owner",
            "amenities",
            "images",
            "documents",
            "view_count",
            "inquiry_count",
            "created_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]
=======
# PropertySerializer has been moved to apps/properties/serializers.py for proper app separation.
from apps.properties.serializers import PropertySerializer as _PropertySerializer
PropertySerializer = _PropertySerializer  # re-export for backward compatibility in kiro app
>>>>>>> e13cee5 (update)


class InquirySerializer(serializers.ModelSerializer):
    """Serializer for Inquiry model."""

    property = PropertySerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Inquiry
        fields = "__all__"


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Review model."""

    property = PropertySerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Review
        fields = "__all__"


class FavoriteSerializer(serializers.ModelSerializer):
    """Serializer for Favorite model."""

    property = PropertySerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = "__all__"


<<<<<<< HEAD
class BookingSerializer(serializers.ModelSerializer):
    """Serializer for Booking model."""

    property = PropertySerializer(read_only=True)
    guest = UserSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = "__all__"


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Booking Payment model."""

    booking = BookingSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    total_amount = serializers.SerializerMethodField()

    def get_total_amount(self, obj):
        return obj.amount + obj.commission_amount

    class Meta:
        model = Payment
        fields = "__all__"




=======
# BookingSerializer has been moved to apps/bookings/serializers.py
# PaymentSerializer has been moved to apps/payment/serializers.py
>>>>>>> e13cee5 (update)

class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model."""

    sender = UserSerializer(read_only=True)
    recipient = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = "__all__"


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model."""

    user = UserSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = "__all__"


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name", "role"]
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
            "role": {
                "required": True,
                "choices": [("guest", "Guest"), ("host", "Host"), ("agent", "Agent")]
            },
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            role=validated_data["role"],
        )
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""

    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def update(self, instance, validated_data):
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance