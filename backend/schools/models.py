import uuid
from django.db import models
from typing import ClassVar


class School(models.Model):
    objects: ClassVar[models.Manager["School"]]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, db_index=True)
    code = models.CharField(max_length=50, unique=True)
    city = models.CharField(max_length=100, db_index=True)
    address = models.TextField()
    board = models.CharField(max_length=100, blank=True, null=True)
    academic_year = models.CharField(max_length=20, help_text="e.g. 2025-2026")
    session_start = models.DateField()
    session_end = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "schools"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"], name="idx_school_name"),
            models.Index(fields=["city"], name="idx_school_city"),
        ]

    def __str__(self) -> str:
        return self.name
