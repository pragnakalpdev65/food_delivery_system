from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.constants.messages import AuthMessages
from apps.core.constants.error_codes import ErrorCodes
from apps.core.constants.choices import UserType
from apps.users.api.v1.serializers.profile import (
    ChangePasswordSerializer,
    UpdateEmailSerializer,
    CurrentEmailConfirmSerializer,
    ConfirmEmailChangeSerializer,
    CustomerProfileSerializer,
    CustomerProfileUpdateSerializer,
    AddressSerializer,
    DriverProfileSerializer,
    RestaurantOwnerProfileSerializer
)
from apps.users.models import CustomUser
from apps.users.models.profile import CustomerProfile, Address, DriverProfile,RestaurantOwnerProfile
from drf_spectacular.utils import extend_schema, OpenApiTypes, OpenApiExample, OpenApiParameter


class CustomerProfileView(APIView):
    """
    API view to retrieve and update the authenticated customer's profile.
    Methods:
    - GET: Retrieve the logged-in user's customer profile.
    - PUT: Update the logged-in user's customer profile (partial update allowed).

    Permissions:
    - Requires authentication.
    """

    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Users"],
        summary="Get user profile",
        description="Get logged-in customer profile details",
        responses=CustomerProfileSerializer,
    )
    def get(self, request):
        """
        Fetch the authenticated user's customer profile.

        Returns:
            200 OK with profile data if found.
            404 NOT FOUND if profile does not exist.
        """
        try:
            profile = request.user.customer_profile
        except CustomerProfile.DoesNotExist:
            return Response(
                {"detail": AuthMessages.CUSTOMER_NOT_FOUND},
                status=ErrorCodes.NOT_FOUND,
            )

        serializer = CustomerProfileSerializer(profile)
        return Response(serializer.data)

    @extend_schema(
        tags=["Users"],
        summary="Update user profile",
        description="Update the logged-in customer's profile details",
        request=CustomerProfileUpdateSerializer,
        responses=CustomerProfileSerializer,
    )
    def put(self, request):
        """
        Update the authenticated user's customer profile.
        Supports partial updates.

        Returns:
            200 OK with updated data on success.
            400 BAD REQUEST if validation fails.
            404 NOT FOUND if profile does not exist.
        """
        try:
            profile = request.user.customer_profile
        except CustomerProfile.DoesNotExist:
            return Response(
                {"detail": AuthMessages.CUSTOMER_NOT_FOUND},
                status=ErrorCodes.NOT_FOUND,
            )

        serializer = CustomerProfileUpdateSerializer(
            profile, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddressView(APIView):
    """
    API view to manage customer addresses.
    Methods:
    - GET: Retrieve all addresses of the authenticated user.
    - POST: Create a new address for the authenticated user.

    Permissions:
    - Requires authentication.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Users"],
        summary="List user addresses",
        description="Return all addresses associated with the authenticated customer's profile.",
        responses=AddressSerializer(many=True),
    )
    def get(self, request):
        """
        Fetch all addresses of the authenticated user's profile.
        Returns:
            200 OK with list of addresses.
        """
        profile = request.user.customer_profile
        addresses = profile.addresses.select_related("customer").all()
    
        serializer = AddressSerializer(addresses, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Users"],
        summary="Create an address",
        description="Create a new address for the authenticated customer.",
        request=AddressSerializer,
        responses=AddressSerializer,
    )
    def post(self, request):
        """
        Create a new address for the authenticated user.
        Returns:
            201 CREATED with created address data.
            400 BAD REQUEST if validation fails.
        """
        profile = request.user.customer_profile

        serializer = AddressSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(customer=profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddressDetailView(APIView):
    """
    API view to retrieve, update, and delete a specific address.
    Methods:
    - GET: Retrieve a specific address.
    - PUT: Update a specific address (partial update allowed).
    - DELETE: Delete a specific address.

    Permissions:
    - Requires authentication.
    """

    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        """
        Helper method to fetch an address belonging to the authenticated user.
        Returns:
            Address instance if found, otherwise None.
        """
        try:
            address = Address.objects.get(pk=pk, customer=request.user.customer_profile)
        except Address.DoesNotExist:
            return None

        self.check_object_permissions(request, address)
        return address

    @extend_schema(
        tags=["Users"],
        summary="Get address details",
        description="Retrieve a specific address belonging to the authenticated customer.",
        responses=AddressSerializer,
    )
    def get(self, request, pk):
        """
        Retrieve a specific address by ID.
        Returns:
            200 OK with address data.
            404 NOT FOUND if address does not exist.
        """
        address = self.get_object(request, pk)
        if not address:
            return Response(
                {"detail": AuthMessages.ADDRESS_NOT_FOUND},
                status=ErrorCodes.NOT_FOUND,
            )

        serializer = AddressSerializer(address)
        return Response(serializer.data)

    @extend_schema(
        tags=["Users"],
        summary="Update address",
        description="Update an existing address for the authenticated customer.",
        request=AddressSerializer,
        responses=AddressSerializer,
    )
    def put(self, request, pk):
        """
        Update a specific address.
        Supports partial updates.
        Returns:
            200 OK with updated data.
            400 BAD REQUEST if validation fails.
            404 NOT FOUND if address does not exist.
        """
        address = self.get_object(request, pk)
        if not address:
            return Response(
                {"detail": AuthMessages.ADDRESS_NOT_FOUND},
                status=ErrorCodes.NOT_FOUND,
            )

        serializer = AddressSerializer(address, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Users"],
        summary="Delete address",
        description="Delete a specific address from the authenticated customer's profile.",
        responses=OpenApiTypes.OBJECT,
    )
    def delete(self, request, pk):
        """
        Delete a specific address.
        Returns:
            204 NO CONTENT on successful deletion.
            404 NOT FOUND if address does not exist.
        """
        address = self.get_object(request, pk)
        if not address:
            return Response(
                {"detail": AuthMessages.ADDRESS_NOT_FOUND},
                status=ErrorCodes.NOT_FOUND,
            )

        address.delete()
        return Response(
            {"detail": "Address deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )


class DriverProfileView(APIView):
    """
    API view to retrieve and update the authenticated driver's profile.
    Methods:
    - GET: Retrieve the logged-in driver's profile.
    - PUT: Update the logged-in driver's profile (partial update allowed).

    Permissions:
    - Requires authentication.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Users"],
        summary="Get driver profile",
        description="Fetch the authenticated driver's profile details.",
        responses=DriverProfileSerializer,
    )
    def get(self, request):
        """
        Fetch the authenticated user's driver profile.
        Returns:
            200 OK with profile data.
            404 NOT FOUND if profile does not exist.
        """
        try:
            profile = request.user.driver_profile
        except DriverProfile.DoesNotExist:
            return Response(
                {"detail": AuthMessages.DRIVER_NOT_FOUND},
                status=ErrorCodes.NOT_FOUND,
            )

        serializer = DriverProfileSerializer(profile)
        return Response(serializer.data)

    @extend_schema(
        tags=["Users"],
        summary="Update driver profile",
        description="Update the authenticated driver's profile details.",
        request=DriverProfileSerializer,
        responses=DriverProfileSerializer,
    )
    def put(self, request):
        """
        Update the authenticated user's driver profile.
        Supports partial updates.

        Returns:
            200 OK with updated data.
            400 BAD REQUEST if validation fails.
            404 NOT FOUND if profile does not exist.
        """
        try:
            profile = request.user.driver_profile
        except DriverProfile.DoesNotExist:
            return Response(
                {"detail": AuthMessages.DRIVER_NOT_FOUND},
                status=ErrorCodes.NOT_FOUND,
            )

        serializer = DriverProfileSerializer(
            profile, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RestaurantOwnerProfileView(APIView):
    """
    Retrieve and update authenticated restaurant owner profile.
    """

    permission_classes = [IsAuthenticated]

    def _get_or_create_profile(self, user):
        if user.user_type != UserType.RESTAURANT_OWNER:
            return None

        profile, _ = RestaurantOwnerProfile.objects.get_or_create(user=user)
        return profile

    @extend_schema(
        tags=["Users"],
        summary="Get restaurant owner profile",
        responses=RestaurantOwnerProfileSerializer,
    )
    def get(self, request):
        profile = self._get_or_create_profile(request.user)

        if profile is None:
            return Response(
                {"detail": AuthMessages.RESTAURANT_OWNER_NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND,
            )

        profile.update_statistics()
        serializer = RestaurantOwnerProfileSerializer(profile)
        return Response(serializer.data)

    @extend_schema(
        tags=["Users"],
        summary="Update restaurant owner profile",
        request=RestaurantOwnerProfileSerializer,
        responses=RestaurantOwnerProfileSerializer,
    )
    def put(self, request):
        return self._update_profile(request)

    @extend_schema(
        tags=["Users"],
        summary="Update restaurant owner profile (POST)",
        description="Same as PUT. Accepts partial profile updates for restaurant owners.",
        request=RestaurantOwnerProfileSerializer,
        responses=RestaurantOwnerProfileSerializer,
    )
    def post(self, request):
        return self._update_profile(request)

    def _update_profile(self, request):
        profile = self._get_or_create_profile(request.user)

        if profile is None:
            return Response(
                {"detail": AuthMessages.RESTAURANT_OWNER_NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = RestaurantOwnerProfileSerializer(
            profile,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            serializer.save()
            profile.update_statistics()
            return Response(serializer.data)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )
class ChangePasswordView(APIView):
    """Allow authenticated user to change password and invalidate all sessions."""

    permission_classes = [IsAuthenticated]
    queryset = CustomUser.objects.all()

    @extend_schema(
        tags=["Users"],
        request=ChangePasswordSerializer,
        responses=OpenApiTypes.OBJECT,
    )
    def post(self, request):
        """
        Handle password change request for authenticated user.

        Validates current password, sets new password,
        and blacklists all existing JWT tokens to force re-login.
        """
        user = request.user
        serializer = ChangePasswordSerializer(data=request.data, context={"user": user})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            AuthMessages.PASSWORD_CHANGE_SUCCESS,
            status=status.HTTP_200_OK,
        )

class UpdateEmailView(APIView):
    """
    API to initiate email change process.

    Workflow:
        1. User provides current password + new email
        2. System validates credentials
        3. Sends verification emails to:
            - current email
            - new email
        4. Stores request in cache for confirmation flow
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Users"],
        request=UpdateEmailSerializer,
        responses=OpenApiTypes.OBJECT,
    )
    def post(self, request):
        """
        Initiate email change request.
        """
        user = request.user

        serializer = UpdateEmailSerializer(
            data=request.data,
            context={"user": user}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": AuthMessages.EMAIL_SENT_TO_UPDATED_ADDRESS},
            status=status.HTTP_200_OK
        )

class CurrentEmailConfirmView(APIView):
    """
    Confirm current (old) email via link from email.

    Email links hit the frontend as:
      {FRONTEND_URL}/current-email-confirm/?token=<token>

    Frontend should call:
      GET /api/v1/users/profile/email/current-confirm/?token=<token>
    """

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Users"],
        summary="Confirm current email for email change",
        description=(
            "Confirm the current email using the `token` query param from the email link. "
            "No auth required — user is resolved from the signed token."
        ),
        auth=[],
        parameters=[
            OpenApiParameter(
                name="token",
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Token from current-email confirmation link",
            )
        ],
        responses=OpenApiTypes.OBJECT,
    )
    def get(self, request):
        serializer = CurrentEmailConfirmSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": AuthMessages.CONFIRM_OLD_EMAIL},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Users"],
        summary="Confirm current email (POST)",
        description="Same as GET; accepts `token` (or legacy `old_token`) in JSON body.",
        auth=[],
        request=CurrentEmailConfirmSerializer,
        responses=OpenApiTypes.OBJECT,
    )
    def post(self, request):
        serializer = CurrentEmailConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": AuthMessages.CONFIRM_OLD_EMAIL},
            status=status.HTTP_200_OK,
        )


class ConfirmEmailChangeView(APIView):
    """
    Finalize email change via link sent to the new address.

    Email links hit the frontend as:
      {FRONTEND_URL}/confirm-email-change/?token=<token>

    Frontend should call:
      GET /api/v1/users/profile/email/change-confirm/?token=<token>

    Note: old email must be confirmed first. After success, JWT sessions are
    invalidated and the user must verify the new email then log in again.
    """

    permission_classes = [AllowAny]

    def _confirm(self, data):
        serializer = ConfirmEmailChangeSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "message": AuthMessages.EMAIL_UPDATED,
                "detail": (
                    "Email updated. Please verify the new email and log in again."
                ),
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Users"],
        summary="Confirm new email for email change",
        description=(
            "Confirm the new email using the `token` query param from the email link. "
            "Requires prior confirmation of the old email."
        ),
        auth=[],
        parameters=[
            OpenApiParameter(
                name="token",
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Token from new-email confirmation link",
            )
        ],
        responses=OpenApiTypes.OBJECT,
    )
    def get(self, request):
        return self._confirm(request.query_params)

    @extend_schema(
        tags=["Users"],
        summary="Confirm new email (POST)",
        description="Same as GET; accepts `token` (or legacy `new_token`) in JSON body.",
        auth=[],
        request=ConfirmEmailChangeSerializer,
        responses=OpenApiTypes.OBJECT,
    )
    def post(self, request):
        return self._confirm(request.data)
