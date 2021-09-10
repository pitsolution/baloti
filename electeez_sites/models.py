from django.conf import settings
from django.contrib.sites.models import Site, SiteManager
from django.db import models


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

    objects = SiteManager()
