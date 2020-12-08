import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse


class Contest(models.Model):
    id = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4
    )
    name = models.CharField(max_length=255)
    type = models.CharField(default='school', max_length=100)
    number_elected = models.IntegerField(default=1)
    votes_allowed = models.IntegerField(default=1)
    start = models.DateTimeField()
    end = models.DateTimeField()
    state = models.CharField(
        max_length=10,
        db_index=True,
        default='planned',
        choices=(
            ('planned', 'Planned'),
            ('ongoing', 'Ongoing'),
            ('finished', 'Finished'),
        )
    )

    @property
    def variation(self):
        return 'one_of_m' if self.votes_allowed == 1 else 'n_of_m'

    def get_absolute_url(self):
        return reverse('contest_detail', args=[self.pk])

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

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Ballot(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    encrypted = models.TextField(blank=True)
