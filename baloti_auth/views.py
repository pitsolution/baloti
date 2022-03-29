import json
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
                user = User.objects.filter(email=username, first_login=False)
                if user:
                    user = user.first()
                    user.is_active = True
                    user.first_login = True
                    user.save()
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
    print('merge_data=================', merge_data)
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
            user = User.objects.filter(email=email, is_active=False)
            if user:
                user = user.first()
                user.set_password(password)
                user.first_login = False
                user.save()
            else:
                user = User.objects.create_user(email, password)
                user.is_active = False
                user.first_login = False
                user.save()
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
            user = User.objects.filter(email=email, is_active=False)
            if user:
                user = user.first()
                user.set_password(password)
                user.first_login = False
                user.save()
            else:
                user = User.objects.create_user(email, password)
                user.is_active = False
                user.first_login = False
                user.save()
        except Exception as err:
            return HttpResponseBadRequest()
        signupMailSent(self, email, password)
        return render(request, 'signup_success.html')


class BalotiDeleteProfileView(TemplateView):
    """
    Contest Anonymous Vote
    """

    def post(self, request):
        """
        Args:
            request (Request): Http request object

        Returns:
            html : returns login.html html file
        """
        password = request.POST.get('password', None)
        username = request.POST.get('username')
        user = request.user
        if not user.check_password(password):
            return HttpResponse({'invalid_password':True}, status=200)
        user.is_active = False
        user.save()
        responseData = {}
        return HttpResponse(json.dumps(responseData), content_type="application/json")