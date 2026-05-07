from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.constants.messages import AuthMessages
from apps.core.constants.error_codes import ErrorCodes
from apps.users.api.v1.serializers.profile import (
    ChangePasswordSerializer,
    UpdateEmailSerializer,
    CurrentEmailConfirmSerializer,
    ConfirmEmailChangeSerializer,
    CustomerProfileSerializer,
    CustomerProfileUpdateSerializer,
    AddressSerializer,
    DriverProfileSerializer,
)
from apps.users.models import CustomUser
from apps.users.models.profile import CustomerProfile, Address, DriverProfile
from drf_spectacular.utils import extend_schema, OpenApiExample


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
    summary="User Profile",
    description="Get logged-in user details"
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
            
class ChangePasswordView(APIView):
    """Allow authenticated user to change password and invalidate all sessions."""

    permission_classes = [IsAuthenticated]
    queryset = CustomUser.objects.all()

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
    API to confirm user's current (old) email.

    Workflow:
        - User clicks link sent to old email
        - Token is validated
        - Marks old email as confirmed in cache
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Confirm old email using token from query params.
        """
        user = request.user

        serializer = CurrentEmailConfirmSerializer(
            data=request.data,
            context={"user": user}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": AuthMessages.CONFIRM_OLD_EMAIL},
            status=status.HTTP_200_OK
        )

class ConfirmEmailChangeView(APIView):
    """
    API to finalize email change.

    Workflow:
        - User clicks link sent to new email
        - Validates new email token
        - Ensures old email already confirmed
        - Updates user's email
        - Invalidates existing sessions (security)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Confirm new email and complete email update process.
        """
        user = request.user

        serializer = ConfirmEmailChangeSerializer(
            data=request.data,
            context={"user": user}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": AuthMessages.EMAIL_UPDATED},
            status=status.HTTP_200_OK
        )
