from django.db import (
    DEFAULT_DB_ALIAS, connections, transaction
)
from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import translation


class Command(BaseCommand):
    help = 'Load language files in DB'

    def handle(self, *args, **options):

        self.using = DEFAULT_DB_ALIAS

        with transaction.atomic(using=self.using):
            self.load_languages()

        if transaction.get_autocommit(self.using):
            connections[self.using].close()

    def load_languages(self):
        default_language = settings.LANGUAGE_CODE
        languages = settings.LANGUAGES

        connection = connections[self.using]

        Site = apps.get_model('electeez_sites', 'Site')
        Language = apps.get_model('djlang', 'Language')

        for site in Site.objects.all():
            for iso, name in languages:
                translation.activate(iso)
                Language.objects.get_or_create(
                    site=site,
                    iso=iso,
                    name=name
                )
