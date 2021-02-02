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
                manifest_url=''.join([
                    settings.BASE_URL,
                    reverse('contest_manifest', args=[self.election.pk]),
                ]),
                manifest_hash=hashlib.sha1(
                    json.dumps(self.election.get_manifest()).encode('utf8'),
                ).hexdigest(),
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

    def artifacts(self, hexdigest):
        return self.call(
            sender=self.sender,
            function='artifacts',
            args=[dict(
                artifacts_url=''.join([
                    settings.BASE_URL[:-1],
                    settings.MEDIA_URL,
                    f'contests/contest-{self.election.pk}.zip',
                ]),
                artifacts_hash=hexdigest,
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
