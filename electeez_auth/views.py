import textwrap

from django import forms
from django import http
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.backends import BaseBackend
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.views import generic
from django.utils import timezone
from django.urls import include, path, reverse
from django_registration.forms import RegistrationForm
from django_registration.backends.activation.views import RegistrationView

from electeez.components import Document, TopPanel, Footer
from .models import Token, User
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class OTPSend(generic.FormView):
    template_name = 'electeez_auth/otp_send.html'

    class form_class(forms.Form):
        email = forms.EmailField()
        submit_label = _('Send magic link')

        def clean_email(self):
            value = self.cleaned_data['email']
            self.user = User.objects.filter(
                email__iexact=value
            ).first()
            if not self.user:
                raise ValidationError(
                    _('Could not find registration with email:') + f'{value}'
                )
            return value

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial'] = dict(
            email=self.request.GET.get('email', '')
        )
        return kwargs

    def form_valid(self, form):
        LINK = form.user.otp_new(
            redirect=self.request.GET.get('redirect', None)
        ).url

        send_mail(
            _('Your magic link'),
            textwrap.dedent(_('''
                Hello,

                This is the magic link you have requested:
                ''') + 
                f'{LINK}'
            ),
            'webmaster@electeez.com',
            [form.cleaned_data['email']],
        )

        messages.success(self.request, _('Link sent by email'))
        redirect = self.request.GET.get(
            'next',
            reverse('otp_email_success'),
        )
        return http.HttpResponseRedirect(redirect)


class OTPEmailSuccess(generic.TemplateView):
    template_name = 'electeez_auth/otp_email_success.html'


class OTPLogin(generic.FormView):
    template_name = 'electeez_auth/otp_login.html'
    form_class = forms.Form

    def post(self, request, *args, **kwargs):
        token = Token.objects.filter(token=kwargs['token']).first()
        if not token:
            messages.success(request, _('Invalid magic link.'))
            return http.HttpResponseRedirect(reverse('otp_send'))

        if token.used or token.expired:
            redirect = reverse('otp_send') + '?redirect=' + token.redirect
            if token.used:
                messages.success(request, _('Magic link already used.'))
                return http.HttpResponseRedirect(redirect)
            else:
                messages.success(request, _('Expired magic link.'))
                return http.HttpResponseRedirect(redirect)

        token.used = timezone.now()
        token.save()
        login(request, token.user)
        messages.success(request, _('You have been authenticated.'))
        return http.HttpResponseRedirect(
            request.GET.get(
                'next',
                token.redirect or reverse('contest_list'),
            )
        )
