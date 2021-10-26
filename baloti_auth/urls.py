from django.urls import path
from .views import *
from django.contrib.auth import views
from baloti_auth.views import BalotiLoginView
from baloti_auth.forms import UserLoginForm


urlpatterns = [
    path('', BalotiIndexView.as_view()),
    path('contest/list/', ContestListView.as_view()),
    path('contest/<str:id>', ContestDetailView.as_view(), name='ContestDetails'),
    path('contest/vote/choices/<str:id>', ContestChoicesView.as_view(), name='VoteChoices'),
    path('choice/submit', ContestChoicesView.as_view(), name='ChoiceSubmit'),
    path('login/', BalotiLoginView.as_view(
                    template_name="login.html",
                    authentication_form=UserLoginForm
                    ), name='login'),
    path('login/redirect', login_redirect, name='login_redirect'),
    path('disclaimer', DisclaimerView.as_view(), name='Disclaimer'),
]