import io
import pytest

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from djelectionguard.models import Candidate, Contest

User = apps.get_model(settings.AUTH_USER_MODEL)


def get(user, url):
    client = Client()
    client.force_login(user)
    url = url if '/' in url else reverse(url)
    return client.get(url)


def post(user, url, **data):
    client = Client()
    client.force_login(user)
    url = url if '/' in url else reverse(url)
    return client.post(url, data)


@pytest.mark.django_db
def test_story(client):
    external = User.objects.create(email='ext@example.com', is_active=True)
    voter1 = User.objects.create(email='vot1@example.com', is_active=True)
    new = User.objects.create(email='new@example.com', is_active=True)

    mediator = User.objects.create(email='med@example.com', is_active=True)
    response = post(
        mediator,
        'contest_create',
        name='Test Contest',
        number_elected=2,
        votes_allowed=2,
        start_0='2000-01-01',
        start_1='10:00',
        end_0='2000-01-02',
        end_1='10:00',
    )
    assert response.status_code == 302
    contest = Contest.objects.get(mediator=mediator)

    # mediator should have been added as default guardian
    assert contest.guardian_set.count() == 1

    contest_url = response['Location']

    # unauthorized users should not see the contest
    assert client.get(contest_url).status_code == 302
    assert get(external, contest_url).status_code == 404
    assert get(voter1, contest_url).status_code == 404

    # but mediator should find the voters edit link there
    response = get(mediator, contest_url)
    assert response.status_code == 200
    voters = f'{contest_url}voters/update/'
    assert voters in response.content.decode('utf8')

    # unauthorized users should not see voters update page
    assert client.get(voters).status_code == 302
    assert get(external, voters).status_code == 404
    assert get(voter1, voters).status_code == 404

    # mediator should see and update voters there
    response = get(mediator, voters)
    assert response.status_code == 200
    assert b'id_voters_emails' in response.content
    post(mediator, voters, voters_emails='\n\n\n\n')
    response = post(mediator, voters, voters_emails='''
vot1@example.com
vot2@example.com\r
mistake@example.com
    ''')
    assert response.status_code == 302

    # but not unauthorized users
    assert client.get(voters).status_code == 302
    assert post(external, voters, voters_emails='x@y').status_code == 404
    assert post(voter1, voters, voters_emails='x@y').status_code == 404

    # check that mediator update wa
    contest.refresh_from_db()
    assert contest.voters_emails == '''
vot1@example.com
vot2@example.com
mistake@example.com
    '''.strip()
    assert list(contest.voter_set.values_list('user__email', flat=True)) == [
        'vot1@example.com',
    ]

    # try another update again, removing one email, with macos
    response = post(mediator, voters, voters_emails='''
vot1@example.com\rvot2@example.com\rnew@example.com
    ''')
    contest.refresh_from_db()
    assert contest.voters_emails == '''
vot1@example.com
vot2@example.com
new@example.com
    '''.strip()
    assert list(contest.voter_set.values_list('user__email', flat=True)) == [
        'vot1@example.com', 'new@example.com',
    ]

    assert get(mediator, contest_url).status_code == 200

    candidate_create = f'{contest_url}candidates/create/'

    # unauthorized users should not see candidate_create page
    assert client.get(candidate_create).status_code == 302
    assert get(external, candidate_create).status_code == 404
    assert get(voter1, candidate_create).status_code == 404

    # mediator should see and use candidate_create there
    response = get(mediator, candidate_create)
    assert response.status_code == 200
    assert b'id_name' in response.content
    assert contest.candidate_set.count() == 0
    response = post(mediator, candidate_create, name='cand1')
    assert response.status_code == 302

    # but not unauthorized users
    assert client.get(candidate_create).status_code == 302
    assert post(external, candidate_create, candidate_create_emails='x@y').status_code == 404
    assert post(voter1, candidate_create, candidate_create_emails='x@y').status_code == 404

    # mediator update should have worked
    assert contest.candidate_set.count() == 1
    post(mediator, candidate_create, name='cand2')

    # we'll need another 2 candidates because we have number_elected=2
    assert contest.candidate_set.count() == 2
    post(mediator, candidate_create, name='cand3')
    assert contest.candidate_set.count() == 3

    # only the guardian should be able to download its key
    guardian = contest.guardian_set.get(user=mediator)
    guardian_url = f'/contest/guardian/{guardian.pk}/'
    download_url = f'{guardian_url}download/'
    response = get(mediator, download_url)
    assert response.status_code == 200
    guardian_key = b''.join(response.streaming_content)

    # but not others
    assert client.get(download_url).status_code == 302
    assert get(external, download_url).status_code == 404
    assert get(voter1, download_url).status_code == 404

    '''
    # including the other guardian that we'll add via the db for now
    # until we add a specific "Add guardian" endpoint
    guardian2 = contest.guardian_set.create(
        user=User.objects.create(email='g2@example.com', is_active=True)
    )
    # guardian2 should not see download url of guardian1
    assert get(guardian2.user, download_url).status_code == 404

    # let's download guardian2 key
    guardian2_url = f'/contest/guardian/{guardian2.pk}/'
    guardian2_key = b''.join(
        get(guardian2.user, f'{guardian2_url}download/').streaming_content
    )

    # only guardians should be able to use their respective key verify urls
    guardian2_verify = f'{guardian2_url}verify/'
    assert get(guardian2.user, guardian2_verify).status_code == 200
    assert client.get(guardian2_verify).status_code == 302
    assert get(mediator, guardian2_verify).status_code == 404
    assert get(external, guardian2_verify).status_code == 404
    assert get(voter1, guardian2_verify).status_code == 404

    # guardian2 should be the only one to verify a key on its url
    assert client.post(guardian2_verify).status_code == 302
    assert post(mediator, guardian2_verify).status_code == 404
    assert post(external, guardian2_verify).status_code == 404
    assert post(voter1, guardian2_verify).status_code == 404

    # guardian2 verify process
    guardian2.refresh_from_db()
    assert not guardian2.verified
    post(
        guardian2.user,
        guardian2_verify,
        pkl_file=io.BytesIO(guardian2_key)
    )
    guardian2.refresh_from_db()
    assert guardian2.verified

    '''
    # prior to verifying guardian (mediator as guardian), check that it
    # actually verifies the file
    guardian_verify = f'{guardian_url}verify/'
    '''
    guardian.refresh_from_db()
    assert not guardian.verified
    post(
        guardian.user,
        guardian_verify,
        pkl_file=io.BytesIO(guardian2_key)
    )
    guardian.refresh_from_db()
    assert not guardian.verified
    '''

    # now that we've proven actual verification, let's proceed
    post(
        guardian.user,
        guardian_verify,
        pkl_file=io.BytesIO(guardian_key)
    )
    guardian.refresh_from_db()
    assert guardian.verified

    # let's move on to creating the joint public key
    contest.refresh_from_db()
    assert not contest.joint_public_key

    # only the mediator should access the public key generation url
    pubkey = f'{contest_url}pubkey/'
    assert client.get(pubkey).status_code == 302
    #assert get(guardian2.user, pubkey).status_code == 404
    assert get(external, pubkey).status_code == 404
    assert get(voter1, pubkey).status_code == 404
    assert get(mediator, pubkey).status_code == 200

    assert client.post(pubkey).status_code == 302
    #assert post(guardian2.user, pubkey).status_code == 404
    assert post(external, pubkey).status_code == 404
    assert post(voter1, pubkey).status_code == 404
    assert post(mediator, pubkey).status_code == 302

    contest.refresh_from_db()
    assert contest.joint_public_key

    # nobody should have the vote pages for now
    vote = f'{contest_url}vote/'
    assert client.get(vote).status_code == 302, vote
    #assert get(guardian2.user, vote).status_code == 404, vote
    assert get(external, vote).status_code == 404, vote
    assert get(voter1, vote).status_code == 404, vote
    assert get(mediator, vote).status_code == 404, vote

    # ballot neither
    ballot = f'{contest_url}ballot/'
    assert client.get(ballot).status_code == 302, ballot
    #assert get(guardian2.user, ballot).status_code == 404, ballot
    assert get(external, ballot).status_code == 404, ballot
    assert get(voter1, ballot).status_code == 404, ballot
    assert get(mediator, ballot).status_code == 404, ballot

    # only mediator should be able to open the vote
    assert not contest.actual_start
    contest_open = f'{contest_url}open/'
    assert client.get(contest_open).status_code == 302
    #assert get(guardian2.user, contest_open).status_code == 404
    assert get(external, contest_open).status_code == 404
    assert get(voter1, contest_open).status_code == 404
    assert get(mediator, contest_open).status_code == 200

    assert client.post(contest_open).status_code == 302
    #assert post(guardian2.user, contest_open).status_code == 404
    assert post(external, contest_open).status_code == 404
    assert post(voter1, contest_open).status_code == 404
    assert post(mediator, contest_open).status_code == 302

    contest.refresh_from_db()
    assert contest.actual_start

    # cannot open again
    assert get(mediator, contest_open).status_code == 404

    # vote page becomes visible to voter1
    vote = f'{contest_url}vote/'
    assert client.get(vote).status_code == 302, vote
    #assert get(guardian2.user, vote).status_code == 404, vote
    assert get(external, vote).status_code == 404, vote
    assert get(voter1, vote).status_code == 200, vote
    assert get(mediator, vote).status_code == 404, vote

    # voter2 just registered, they should access the page too
    voter2 = User.objects.create(email='vot2@example.com', is_active=True)
    assert get(voter2, vote).status_code == 200, vote

    # let's vote!
    candidates = [
        str(i)
        for i in contest.candidate_set.values_list('pk', flat=True)
    ]
    response = post(
        voter1,
        vote,
        selections=(candidates[0], candidates[1])
    )
    ballot = f'{contest_url}ballot/'
    assert response.url == ballot
    assert not voter1.voter_set.get(contest=contest).casted

    # ballot view should be visible to voter1 only
    assert client.get(ballot).status_code == 302, ballot
    #assert get(guardian2.user, ballot).status_code == 404, ballot
    assert get(external, ballot).status_code == 404, ballot
    assert get(voter1, ballot).status_code == 200, ballot
    assert get(voter2, ballot).status_code == 302, ballot
    assert get(mediator, ballot).status_code == 404, ballot

    # voter2 creates ballot
    response = post(
        voter2,
        vote,
        selections=(candidates[1],)
    )
    assert response.url == ballot
    assert get(voter2, ballot).status_code == 200, ballot

    # voter1 encrypts
    response = post(voter1, ballot)
    cast = f'{contest_url}ballot/cast/'
    assert response.url == cast
    assert not voter1.voter_set.get(contest=contest).casted

    # and casts, then cannot vote again
    response = post(voter1, cast)
    assert voter1.voter_set.get(contest=contest).casted
    assert get(voter1, vote).status_code == 404, vote
    assert get(voter1, ballot).status_code == 404, vote
    assert get(voter1, cast).status_code == 404, vote

    # let's close the vote ... if we're mediator
    contest.refresh_from_db()
    assert not contest.actual_end
    close = f'{contest_url}close/'
    assert client.get(close).status_code == 302
    #assert get(guardian2.user, close).status_code == 404
    assert get(external, close).status_code == 404
    assert get(voter1, close).status_code == 404
    assert get(voter2, close).status_code == 404
    assert get(mediator, close).status_code == 200

    assert client.post(close).status_code == 302
    #assert post(guardian2.user, close).status_code == 404
    assert post(external, close).status_code == 404
    assert post(voter1, close).status_code == 404
    assert post(voter2, close).status_code == 404
    assert post(mediator, close).status_code == 302
    contest.refresh_from_db()
    assert contest.actual_end

    # only guardians should be able to use their respective key upload urls
    guardian_upload = f'{guardian_url}upload/'
    assert get(guardian.user, guardian_upload).status_code == 200
    assert client.get(guardian_upload).status_code == 302
    assert get(mediator, guardian_upload).status_code == 200
    assert get(external, guardian_upload).status_code == 404
    assert get(voter1, guardian_upload).status_code == 404
    #assert get(guardian2.user, guardian_upload).status_code == 404

    # guardian should be the only one to upload a key on its url
    assert client.post(guardian_upload).status_code == 302
    assert post(external, guardian_upload).status_code == 404
    assert post(voter1, guardian_upload).status_code == 404
    #assert post(guardian2.user, guardian_upload).status_code == 404

    # actually post first guardian key
    guardian.refresh_from_db()
    assert not guardian.uploaded
    response = post(
        guardian.user,
        guardian_upload,
        pkl_file=io.BytesIO(guardian_key)
    )
    assert response.status_code == 302
    guardian.refresh_from_db()
    assert guardian.uploaded
    '''
    # and the next one
    guardian2_upload = f'{guardian2_url}upload/'
    response = post(
        guardian2.user,
        guardian2_upload,
        pkl_file=io.BytesIO(guardian2_key)
    )
    assert response.status_code == 302
    guardian2.refresh_from_db()
    assert guardian2.uploaded
    '''

    # only mediator should be able to see decrypt page
    decrypt = f'{contest_url}decrypt/'
    assert client.get(decrypt).status_code == 302
    assert get(mediator, decrypt).status_code == 200
    assert get(external, decrypt).status_code == 404
    assert get(voter1, decrypt).status_code == 404
    #assert get(guardian2.user, decrypt).status_code == 404
    # and eventually decrypt
    assert client.post(decrypt).status_code == 302
    assert post(external, decrypt).status_code == 404
    assert post(voter1, decrypt).status_code == 404
    #assert post(guardian2.user, decrypt).status_code == 404

    # decrypt tally
    assert post(mediator, decrypt).status_code == 302
    score = lambda pk: contest.candidate_set.get(pk=pk).score
    assert score(candidates[0]) == 1
    assert score(candidates[1]) == 1
    assert score(candidates[2]) == 0
