import pytest

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError

User = apps.get_model(settings.AUTH_USER_MODEL)


@pytest.mark.django_db
def test_manifest(contest, manifest):
    assert contest.get_manifest() == manifest
