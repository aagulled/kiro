"""
Views for Kiro API.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from .permissions import IsBookingParticipant, IsGuestOrReadOnly, PropertyPermissions
from django.db import models

from .models import (
    Amenity,
    Booking,
    Favorite,
    Inquiry,
    Message,
    Notification,
    Payment,
    Property,
    PropertyDocument,
    PropertyImage,
    Review,
    UserProfile,
)
from .serializers import (
    AmenitySerializer,
    BookingSerializer,
    ChangePasswordSerializer,
    FavoriteSerializer,
    GroupSerializer,
    InquirySerializer,
    MessageSerializer,
    NotificationSerializer,
    PaymentSerializer,
    PropertySerializer,
    PropertyDocumentSerializer,
    PropertyImageSerializer,
    RegisterSerializer,
    ReviewSerializer,
    UserSerializer,
    UserProfileSerializer,
)

User = get_user_model()


class GroupViewSet(viewsets.ModelViewSet):
    """ViewSet for Group model."""

    queryset = Group.objects.prefetch_related("permissions").all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name"]



class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User model."""

    queryset = User.objects.prefetch_related("groups").all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["role", "is_verified", "groups"]
    search_fields = ["email", "first_name", "last_name"]
    ordering_fields = ["created_at", "email"]


class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for UserProfile model."""

    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]


class AmenityViewSet(viewsets.ModelViewSet):
    """ViewSet for Amenity model."""

    queryset = Amenity.objects.all()
    serializer_class = AmenitySerializer
    permission_classes = [IsGuestOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "category"]
    ordering_fields = ["name"]


class PropertyViewSet(viewsets.ModelViewSet):
    """ViewSet for Property model."""

    queryset = Property.objects.with_related()
    serializer_class = PropertySerializer
    permission_classes = [PropertyPermissions]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["category", "listing_type", "status", "city", "state", "country"]
    search_fields = ["title", "description", "address"]
    ordering_fields = ["created_at", "sale_price", "rent_price"]


class PropertyImageViewSet(viewsets.ModelViewSet):
    """ViewSet for PropertyImage model."""

    queryset = PropertyImage.objects.all()
    serializer_class = PropertyImageSerializer
    permission_classes = [IsAuthenticated]


class PropertyDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for PropertyDocument model."""

    queryset = PropertyDocument.objects.all()
    serializer_class = PropertyDocumentSerializer
    permission_classes = [IsAuthenticated]


class InquiryViewSet(viewsets.ModelViewSet):
    """ViewSet for Inquiry model."""

    queryset = Inquiry.objects.all()
    serializer_class = InquirySerializer
    permission_classes = [IsGuestOrReadOnly]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["is_read", "is_responded"]
    ordering_fields = ["created_at"]


class ReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for Review model."""

    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsGuestOrReadOnly]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["rating"]
    ordering_fields = ["created_at"]


class FavoriteViewSet(viewsets.ModelViewSet):
    """ViewSet for Favorite model."""

    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]


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


class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for Booking Payment model."""

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["status"]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Payment.objects.all()
        return Payment.objects.filter(user=user)





class MessageViewSet(viewsets.ModelViewSet):
    """ViewSet for Message model."""

    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["is_read"]
    ordering_fields = ["created_at"]


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for Notification model."""

    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["is_read", "notification_type"]
    ordering_fields = ["created_at"]


class RegisterView(generics.CreateAPIView):
    """View for user registration."""

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class ChangePasswordView(generics.UpdateAPIView):
    """View for password change."""

    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user