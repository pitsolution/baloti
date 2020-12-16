import pytest

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError

User = apps.get_model(settings.AUTH_USER_MODEL)


@pytest.mark.django_db
def test_manifest(contest, manifest):
    assert contest.get_manifest() == manifest


@pytest.mark.django_db
def test_voters_emails_validation(contest):
    contest.voters_emails = '''
    lol
    test@example.com
    foo
    test2@example.com
    '''

    with pytest.raises(ValidationError) as e:
        contest.full_clean()
    assert e._excinfo[1].messages == [
        'Please remove lines containing invalid emails: lol, foo'
    ]

    contest.voters_emails = '''
    test@example.com
    test2@example.com
    '''
    contest.full_clean()


@pytest.mark.django_db
def test_voters(contest):
    test = User.objects.create(email='test@example.com')
    contest.voters_emails = '''
    Test@example.com
    Test2@example.com
    '''
    contest.save()
    contest.voters_update()
    assert list(contest.voter_set.values_list(
        'user__email', flat=True
    )) == ['test@example.com']

    test2 = User.objects.create(email='test2@example.com')
    assert list(contest.voter_set.values_list(
        'user__email', flat=True
    )) == ['test@example.com', 'test2@example.com']
