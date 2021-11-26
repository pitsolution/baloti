from django.urls import path
from .views import *
from baloti_auth.forms import UserLoginForm
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('login/', BalotiLoginView.as_view(
                    template_name="login.html",
                    authentication_form=UserLoginForm
                    ), name='login'),
    path('logout/', LogoutView.as_view(
                    ), name='logout'),
]
