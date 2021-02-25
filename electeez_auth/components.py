from django.urls import include, path, reverse
from django_registration.forms import RegistrationForm
import ryzom
from ryzom.components import components as html
from ryzom.py2js.decorator import JavaScript
from .models import User
from electeez.components import Document
from electeez.mdc import (
    MDCButton,
    MDCButtonOutlined,
    MDCTextButton,
    MDCTextButtonLabel,
    MDCFormField,
    MDCTextFieldFilled,
    MDCTextFieldOutlined,
    CSRFInput,
)

from djelectionguard.components import CircleIcon


class RegistrationForm(RegistrationForm):
    class Meta(RegistrationForm.Meta):
        model = User


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
        self.google_btn = MDCButtonOutlined('continue with google', icon=GoogleIcon())
        self.facebook_btn = MDCButton('continue with facebook', p=False, icon=FacebookIcon())
        self.apple_btn = MDCButton('continue with apple', icon=AppleIcon())

        super().__init__(
            self.google_btn,
            self.facebook_btn,
            self.apple_btn,
            cls='card',
            style='display: flex; flex-flow: column wrap;'
        )


def MDCDjangoForm(form):
    from django import forms
    def to_html(self, **kwargs):
        content = []
        for boundfield in self.visible_fields():
            errors = boundfield.form.error_class(boundfield.errors)
            help_text = boundfield.help_text

            if isinstance(boundfield.field, forms.CharField):
                component = MDCTextFieldOutlined(
                    boundfield.field.label,
                    f'id_{boundfield.name}',
                    f'id_{boundfield.name}_label',
                    **boundfield.build_widget_attrs({}, boundfield.field.widget)
                )
            if errors:
                component.set_error('<br>'.join(errors))
            content.append(component)
        # TODO:
        '''
        if self.form.non_field_errors():
            self.content.append(NonFieldErrors(self.form))
        if self.hidden_errors():  # Local method.
            self.content.append(HiddenErrors(self.form))
        if self.form.hidden_fields():
            self.content.append(HiddenFields(self.form))
        '''
        return html.CList(*content).to_html()
    form.to_html = to_html.__get__(form, type(form))
    return form


@ryzom.template('registration/login.html', Document)
class EmailLoginCard(html.Div):
    def __init__(self, request, form, **kwargs):
        self.forgot_pass = MDCTextButtonLabel('forgot password?')
        self.login = MDCButton('continue')
        self.form = html.Form(
            CSRFInput(request),
            MDCDjangoForm(form),
            html.Div(
                self.forgot_pass,
                self.login,
                style='display: flex; justify-content: space-between;'
            ),
            method='POST',
            style='display: flex; flex-flow: column wrap; '
        )

        super().__init__(
            html.Div(
                html.H4('Welcome to Electeez', style='text-align: center;'),
                OAuthConnect(),
                html.Span('Or enter email and password:', cls='center-text'),
                self.form,
                cls='card'
            )
        )

    def click_events():
        def handle_forgot(event):
            route('/accounts/password_reset/')

        def handle_login(event):
            getElementByUuid(form_id).submit()

        getElementByUuid(login_id).addEventListener('click', handle_login)
        getElementByUuid(forgot_id).addEventListener('click', handle_forgot)

    def render_js(self):
        return JavaScript(self.click_events, {
            'forgot_id': self.forgot_pass._id,
            'login_id': self.login._id,
            'form_id': self.form._id
        })


class LogoutCard(html.Div):
    def __init__(self, view, ctx):
        self.login_btn = MDCButton('Login again')
        super().__init__(
            html.H4('You have been logged out'),
            html.Div(
                'Thank you for spending time on our site today.',
                cls='section'),
            html.Div(
                self.login_btn,
                style='display:flex; justify-content: flex-end;'),
            cls='card',
            style='text-align: center'
        )

    def click_events():
        def handle_login(event):
            route('/accounts/login/')

        getElementByUuid(login_id).addEventListener('click', handle_login)

    def render_js(self):
        return JavaScript(self.click_events, {
            'login_id': self.login_btn._id,
        })


class PasswordResetCard(html.Div):
    def __init__(self, view, ctx):
        self.email_field = MDCTextFieldOutlined(
            'Email',
            'email_input',
            'email_input_label',
            name='email'
        )
        self.form = html.Form(
            CSRFInput(view),
            self.email_field,
            html.Div(
                MDCButton('reset password'),
                style='margin-left: auto;'
            ),
            method='POST',
            style='display: flex; flex-flow: column wrap; '
        )

        super().__init__(
            html.H4('Reset your password', style='text-align: center;'),
            self.form,
            cls='card'
        )


class PasswordResetDoneCard(html.Div):
    def __init__(self, view, ctx):
        super().__init__(
            html.H4('A link has been sent to your email address'),
            html.A('Go to login page', href=reverse('login')),
            cls='card',
            style='text-align: center;'
        )


class EmailRegistrationCard(html.Div):
    form_class = RegistrationForm

    def __init__(self, view, ctx):
        form = ctx.get('form', None) if ctx else None
        self.email_field = MDCTextFieldOutlined(
            'Email',
            'email_input',
            'email_input_label',
            type='email',
            name='email',
            required=True
        )
        self.password1_field = MDCTextFieldOutlined(
            'Password',
            'password_input',
            'password_input_label',
            type='password',
            name='password1',
            required=True,
            minlength=8
        )
        self.password2_field = MDCTextFieldOutlined(
            'Repeat password',
            'password2_input',
            'password2_input_label',
            type='password',
            name='password2',
            required=True,
            minlength=8
        )
        self.form = html.Form(
            CSRFInput(view),
            self.email_field,
            self.password1_field,
            html.Span('Your password has to match the following criteria:', style='font-weight: bold;'),
            html.Ul(
                html.Li('Contains at least 8 characters'),
                html.Li('Not too similar to your other personal informations'),
                html.Li('Not entirely numeric'),
                html.Li('Not a commonly used password'),
            ),
            self.password2_field,
            html.Div(
                MDCButton('Sign up'),
                style='display: flex; justify-content: flex-end;'
            ),
            method='POST',
            style='display: flex; flex-flow: column wrap; '
        )

        if form:
            for k in form.errors.keys():
                if attr := getattr(self, k + '_field', None):
                    for e in form.errors[k]:
                        attr.set_error(e)

        super().__init__(
            html.Div(
                html.H4('Looks like you need to register', style='text-align: center;'),
                self.form,
                html.Span('Or use:', cls='center-text'),
                OAuthConnect(view),
                cls='card'
            )
        )


class RegistrationCompleteCard(html.Div):
    def __init__(self, view, ctx):
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


class ActivationCompleteCard(html.Div):
    def __init__(self, view, ctx):
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


class ActivationFailureCard(html.Div):
    def __init__(self, view, ctx):
        super().__init__(
            html.H4('Account activation failure'),
            html.Div(
                'Most likely your account has already been activated.',
                style='margin-bottom: 24px'
            ),
            cls='card',
            style='text-align: center'
        )
