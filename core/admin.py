from django.contrib import admin

from . import user_admin  # Ensure custom User admin is registered
from .models import Site, SiteManager, SiteToken
@admin.register(SiteToken)
class SiteTokenAdmin(admin.ModelAdmin):
    list_display = ("site", "type", "token", "is_active", "created_at")
    list_filter = ("site", "type", "is_active")
    search_fields = ("site__name", "token")

# Import and register the custom User admin

@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    search_fields = ("name",)
    fields = ("name", "address", "is_active", "confidentiality_terms", "health_safety_procedures")

@admin.register(SiteManager)
class SiteManagerAdmin(admin.ModelAdmin):
    list_display = ("site", "user")
    search_fields = ("site__name", "user__username", "user__email")

