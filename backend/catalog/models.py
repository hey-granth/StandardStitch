import uuid
from django.db import models
from typing import ClassVar
from schools.models import School


class UniformSpec(models.Model):
    # Use a non-parameterized Manager type to avoid IDE/type Checker issues
    objects: ClassVar[models.Manager]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        School, on_delete=models.CASCADE, related_name="uniform_specs"
    )
    item_type = models.CharField(max_length=100)
    gender = models.CharField(max_length=20)
    season = models.CharField(max_length=50)
    fabric_gsm = models.IntegerField()
    pantone = models.CharField(max_length=50)
    measurements = models.JSONField(default=dict)
    frozen = models.BooleanField(default=False)
    version = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "uniform_specs"
        ordering = ["item_type", "-version"]
        indexes = [
            models.Index(
                fields=["school", "item_type", "version"],
                name="idx_school_item_version",
            ),
            models.Index(fields=["item_type"], name="idx_spec_item_type"),
            # idx_spec_gender created in 0002_add_performance_indexes migration
            models.Index(fields=["school", "frozen"], name="idx_school_frozen"),
        ]

    def __str__(self) -> str:
        return f"{self.school.name} - {self.item_type} v{self.version}"
