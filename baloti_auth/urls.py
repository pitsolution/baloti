from django.urls import path
from .views import *
from django.contrib.auth import views
from baloti_auth.forms import UserLoginForm


urlpatterns = [
    path('', baloti_index, name='baloti_index'),
    path('contest/list/', getContestList, name='getContestList'),
    path('contest/<str:id>', getContestDetails, name='ContestDetails'),
    path('contest/vote/choices/<str:id>', getVoteChoices, name='VoteChoices'),
    path('disclaimer', baloti_disclaimer, name='baloti_disclaimer'),
    path(
        'login/',
        views.LoginView.as_view(
            template_name="login.html",
            authentication_form=UserLoginForm
            ),
        name='login'
)
]