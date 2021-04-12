import hashlib
import json
import os
from pathlib import Path
import pickle
import shutil
import subprocess
import uuid

from enum import IntEnum

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import models, transaction
from django.db.models import signals
from django.urls import reverse
from django.utils import timezone

from djcall.models import Caller
from pymemcache.client.base import Client
from picklefield.fields import PickledObjectField
from timezone_field import TimeZoneField


def above_0(value):
    if value <= 0:
        raise ValidationError(
            f'Must be above 0, you have choosen: {value}'
        )


class Contest(models.Model):
    id = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4
    )
    mediator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=255)
    type = models.CharField(default='school', max_length=100)
    votes_allowed = models.PositiveIntegerField(
        default=1,
        validators=[above_0],
    )
    quorum = models.IntegerField(
        default=1,
        verbose_name='quorum',
    )
    start = models.DateTimeField()
    end = models.DateTimeField()
    timezone = TimeZoneField(
        choices_display='WITH_GMT_OFFSET',
        default='Europe/Paris',
    )

    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)

    joint_public_key = PickledObjectField(null=True, blank=True)
    metadata = PickledObjectField(null=True)
    context = PickledObjectField(null=True)
    device = PickledObjectField(null=True)
    store = PickledObjectField(null=True)
    plaintext_tally = PickledObjectField(null=True)
    ciphertext_tally = PickledObjectField(null=True)
    coefficient_validation_sets = PickledObjectField(null=True)

    artifacts_sha1 = models.CharField(max_length=255, null=True, blank=True)
    artifacts_ipfs = models.CharField(max_length=255, null=True, blank=True)

    class PublishStates(IntEnum):
        ELECTION_NOT_DECENTRALIZED = 0,
        ELECTION_CONTRACT_CREATED = 1,
        ELECTION_OPENED = 2,
        ELECTION_CLOSED = 3,
        ELECTION_DECRYPTED = 4,
        ELECTION_PUBLISHED = 5

    @property
    def number_elected(self):
        return self.votes_allowed

    @property
    def number_guardians(self):
        return self.guardian_set.count()

    @property
    def current_sequence(self):
        client = Client(settings.MEMCACHED_HOST)
        sequence = int(client.get(f'{self.pk}.sequence', 1))
        client.set(f'{self.pk}.sequence', sequence + 1)
        return sequence

    @property
    def artifacts_path(self):
        return (
            Path(settings.MEDIA_ROOT)
            / 'artifacts'
            / f'contest-{self.pk}'
        )

    @property
    def artifacts_zip_path(self):
        return Path(str(self.artifacts_path) + '.zip')

    @property
    def artifacts_url(self):
        if self.artifacts_ipfs_url:
            return self.artifacts_ipfs_url
        return self.artifacts_local_url

    @property
    def artifacts_local_url(self):
        return ''.join([
            settings.BASE_URL,
            settings.MEDIA_URL,
            'artifacts/',
            f'contest-{self.pk}.zip',
        ])

    @property
    def artifacts_ipfs_url(self):
        if self.artifacts_ipfs:
            return 'https://ipfs.io/ipfs/' + self.artifacts_ipfs

    @property
    def manifest_url(self):
        return ''.join([
            settings.BASE_URL,
            reverse('contest_manifest', args=[self.pk]),
        ])

    @property
    def manifest_sha1(self):
        return hashlib.sha1(
            json.dumps(self.get_manifest()).encode('utf8'),
        ).hexdigest()

    def decrypt(self):
        from electionguard.tally import CiphertextTally
        self.ciphertext_tally = CiphertextTally(
            f'{self.pk}-tally',
            self.metadata,
            self.context,
        )
        for ballot in self.store.all():
            assert self.ciphertext_tally.append(ballot)

        from electionguard.decryption_mediator import DecryptionMediator
        decryption_mediator = DecryptionMediator(
            self.metadata,
            self.context,
            self.ciphertext_tally,
        )

        # Decrypt the tally with available guardian keys
        for guardian in self.guardian_set.all().order_by('sequence'):
            if decryption_mediator.announce(guardian.get_guardian()) is None:
                break
        self.plaintext_tally = decryption_mediator.get_plaintext_tally()
        if not self.plaintext_tally:
            raise AttributeError('"self.plaintext_tally" is None')

        # And delete keys from memory
        for guardian in self.guardian_set.all():
            guardian.delete_keypair()

        self.save()

        plaintext_tally_contest = self.plaintext_tally.contests[str(self.pk)]
        for candidate in self.candidate_set.all():
            candidate.score = plaintext_tally_contest.selections[f'{candidate.pk}-selection'].tally
            candidate.save()

    def publish(self):
        cwd = os.getcwd()

        # provision directory path
        from electionguard.election import ElectionConstants
        from electionguard.publish import publish
        from electionguard.tally import publish_ciphertext_tally
        self.artifacts_path.mkdir(parents=True, exist_ok=True)
        os.chdir(self.artifacts_path)
        publish(
            self.description,
            self.context,
            ElectionConstants(),
            [self.device],
            self.store.all(),
            self.ciphertext_tally.spoiled_ballots.values(),
            publish_ciphertext_tally(self.ciphertext_tally),
            self.plaintext_tally,
            self.coefficient_validation_sets,
        )

        # create the zip file of key to key.zip
        os.chdir(self.artifacts_path / '..')
        name = f'contest-{self.pk}'
        shutil.make_archive(name, 'zip', name)

        sha1 = hashlib.sha1()
        with self.artifacts_zip_path.open('rb') as f:
            while data := f.read(65536):
                sha1.update(data)
        self.artifacts_sha1 = sha1.hexdigest()

        os.chdir(cwd)

    def publish_ipfs(self):
        try:
            out = subprocess.check_output(
                ['ipfs', 'add', self.artifacts_zip_path],
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError as e:
            print(e)
            print('Could not upload to IPFS, see error above')
        else:
            print(out.decode('utf8'))
            address = out.split(b' ')[1].decode('utf8')
            self.artifacts_ipfs = address
            self.save()

    @property
    def state(self):
        if self.actual_end:
            return 'finished'
        elif self.actual_start:
            return 'started'
        return 'pending'


    @property
    def publish_state(self):
        if self.artifacts_sha1:
            return self.PublishStates.ELECTION_PUBLISHED
        elif self.plaintext_tally:
            return self.PublishStates.ELECTION_DECRYPTED
        elif self.actual_end:
            return self.PublishStates.ELECTION_CLOSED
        elif self.actual_start:
            return self.PublishStates.ELECTION_OPENED
        elif getattr(self, 'electioncontract', None):
            return self.PublishStates.ELECTION_CONTRACT_CREATED
        else:
            return self.PublishStates.ELECTION_NOT_DECENTRALIZED

    @property
    def variation(self):
        return 'one_of_m' if self.votes_allowed == 1 else 'n_of_m'

    def get_absolute_url(self):
        return reverse('contest_detail', args=[self.pk])

    def get_ballot(self, *selections):
        from electionguard.ballot import (
            PlaintextBallot,
            PlaintextBallotContest,
            PlaintextBallotSelection,
        )
        ballot = PlaintextBallot(
            object_id=uuid.uuid4(),
            ballot_style=f"{self.pk}-style",
            contests=[
                PlaintextBallotContest(
                    object_id=str(self.pk),
                    ballot_selections=[
                        PlaintextBallotSelection(
                            object_id=f"{selection}-selection",
                            vote='True',
                            is_placeholder_selection=False,
                            extended_data=None,
                        ) for selection in selections
                    ]
                )
            ]
        )
        return ballot

    @property
    def description(self):
        from electionguard.election import ElectionDescription
        return ElectionDescription.from_json_object(
            self.get_manifest()
        )

    def prepare(self):
        from electionguard.election_builder import ElectionBuilder
        builder = ElectionBuilder(
            number_of_guardians=self.number_guardians,
            quorum=self.quorum,
            description=self.description,
        )
        builder.set_public_key(self.joint_public_key)

        self.metadata, self.context = builder.build()
        from electionguard.ballot_store import BallotStore
        self.store = BallotStore()

        from electionguard.encrypt import EncryptionDevice, EncryptionMediator
        self.device = EncryptionDevice(str(self.pk))

    @property
    def encrypter(self):
        from electionguard.encrypt import EncryptionMediator
        return EncryptionMediator(
            self.metadata,
            self.context,
            self.device,
        )

    @property
    def ballot_box(self):
        from electionguard.ballot_box import BallotBox
        return BallotBox(self.metadata, self.context, self.store)

    def get_manifest(self):
        return {
            "geopolitical_units": [
                {
                    "type": self.type,
                    "name": self.name,
                    "object_id": str(self.pk) + '-unit',
                },
            ],
            "parties": [],
            "candidates": [
                {
                    "object_id": str(candidate.pk),
                    "ballot_name": {
                        "text": [
                            {
                                "language": 'en',
                                "value": candidate.name,
                            }
                        ]
                    },
                } for candidate in self.candidate_set.all()
            ],
            "contests": [
                {
                    "@type": "CandidateContest",
                    "object_id": str(self.pk),
                    "sequence_order": 0,
                    "ballot_selections": [
                        {
                            "object_id": f"{candidate.pk}-selection",
                            "sequence_order": i,
                            "candidate_id": str(candidate.pk),
                        }
                        for i, candidate in enumerate(self.candidate_set.all())
                    ],
                    "ballot_title": {
                        "text": [
                            {
                                "value": self.name,
                                "language": "en"
                            }
                        ]
                    },
                    "ballot_subtitle": {
                        "text": [
                            {
                                "value": self.name,
                                "language": "en"
                            }
                        ]
                    },
                    "vote_variation": self.variation,
                    "electoral_district_id": f"{self.pk}-unit",
                    "name": self.name,
                    "number_elected": self.number_elected,
                    "votes_allowed": self.votes_allowed,
                }
            ],
            "ballot_styles": [
                {
                    "object_id": f"{self.pk}-style",
                    "geopolitical_unit_ids": [f"{self.pk}-unit"],
                }
            ],
            "name": {
                "text": [
                    {
                        "value": "Test Contest",
                        "language": "en"
                    }
                ]
            },
            "start_date": "2020-03-01T08:00:00-05:00",
            "end_date": "2020-03-01T20:00:00-05:00",
            "election_scope_id": f"{self.pk}-style",
            "type": "primary"
        }

    def __str__(self):
        return self.name

    def send_mail(self, title, body, link, field):
        Caller(
            callback='djelectionguard.models.send_contest_mail',
            kwargs=dict(
                contest_id=str(self.pk),
                title=title,
                body=body,
                link=link,
                field=field,
            ),
        ).spool('email')


def send_contest_mail(contest_id, title, body, link, field, **kwargs):
    voters_pks = Voter.objects.filter(
        contest__pk=contest_id
    ).values_list('pk', flat=True)

    for pk in voters_pks:
        Caller(
            callback='djelectionguard.models.send_voter_mail',
            max_attempts=25,
            kwargs=dict(
                voter_id=str(pk),
                title=title,
                body=body,
                link=link,
                field=field,
            ),
        ).spool('email')


def send_voter_mail(voter_id, title, body, link, field):
    voter = Voter.objects.select_related('user').get(pk=voter_id)
    otp_link = voter.user.otp_new(redirect=link).url
    voter.user.save()
    send_mail(
        title,
        body.replace('LINK', otp_link),
        'webmaster@electeez.com',
        [voter.user.email],
    )

    setattr(voter, field, timezone.now())
    voter.save()


class Candidate(models.Model):
    id = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4
    )
    contest = models.ForeignKey(
        Contest,
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=255)
    description = models.CharField(
        max_length=1024,
        blank=True,
        null=True
    )
    picture = models.ImageField(
        upload_to='candidates',
        blank=True,
        null=True
    )
    score = models.IntegerField(null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-score', 'name']
        unique_together = [('name', 'contest')]


class Guardian(models.Model):
    id = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4
    )
    contest = models.ForeignKey(
        Contest,
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    created = models.DateTimeField(auto_now_add=True)
    downloaded = models.DateTimeField(null=True, blank=True)
    verified = models.DateTimeField(null=True, blank=True)
    erased = models.DateTimeField(null=True, blank=True)
    uploaded = models.DateTimeField(null=True, blank=True)
    uploaded_erased = models.DateTimeField(null=True, blank=True)
    sequence = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return str(self.user)

    class Meta:
        ordering = ['created']

    def delete_keypair(self):
        Client(settings.MEMCACHED_HOST).delete(str(self.pk))
        if not self.uploaded:
            self.erased = timezone.now()
        else:
            self.uploaded_erased = timezone.now()
        self.save()

    def upload_keypair(self, content):
        Client(settings.MEMCACHED_HOST).set(str(self.pk), content)
        self.uploaded = timezone.now()
        self.save()

    def get_keypair(self):
        client = Client(settings.MEMCACHED_HOST)
        result = client.get(str(self.pk))
        if not result:
            from electionguard.guardian import Guardian
            sequence = self.contest.current_sequence
            guardian = Guardian(
                f'guardian-{self.pk}',
                sequence,
                self.contest.number_guardians,
                self.contest.quorum,
            )
            result = pickle.dumps(guardian)
            client.set(str(self.pk), result)
            self.sequence = sequence
            self.save()
        return result

    def get_guardian(self):
        return pickle.loads(self.get_keypair())


class Voter(models.Model):
    id = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4
    )
    contest = models.ForeignKey(
        Contest,
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    casted = models.DateTimeField(null=True, blank=True)
    open_email_sent = models.DateTimeField(null=True, blank=True)
    close_email_sent = models.DateTimeField(null=True, blank=True)
