from datetime import timedelta
import secrets

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import signals
from django.utils import timezone
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.contrib.auth.models import BaseUserManager

class BalotiUserManager(BaseUserManager):
    def create_user(self, email, password=None, username=""):
        """
        Creates and saves a User with the given email and password.

        NOTE: Argument 'username' is needed for social-auth. It is not actually used.
        """
        if not email:
            raise ValueError('Users must have an email address.')

        # Validate email is unique in database
        if User.objects.filter(email = self.normalize_email(email).lower()).exists():
            raise ValueError('This email has already been registered.')

        user = self.model(
            email=self.normalize_email(email).lower(),
        )

        user.set_password(password)

        # Save and catch IntegrityError (due to email being unique)
        try:
            user.save(using=self._db)

        except IntegrityError:
            raise ValueError('This email has already been registered.')

        return user

class User(AbstractUser):
    objects = BalotiUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    username = None
    email = models.EmailField(
        verbose_name=_('email address'),
        max_length=255,
        unique=True,
    )
    first_login = models.BooleanField(blank=True, null=True)

    def otp_new(self, redirect=None):
        return self.token_set.create(
            redirect=redirect or reverse('contest_list')
        )

    def save(self, *args, **kwargs):
        if self.email:
            # ensure emails are saved lowercased, for compat with
            # VotersEmailsForm
            self.email = self.email.lower()

            if self.email in settings.ADMINS_EMAIL:
                self.is_superuser = True
                self.is_staff = True
        return super().save(*args, **kwargs)


    def get_full_name(self):
        # The user is identified by their email address
        return self.email

    def get_short_name(self):
        # The user is identified by their email address
        return self.email

    def __str__(self):
        return self.email

    def __unicode__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True


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
