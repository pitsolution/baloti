import json
import hashlib
import os

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from djtezos.models import Transaction


class ElectionContract(Transaction):
    election = models.OneToOneField(
        'djelectionguard.contest',
        on_delete=models.CASCADE,
    )

    def save(self, *args, **kwargs):
        if not self.contract_micheline and not self.function:
            contract_path = os.path.join(
                os.path.dirname(__file__),
                'tezos/election_compiled.json',
            )
            with open(contract_path, 'r') as f:
                self.contract_micheline = json.loads(f.read())
            self.contract_name = 'election_compiled'
            self.args = election_storage(self.sender.address)
        return super().save(*args, **kwargs)

    def open(self):
        return self.call(
            sender=self.sender,
            function='open',
            args=[
                str(timezone.now()),
                self.election.manifest_sha1,
                self.election.manifest_url,
            ],
            state='deploy',
        )

    def close(self):
        return self.call(
            sender=self.sender,
            function='close',
            args=[str(timezone.now())],
            state='deploy',
        )

    def artifacts(self):
        return self.call(
            sender=self.sender,
            function='artifacts',
            args=[
                self.election.artifacts_sha1,
                self.election.artifacts_url,
            ],
            state='deploy',
        )

    @property
    def explorer_link(self):
        return self.blockchain.explorer.format(self.contract_address)


def election_storage(admin):
    return {
        "prim": "Pair",
        "args": [
            {
                "prim": "Pair",
                "args": [
                    dict(string=admin),
                    {
                        "prim": "Pair",
                        "args": [dict(string=""), dict(string="")],
                    }
                ]
            },
            {
                "prim": "Pair",
                "args": [
                    {
                        "prim": "Pair",
                        "args": [dict(string=""), dict(string="")],
                    },
                    {
                        "prim": "Pair",
                        "args": [dict(string=""), dict(string="")],
                    }
                ]
            }
        ]
    }
