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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial'] = dict(
            email=self.request.GET.get('email', '')
        )
        return kwargs

    def form_valid(self, form):
        form.user.otp_new()
        form.user.save()

        nextlink = self.request.GET.get('next', '')

        LINK = ''.join([
            settings.BASE_URL,
            reverse('otp_login', args=[form.user.otp_token]),
            ('?next=' + nextlink) if nextlink else ''
        ])

        RENEW_LINK = ''.join([
            settings.BASE_URL,
            reverse('otp_send'),
            '?email=',
            form.cleaned_data['email'],
            ('&next=' + nextlink) if nextlink else ''
        ])

        send_mail(
            'Your magic link',
            textwrap.dedent(f'''
                Hello,

                This is the magic link you have requested:

                {LINK}

                It is useable once and will expire in 24h, you can request a new magic link here:

                {RENEW_LINK}
            '''),
            'webmaster@electeez.com',
            [form.cleaned_data['email']],
        )

        messages.success(self.request, 'Link sent by email')
        return http.HttpResponseRedirect(reverse('otp_email_success'))


class OTPEmailSuccess(generic.TemplateView):
    template_name = 'electeez_auth/otp_email_success.html'


class OTPBackend(BaseBackend):
    def authenticate(self, request, otp_token=None):
        if otp_token:
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
