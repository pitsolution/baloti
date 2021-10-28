from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views import generic
from djelectionguard.models import Contest, Candidate
from django.db.models import ObjectDoesNotExist, Q
from django.http import *
from django.shortcuts import redirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views.generic import TemplateView
from django.contrib.auth.views import LoginView
from baloti_auth.forms import UserLoginForm
from djlang.utils import gettext as _
from electeez_common.components import *
from django.db import transaction
import hashlib

class BalotiIndexView(TemplateView):
    """
    Index view.
    """
    template_name = "baloti_index.html"


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
        # if request.user.is_anonymous:
        contests = Contest.objects.exclude(actual_start=None
                    ).distinct('id')
        return render(request, 'contest_list.html',{'title':'Contests',"contests":contests})
    

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
        contest = Contest.objects.filter(id=id
                    )
        return render(request, 'contest_details.html',{"contests":contest})


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
        choice = ''
        if request.method == 'POST':
            choice = request.POST.get('choice')
        return render(request, 'login.html',{'name':request.user, 'title':'Login', 'choice': choice})
 
class BalotiDisclaimerView(TemplateView):
    """
    Disclaimer View
    """
    
    def get(self, request):
        """
        Args:
            request (Request): Http request object

        Returns:
            html : returns baloti_disclaimer.html html file
        """
        return render(request, 'baloti/baloti_disclaimer.html',{'name':request.user, 'title':'Disclaimer'})


class BalotiLoginView(LoginView):
    """
    Baloti login view.
    """

    form_class = UserLoginForm
    template_name = 'login.html'

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

def home(request):
    """Home View
 
     Args:
         request (Request): Http request object
     Returns:
         html : returns home.html html file
     """
    return render(request, 'home.html')