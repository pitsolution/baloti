from datetime import timedelta
import pytest

from django.utils import timezone
from electeez_auth.models import User


@pytest.mark.django_db
def test_otp(client):
    user = User.objects.create(email='otp@example.com')
    user.otp_new()
    user.save()

    response = client.get(f'/accounts/otp/{user.otp_token}/?next=valid')
    assert response['Location'] == 'valid'

    # can't use the link twice
    response = client.get(f'/accounts/otp/{user.otp_token}/?next=valid')
    assert response['Location'] != 'valid'

    # try expired link
    user.otp_new()
    user.otp_expiry = timezone.now() - timedelta(minutes=1)
    user.save()
    response = client.get(f'/accounts/otp/{user.otp_token}/?next=valid')
    assert response['Location'] != 'valid'
