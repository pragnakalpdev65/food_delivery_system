import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class BaseEmailService:
    """
    Base service to handle email sending logic.
    Used for verification emails, resend verification, etc.
    """

    def send_email(
        self, subject: str, to_email: str, template_name: str, context: dict
    ):
        """
        Send email with both HTML and plain text versions.

        :param subject: Email subject
        :param to_email: Recipient email
        :param template_name: Base template path (without extension)
        :param context: Context data for rendering templates
        """
        try:
            # Render plain text version
            text_content = render_to_string(f"email/{template_name}.txt", context)

            # Render HTML version
            html_content = render_to_string(f"email/{template_name}.html", context)

            # Create email message
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[to_email],
            )

            # Attach HTML version
            email.attach_alternative(html_content, "text/html")

            # Send email
            email.send(fail_silently=False)

            logger.info(f"Email sent successfully to {to_email}")

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            raise e
