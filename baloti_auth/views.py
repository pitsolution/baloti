from django.shortcuts import render
from django.contrib.auth.views import LoginView
from baloti_auth.forms import UserLoginForm
from django.views.generic import TemplateView


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


def home(request):
    """Home View
 
     Args:
         request (Request): Http request object
     Returns:
         html : returns home.html html file
     """
    return render(request, 'home.html')