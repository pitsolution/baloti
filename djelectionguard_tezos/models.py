import json
import hashlib

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
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

    def open(self):
        return self.call(
            sender=self.sender,
            function='open',
            args=[dict(
                manifest_url=self.election.manifest_url,
                manifest_hash=self.election.manifest_sha1,
                open=str(timezone.now()),
            )],
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
            args=[dict(
                artifacts_url=self.election.artifacts_url,
                artifacts_hash=self.election.artifacts_sha1,
            )],
            state='deploy',
        )


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
