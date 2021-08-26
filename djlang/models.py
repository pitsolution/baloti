import re

from django.db import models
from django.conf import settings
from django.utils.translation import get_language
from django.utils.html import escape
from django.utils.safestring import mark_safe

from electeez_sites.models import Site

# Create your models here.

class Language(models.Model):
    iso = models.CharField(max_length=3)
    name = models.CharField(max_length=255)
    active = models.BooleanField(default=True, blank=True)
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE
    )


class Text(models.Model):
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE
    )
    key = models.CharField(
        max_length=1024,
    )
    val = models.TextField(blank=True, null=True)
    nval = models.TextField(blank=True, null=True)

    def process(self, n=0, allow_unsecure=False, **placeholders):
        #  If pluralize return nval
        #  If not nval use val
        #  If not val use key
        val = self.val or self.key
        if self.val and n > 1:
            val = self.nval or self.val

        if not allow_unsecure:
            val = escape(val)

        #  Replace strings by placeholders
        matches = re.findall(r'(%\((?P<ph>[^%( )]*?)\)s)', val)

        for match in matches:
            if match[1] in placeholders:
                val = val.replace(match[0], str(placeholders[match[1]]))

        return mark_safe(val)
