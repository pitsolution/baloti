import importlib
import inspect
import re

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
            self.load_texts()
            self.load_locales()

        if transaction.get_autocommit(self.using):
            connections[self.using].close()

    def load_languages(self):
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

    def load_texts(self):
        Language = apps.get_model('djlang', 'Language')
        Text = apps.get_model('djlang', 'Text')
        submodules = []
        for app in settings.INSTALLED_APPS:
            if not re.match(r'^((electeez)|(djelectionguard))', app):
                continue
            app_module = importlib.import_module(app)
            for value in app_module.__dict__.values():
                if type(value).__name__ == 'module':
                    submodules.append(value)
        for module in submodules:
            try:
                source = inspect.getsource(module)
                matches = re.findall(r"[^_]_\(['\"](?P<key>.*?)['\"].*?\)", source)
            except Exception:
                continue
            for m in matches:
                for language in Language.objects.all():
                    Text.objects.get_or_create(
                        language=language,
                        key=m.strip()
                    )


    # approximative way of loading existing locales:
    def load_locales(self):
        Language = apps.get_model('djlang', 'Language')
        Text = apps.get_model('djlang', 'Text')

        for language in Language.objects.all():
            print(f'Loading locales for {language.name}')
            with open(f'locale/{language.iso}/LC_MESSAGES/django.po', 'r') as f:
                locale = f.read()

            locale = locale.replace('\n\n', '#')
            locale = locale.replace('\n', '')
            locale += '#'
            matches = re.findall(r"#:(?P<m>.*?)[#$]", locale)

            for m in matches:
                msg = m.split('msgid')
                if len(msg) > 1:
                    msg_arr = msg[1].split('msgstr')
                    key = msg_arr[0].replace('"', '')
                    key = key.strip()
                    val = msg_arr[1].replace('"', '')

                    text = Text.objects.filter(
                        language=language,
                        key=key
                    ).first()

                    if text and not text.val:
                        text.val = val.strip()
                        text.save()
