from django import forms
from django.urls import include, path, reverse
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django_registration.forms import RegistrationForm
from django_registration.backends.activation.views import RegistrationView
import ryzom
from ryzom import html
from ryzom_mdc import template
from py2js.renderer import JS
from .models import User
from electeez.components import Document, Card
from ryzom_django_mdc.components import *

from djelectionguard.components import CircleIcon


class GoogleIcon(CircleIcon):
    def __init__(self):
        super().__init__('google-icon', 'white', small=True)


class FacebookIcon(CircleIcon):
    def __init__(self):
        super().__init__('facebook-icon', 'fb-blue', small=True)


class AppleIcon(CircleIcon):
    def __init__(self):
        super().__init__('apple-icon', 'black', small=True)


class OAuthConnect(html.Div):
    def __init__(self):
        self.google_btn = MDCButtonOutlined('continue with google', icon=GoogleIcon(), tag='a')
        self.facebook_btn = MDCButton('continue with facebook', p=False, icon=FacebookIcon(), tag='a')
        self.apple_btn = MDCButton('continue with apple', icon=AppleIcon(), tag='a')

        super().__init__(
            self.google_btn,
            self.facebook_btn,
            self.apple_btn,
            cls='oauth',
            style='display: flex; flex-flow: column wrap;'
        )


class RegistrationForm(RegistrationForm):
    password2 = forms.CharField(
        label='Repeat password',
        required=True,
        widget=forms.PasswordInput,
    )

    class Meta(RegistrationForm.Meta):
        model = User


@template('django_registration/registration_form.html', Document, Card)
class RegistrationFormViewComponent(html.Html):
    def __init__(self, *content, view, form, **context):
        super().__init__(
            html.H4('Looks like you need to register', cls='center-text'),
            html.Form(
                CSRFInput(view.request),
                form['email'],
                form['password1'],
                html.H6('Your password needs to follow these criteria:'),
                html.Ul(
                    html.Li('Contains at least 8 characters'),
                    html.Li('Not too similar to your other personal information'),
                    html.Li('Not entirely numeric'),
                    html.Li('Not a commonly used password'),
                    cls='body-2'),
                form['password2'],
                MDCButton('Register'),
                method='POST',
                cls='form card'),
            html.Div(
                html.Div('Or use:', cls='center-text'),
                OAuthConnect(),
                cls='card'),
        )


RegistrationView.form_class = RegistrationForm


@template('registration/login.html', Document, Card)
class LoginFormViewComponent(html.Div):
    def __init__(self, *content, view, form, **kwargs):
        super().__init__(
            html.Form(
                html.H4('Welcome to Electeez', style='text-align: center;'),
                OAuthConnect(),
                html.Span('Or enter email and password:', cls='center-text'),
                CSRFInput(view.request),
                form,
                html.Div(
                    MDCTextButton(
                        'forgot password',
                        tag='a',
                        href=reverse('password_reset')),
                    MDCButton('Continue'),
                    style='display: flex; justify-content: space-between'),
                method='POST',
                cls='form card'),
            cls='')


@template('registration/logged_out.html', Document, Card)
class LogoutViewComponent(html.Div):
    def __init__(self, *content, **context):
        super().__init__(
            html.H4('You have been logged out'),
            html.Div(
                'Thank you for spending time on our site today.',
                cls='section'),
            html.Div(
                MDCButton(
                    'Login again',
                    tag='a',
                    href=reverse('login')),
                style='display:flex; justify-content: flex-end;'),
            cls='card',
            style='text-align: center'
        )

@template('registration/password_reset_form.html', Document, Card)
class PasswordResetCard(html.Div):
    def __init__(self, *content, view, form, **context):
        super().__init__(
            html.H4('Reset your password', style='text-align: center;'),
            html.Form(
                CSRFInput(view.request),
                form,
                MDCButton('Reset password'),
                method='POST',
                cls='form'),
            cls='card')


@template('registration/password_reset_confirm.html', Document, Card)
class PasswordResetConfirm(html.Div):
    def __init__(self, *content, view, form, **context):
        super().__init__(
            html.H4('Reset your password', style='text-align: center;'),
            html.Form(
                CSRFInput(view.request),
                form,
                MDCButton('confirm'),
                method='POST',
                cls='form'),
            cls='card')


@template('registration/password_reset_complete.html', Document, Card)
class PasswordResetComplete(html.Div):
    def __init__(self, *content, view, **context):
        super().__init__(
            html.H4('Your password have been reset', cls='center-text'),
            html.Div(
                'You may go ahead and ',
                html.A('log in', href=reverse('login')),
                ' now',
            )
        )


@template('registration/password_reset_done.html', Document, Card)
class PasswordResetDoneCard(html.Div):
    def __init__(self, *content, view, **context):
        super().__init__(
            html.H4('A link has been sent to your email address'),
            html.A('Go to login page', href=reverse('login')),
            cls='card',
            style='text-align: center;'
        )


@template('django_registration/registration_complete.html', Document, Card)
class RegistrationCompleteCard(html.Div):
    def __init__(self, *content, view, **context):
        super().__init__(
            html.H4('Check your emails to finish !'),
            html.Div(
                'An activation link has been sent to your email address, ' +
                'please open it to finish the signup process.',
                style='margin-bottom: 24px'
            ),
            html.Div(
                'Then, come back and login to participate to your election.',
                style='margin-bottom: 24px;'
            ),
            cls='card',
            style='text-align: center'
        )


@template('django_registration/activation_complete.html', Document, Card)
class ActivationCompleteCard(html.Div):
    def __init__(self, *content, view, **context):
        super().__init__(
            html.H4('Your account has been activated !'),
            html.Div(
                'You may now ',
                html.A('login', href=reverse('login')),
                ' and particiapte to an election',
                style='margin-bottom: 24px'
            ),
            cls='card',
            style='text-align: center'
        )


@template('django_registration/activation_failed.html', Document, Card)
class ActivationFailureCard(html.Div):
    def __init__(self, *content, view, **context):
        super().__init__(
            html.H4('Account activation failure'),
            html.Div(
                'Most likely your account has already been activated.',
                style='margin-bottom: 24px'
            ),
            cls='card',
            style='text-align: center'
        )


@template('electeez_auth/otp_send.html', Document, Card)
class OTPSendCard(html.Div):
    def __init__(self, *content, view, form, **context):
        super().__init__(
            html.H4('Receive a magik link by email'),
            html.Form(
                form,
                CSRFInput(view.request),
                MDCButton(form.submit_label),
                method='POST',
                cls='form'),
            cls='card',)
