"""
Serializers for properties app.
"""
from rest_framework import serializers

from kiro.serializers import UserSerializer

from .models import Amenity, Favorite, Property, PropertyDocument, PropertyImage


class AmenitySerializer(serializers.ModelSerializer):
    """
    Serializer for Amenity model.
    """

    class Meta:
        model = Amenity
        fields = ["id", "name", "icon", "description", "category", "created_at"]


class PropertyImageSerializer(serializers.ModelSerializer):
    """
    Serializer for PropertyImage model.
    """

    class Meta:
        model = PropertyImage
        fields = ["id", "image", "caption", "is_primary", "order", "created_at"]


class PropertyDocumentSerializer(serializers.ModelSerializer):
    """
    Serializer for PropertyDocument model.
    """

    class Meta:
        model = PropertyDocument
        fields = [
            "id",
            "document",
            "document_type",
            "title",
            "description",
            "is_public",
            "created_at",
        ]


class PropertyListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing properties (lightweight).
    """

    display_price = serializers.ReadOnlyField()
    is_available = serializers.ReadOnlyField()
    primary_image = serializers.SerializerMethodField()
    owner = UserSerializer(read_only=True)

    class Meta:
        model = Property
        fields = [
            "id",
            "title",
            "slug",
            "category",
            "listing_type",
            "status",
            "city",
            "state",
            "country",
            "bedrooms",
            "bathrooms",
            "total_area",
            "display_price",
            "currency",
            "featured_image",
            "primary_image",
            "is_available",
            "view_count",
            "favorite_count",
            "created_at",
            "owner",
        ]

    def get_primary_image(self, obj):
        """Get primary image URL."""
        primary = obj.images.filter(is_primary=True).first()
        if primary:
            return PropertyImageSerializer(primary).data
        first = obj.images.first()
        if first:
            return PropertyImageSerializer(first).data
        return None


class PropertyDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for property details.
    """

    display_price = serializers.ReadOnlyField()
    is_available = serializers.ReadOnlyField()
    amenities = AmenitySerializer(many=True, read_only=True)
    images = PropertyImageSerializer(many=True, read_only=True)
    documents = PropertyDocumentSerializer(many=True, read_only=True)
    owner = UserSerializer(read_only=True)
    agent = UserSerializer(read_only=True)
    is_favorite = serializers.SerializerMethodField()

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
            "floor_number",
            "total_floors",
            "sale_price",
            "rent_price",
            "price_per_unit",
            "currency",
            "price_negotiable",
            "amenities",
            "furnished",
            "parking_spaces",
            "pets_allowed",
            "available_from",
            "minimum_lease",
            "maximum_lease",
            "featured_image",
            "images",
            "documents",
            "video_url",
            "virtual_tour_url",
            "meta_title",
            "meta_description",
            "view_count",
            "inquiry_count",
            "favorite_count",
            "display_price",
            "is_available",
            "is_favorite",
            "created_at",
            "updated_at",
            "owner",
            "agent",
        ]

    def get_is_favorite(self, obj):
        """Check if property is favorited by current user."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, property=obj).exists()
        return False


class PropertyCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating properties.
    """

    amenities = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Amenity.objects.all(), required=False
    )

    class Meta:
        model = Property
        fields = [
            "title",
            "description",
            "category",
            "listing_type",
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
            "floor_number",
            "total_floors",
            "sale_price",
            "rent_price",
            "currency",
            "price_negotiable",
            "amenities",
            "furnished",
            "parking_spaces",
            "pets_allowed",
            "available_from",
            "minimum_lease",
            "maximum_lease",
            "video_url",
            "virtual_tour_url",
            "meta_title",
            "meta_description",
        ]

    def create(self, validated_data):
        amenities = validated_data.pop("amenities", [])
        property_obj = Property.objects.create(**validated_data)
        property_obj.amenities.set(amenities)
        return property_obj

    def update(self, instance, validated_data):
        amenities = validated_data.pop("amenities", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if amenities is not None:
            instance.amenities.set(amenities)
        return instance


class FavoriteSerializer(serializers.ModelSerializer):
    """
    Serializer for Favorite model.
    """

    property_details = PropertyListSerializer(source="property", read_only=True)

    class Meta:
        model = Favorite
        fields = ["id", "property", "property_details", "created_at"]
        read_only_fields = ["id", "created_at"]
