from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path("auth/signup", views.signup, name="signup"),
    path("auth/login", views.login, name="login"),
    path("auth/google", views.google_auth, name="google_auth"),
    path("auth/me", views.me, name="me"),
    path("auth/refresh", TokenRefreshView.as_view(), name="token_refresh"),
]
