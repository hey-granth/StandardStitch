from rest_framework import serializers
from .models import School


class SchoolSerializer(serializers.ModelSerializer[School]):
    class Meta:
        model = School
        fields = [
            "id",
            "name",
            "city",
            "board",
            "session_start",
            "session_end",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

