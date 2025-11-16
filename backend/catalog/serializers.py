from rest_framework import serializers
from .models import UniformSpec


class UniformSpecSerializer(serializers.ModelSerializer[UniformSpec]):
    school_name = serializers.CharField(source="school.name", read_only=True)

    class Meta:
        model = UniformSpec
        fields = [
            "id",
            "school",
            "school_name",
            "item_type",
            "gender",
            "season",
            "fabric_gsm",
            "pantone",
            "measurements",
            "frozen",
            "version",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
