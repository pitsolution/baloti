from datetime import timedelta
import secrets

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import signals
from django.utils import timezone
from django.urls import reverse


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    username = None
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )

    def otp_new(self, redirect=None):
        return self.token_set.create(
            redirect=redirect or reverse('contest_list')
        )

    def save(self, *args, **kwargs):
        if self.email:
            # ensure emails are saved lowercased, for compat with
            # VotersEmailsForm
            self.email = self.email.lower()
        return super().save(*args, **kwargs)


def default_token():
    return secrets.token_urlsafe()


def default_expiry():
    return timezone.now() + timedelta(days=30)


class Token(models.Model):
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
    )
    token = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        default=default_token,
    )
    expiry = models.DateTimeField(
        null=True,
        blank=True,
        default=default_expiry,
    )
    redirect = models.CharField(max_length=200, null=True, blank=True)
    used = models.DateTimeField(null=True, blank=True)

    @property
    def url(self):
        return settings.BASE_URL + self.path

    @property
    def path(self):
        return reverse('otp_login', args=[self.token])

    @property
    def expired(self):
        return self.expiry <= timezone.now()
