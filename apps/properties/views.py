"""
Views for properties app.
"""
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.pagination import StandardPagination
from apps.core.permissions import CanManageProperty, IsOwnerOrReadOnly, IsTenantHost, IsTenantStaff

from .models import Amenity, Favorite, Property, PropertyStatus
from .serializers import (
    AmenitySerializer,
    FavoriteSerializer,
    PropertyCreateUpdateSerializer,
    PropertyDetailSerializer,
    PropertyListSerializer,
)


class PropertyListView(generics.ListAPIView):
    """
    List all active properties.
    """

    queryset = Property.objects.active().with_related()
    serializer_class = PropertyListSerializer
    pagination_class = StandardPagination
    throttle_scope = "property_list"
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        "category",
        "listing_type",
        "city",
        "state",
        "country",
        "bedrooms",
        "bathrooms",
    ]
    search_fields = ["title", "description", "address", "city"]
    ordering_fields = ["created_at", "sale_price", "rent_price", "view_count"]
    ordering = ["-created_at"]

    def get_permissions(self):
        """Return appropriate permissions based on HTTP method."""
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), IsTenantHost()]


class PropertyDetailView(generics.RetrieveAPIView):
    """
    Retrieve a property.
    """

    queryset = Property.objects.filter(is_deleted=False)
    serializer_class = PropertyDetailSerializer
    lookup_field = "slug"
    permission_classes = [AllowAny]

    def get_object(self):
        obj = super().get_object()
        # Increment view count
        obj.increment_view_count()
        return obj


class PropertyCreateView(generics.CreateAPIView):
    """
    Create a new property.
    """

    queryset = Property.objects.all()
    serializer_class = PropertyCreateUpdateSerializer
    permission_classes = [IsAuthenticated, IsTenantHost]
    throttle_scope = "property_create"

    def perform_create(self, serializer):
        serializer.save(
            owner=self.request.user,
            created_by=self.request.user,
        )


class PropertyUpdateView(generics.UpdateAPIView):
    """
    Update a property.
    """

    queryset = Property.objects.filter(is_deleted=False)
    serializer_class = PropertyCreateUpdateSerializer
    permission_classes = [IsAuthenticated, CanManageProperty]
    lookup_field = "slug"

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class PropertyDeleteView(generics.DestroyAPIView):
    """
    Delete a property (soft delete).
    """

    queryset = Property.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated, CanManageProperty]
    lookup_field = "slug"

    def perform_destroy(self, instance):
        instance.soft_delete(user=self.request.user)


class MyPropertiesView(generics.ListAPIView):
    """
    List properties owned by current user.
    """

    serializer_class = PropertyListSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Property.objects.by_owner(self.request.user).with_related()


class AmenityListView(generics.ListAPIView):
    """
    List all amenities.
    """

    queryset = Amenity.objects.all()
    serializer_class = AmenitySerializer
    permission_classes = [AllowAny]


class FavoriteListView(generics.ListAPIView):
    """
    List user's favorite properties.
    """

    serializer_class = FavoriteSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)


class FavoriteToggleView(APIView):
    """
    Toggle favorite status for a property.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, property_id):
        try:
            property_obj = Property.objects.get(id=property_id)
            favorite, created = Favorite.objects.get_or_create(
                user=request.user, property=property_obj
            )
            if not created:
                favorite.delete()
                property_obj.favorite_count = max(0, property_obj.favorite_count - 1)
                property_obj.save(update_fields=["favorite_count"])
                return Response(
                    {"status": "removed", "favorite_count": property_obj.favorite_count}
                )
            else:
                property_obj.favorite_count += 1
                property_obj.save(update_fields=["favorite_count"])
                return Response(
                    {"status": "added", "favorite_count": property_obj.favorite_count},
                    status=status.HTTP_201_CREATED,
                )
        except Property.DoesNotExist:
            return Response(
                {"error": "Property not found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class PropertyApprovalView(APIView):
    """
    Approve or reject a property (staff only).
    """

    permission_classes = [IsAuthenticated, IsTenantStaff]

    def post(self, request, slug):
        try:
            property_obj = Property.objects.get(slug=slug, is_deleted=False)
            action = request.data.get("action")
            
            if action == "approve":
                property_obj.status = PropertyStatus.ACTIVE
            elif action == "reject":
                property_obj.status = PropertyStatus.REJECTED
            else:
                return Response(
                    {"error": "Invalid action. Use 'approve' or 'reject'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            property_obj.save(update_fields=["status"])
            return Response(
                {"status": "success", "property_status": property_obj.status}
            )
        except Property.DoesNotExist:
            return Response(
                {"error": "Property not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
