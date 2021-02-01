from django.db import models
from djblockchain.models import Transaction


class ElectionContract(Transaction):
    election = models.OneToOneField(
        'djelectionguard.contest',
        on_delete=models.CASCADE,
    )

    def deploy(self):
        self.contract_name = 'election_compiled'
        self.args = [
            election_storage(self.sender.address),
        ]
        return super().deploy()


def election_storage(sender):
    return {
        "prim": "Pair",
        "args": [
            {
                "string": sender
            },
            {
                "string": ""
            }
        ]
    }
