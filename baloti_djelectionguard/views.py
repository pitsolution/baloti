from django.shortcuts import render
from djelectionguard.models import Contest, Candidate, ParentContest
from django.db.models import ObjectDoesNotExist, Q
from django.http import *
from django.views.generic import TemplateView
from djlang.utils import gettext as _
from electeez_common.components import *
import hashlib

class BalotiIndexView(TemplateView):
    """
    Index view.
    """
    template_name = "index.html"


class BalotiContestListView(TemplateView):
    """
    Contest List View
    """

    def get(self, request):
        """
        Args:
            request (Request): Http request object

        Returns:
            html : returns contest_list.html html file
        """
        contest_list = []
        action = ''
        parentcontest = ParentContest.objects.filter()
        for parent_id in parentcontest:
            data = {}
            contests = Contest.objects.filter(parent=parent_id)

            data = {
                    'name': parent_id.name,
                    'id': parent_id.uid,
                    'start_date': parent_id.start,
                    'child_count': len(contests),
                    'child_contests': contests
                    }
            if parent_id.status == 'closed':
                action = 'view_result'
            elif parent_id.status == 'draft':
                action = 'view_detail'
            else:
                if not request.user.is_anonymous:
                    for contest_id in contests:
                        voter = contest_id.voter_set.filter(user=request.user)
                        if voter and voter.first().casted and action != 'vote_now':
                            action = 'view_detail'
                        else:
                            action = 'vote_now'
                else:
                    action = 'vote_now'
            data['action'] = action
            contest_list.append(data)
        return render(request, 'contest_list.html',{'title':'Contests',"contests":contest_list})
    

class BalotiContestDetailView(TemplateView):
    """
    Contest Detail View
    """
    
    def get(self, request, id):
        """
        Args:
            request (Request): Http request object
            id: Contest UID

        Returns:
            html : returns contest_details.html html file
        """
        contest = ParentContest.objects.filter(uid=id)
        child_contests = Contest.objects.filter(
                parent=contest.first()
                ).distinct('id')
        return render(request, 'contest_details.html',{"contest": contest, "child_contests": child_contests})


class BalotiContestResultView(TemplateView):
    """
    Contest Result View
    """

    def get(self, request, id):
        """
        Args:
            request (Request): Http request object
            id: Contest UID

        Returns:
            html : returns contest_results.html html file
        """
        contest = ParentContest.objects.filter(uid=id)
        child_contests = Contest.objects.filter(
                parent=contest.first()
                ).distinct('id')
        return render(request, 'contest_results.html',{"contest": contest, "child_contests": child_contests})


class BalotiContestChoicesView(TemplateView):
    """
    Contest Choices View
    """
    
    def get(self, request, id):
        """
        Args:
            request (Request): Http request object
            id: Candidate UID

        Returns:
            html : returns contest_vote_choices.html html file
        """
        candidates = Candidate.objects.filter(contest=id)
        return render(request, 'contest_vote_choices.html',{"candidates":candidates})

    def post(self, request):
        """
        Args:
            request (Request): Http request object

        Returns:
            html : returns login.html html file
        """
        choice = request.POST.get('choice')
        if request.user.is_anonymous:
            return render(request, 'login.html',{'name':request.user, 'title':'Login', 'choice': choice})
        else:
            return VoteView().casteVote(request, choice)

class VoteView(TemplateView):
    """
    Vote Caste View
    """

    def get(self, request, id):
        """
        Args:
            request (Request): Http request object
            id: Candidate UID

        Returns:
            html : returns contest_details.html html file
        """
        return VoteView().casteVote(request, id)

    def casteVote(self, request, id):
        """
        Args:
            request (Request): Http request object
            id: Candidate UID

        Returns:
            html : returns contest_details.html html file
        """

        candidate = Candidate.objects.filter(id=id)
        contest = Contest.objects.get(id=candidate.first().contest.id)
        voter = contest.voter_set.filter(user=request.user)
        if voter and voter.first().casted:
            voter = voter.first()
            return render(request, 'vote_success.html',{'user':request.user, 'title':'Already voted.'})
        else:
            ballot = contest.get_ballot(*[
                    selection.pk
                    for selection in candidate
                ])
            encrypted_ballot = contest.encrypter.encrypt(ballot)
            contest.ballot_box.cast(encrypted_ballot)

            submitted_ballot = contest.ballot_box._store.get(
                encrypted_ballot.object_id
            )
            ballot_sha1 = hashlib.sha1(
                submitted_ballot.to_json().encode('utf8'),
            ).hexdigest()

            contest.voter_set.update_or_create(
                user=request.user,
                defaults=dict(
                    casted=True,
                    ballot_id=encrypted_ballot.object_id,
                    ballot_sha1=ballot_sha1
                ),
            )
            contest.save()
            messages.success(
                    request,
                    _('You casted your ballot for %(obj)s', obj=contest)
                )
            uid = contest.voter_set.get(user=request.user).id
            return render(request, 'vote_success.html',{'user':request.user, 'title':'Your vote has been Validated'})