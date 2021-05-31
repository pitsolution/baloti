import io
import pytest
import re

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import Client
from django.urls import reverse
from djelectionguard.models import Candidate, Contest, Voter
from djelectionguard.views import VotersEmailsForm, VotersEmailsField

User = apps.get_model(settings.AUTH_USER_MODEL)


@pytest.mark.django_db
def test_voters_emails_validation(contest):
    form = VotersEmailsForm(
        dict(
            voters_emails='''
                lol
                test@example.com
                foo
                test2@example.com
            '''
        ),
        instance=contest,
    )

    assert not form.is_valid()

    msg = 'Please remove lines containing invalid emails: lol, foo'
    assert form.errors['voters_emails'] == [msg]

    form = VotersEmailsForm(
        dict(
            voters_emails='''
                test@example.com
                test2@example.com
            '''
        ),
        instance=contest,
    )
    assert form.is_valid()


@pytest.mark.django_db
def test_voters_emails_save(contest):
    existing = User.objects.create(email='existing@example.com')
    Voter.objects.create(user=existing, contest=contest)

    deleted = User.objects.create(email='deleted@example.com')
    Voter.objects.create(user=deleted, contest=contest)

    form = VotersEmailsForm(
        dict(
            voters_emails='''
                new@example.com
                existing@example.com
            '''
        ),
        instance=contest,
    )
    assert form.is_valid()
    form.save()
    assert list(contest.voter_set.values_list('user__email', flat=True)) == [
        'existing@example.com',
        'new@example.com',
    ]


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


@pytest.fixture
def mediator():
    return User.objects.create(email='med@example.com', is_active=True)


