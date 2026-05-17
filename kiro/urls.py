"""
URLs for Kiro API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AmenityViewSet,
    BookingViewSet,
    ChangePasswordView,
    FavoriteViewSet,
    GroupViewSet,
    InquiryViewSet,
    MessageViewSet,
    PaymentViewSet,
    PropertyDocumentViewSet,
    PropertyImageViewSet,
    PropertyViewSet,
    RegisterView,
    ReviewViewSet,
    UserProfileViewSet,
    UserViewSet,
)

router = DefaultRouter()
router.register(r"groups", GroupViewSet)
router.register(r"users", UserViewSet)
router.register(r"user-profiles", UserProfileViewSet)
router.register(r"amenities", AmenityViewSet)
router.register(r"properties", PropertyViewSet)
router.register(r"property-images", PropertyImageViewSet)
router.register(r"property-documents", PropertyDocumentViewSet)
router.register(r"inquiries", InquiryViewSet)
router.register(r"reviews", ReviewViewSet)
router.register(r"favorites", FavoriteViewSet)
router.register(r"bookings", BookingViewSet)
router.register(r"booking-payments", PaymentViewSet)
router.register(r"messages", MessageViewSet)

urlpatterns = router.urls + [
    path("register/", RegisterView.as_view(), name="register"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    # New notification system
    path("notifications/", include("apps.notifications.urls")),
    # Search system
    path("search/", include("apps.search.urls")),
    # Analytics system
    path("analytics/", include("apps.analytics.urls")),
    # Activity logging system
    path("activity/", include("apps.activity.urls")),
]