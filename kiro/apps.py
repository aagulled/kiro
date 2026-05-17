from django.apps import AppConfig, apps
from django.contrib import admin


class KiroConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "kiro"

    def ready(self):
        """
        Automatically register all models with the Django admin.
        This ensures full CRUD operations for every model without manual registration.
        We exclude certain Payment models to avoid duplicates.
        """
        from django.conf import settings
        from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
        from django.contrib.auth.models import Group
        from .models import User, UserProfile

        # Customize admin site
        admin.site.site_header = getattr(settings, 'ADMIN_SITE_HEADER', 'Django administration')
        admin.site.site_title = getattr(settings, 'ADMIN_SITE_TITLE', 'Django site admin')
        admin.site.index_title = getattr(settings, 'ADMIN_INDEX_TITLE', 'Site administration')

        # Define UserAdmin class
        class UserProfileInline(admin.StackedInline):
            model = UserProfile
            can_delete = False
            verbose_name_plural = "Profile"

        class UserAdmin(BaseUserAdmin):
            """Custom admin for Users."""
            inlines = (UserProfileInline,)
            list_display = ("email", "first_name", "last_name", "role", "is_active", "is_staff")
            list_filter = ("role", "is_active", "is_staff", "groups")
            search_fields = ("email", "first_name", "last_name")
            ordering = ("email",)
            filter_horizontal = ("groups", "user_permissions")

            fieldsets = (
                (None, {"fields": ("email", "password")}),
                ("Personal info", {"fields": ("first_name", "last_name", "phone_number", "avatar")}),
                ("Role & Status", {"fields": ("role", "is_active", "is_staff", "is_superuser", "is_verified")}),
                ("Groups & Permissions", {"fields": ("groups", "user_permissions")}),
                ("Important dates", {"fields": ("last_login",)}),
            )
            add_fieldsets = (
                (None, {
                    "classes": ("wide",),
                    "fields": ("email", "password1", "password2", "first_name", "last_name", "role"),
                }),
            )

        # Customize User admin
        if admin.site.is_registered(User):
            admin.site.unregister(User)
        admin.site.register(User, UserAdmin)
        # Connect signals for user group management
        from django.db.models.signals import post_save
        from django.dispatch import receiver

        @receiver(post_save, sender=User)
        def manage_user_groups(sender, instance, created, **kwargs):
            """Manage user group assignments based on role."""
            if instance.role == "staff":
                try:
                    staff_group, _ = Group.objects.get_or_create(name="Staff")
                    if not instance.groups.filter(name="Staff").exists():
                        instance.groups.add(staff_group)
                except Exception:
                    # Ignore errors during app initialization
                    pass

        # Iterate over all models in the project
        for model in apps.get_models():
            # Check if the model is not already registered to avoid duplicates
            if admin.site.is_registered(model):
                continue

            # Skip duplicate Booking/Payment models from kiro/bookings/payment apps
            app_label = model._meta.app_label
            model_name = model.__name__
            if model_name in ('Booking', 'Payment') and app_label in ('kiro', 'bookings', 'payment'):
                continue

            # Register the model with default ModelAdmin
            admin.site.register(model)