@pytest.mark.django_db
def test_story(client, mediator, mailoutbox):
    external = User.objects.create(email='ext@example.com', is_active=True)
    voter1 = User.objects.create(email='vot1@example.com', is_active=True)
    new = User.objects.create(email='new@example.com', is_active=True)

    response = post(
        mediator,
        'contest_create',
        name='Test Contest',
        about='about contest',
        number_elected=2,
        votes_allowed=2,
        start_0='2000-01-01',
        start_1='10:00',
        end_0='2000-01-02',
        end_1='10:00',
        timezone='Europe/Paris',
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
vot1@example.com\rvot2@example.com\rnew@example.com
    ''')
    assert response.status_code == 302

    # but not unauthorized users
    assert client.get(voters).status_code == 302
    assert post(external, voters, voters_emails='x@y').status_code == 404
    assert post(voter1, voters, voters_emails='x@y').status_code == 404

    # check that mediator update was saved and lowercased
    contest.refresh_from_db()
    voters_emails = list(
        contest.voter_set.values_list(
            'user__email',
            flat=True,
        ).order_by('user__email')
    )
    assert voters_emails == [
        'new@example.com',
        'vot1@example.com',
        'vot2@example.com'
    ]
    # check that the emails are in the textarea
    response = get(mediator, voters)
    for voter_email in voters_emails:
        assert voter_email.encode('utf8') in response.content

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
    response = post(mediator, candidate_create, name='cand1', description='desc')
    assert response.status_code == 302

    # but not unauthorized users
    assert client.get(candidate_create).status_code == 302
    assert post(external, candidate_create, candidate_create_emails='x@y').status_code == 404
    assert post(voter1, candidate_create, candidate_create_emails='x@y').status_code == 404

    # mediator update should have worked
    assert contest.candidate_set.count() == 1
    post(mediator, candidate_create, name='cand2', description='desc')

    # we'll need another 2 candidates because we have number_elected=2
    assert contest.candidate_set.count() == 2
    post(mediator, candidate_create, name='cand3', description='desc')
    assert contest.candidate_set.count() == 3

    # only the guardian should be able to download its key
    guardian = contest.guardian_set.get(user=mediator)
    guardian_url = f'/en/contest/guardian/{guardian.pk}/'
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
    contract = f'/en/tezos/{contest.id}/create/'
    assert client.get(pubkey).status_code == 302
    #assert get(guardian2.user, pubkey).status_code == 404
    assert get(external, pubkey).status_code == 404
    assert get(voter1, pubkey).status_code == 404
    assert get(mediator, pubkey).status_code == 404
    from djtezos.models import Blockchain
    blockchain = Blockchain.objects.create(
        name='fake',
        provider_class='djtezos.fake.Provider',
        confirmation_blocks=0,
        is_active=True,
        endpoint='http://localhost:1337',
        explorer='http://localhost:1337/',
    )
    res = post(mediator, contract, blockchain=blockchain.id)
    assert res.status_code == 302
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
    assert get(voter1, vote).status_code == 302, vote
    assert get(mediator, vote).status_code == 404, vote

    candidate = contest.candidate_set.first()
    candidate_delete = f'/en/contest/candidates/{candidate.id}/delete/'

    # mediator can delete candidate
    assert get(mediator, candidate_delete).status_code == 302
    assert not contest.actual_start
    contest_open = f'{contest_url}open/'

    # open is not permitted due to candidate number
    res = post(
        mediator,
        contest_open,
        email_title='title',
        email_message='Hi LINK')
    assert res.status_code == 200
    assert (
        'Must have more candidates than number elected'
        in res.context_data['form'].non_field_errors()
    )
    contest.candidate_set.create(name=candidate.name, description='desc')

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
    assert post(
        mediator,
        contest_open,
        email_title='title',
        email_message='Hi LINK'
    ).status_code == 302

    contest.refresh_from_db()
    assert contest.actual_start

    # cannot open again
    assert get(mediator, contest_open).status_code == 404

    # cannot create candidate or update contest params
    assert get(mediator, contest_url+'update/').status_code == 404
    assert get(mediator, candidate_create).status_code == 404

    # can update voters list
    assert get(mediator, voters).status_code == 200

    candidate = contest.candidate_set.first()
    candidate_update = f'/en/contest/candidates/{candidate.id}/update/'
    assert get(mediator, candidate_update).status_code == 404

    candidate_delete = f'/en/contest/candidates/{candidate.id}/delete/'
    assert get(mediator, candidate_update).status_code == 404

    # OTP links should have been sent and take directly to the vote page
    emails = contest.voter_set.values_list('user__email', flat=True)
    assert len(mailoutbox) == len(emails)
    assert mailoutbox[-1].subject == 'title'
    link = mailoutbox[-1].body[3:]

    _client = Client()
    assert _client.post(link)['Location'] == vote
    assert _client.get(vote).status_code == 200

    # vote page becomes visible to voter1
    vote = f'{contest_url}vote/'
    assert client.get(vote).status_code == 302, vote
    #assert get(guardian2.user, vote).status_code == 404, vote
    assert get(external, vote).status_code == 404, vote
    assert get(voter1, vote).status_code == 200, vote
    assert get(mediator, vote).status_code == 404, vote

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
    m = re.match(r'/en/track/(?P<contest>.*)\/(?P<ballot>.*)/', response.url)
    assert m
    m = m.groupdict()
    assert 'contest' in m.keys()
    assert 'ballot' in m.keys()

    response = get(external, response.url)
    assert response.status_code == 200
    assert b'Ballot found' in response.content

    assert voter1.voter_set.get(contest=contest).casted

    # let's close the vote ... if we're mediator
    contest.refresh_from_db()
    assert not contest.actual_end
    close = f'{contest_url}close/'
    assert client.get(close).status_code == 302
    #assert get(guardian2.user, close).status_code == 404
    assert get(external, close).status_code == 404
    assert get(voter1, close).status_code == 404
    assert get(mediator, close).status_code == 200

    assert client.post(close).status_code == 302
    #assert post(guardian2.user, close).status_code == 404
    assert post(external, close).status_code == 404
    assert post(voter1, close).status_code == 404
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
    assert post(
        mediator,
        decrypt,
        email_title='results title',
        email_message='Hi LINK',
    ).status_code == 302
    score = lambda pk: contest.candidate_set.get(pk=pk).score
    assert score(candidates[0]) == 1
    assert score(candidates[1]) == 1
    assert score(candidates[2]) == 0

    # OTP links should have been sent and take directly to the results page
    emails = contest.voter_set.values_list('user__email', flat=True)
    assert len(mailoutbox) == len(emails) * 2
    assert mailoutbox[-1].subject == 'results title'
    link = mailoutbox[-1].body[3:]
    _client = Client()
    assert _client.post(link)['Location'] == contest_url
    assert _client.get(contest_url).status_code == 200
