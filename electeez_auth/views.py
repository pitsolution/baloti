from django import forms
from django import http
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.backends import BaseBackend
from django.core.exceptions import ValidationError
from django.views import generic
from django.utils import timezone
from django.urls import include, path, reverse
from django_registration.forms import RegistrationForm
from django_registration.backends.activation.views import RegistrationView

from electeez.components import Document, TopPanel, Footer
from .models import User


class OTPSend(generic.FormView):
    template_name = 'electeez_auth/otp_send.html'

    class form_class(forms.Form):
        email = forms.EmailField()
        submit_label = 'Send magic link'

        def clean_email(self):
            value = self.cleaned_data['email']
            self.user = User.objects.filter(
                email__iexact=value
            ).first()
            if not self.user:
                raise ValidationError(
                    f'Could not find registration with email: {value}'
                )
            return value

    def form_valid(self, form):
        form.user.otp_new()
        form.user.save()
        messages.success(self.request, 'Link sent by email')
        return self.get(self.request)


class OTPBackend(BaseBackend):
    def authenticate(self, request, otp_token=None):
        user = User.objects.filter(
            otp_token=otp_token,
            otp_expiry__gte=timezone.now(),
        ).first()

        if user:  # tokens are usable OAOO
            user.otp_token = None
            user.otp_expiry = None
            user.save()
            return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class OTPLogin(generic.View):
    def get(self, request, *args, **kwargs):
        user = authenticate(request, otp_token=kwargs['token'])
        if user:
            login(request, user)
            messages.success(request, 'You have been authenticated.')
            return http.HttpResponseRedirect(
                request.GET.get('next', reverse('contest_list'))
            )
        else:
            messages.success(request, 'Invalid or expired magic link.')
            return http.HttpResponseRedirect('/')
