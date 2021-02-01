import os

from django import test
from django.contrib.auth import get_user_model
from django.utils import timezone

from djblockchain.models import Account, Blockchain
from djelectionguard.models import Contest
from djelectionguard_tezos.models import ElectionContract

os.environ['DJBLOCKCHAIN_MOCK'] = '1'
User = get_user_model()


class ModelStory:
    fixtures = ['data.json']

    def assertIsOnBlockchain(self, transaction):
        transaction.refresh_from_db()
        assert transaction.state == 'done'
        assert transaction.gas
        assert transaction.contract_address

    def test_sft_story(self):
        user = User.objects.get(email='admin@example.com')
        blockchain = Blockchain.objects.get(name=self.bcname)
        account = user.account_set.create(blockchain=blockchain)
        election = Contest.objects.create(
            mediator=user,
            start=timezone.now(),
            end=timezone.now(),
        )

        contract = ElectionContract.objects.create(
            state='deploy',
            sender=account,
            election=election,
        )

        self.assertIsOnBlockchain(contract)


class TezosTestCase(ModelStory, test.TransactionTestCase):
    bcname = 'tzlocal'


#class FakeTestCase(ModelStory, test.TransactionTestCase):
#    bcname = 'fake'
