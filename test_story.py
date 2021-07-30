import pytest
from django.core.management import call_command
from electeez_sites.models import Site


@pytest.fixture(autouse=True)
def django_fixtures_setup(django_db_setup, django_db_blocker):
    fixture = 'electeez_sites/sites_data.json'
    with django_db_blocker.unblock():
        call_command('loaddata', fixture)
        Site.objects.clear_cache()
        Site.objects.get_current()


def test_home(client):
    response = client.get('/en/')
    assert response.status_code == 302
    assert response['Location'] == '/static/electis/landing/index.html'


@pytest.mark.django_db
def test_register(client):
    response = client.get('/en/accounts/register/')
    assert response.status_code == 200
    assert b'id_password1' in response.content
    assert b'id_password2' in response.content
    assert b'id_email' in response.content

    response = client.post('/en/accounts/register/', dict(
        password1='3L51a231',
        password2='3L51a231',
        email='foo@example.com',
    ))
    assert response.status_code == 302

    response = client.get(response['Location'])
    assert response.status_code == 200
