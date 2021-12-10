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

from django.utils.translation import gettext_lazy as _
from django.conf import settings

from electeez_auth.models import User
from electeez_sites.models import Site
from ckeditor.fields import RichTextField

def above_0(value):
    if value <= 0:
        raise ValidationError(
            _('Must be above 0, you have choosen:') + f'{value}'
        )

def upload_picture(instance, filename):
    return f'{uuid.uuid4()}.{filename.split(".")[-1]}'

class ParentContest(models.Model):

    STATUS = (
        ('draft', 'DRAFT'),
        ('open', 'OPEN'),
        ('closed', 'CLOSED')
    )

    uid = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4
    )
    name = models.CharField(max_length=255)
    start = models.DateTimeField()
    end = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True, db_index=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    timezone = TimeZoneField(
        choices_display='WITH_GMT_OFFSET',
        default='Europe/Paris',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default='draft',
        null=True
    )
    mediator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True, null=True
    )

    def __str__(self):
        return self.name

    # def get_absolute_url(self):
    #     return reverse('parentcontest_list', args=[self.pk])

    def get_absolute_url(self):
        return reverse('parentcontest_detail', args=[self.pk])



class Recommender(models.Model):
    name = models.CharField(max_length=255)
    recommender_type = models.CharField(max_length=255, blank=True)
    picture = models.ImageField(
        upload_to=upload_picture,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name

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
    about = models.CharField(
        max_length=2048,
        blank=True,
        null=True
    )
    referendum_type = models.CharField(null=True, max_length=100)
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

    actual_start = models.DateTimeField(null=True, blank=True, db_index=True)
    actual_end = models.DateTimeField(null=True, blank=True)

    decrypting = models.BooleanField(default=False)

    joint_public_key = PickledObjectField(null=True, blank=True)
    metadata = PickledObjectField(null=True)
    context = PickledObjectField(null=True)
    device = PickledObjectField(null=True)
    store = PickledObjectField(null=True)
    plaintext_tally = PickledObjectField(null=True)
    plaintext_spoiled_ballots = PickledObjectField(null=True)
    ciphertext_tally = PickledObjectField(null=True)
    coefficient_validation_sets = PickledObjectField(null=True)

    artifacts_sha1 = models.CharField(max_length=255, null=True, blank=True)
    artifacts_ipfs = models.CharField(max_length=255, null=True, blank=True)

    parent = models.ForeignKey(
        ParentContest,
        related_name='parent',
        on_delete=models.CASCADE,
        null=True
    )
    initiator = models.ForeignKey(
        Recommender,
        on_delete=models.CASCADE,
        null=True
    )
    infavour_arguments = RichTextField(
        null=True
    )
    against_arguments = RichTextField(
        null=True
    )

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
            self.description.to_json().encode('utf8')
        ).hexdigest()

    def launch_decryption(
            self,
            send_voters_email,
            email_title,
            email_body,
    ):
        if self.decrypting or self.plaintext_tally:
            return

        self.decrypting = True
        self.save()

        Caller(
            callback='djelectionguard.models.decrypt_contest',
            kwargs=dict(
                contest_id=str(self.pk),
                user_id=self.mediator.pk,
                send_voters_email=send_voters_email,
                voters_email_title=email_title,
                voters_email_msg=email_body
            ),
        ).spool('tally')

    def decrypt(self):
        from electionguard.tally import tally_ballots
        self.ciphertext_tally = tally_ballots(self.store, self.metadata, self.context)

        from electionguard.decryption_mediator import DecryptionMediator
        decryption_mediator = self.decrypter

        from electionguard.ballot import BallotBoxState
        from electionguard.ballot_box import get_ballots
        submitted_ballots = get_ballots(self.store, BallotBoxState.CAST)
        submitted_ballots_list = list(submitted_ballots.values())

        # Decrypt the tally with available guardian keys
        for g in self.guardian_set.all().order_by('sequence'):
            guardian = g.get_guardian()
            guardian_key = guardian.share_election_public_key()
            tally_share = guardian.compute_tally_share(
                self.ciphertext_tally, self.context
            )
            ballot_shares = guardian.compute_ballot_shares(
                submitted_ballots_list, self.context
            )
            decryption_mediator.announce(
                guardian_key, tally_share, ballot_shares
            )

        self.plaintext_tally = decryption_mediator.get_plaintext_tally(
            self.ciphertext_tally
        )
        if not self.plaintext_tally:
            raise AttributeError('"self.plaintext_tally" is None')

        self.plaintext_spoiled_ballots = decryption_mediator.get_plaintext_ballots([])

        # And delete keys from memory
        for guardian in self.guardian_set.all():
            guardian.delete_keypair()

        self.save()

        plaintext_tally_contest = self.plaintext_tally.contests[str(self.pk)]
        for candidate in self.candidate_set.all():
            candidate.score = plaintext_tally_contest.selections[f'{candidate.pk}-selection'].tally
            candidate.save()

        self.decrypting = False
        self.save()
        self.publish()

    def publish(self):
        cwd = os.getcwd()

        # provision directory path
        from electionguard.election import ElectionConstants
        from electionguard.publish import publish
        self.artifacts_path.mkdir(parents=True, exist_ok=True)
        os.chdir(self.artifacts_path)
        publish(
            self.description,
            self.context,
            ElectionConstants(),
            [self.device],
            self.store.all(),
            [],
            self.ciphertext_tally.publish(),
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
        self.save()

        os.chdir(cwd)

    def publish_ipfs(self):
        try:
            url = settings.IPFS_URL + '/api/v0/'
            out = subprocess.check_output(
                ['curl', '-F', f'file=@{self.artifacts_zip_path}', url+'add'],
                stderr=subprocess.PIPE,
            )
            result = json.loads(out)
            self.artifacts_ipfs = result['Hash']
            self.save()
            out = subprocess.check_output(
                ['curl', '-X', 'POST', url+f'pin/add?arg={self.artifacts_ipfs}'],
                stderr=subprocess.PIPE,
            )
        except Exception as e:
            print(e)
            print('Could not upload to IPFS, see error above')

    @property
    def state(self):
        if self.actual_end:
            return 'finished'
        elif self.actual_start:
            return 'started'
        return 'pending'


    @property
    def publish_state(self):
        if self.artifacts_ipfs:
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
            object_id=str(uuid.uuid4()),
            style_id=f"{self.pk}-style",
            contests=[
                PlaintextBallotContest(
                    object_id=str(self.pk),
                    ballot_selections=[
                        PlaintextBallotSelection(
                            object_id=f"{selection}-selection",
                            vote=1,
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
        from electionguard.manifest import Manifest
        return Manifest.from_json_object(
            self.get_manifest()
        )

    def prepare(self):
        from electionguard.election_builder import ElectionBuilder
        builder = ElectionBuilder(
            number_of_guardians=self.number_guardians,
            quorum=self.quorum,
            manifest=self.description,
        )
        builder.set_public_key(self.joint_public_key.joint_public_key)
        builder.set_commitment_hash(self.joint_public_key.commitment_hash)

        self.metadata, self.context = builder.build()
        from electionguard.data_store import DataStore
        self.store = DataStore()

        from electionguard.encrypt import EncryptionDevice, EncryptionMediator, generate_device_uuid
        self.device = EncryptionDevice(
            generate_device_uuid(),
            12345,
            67890,
            str(self.pk),  # location: str
        )

    @property
    def encrypter(self):
        from electionguard.encrypt import EncryptionMediator
        return EncryptionMediator(
            self.metadata,
            self.context,
            self.device,
        )

    @property
    def decrypter(self):
        from electionguard.decryption_mediator import DecryptionMediator
        return DecryptionMediator(
            'decryption-mediator',
            self.context,
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
                    "name": {
                        "text": []
                    }
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
            "type": "primary",
            "spec_version": "v1.2.1"
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

    if f := getattr(voter, field):
        return

    otp_link = voter.user.otp_new(redirect=link).url
    voter.user.save()
    send_mail(
        title,
        body.replace('LINK', otp_link),
        settings.DEFAULT_FROM_EMAIL,
        [voter.user.email],
    )

    setattr(voter, field, timezone.now())
    voter.save()


def decrypt_contest(
        contest_id,
        user_id,
        send_voters_email,
        voters_email_title,
        voters_email_msg
):
    from djlang.utils import gettext as _

    contest = None
    med_email_msg = None
    has_error = True
    user = User.objects.get(id=user_id)
    try:
        contest = Contest.objects.get(id=contest_id)
        contest.decrypt()
        has_error = False
        med_email_msg = _('The contest %(contest)s has been tallied', contest=contest.name)

    except Contest.DoesNotExist:
        med_email_msg = _('The contest you wanted to decrypt was not found')
    except Exception as e:
        med_email_msg = _(
            'The decryption raised the exception %(exception)s',
            exception=e
        )
    finally:
        if med_email_msg:
            send_mail(
                _(
                    'Contest %(contest)s decryption',
                    contest=contest.name if contest else _('unknown')
                ),
                med_email_msg,
                settings.DEFAULT_FROM_EMAIL,
                [user.email]
            )

        if send_voters_email and not has_error:
            contest.send_mail(
                voters_email_title,
                voters_email_msg,
                reverse('contest_detail', args=[contest_id]),
                'close_email_sent'
            )




class Candidate(models.Model):
    CANDIDATE_TYPE = (
        ('yes', 'YES'),
        ('no', 'NO'),
        ('others', 'OTHERS'),
    )

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
    subtext = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    description = models.CharField(
        max_length=300,
        blank=True,
        null=True
    )
    picture = models.ImageField(
        upload_to=upload_picture,
        blank=True,
        null=True
    )
    score = models.IntegerField(null=True)

    candidate_type = models.CharField(
        max_length=10,
        choices=CANDIDATE_TYPE,
        null=True
    )

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
    key_sha1 = models.CharField(max_length=255, null=True, blank=True)

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
            self.key_sha1 = hashlib.sha1(result).hexdigest()
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
    casted = models.BooleanField(null=True, blank=True)
    ballot_id = models.UUIDField(null=True, blank=True)
    ballot_sha1 = models.CharField(max_length=255, null=True, blank=True)
    open_email_sent = models.DateTimeField(null=True, blank=True)
    close_email_sent = models.DateTimeField(null=True, blank=True)




class ContestRecommender(models.Model):

    RECOMMENDER_TYPE = (
        ('infavour', 'IN FAVOUR'),
        ('against', 'AGAINST'),
    )

    contest = models.ForeignKey(
        Contest,
        on_delete=models.CASCADE,
        null=True
    )
    recommender = models.ForeignKey(
        Recommender,
        on_delete=models.CASCADE,
        null=True
    )
    recommender_type = models.CharField(
        max_length=20,
        choices=RECOMMENDER_TYPE,
        null=True
    )
