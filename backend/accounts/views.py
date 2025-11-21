from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from .models import User
from .serializers import (
    SignupSerializer,
    LoginSerializer,
    GoogleAuthSerializer,
    UserSerializer,
)


def get_tokens_for_user(user):
    """Generate JWT tokens for user"""
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


@api_view(["POST"])
@permission_classes([AllowAny])
def signup(request):
    """Email/password signup"""
    serializer = SignupSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = serializer.save()
    tokens = get_tokens_for_user(user)

    return Response(
        {**tokens, "user": UserSerializer(user).data}, status=status.HTTP_201_CREATED
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """Email/password login"""
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = serializer.validated_data["user"]
    tokens = get_tokens_for_user(user)

    return Response(
        {**tokens, "user": UserSerializer(user).data}, status=status.HTTP_200_OK
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def google_auth(request):
    """Google OAuth authentication"""
    serializer = GoogleAuthSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    token = serializer.validated_data["token"]

    try:
        # Verify Google token
        idinfo = id_token.verify_oauth2_token(
            token, requests.Request(), getattr(settings, "GOOGLE_OAUTH_CLIENT_ID", None)
        )

        # Get user info from Google
        google_id = idinfo["sub"]
        email = idinfo["email"]

        # Get or create user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "google_id": google_id,
                "role": "parent",  # Always default to parent
            },
        )

        # Update google_id if missing
        if not user.google_id:
            user.google_id = google_id
            user.save(update_fields=["google_id"])

        tokens = get_tokens_for_user(user)

        return Response(
            {**tokens, "user": UserSerializer(user).data, "created": created},
            status=status.HTTP_200_OK,
        )

    except ValueError as e:
        return Response(
            {"error": "Invalid Google token"}, status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    """Get current user profile"""
    return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)
