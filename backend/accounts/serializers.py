from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "phone", "role", "is_active", "date_joined"]
        read_only_fields = ["id", "date_joined"]


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    phone = serializers.CharField(max_length=15, required=False, allow_blank=True)
    role = serializers.ChoiceField(
        choices=["parent", "vendor", "school_admin", "ops"], default="parent"
    )

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

    def validate_phone(self, value):
        if value and User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Phone number already exists")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            phone=validated_data.get("phone") or None,
            role=validated_data.get("role", "parent"),
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError("Invalid credentials")
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled")
            data["user"] = user
        else:
            raise serializers.ValidationError("Must include email and password")

        return data


class GoogleAuthSerializer(serializers.Serializer):
    token = serializers.CharField()
    role = serializers.ChoiceField(
        choices=["parent", "vendor", "school_admin", "ops"],
        default="parent",
        required=False,
    )
