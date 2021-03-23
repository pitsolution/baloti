from datetime import timedelta
import secrets

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import signals
from django.utils import timezone


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    username = None
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )
    otp_token = models.CharField(max_length=255, null=True, blank=True)
    otp_expiry = models.DateTimeField(null=True, blank=True)

    def otp_new(self, expiry=None):
        self.otp_token = secrets.token_urlsafe()
        self.otp_expiry = timezone.now() + timedelta(days=20)

    def save(self, *args, **kwargs):
        if self.email:
            # ensure emails are saved lowercased, for compat with
            # VotersEmailsForm
            self.email = self.email.lower()
        return super().save(*args, **kwargs)
