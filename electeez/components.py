from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from ryzom_django_mdc import html
from ryzom.contrib.django import Static
from py2js.renderer import JS
from sass_processor.processor import sass_processor
from ryzom_mdc import MDCButton, MDCTextButton, MDCSnackBar


class TopPanel(html.Div):
    def __init__(self, request=None, **kwargs):
        self.user = user = request.user

        if user.is_authenticated:
            text = user.email
            account_btn = MDCButton('log out', tag='a', href=reverse('logout'))
        else:
            text = 'Anonymous'
            if request.path.rstrip('/') == reverse('login').rstrip('/'):
                url = reverse('django_registration_register')
                account_btn = MDCButton('sign up', tag='a', href=url)
            else:
                account_btn = MDCButton('log in', tag='a', href=reverse('login'))

        super().__init__(
            html.A(
                html.Img(
                    src=Static('electis.png'),
                    cls='top-panel-sub top-panel-logo'),
                href='/'),
            html.Span(
                html.Span(f"Hello, {text}", cls='top-panel-sub top-panel-msg'),
                cls='top-panel-elem over'),
            html.Span(account_btn, cls='top-panel-elem top-panel-btn'),
            html.Span(
                html.Span(f"Hello, {text}", cls='top-panel-sub top-panel-msg'),
                cls='top-panel-elem under'),
            cls='top-panel')


class Footer(html.Div):
    def __init__(self):
        super().__init__(
            html.Div(style='height:96px'),
            html.Div(
                html.Span('Made by ', cls='caption'),
                html.A('Electis.io', href='https://electis.io', cls='caption'),
                cls='footer'
            )
        )


class BackLink(html.Div):
    def __init__(self, text, url):
        super().__init__(
            html.Div(
                MDCTextButton(
                    text,
                    'chevron_left',
                    tag='a',
                    href=url),
                cls='card backlink'),
            cls='card backlink')


class Messages(html.CList):
    def __init__(self, request):
        msgs = messages.get_messages(request)
        if msgs:
            super().__init__(*(
                MDCSnackBar(msg.message) for msg in msgs
            ))
        else:
            super().__init__()


class Card(html.Div):
    def __init__(self, main_component, **kwargs):
        if backlink := getattr(main_component, 'backlink', None):
            self.backlink = backlink
        super().__init__(main_component, cls='card')


if settings.DEBUG:
    style_src = sass_processor('css/style.scss')
else:
    style_src = '/static/css/style.css'


class Document(html.Html):
    title = 'Secure elections with homomorphic encryption'
    stylesheets = [style_src]

    def __init__(self, main_component, **kwargs):
        self.main_component = main_component

        messages_component = Messages(kwargs['request'])

        super().__init__(
            TopPanel(**kwargs),
            getattr(main_component, 'backlink', ''),
            self.main_component,
            messages_component,
            Footer(),
        )
