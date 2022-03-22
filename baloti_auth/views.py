from django.shortcuts import render
from django.contrib.auth.views import LoginView
from baloti_auth.forms import LoginForm
from django.views.generic import TemplateView
from django.contrib import messages
from django.conf import settings
from djlang.utils import gettext as _
from electeez_auth.models import User
import random
import string
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.http import *
from baloti_auth.models import BalotiUser
from django.contrib.auth import login, authenticate

class BalotiLoginView(LoginView):

    def get(self, request):
        form = LoginForm()
        return render(request, 'login.html', context={'form': form})

    def post(self, request):
        error = ''
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                try:
                    login(request, user)
                    return HttpResponseRedirect('/baloti/success/login')
                    # return render(request, 'index.html',{"contests": contests, "login":True})
                except Exception as err:
                    error = "Your username and password didn't match. Please try again."
            else:
                baloti_user = BalotiUser.objects.filter(username=username, password=password, status='draft')
                if baloti_user:
                    baloti_user = baloti_user.first()
                    user = User.objects.filter(email=username, is_active=False)
                    if user:
                        user = user.first()
                        user.is_active = True
                        user.set_password(password)
                        user.save()
                    else:
                        user = User.objects.create_user(username, password)
                    baloti_user.status = 'done'
                    baloti_user.save()
                    try:
                        user = authenticate(username=username, password=password)
                        login(request, user)
                        return HttpResponseRedirect('/baloti/success/registration')
                    except Exception as err:
                        error = "Your username and password didn't match. Please try again."
                else:
                    error = "Login failed!"
        return render(request, 'login.html', {"error":error})

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


def signupMailSent(self, email, password):
    subject = 'Baloti Registration Information'
    email_from = settings.DEFAULT_FROM_EMAIL
    login_url = settings.BASE_URL + '/en/baloti/login/'
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
        email = request.POST.get('email')
        password = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
        try:
            # user = User.objects.create_user(email, password)
            user = User.objects.filter(email=email, is_active=True)
            baloti_user = BalotiUser.objects.filter(username=email, status='draft')
            if not user and not baloti_user:
                BalotiUser.objects.create(username=email,password=password)
        except Exception as err:
            return render(request, 'signup.html', {"email": email, "error":err})
        signupMailSent(self, email, password)
        return render(request, 'signup_success.html')


class BalotiModalSignupMailView(TemplateView):
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
        email = request.POST.get('email')
        password = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
        try:
            user = User.objects.filter(email=email, is_active=True)
            baloti_user = BalotiUser.objects.filter(username=email, status='draft')
            if not user and not baloti_user:
                BalotiUser.objects.create(username=email,password=password)
        except Exception as err:
            return HttpResponseBadRequest()
        signupMailSent(self, email, password)
        return render(request, 'signup_success.html')
