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


def baloti_index(request):
    """Index View

    Args:
        request (Request): Http request object

    Returns:
        html : returns baloti_index.html html file
    """
    return render(request, 'baloti_index.html')

def getContestList(request):
    """Contest List View

    Args:
        request (Request): Http request object

    Returns:
        html : returns contest_list.html html file
    """
    # if request.user.is_anonymous:
    contests = Contest.objects.filter(~Q(actual_start=None)
                ).distinct('id')
    return render(request, 'contest_list.html',{'title':'Contests',"contests":contests})
    

def getContestDetails(request, id):
    """Contest Detail View

    Args:
        request (Request): Http request object

    Returns:
        html : returns contest_details.html html file
    """
    contest = Contest.objects.filter(id=id
                )
    return render(request, 'contest_details.html',{"contests":contest})

def getVoteChoices(request, id):
    """Contest Choices View

    Args:
        request (Request): Http request object

    Returns:
        html : returns contest_vote_choices.html html file
    """
    candidates = Candidate.objects.filter(contest=id)
    return render(request, 'contest_vote_choices.html',{"candidates":candidates})

def baloti_disclaimer(request):
    """Disclaimer View

    Args:
        request (Request): Http request object

    Returns:
        html : returns baloti_disclaimer.html html file
    """
    return render(request, 'baloti/baloti_disclaimer.html',{'name':request.user, 'title':'Disclaimer'})
 
def home(request):
    """Home View
 
     Args:
         request (Request): Http request object
     Returns:
         html : returns home.html html file
     """
    return render(request, 'home.html')


class BalotiLoginView(LoginView):
    """
    Baloti login view.
    """

    form_class = UserLoginForm
    template_name = 'login.html'


def choice_submit_url(request):
    """Choice Submit View

    Args:
        request (Request): Http request object

    Returns:
        html : returns login.html html file
    """
    choice = ''
    if request.method == 'POST':
        choice = request.POST.get('choice')
    return render(request, 'login.html',{'name':request.user, 'title':'Login', 'choice': choice})

@login_required
def login_redirect(request):
    """Login Redirect View

    Args:
        request (Request): Http request object

    Returns:
        html : returns baloti_disclaimer.html html file
    """
    return render(request, 'baloti/baloti_disclaimer.html',{'name':request.user, 'title':'Disclaimer'})