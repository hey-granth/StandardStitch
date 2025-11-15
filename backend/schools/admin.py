from django.contrib import admin
from .models import School


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ["name", "city", "board", "session_start", "session_end", "is_active"]
    list_filter = ["city", "is_active", "board"]
    search_fields = ["name", "city"]
    ordering = ["name"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (None, {"fields": ("id", "name", "city", "board")}),
        ("Session", {"fields": ("session_start", "session_end")}),
        ("Status", {"fields": ("is_active",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

