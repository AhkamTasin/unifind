"""Django admin configuration (for the built-in /admin/ site)."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Category, Claim, FoundItem, LostItem, Notification, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "full_name", "email", "role", "department", "is_active", "created_at")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "first_name", "last_name", "email", "department")
    fieldsets = UserAdmin.fieldsets + (
        ("Campus Info", {"fields": ("role", "phone", "department", "profile_photo")}),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "icon")


@admin.register(LostItem)
class LostItemAdmin(admin.ModelAdmin):
    list_display = ("id", "item_name", "reporter", "category", "lost_location", "status", "created_at")
    list_filter = ("status", "category")
    search_fields = ("item_name", "description", "lost_location")


@admin.register(FoundItem)
class FoundItemAdmin(admin.ModelAdmin):
    list_display = ("id", "tracking_id", "item_name", "finder", "category", "status", "verified_by", "created_at")
    list_filter = ("status", "category")
    search_fields = ("item_name", "tracking_id", "description")


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ("id", "found_item", "claimant", "status", "reviewed_by", "created_at")
    list_filter = ("status",)
    search_fields = ("claim_description", "claimant__username")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "is_read", "created_at")
    list_filter = ("is_read",)
    search_fields = ("user__username", "title")
