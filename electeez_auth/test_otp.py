from datetime import timedelta
import pytest

from django.utils import timezone
from electeez_auth.models import User


@pytest.mark.django_db
def test_otp(client):
    user = User.objects.create(email='otp@example.com')
    token = user.otp_new(redirect='valid')

    response = client.post(token.path)
    assert response['Location'] == 'valid'

    # can't use the link twice
    response = client.post(token.path)
    assert response['Location'] != 'valid'

    # try expired link
    token = user.otp_new()
    token.otp_expiry = timezone.now() - timedelta(minutes=1)
    token.save()
    response = client.post(token.path)
    assert response['Location'] != 'valid'
