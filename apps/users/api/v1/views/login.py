from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.core.constants.messages import AuthMessages
from apps.users.api.v1.serializers.login import LoginSerializer, LoginResponseSerializer, LogoutSerializer
from apps.users.services.auth_services import LoginService
from drf_spectacular.utils import OpenApiExample, OpenApiTypes, extend_schema

@extend_schema(
    tags=["Auth"],
    summary="Login",
    description="""
Login and receive JWT tokens

Use token:
Authorization: Bearer <access_token>
""",
    request=LoginSerializer,
    responses=LoginResponseSerializer,
    auth=[],
    examples=[
        OpenApiExample(
            "Login",
            value={
                "username": "user@test.com",
                "password": "StrongPass123!"
            }
        )
    ]
)
class LoginView(APIView):
    """Login API endpoint.Handles user authentication using email and password credentials."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        tokens = LoginService.generate_tokens_for_user(user)
        return Response(tokens)


class LogoutView(APIView):
    """Logout API endpoint.Invalidates a user's refresh token by blacklisting it."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Auth"],
        request=LogoutSerializer,
        responses=OpenApiTypes.OBJECT,
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(
            AuthMessages.LOGOUT_SUCCESS,
            status=status.HTTP_205_RESET_CONTENT,
        )
