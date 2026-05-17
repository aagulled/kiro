"""
Views for tenants app.
"""
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsTenantAdmin

from .models import Domain, Tenant
from .serializers import DomainSerializer, TenantCreateSerializer, TenantSerializer


class TenantListView(generics.ListAPIView):
    """
    List all tenants (superuser only).
    """

    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Tenant.objects.all()
        return Tenant.objects.filter(id=self.request.user.tenant_id)


class TenantDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update a tenant.
    """

    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated, IsTenantAdmin]
    lookup_field = "slug"

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Tenant.objects.all()
        return Tenant.objects.filter(id=self.request.user.tenant_id)


class TenantCreateView(generics.CreateAPIView):
    """
    Create a new tenant.
    """

    queryset = Tenant.objects.all()
    serializer_class = TenantCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Only superusers can create tenants
        if not self.request.user.is_superuser:
            raise PermissionError("Only superusers can create tenants.")
        serializer.save()


class DomainListView(generics.ListCreateAPIView):
    """
    List or create domains for a tenant.
    """

    serializer_class = DomainSerializer
    permission_classes = [IsAuthenticated, IsTenantAdmin]

    def get_queryset(self):
        tenant_slug = self.kwargs.get("tenant_slug")
        return Domain.objects.filter(tenant__slug=tenant_slug)

    def perform_create(self, serializer):
        tenant_slug = self.kwargs.get("tenant_slug")
        tenant = Tenant.objects.get(slug=tenant_slug)
        serializer.save(tenant=tenant)


class DomainDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a domain.
    """

    serializer_class = DomainSerializer
    permission_classes = [IsAuthenticated, IsTenantAdmin]
    lookup_field = "pk"

    def get_queryset(self):
        tenant_slug = self.kwargs.get("tenant_slug")
        return Domain.objects.filter(tenant__slug=tenant_slug)


class CurrentTenantView(APIView):
    """
    Get current tenant information.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant = request.user.tenant
        if not tenant:
            return Response(
                {"error": "No tenant associated with user"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = TenantSerializer(tenant)
        return Response(serializer.data)
