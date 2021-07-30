import sys

from django.conf import settings
from django.utils.translation import get_language

from django.contrib.sites.models import Site

from .models import Language, Text


def gettext(key, n=0, **ph):
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
        for l in Language.objects.all():
            created, text = l.text_set.get_or_create(key=key)
        return key
    except Exception:
        return key

    return text.process(n, **ph)

