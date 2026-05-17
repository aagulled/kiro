"""
Django admin configuration for search app.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.search.models import SavedSearch, SearchQuery, PopularSearch, PropertySearchIndex


@admin.register(SavedSearch)
class SavedSearchAdmin(admin.ModelAdmin):
    """
    Admin interface for SavedSearch model.
    """
    list_display = [
        'name', 'user', 'email_notifications', 'notification_frequency',
        'last_run_at', 'result_count', 'is_active'
    ]
    list_filter = [
        'is_active', 'email_notifications', 'notification_frequency', 'last_run_at'
    ]
    search_fields = ['name', 'user__email']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'last_run_at', 'result_count'
    ]
    ordering = ['-updated_at']

    fieldsets = (
        (_('Search Information'), {
            'fields': ('name', 'user', 'search_params')
        }),
        (_('Notifications'), {
            'fields': ('email_notifications', 'notification_frequency')
        }),
        (_('Status'), {
            'fields': ('is_active', 'last_run_at', 'result_count')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    """
    Admin interface for SearchQuery model.
    """
    list_display = [
        'query', 'user', 'result_count', 'execution_time',
        'source', 'created_at'
    ]
    list_filter = [
        'source', 'created_at'
    ]
    search_fields = ['query', 'user__email']
    readonly_fields = [
        'id', 'created_at', 'updated_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        (_('Search Information'), {
            'fields': ('query', 'filters', 'sort_by', 'page')
        }),
        (_('Results'), {
            'fields': ('result_count', 'execution_time')
        }),
        (_('User & Context'), {
            'fields': ('user', 'session_id', 'source', 'user_agent', 'ip_address')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        """Prevent manual creation of search queries."""
        return False


@admin.register(PopularSearch)
class PopularSearchAdmin(admin.ModelAdmin):
    """
    Admin interface for PopularSearch model.
    """
    list_display = [
        'term', 'search_count', 'trending_score', 'category', 'last_searched'
    ]
    list_filter = ['category', 'last_searched']
    search_fields = ['term']
    readonly_fields = [
        'id', 'created_at', 'updated_at'
    ]
    ordering = ['-trending_score']

    fieldsets = (
        (_('Search Term'), {
            'fields': ('term', 'category')
        }),
        (_('Metrics'), {
            'fields': ('search_count', 'trending_score', 'last_searched')
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        """Prevent manual creation of popular searches."""
        return False


@admin.register(PropertySearchIndex)
class PropertySearchIndexAdmin(admin.ModelAdmin):
    """
    Admin interface for PropertySearchIndex model.
    """
    list_display = [
        'property', 'is_active', 'last_indexed'
    ]
    list_filter = ['is_active', 'last_indexed']
    search_fields = ['property__title']
    readonly_fields = [
        'property', 'created_at', 'updated_at'
    ]
    ordering = ['-last_indexed']

    fieldsets = (
        (_('Property'), {
            'fields': ('property',)
        }),
        (_('Search Index'), {
            'fields': ('search_vector', 'title_vector', 'description_vector'),
            'classes': ('collapse',)
        }),
        (_('Filters'), {
            'fields': ('price_range', 'bedroom_range', 'property_type')
        }),
        (_('Status'), {
            'fields': ('is_active', 'last_indexed')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        """Prevent manual creation of search indexes."""
        return False

    actions = ['rebuild_index']

    @admin.action(description=_('Rebuild search index for selected properties'))
    def rebuild_index(self, request, queryset):
        """Rebuild search index for selected properties."""
        updated = 0
        for search_index in queryset:
            try:
                search_index.update_index()
                updated += 1
            except Exception as e:
                self.message_user(
                    request,
                    _(f'Failed to rebuild index for {search_index.property.title}: {e}'),
                    level='error'
                )

        self.message_user(
            request,
            ngettext(
                '%d search index was successfully rebuilt.',
                '%d search indexes were successfully rebuilt.',
                updated,
            ) % updated,
        )