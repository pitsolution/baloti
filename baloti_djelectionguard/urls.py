from django.urls import path
from .views import *

urlpatterns = [
    path('', BalotiIndexView.as_view()),
    path('contest/list/', BalotiContestListView.as_view()),
    path('contest/<str:id>', BalotiContestDetailView.as_view(), name='ContestDetails'),
    path('contest/vote/choices/<str:id>', BalotiContestChoicesView.as_view(), name='VoteChoices'),
    path('choice/submit', BalotiContestChoicesView.as_view(), name='ChoiceSubmit'),
    path('vote/<str:id>', VoteView.as_view(), name='casteVote'),
]
