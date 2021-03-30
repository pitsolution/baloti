from django import forms
from django.urls import include, path, reverse
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django_registration.forms import RegistrationForm
from django_registration.backends.activation.views import RegistrationView
import ryzom
from .models import User
from ryzom_django_mdc.html import *
from electeez.components import Document, Card, BackLink, MDCButton

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


class OAuthConnect(Div):
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
class RegistrationFormViewComponent(Html):
    def to_html(self, *content, view, form, **context):
        return super().to_html(
            *content,
            H4('Looks like you need to register', cls='center-text'),
            Form(
                CSRFInput(view.request),
                form['email'],
                form['password1'],
                H6('Your password needs to follow these criteria:'),
                Ul(
                    Li('Contains at least 8 characters'),
                    Li('Not too similar to your other personal information'),
                    Li('Not entirely numeric'),
                    Li('Not a commonly used password'),
                    cls='body-2'),
                form['password2'],
                MDCButton('Register'),
                method='POST',
                cls='form card'),
            # Div(
            #     Div('Or use:', cls='center-text'),
            #     OAuthConnect(),
            #     cls='card'),
        )


RegistrationView.form_class = RegistrationForm


@template('registration/login.html', Document, Card)
class LoginFormViewComponent(Div):
    def to_html(self, *content, view, form, **kwargs):
        if view.request.user.is_authenticated:
            self.backlink = BackLink('my elections', reverse('contest_list'))

        return super().to_html(
            Form(
                H4('Welcome to Electeez', style='text-align: center;'),
                # OAuthConnect(),
                # Span('Or enter email and password:', cls='center-text'),
                Span('Enter email and password:', cls='center-text'),
                CSRFInput(view.request),
                form,
                Div(
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
class LogoutViewComponent(Div):
    def __init__(self, *content, **context):
        super().__init__(
            H4('You have been logged out'),
            Div(
                'Thank you for spending time on our site today.',
                cls='section'),
            Div(
                MDCButton(
                    'Login again',
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
            H4('Reset your password', style='text-align: center;'),
            Form(
                CSRFInput(view.request),
                form,
                MDCButton('Reset password'),
                method='POST',
                cls='form'),
            cls='card')


@template('registration/password_reset_confirm.html', Document, Card)
class PasswordResetConfirm(Div):
    def to_html(self, *content, view, form, **context):
        return super().to_html(
            H4('Reset your password', style='text-align: center;'),
            Form(
                CSRFInput(view.request),
                form,
                MDCButton('confirm'),
                method='POST',
                cls='form'),
            cls='card')


@template('registration/password_reset_complete.html', Document, Card)
class PasswordResetComplete(Div):
    def __init__(self, **context):
        super().__init__(
            H4('Your password have been reset', cls='center-text'),
            Div(
                'You may go ahead and ',
                A('log in', href=reverse('login')),
                ' now',
            )
        )


@template('registration/password_reset_done.html', Document, Card)
class PasswordResetDoneCard(Div):
    def __init__(self, **context):
        super().__init__(
            H4('A link has been sent to your email address'),
            A('Go to login page', href=reverse('login')),
            cls='card',
            style='text-align: center;'
        )


@template('django_registration/registration_complete.html', Document, Card)
class RegistrationCompleteCard(Div):
    def __init__(self, **context):
        super().__init__(
            H4('Check your emails to finish !'),
            Div(
                'An activation link has been sent to your email address, ' +
                'please open it to finish the signup process.',
                style='margin-bottom: 24px'
            ),
            Div(
                'Then, come back and login to participate to your election.',
                style='margin-bottom: 24px;'
            ),
            cls='card',
            style='text-align: center'
        )


@template('django_registration/activation_complete.html', Document, Card)
class ActivationCompleteCard(Div):
    def __init__(self, **context):
        super().__init__(
            H4('Your account has been activated !'),
            Div(
                'You may now ',
                A('login', href=reverse('login')),
                ' and particiapte to an election',
                style='margin-bottom: 24px'
            ),
            cls='card',
            style='text-align: center'
        )


@template('django_registration/activation_failed.html', Document, Card)
class ActivationFailureCard(Div):
    def __init__(self, **context):
        super().__init__(
            H4('Account activation failure'),
            Div(
                'Most likely your account has already been activated.',
                style='margin-bottom: 24px'
            ),
            cls='card',
            style='text-align: center'
        )


@template('electeez_auth/otp_login.html', Document, Card)
class OTPLoginForm(Div):
    def to_html(self, *content, **context):
        return super().to_html(
            H4('Proceed to automatic authentification'),
            Form(
                CSRFInput(context['view'].request),
                MDCButton('Click here to continue'),
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
            H4('Receive a magic link by email'),
            Form(
                form,
                CSRFInput(view.request),
                MDCButton(form.submit_label),
                method='POST',
                cls='form'),
            cls='card',)

        if view.request.GET.get('next', ''):
            content += Div(
                'To proceed to your ',
                A('secure link', href=view.request.GET['next'])
            ).to_html(**context)

        return content


@template('electeez_auth/otp_email_success.html', Document, Card)
class OTPSendCard(Div):
    def __init__(self, **context):
        super().__init__(
            H4('Email sent with success'),
            cls='card',
        )
