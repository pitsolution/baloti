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
    candidates = Candidate.objects.filter(contest=id
                )
    return render(request, 'contest_vote_choices.html',{"candidates":candidates})

def login(request):
    """Baloti Login View

    Args:
        request (Request): Http request object

    Returns:
        html : returns login.html html file
    """
    logout(request)
    username = password = ''
    if request.POST:
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect('/main/')
    return render('login.html', context_instance=RequestContext(request))

def baloti_disclaimer(request):
    """Disclaimer View

    Args:
        request (Request): Http request object

    Returns:
        html : returns baloti_disclaimer.html html file
    """
    return render(request, 'baloti/baloti_disclaimer.html',{'name':request.user, 'title':'Disclaimer'})


# def login(request):
#     """Login View

#     Args:
#         request (Request): Http request object

#     Returns:
#         html : returns login.html html file
#     """
#     return render(request, 'login.html')
 
def home(request):
    """Home View
 
     Args:
         request (Request): Http request object
     Returns:
         html : returns home.html html file
     """
    return render(request, 'home.html')
 
