import pytest


def test_home(client):
    response = client.get('/')
    assert response.status_code == 302
    assert response['Location'] == '/contest/'


@pytest.mark.django_db
def test_register(client):
    response = client.get('/accounts/register/')
    assert response.status_code == 200
    assert b'id_password1' in response.content
    assert b'id_password2' in response.content
    assert b'id_email' in response.content

    response = client.post('/accounts/register/', dict(
        password1='3L51a231',
        password2='3L51a231',
        email='foo@example.com',
    ))
    assert response.status_code == 302

    response = client.get(response['Location'])
    assert response.status_code == 200
