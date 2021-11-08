from django.urls import path
from .views import *
from baloti_auth.forms import UserLoginForm

urlpatterns = [
    path('login/', BalotiLoginView.as_view(
                    template_name="login.html",
                    authentication_form=UserLoginForm
                    ), name='login'),
    path('disclaimer', BalotiDisclaimerView.as_view(), name='Disclaimer'),
]
