import sys

from django.core import serializers
from django.core.cache import cache
from django.conf import settings
from django.utils.translation import get_language
from django.utils.functional import lazy
from django.utils.html import escape
from django.utils.safestring import SafeString, mark_safe

from django.contrib.sites.models import Site

from .models import Language, Text


def _gettext(key, n=0, **ph):
    '''Usage
    given:
        {
            key: 'FOO',
            val: '%(foo)s is %(bar)s',
            nval: '%(foo)s are %(bar)s'
        },

    so:
    _('FOO', 1, foo='fish', bar='something')
    _('FOO', 3, foo='fishes', bar='something')

    will return:
    -->   'fish is something'
    -->   'fishes are something'

    or, given also:
        {
            key: 'FISH',
            val: 'fish',
            nval: 'fishes'
        }

    so:
    _('FOO', 3, foo=_('FISH', 3), bar='something')

    will return:
    -->   'fishes are something'

    '''
    try:
        current_language = get_language()

        current_site = Site.objects.get_current()


        text = Text.objects.get(
            language__site=current_site,
            language__iso=current_language,
            key=key
        )

    except Text.DoesNotExist:
        text = None
        for l in Language.objects.all():
            text_obj, created = l.text_set.get_or_create(key=key)
            if l.iso == current_language:
                text = text_obj
        return text.process(n, **ph) if text else key
    except Exception as e:
        print(f'djlang - Exception {e} was raised trying to get value for key: {key}')
        return key

    return text.process(n, **ph)


def gettext(*args, **kwargs):
    text = _gettext(*args, **kwargs)
    if not isinstance(text, SafeString):
        text = escape(text)
    return text


gettext = lazy(gettext, str)
