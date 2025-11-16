import uuid
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone
from typing import ClassVar, Optional, Any


class UserManager(BaseUserManager["User"]):
    def create_user(
        self, email: str, password: Optional[str] = None, **extra_fields: Any
    ) -> "User":
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, email: str, password: Optional[str] = None, **extra_fields: Any
    ) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "ops")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ("parent", "Parent"),
        ("vendor", "Vendor"),
        ("school_admin", "School Admin"),
        ("ops", "Operations"),
    ]

    objects: ClassVar[UserManager] = UserManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=255, unique=True, db_index=True)
    phone = models.CharField(
        max_length=15, unique=True, null=True, blank=True, db_index=True
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="parent")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    # Google OAuth fields
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["role"]

    class Meta:
        db_table = "users"
        indexes = [
            models.Index(fields=["email"], name="idx_email"),
            models.Index(fields=["phone"], name="idx_phone"),
        ]

    def __str__(self) -> str:
        return self.email
