from django import forms
from django.urls import include, path, reverse
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django_registration.forms import RegistrationForm
from django_registration.backends.activation.views import RegistrationView
import ryzom
from .models import User
from ryzom_django_mdc.html import *
from electeez_common.components import Document, Card, BackLink, MDCButton

from djelectionguard.components import CircleIcon
from django.conf import settings

from djlang.utils import gettext as _

class RegistrationForm(RegistrationForm):
    password2 = forms.CharField(
        label=_('Repeat password'),
        required=True,
        widget=forms.PasswordInput,
    )

    class Meta(RegistrationForm.Meta):
        model = User


@template('django_registration/registration_form.html', Document, Card)
class RegistrationFormViewComponent(Html):
    def to_html(self, *content, view, form, **context):
        return super().to_html(
            *content,
            H4(_('Looks like you need to register'), cls='center-text'),
            Form(
                CSRFInput(view.request),
                form['email'],
                form['password1'],
                H6(_('Your password needs to follow these criteria:')),
                Ul(
                    Li(_('Contains at least 8 characters')),
                    Li(_('Not too similar to your other personal information')),
                    Li(_('Not entirely numeric')),
                    Li(_('Not a commonly used password')),
                    cls='body-2'),
                form['password2'],
                MDCButton(_('Register')),
                method='POST',
                cls='form card'),
        )


RegistrationView.form_class = RegistrationForm


@template('registration/login.html', Document, Card)
class LoginFormViewComponent(Div):
    def to_html(self, *content, view, form, **kwargs):
        if view.request.user.is_authenticated:
            self.backlink = BackLink(_('my elections'), reverse('contest_list'))

        return super().to_html(
            Form(
                H4(_('Welcome to Electis.app'), style='text-align: center;'),
                # OAuthConnect(),
                # Span('Or enter email and password:', cls='center-text'),
                Span(_('Enter email and password:'), cls='center-text'),
                CSRFInput(view.request),
                form,
                Div(
                    MDCTextButton(
                        _('forgot password'),
                        tag='a',
                        href=reverse('password_reset')),
                    MDCButton(_('Continue')),
                    style='display: flex; justify-content: space-between'),
                method='POST',
                cls='form card'),
            cls='')


@template('registration/logged_out.html', Document, Card)
class LogoutViewComponent(Div):
    def __init__(self, *content, **context):
        super().__init__(
            H4(_('You have been logged out'), style='text-align: center'),
            Div(
                _('Thank you for spending time on our site today.'),
                cls='section'),
            Div(
                MDCButton(
                    _('Login again'),
                    tag='a',
                    href=reverse('login')),
                style='display:flex; justify-content: flex-end;'),
            cls='card',
            style='text-align: center'
        )

@template('registration/password_reset_form.html', Document, Card)
class PasswordResetCard(Div):
    def to_html(self, *content, view, form, **context):
        return super().to_html(
            H4(_('Reset your password'), style='text-align: center;'),
            Form(
                CSRFInput(view.request),
                form,
                MDCButton(_('Reset password')),
                method='POST',
                cls='form'),
            cls='card')


@template('registration/password_reset_confirm.html', Document, Card)
class PasswordResetConfirm(Div):
    def to_html(self, *content, view, form, **context):
        return super().to_html(
            H4(_('Reset your password'), style='text-align: center;'),
            Form(
                CSRFInput(view.request),
                form,
                MDCButton(_('confirm')),
                method='POST',
                cls='form'),
            cls='card')


@template('registration/password_reset_complete.html', Document, Card)
class PasswordResetComplete(Div):
    def __init__(self, **context):
        super().__init__(
            H4(_('Your password have been reset'), cls='center-text'),
            Div(
                _('You may go ahead and '),
                A(_('login '), href=reverse('login')),
                ' ', _('now'),
            )
        )


@template('registration/password_reset_done.html', Document, Card)
class PasswordResetDoneCard(Div):
    def __init__(self, **context):
        super().__init__(
            H4(_('A link has been sent to your email address'), style='text-align:center'),
            A(_('Go to login page'), href=reverse('login')),
            cls='card',
            style='text-align: center;'
        )


@template('django_registration/registration_complete.html', Document, Card)
class RegistrationCompleteCard(Div):
    def __init__(self, **context):
        super().__init__(
            H4(_('Check your emails to finish !'), style='text-align: center'),
            Div(
                _('An activation link has been sent to your email address, '
                'please open it to finish the signup process.'),
                style='margin-bottom: 24px'
            ),
            Div(
                _('Then, come back and login to participate to your election.'),
                style='margin-bottom: 24px;'
            ),
            cls='card',
            style='text-align: center'
        )


@template('django_registration/activation_complete.html', Document, Card)
class ActivationCompleteCard(Div):
    def __init__(self, **context):
        super().__init__(
            H4(_('Your account has been activated !'), style='text-align: center'),
            Div(
                _('You may now '),
                A(_('login '), href=reverse('login')),
                ' ', _('and particiapte to an election'),
                style='margin-bottom: 24px'
            ),
            cls='card',
            style='text-align: center'
        )


@template('django_registration/activation_failed.html', Document, Card)
class ActivationFailureCard(Div):
    def __init__(self, **context):
        super().__init__(
            H4(_('Account activation failure'), style='text-align: center'),
            Div(
                _('Most likely your account has already been activated.'),
                style='margin-bottom: 24px'
            ),
            cls='card',
            style='text-align: center'
        )


@template('electeez_auth/otp_login.html', Document, Card)
class OTPLoginForm(Div):
    def to_html(self, *content, **context):
        return super().to_html(
            H4(_('Proceed to automatic authentification'), style='text-align: center'),
            Form(
                CSRFInput(context['view'].request),
                MDCButton(_('Click here to continue')),
                style='display: flex; justify-content: center',
                method='post',
            ),
            cl='card',
            **context,
        )


@template('electeez_auth/otp_send.html', Document, Card)
class OTPSendCard(Div):
    def to_html(self, *content, view, form, **context):
        content = super().to_html(
            H4(_('Receive a magic link by email'), style='text-align: center'),
            Form(
                form,
                CSRFInput(view.request),
                MDCButton(form.submit_label),
                method='POST',
                cls='form'),
            cls='card',)

        if view.request.GET.get('next', ''):
            content += Div(
                _('To proceed to your '),
                A(_('secure link'), href=view.request.GET['next'])
            ).to_html(**context)

        return content


@template('electeez_auth/otp_email_success.html', Document, Card)
class OTPSendCard(Div):
    def __init__(self, **context):
        super().__init__(
            H4(_('Email sent with success'), style='text-align:center'),
            cls='card',
        )
