from datetime import datetime
import pytest

from django.urls import reverse

from djelectionguard.models import Candidate, Contest


@pytest.mark.django_db
def test_story(client):
    contest = Contest.objects.create(
        id='3743773f-d923-4b20-a5c6-b585a0c5662f',
        name='Test Contest',
        number_elected=2,
        votes_allowed=2,
        start=datetime.fromisoformat("2020-03-01T08:00:00-05:00"),
        end=datetime.fromisoformat("2020-03-01T20:00:00-05:00"),
    )
    contest.candidate_set.create(
        id='ae1f14fa-4b34-4a27-8efc-9016246905dc',
        name='Adams',
    )
    contest.candidate_set.create(
        id='38b8e19f-1447-47a3-8df3-8a42be422f9a',
        name='Lincoln',
    )
    contest.candidate_set.create(
        id='46dd83c8-26de-417d-9421-a61c5e5f4d36',
        name='Mozart',
    )

    response = client.get(contest.get_absolute_url() + 'manifest/')
    assert response.json() == {
        "geopolitical_units": [
            {
                "type": "school",
                "object_id": "3743773f-d923-4b20-a5c6-b585a0c5662f-unit",
                "name": "Test Contest",
            }
        ],
        "parties": [],
        "candidates": [
            {
                "object_id": "ae1f14fa-4b34-4a27-8efc-9016246905dc",
                "ballot_name": {
                    "text": [
                        {
                            "value": "Adams",
                            "language": "en"
                        }
                    ]
                }
            },
            {
                "object_id": "38b8e19f-1447-47a3-8df3-8a42be422f9a",
                "ballot_name": {
                    "text": [
                        {
                            "value": "Lincoln",
                            "language": "en"
                        }
                    ]
                }
            },
            {
                "object_id": "46dd83c8-26de-417d-9421-a61c5e5f4d36",
                "ballot_name": {
                    "text": [
                        {
                            "value": "Mozart",
                            "language": "en"
                        }
                    ]
                }
            },
        ],
        "contests": [
            {
                "@type": "CandidateContest",
                "object_id": "3743773f-d923-4b20-a5c6-b585a0c5662f",
                "sequence_order": 0,
                "ballot_selections": [
                    {
                        "object_id": "ae1f14fa-4b34-4a27-8efc-9016246905dc-selection",
                        "sequence_order": 0,
                        "candidate_id": "ae1f14fa-4b34-4a27-8efc-9016246905dc"
                    },
                    {
                        "object_id": "38b8e19f-1447-47a3-8df3-8a42be422f9a-selection",
                        "sequence_order": 1,
                        "candidate_id": "38b8e19f-1447-47a3-8df3-8a42be422f9a"
                    },
                    {
                        "object_id": "46dd83c8-26de-417d-9421-a61c5e5f4d36-selection",
                        "sequence_order": 2,
                        "candidate_id": "46dd83c8-26de-417d-9421-a61c5e5f4d36"
                    },
                ],
                "ballot_title": {
                    "text": [
                        {
                            "value": "Test Contest",
                            "language": "en"
                        }
                    ]
                },
                "ballot_subtitle": {
                    "text": [
                        {
                            "value": "Test Contest",
                            "language": "en"
                        }
                    ]
                },
                "vote_variation": "n_of_m",
                "electoral_district_id": "3743773f-d923-4b20-a5c6-b585a0c5662f-unit",
                "name": "Test Contest",
                "number_elected": 2,
                "votes_allowed": 2
            }
        ],
        "ballot_styles": [
            {
                "object_id": "3743773f-d923-4b20-a5c6-b585a0c5662f-style",
                "geopolitical_unit_ids": [
                    "3743773f-d923-4b20-a5c6-b585a0c5662f-unit"
                ]
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
        "election_scope_id": "3743773f-d923-4b20-a5c6-b585a0c5662f-style",
        "type": "primary"
    }
