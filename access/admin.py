from django.contrib import admin
from .models import AssociatedStaff
@admin.register(AssociatedStaff)
class AssociatedStaffAdmin(admin.ModelAdmin):
    list_display = ("name", "site", "association_type", "work_description", "signed_in_at", "signed_out_at", "is_active")
    list_filter = ("site", "is_active")
    search_fields = ("name", "association_type", "work_description")
    date_hierarchy = "signed_in_at"
from django.contrib import admin
from .models import StaffMember, AccessEvent, Visitor, Contractor
@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ("name", "site", "company", "reason", "signed_in_at", "signed_out_at", "is_active")
    list_filter = ("site", "is_active")
    search_fields = ("name", "company", "reason")
    date_hierarchy = "signed_in_at"

@admin.register(Contractor)
class ContractorAdmin(admin.ModelAdmin):
    list_display = ("name", "site", "company", "work_description", "signed_in_at", "signed_out_at", "is_active")
    list_filter = ("site", "is_active")
    search_fields = ("name", "company", "work_description")
    date_hierarchy = "signed_in_at"

@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    list_display = ("name", "site", "pin_value", "is_active")
    list_filter = ("site", "is_active")
    search_fields = ("name", "pin_value")

@admin.register(AccessEvent)
class AccessEventAdmin(admin.ModelAdmin):
    list_display = ("occurred_at", "site", "staff", "direction")
    list_filter = ("site", "direction")
    search_fields = ("staff__name",)
    date_hierarchy = "occurred_at"
