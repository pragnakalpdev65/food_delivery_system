from django.conf import settings
from django.core import signing
from django.urls import reverse

from common.services.email import BaseEmailService

class AuthEmailService(BaseEmailService):

    def generate_token(self, user,salt):
        """
        Generate a cryptographically signed token containing user ID.

        The token:
        - cannot be tampered with (signature protected)
        - can be time-limited during verification
        - avoids exposing raw user IDs directly
        """
        return signing.dumps(
            {"user_id": str(user.id)},  # payload stored inside token
            salt=salt,  # unique salt for email verification tokens
         )

    def send_token_email(self,*,user,salt,url_name,subject,template_name,context_key,to_email=None):
        """
        Generic method to send any token-based email.
        """

        # Generate token
        token = self.generate_token(user,salt)

        # Build URL
        path = reverse(url_name)
        url = f"{settings.SITE_BASE_URL}{path}?token={token}"

        # Default email = user's email
        to_email = to_email or user.email

        # Context
        context = {
            "user": user,
            context_key: url,
        }

        # Send email
        self.send_email(
            subject=subject,
            to_email=to_email,
            template_name=template_name,
            context=context,
        )
