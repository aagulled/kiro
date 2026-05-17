"""
URL configuration for users app.
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("me/", views.UserDetailView.as_view(), name="user-detail"),
    path("me/password/", views.ChangePasswordView.as_view(), name="change-password"),
    path("me/profile/", views.UserProfileView.as_view(), name="user-profile"),
    path("users/", views.UserListView.as_view(), name="user-list"),
]
