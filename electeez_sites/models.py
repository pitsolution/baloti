from django.db import models
from django.conf import settings
from django.contrib.sites.models import Site, SiteManager
from django.core.files.storage import FileSystemStorage


class SiteManager(SiteManager):
    def get_current(self):
        if settings.DEBUG:
            self.clear_cache()
        return super().get_current()


class Site(Site):
    contact_email = models.EmailField(default='contact@electis.app')
    sender_email = models.EmailField(default='contact@electis.app')

    all_users_can_create = models.BooleanField(default=True)
    all_results_are_visible = models.BooleanField(default=True)

    footer_url = models.CharField(max_length=255, default='https://electis.app')

    email_banner_fg = models.CharField(
        max_length=7,
        default='#000000'
    )

    email_banner_bg = models.CharField(
        max_length=7,
        default='#ffffff'
    )

    email_banner = models.ImageField(
        upload_to=f'{settings.STATIC_ROOT_DIR}/images',
        null=True,
        blank=True
    )

    email_footer_fg = models.CharField(
        max_length=7,
        default='#000000'
    )

    email_footer_bg = models.CharField(
        max_length=7,
        default='#ffffff'
    )

    email_footer = models.ImageField(
        upload_to=f'{settings.STATIC_ROOT_DIR}/images',
        null=True,
        blank=True
    )

    objects = SiteManager()
