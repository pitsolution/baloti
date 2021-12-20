from django.shortcuts import render
from django.contrib.auth.views import LoginView
from baloti_auth.forms import UserLoginForm
from django.views.generic import TemplateView
from django.contrib import messages
from django.conf import settings
from djlang.utils import gettext as _
from electeez_auth.models import User
import random
import string
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

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

class BalotiSignupView(TemplateView):
    """
    Baloti Signup View
    """
    template_name = "signup.html"


class BalotiSignupMailView(TemplateView):
    """
    Baloti Signup Mail View
    """

    def post(self, request):
        """
        Args:
            request (Request): Http request object

        Returns:
            html : returns signup_success.html html file
        """
        subject = 'Baloti Registration Information'
        email_from = settings.DEFAULT_FROM_EMAIL
        email = request.POST.get('email')
        password = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
        login_url = settings.BASE_URL + '/en/baloti/login/'

        try:
            user = User.objects.create_user(email, password)
        except Exception as err:
            return render(request, 'signup.html', {"email": email, "error":err})

        merge_data = {
                    'username': email,
                    'password': password,
                    'login_url': login_url
                    }
        html_body = render_to_string("signup_mail.html", merge_data)

        message = EmailMultiAlternatives(
           subject=subject,
           body="mail testing",
           from_email=email_from,
           to=[email],
        )
        message.attach_alternative(html_body, "text/html")
        message.send()
        messages.success(self.request, _('Registration information sent by email'))
        return render(request, 'signup_success.html')
