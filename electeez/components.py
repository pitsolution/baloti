from django.contrib import messages
from django.urls import reverse
from ryzom.components import components as html
from ryzom.contrib.django import Static
from ryzom.py2js.decorator import JavaScript
from sass_processor.processor import sass_processor
from electeez.mdc import MDCButton, MDCTextButton, MDCSnackBar


class TopPanel(html.Div):
    def __init__(self, view):
        self.user = user = view.request.user

        if user.is_authenticated:
            text = user.email
            self.account_btn = MDCButton('log out')
            self.account_btn.url = reverse('logout')
        else:
            text = 'Anonymous'
            if view.url.rstrip('/') == reverse('login').rstrip('/'):
                self.account_btn = MDCButton('sign up')
                self.account_btn.url = reverse('signup')
            else:
                self.account_btn = MDCButton('log in')
                self.account_btn.url = reverse('login')

        super().__init__(
            html.Span(
                html.Img(
                    src=Static('electis.png'),
                    cls='top-panel-sub top-panel-logo'
                ),
                cls='top-panel-elem'
            ),
            html.Span(
                html.Span(f"Hello, {text}", cls='top-panel-sub top-panel-msg'),
                cls='top-panel-elem'
            ),
            html.Span(self.account_btn, cls='top-panel-elem top-panel-btn'),
            cls='top-panel'
        )

    def render_js(self):
        def click_event():
            def handle_login(event):
                route(url)

            getElementByUuid(btn_id).addEventListener('click', handle_login)

        return JavaScript(click_event, dict(
            btn_id=self.account_btn._id,
            url=self.account_btn.url
        ))


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
        self.url = url
        self.link = MDCTextButton(text, 'chevron_left')
        super().__init__(self.link, cls='card')

    def render_js(self):
        def click_event():
            def go_back(event):
                route(url)
            getElementByUuid(btn_id).addEventListener('click', go_back)

        return JavaScript(click_event, dict(
            url=self.url,
            btn_id=self.link._id
        ))


class Messages(html.CList):
    def __init__(self, request):
        msgs = messages.get_messages(request)
        if msgs:
            super().__init__(*(
                MDCSnackBar(msg.message) for msg in msgs
            ))
        else:
            super().__init__()


class Document(html.Html):
    def __init__(self, view, main_component, ctx=None):
        self.view = view
        self.main_component = main_component
        mdc_icons_src = 'https://fonts.googleapis.com/icon?family=Material+Icons'
        nanum_pen_src = 'https://fonts.googleapis.com/css2?family=Nanum+Pen+Script&display=swap'
        mdc_style_src = 'https://unpkg.com/material-components-web@latest/dist/material-components-web.min.css'
        mdc_script_src = 'https://unpkg.com/material-components-web@latest/dist/material-components-web.min.js'
        style_src = sass_processor('css/style.scss')

        body = html.Body(
            TopPanel(view),
            cls='mdc-typography'
        )

        if backlink := getattr(view, 'backlink', None):
            body.content.append(backlink)

        body.content += [
            main_component(view, ctx),
            Messages(view.request),
            Footer(),
            html.Script('mdc.autoInit()', type='text/javascript'),
        ]

        content = [
            html.Head(
                html.Title('Secure elections with homomorphic encryption'),
                html.Meta(charset='utf-8'),
                html.Meta(
                    name='viewport',
                    content='width=device-width, initial-scale=1.0'),
                html.Link(rel='stylesheet', href=mdc_icons_src),
                html.Link(rel='stylesheet', href=mdc_style_src),
                html.Link(rel='stylesheet', href=nanum_pen_src),
                html.Link(rel='stylesheet', href=style_src),
                html.Script(type='text/javascript', src=mdc_script_src),
            ),
            body
        ]
        super().__init__(*content)
