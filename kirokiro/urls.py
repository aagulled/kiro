"""
URL configuration for Kirokiro project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
 
    # Root landing page - redirect to admin login
    path("", RedirectView.as_view(url="/admin/login/", permanent=False), name="root"),
 
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
     
    # API Endpoints
    path("api/v1/", include("kiro.urls")),
    path("api/v1/payments/", include("apps.payment.urls")),
<<<<<<< HEAD
=======
    path("api/v1/bookings/", include("apps.bookings.urls")),
>>>>>>> e13cee5 (update)
 
    # Health check
    # path("health/", include("apps.core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
