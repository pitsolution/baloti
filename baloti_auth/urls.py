from django.urls import path
from .views import *
from django.contrib.auth import views
from baloti_auth.views import BalotiLoginView
from baloti_auth.forms import UserLoginForm

urlpatterns = [
    path('', BalotiIndexView.as_view()),
    path('contest/list/', BalotiContestListView.as_view()),
    path('contest/<str:id>', BalotiContestDetailView.as_view(), name='ContestDetails'),
    path('contest/vote/choices/<str:id>', BalotiContestChoicesView.as_view(), name='VoteChoices'),
    path('choice/submit', BalotiContestChoicesView.as_view(), name='ChoiceSubmit'),
    path('login/', BalotiLoginView.as_view(
                    template_name="login.html",
                    authentication_form=UserLoginForm
                    ), name='login'),
    path('disclaimer', BalotiDisclaimerView.as_view(), name='Disclaimer'),
    path('vote/<str:id>', VoteView.as_view(), name='casteVote'),
]
