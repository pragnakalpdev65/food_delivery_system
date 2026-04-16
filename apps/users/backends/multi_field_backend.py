from django.contrib.auth import get_user_model
from django.db.models import Q        
from apps.core.constants.error_codes import ErrorCodes
from apps.core.constants.messages import AuthMessages  
from rest_framework.exceptions import AuthenticationFailed      

User= get_user_model()         
class MultiFieldBackend:
    def authenticate(self, username, password):
               
        user = User.objects.get(
            Q(username=username) | Q(email=username)
        )
        if not user or not user.check_password(password):
            self.track_failed_attempt()
            raise AuthenticationFailed(
                AuthMessages.INVALID_CREDENTIALS,
                code=ErrorCodes.INVALID_CREDENTIALS,
            )

        return user