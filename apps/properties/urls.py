"""
URL configuration for properties app.
"""
from django.urls import path

from . import views

urlpatterns = [
    # Properties
    path("", views.PropertyListView.as_view(), name="property-list"),
    path("create/", views.PropertyCreateView.as_view(), name="property-create"),
    path("my-properties/", views.MyPropertiesView.as_view(), name="my-properties"),
    path("<slug:slug>/", views.PropertyDetailView.as_view(), name="property-detail"),
    path("<slug:slug>/update/", views.PropertyUpdateView.as_view(), name="property-update"),
    path("<slug:slug>/delete/", views.PropertyDeleteView.as_view(), name="property-delete"),
    path(
        "<slug:slug>/approve/",
        views.PropertyApprovalView.as_view(),
        name="property-approval",
    ),
    
    # Amenities
    path("amenities/", views.AmenityListView.as_view(), name="amenity-list"),
    
    # Favorites
    path("favorites/", views.FavoriteListView.as_view(), name="favorite-list"),
    path(
        "favorites/toggle/<uuid:property_id>/",
        views.FavoriteToggleView.as_view(),
        name="favorite-toggle",
    ),
]
