from django.contrib import admin
from .models import UniformSpec


@admin.register(UniformSpec)
class UniformSpecAdmin(admin.ModelAdmin):
    list_display = [
        "school",
        "item_type",
        "gender",
        "season",
        "version",
        "frozen",
        "created_at",
    ]
    list_filter = ["item_type", "gender", "season", "frozen"]
    search_fields = ["school__name", "item_type", "pantone"]
    ordering = ["school", "item_type", "-version"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (None, {"fields": ("id", "school", "item_type", "gender", "season")}),
        ("Specifications", {"fields": ("fabric_gsm", "pantone", "measurements")}),
        ("Version Control", {"fields": ("version", "frozen")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
