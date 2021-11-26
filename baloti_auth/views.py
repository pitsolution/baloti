from django.shortcuts import render
from django.contrib.auth.views import LoginView
from baloti_auth.forms import UserLoginForm
from django.views.generic import TemplateView

class BalotiLoginView(LoginView):
    """
    Baloti login view.
    """

    form_class = UserLoginForm
    template_name = 'login.html'


def home(request):
    """Home View
 
     Args:
         request (Request): Http request object
     Returns:
         html : returns home.html html file
     """
    return render(request, 'home.html')