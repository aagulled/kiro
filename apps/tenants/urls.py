"""
URL configuration for tenants app.
"""
from django.urls import path

from . import views

urlpatterns = [
    path("", views.TenantListView.as_view(), name="tenant-list"),
    path("create/", views.TenantCreateView.as_view(), name="tenant-create"),
    path("current/", views.CurrentTenantView.as_view(), name="tenant-current"),
    path("<slug:slug>/", views.TenantDetailView.as_view(), name="tenant-detail"),
    path("<slug:tenant_slug>/domains/", views.DomainListView.as_view(), name="domain-list"),
    path(
        "<slug:tenant_slug>/domains/<int:pk>/",
        views.DomainDetailView.as_view(),
        name="domain-detail",
    ),
]
