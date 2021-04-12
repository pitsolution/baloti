import pytest

from django.utils import timezone
from djtezos.models import Blockchain
from electeez_auth.models import User
from djelectionguard.models import Contest


@pytest.mark.django_db
def test_create_contract(client):
    user = User.objects.create(email='admin@example.com')
    client.force_login(user)
    blockchain = Blockchain.objects.create(
        name='tzlocal',
        provider_class='djtezos.tezos.Provider',
        confirmation_blocks=1,
        is_active=True,
        endpoint='http://tz:8732',
    )
    account = user.account_set.create(blockchain=blockchain)
    election = Contest.objects.create(
        mediator=user,
        start=timezone.now(),
        end=timezone.now(),
    )
    response = client.post(
        f'/tezos/{election.pk}/create/',
        data=dict(blockchain=str(blockchain.pk)),
    )
    assert response.status_code == 302
    assert response['Location'] == f'/contest/{election.pk}/'
