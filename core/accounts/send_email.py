from django.core.mail import EmailMessage
from core import settings


class SendEmail:
    @staticmethod
    def send_email(email, subject, body):
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.EMAIL_HOST_USER,
            to=[email]
        )
        email.fail_silently = False
        email.send()
