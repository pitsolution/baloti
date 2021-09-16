from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.urls import reverse

from sass_processor.processor import sass_processor

from py2js.transpiler import transpile_body
from ryzom_django_mdc.html import *

from djlang.utils import gettext as _

from electeez_common.components import Messages


class Body(Body):
    def __init__(self, main_component, **context):
        self.main_component = main_component
        super().__init__(**context)

    def to_html(self, **context):
        main_html = self.main_component.to_html(**context)
        self.content += [
            Header(),
            main_html,
            Messages(context['view']),
            Footer()
        ]
        return super().to_html(**context)


class Header(Div):
    def __init__(self):
        welcome = _(
            'Welcome to %(app)s',
            app=Span(_('NeuillyVote'), cls='red').to_html()
        )
        super().__init__(
            Div(
                Span(
                    A(
                        href=reverse('home'),
                        cls='top-panel-logo'
                    ),
                    cls='link',
                    style=dict(
                        width=180,
                        height=100,
                        margin='50 100',
                        align_self='flex-start',
                    ),
                ),
                Span(
                    MDCButtonRaised(
                        _('log in'),
                        tag='a',
                        href=reverse('login'),
                        style=dict(
                            background_color='var(--danger)'
                        )
                    ),
                    style=dict(
                        margin='50 100',
                        align_self='flex-end',
                        margin_top=-120
                    ),
                ),
                Span(
                    B(
                        I(
                            'how_to_vote',
                            cls='material-icons',
                            style=dict(
                                font_size=72,
                                display='inline-block',
                                position='relative',
                                bottom=-6
                            )
                        ),
                        ' ',
                        welcome
                    ),
                    style=dict(
                        width='100%',
                        text_align='center',
                        font_size='3.5em',
                        font_family="'Open Sans', Arial, Helvetica, sans-serif"
                    )
                ),
                cls='top-panel',
                style=dict(
                    width='100%',
                    padding_bottom=200,
                    justify_content='flex-start',
                    flex_direction='column'
                )
            )
        )


class Footer(Footer):
    sass = '''
    footer.Footer
        font-size: 22
        a, a:visited
            color: black
            text-decoration: underline
    '''
    def __init__(self):
        super().__init__(
            Div(
                _('Made by %(electis)s', electis=A(_('Electis.io'), href='https://electis.io').to_html()),
                style=dict(
                    width='100%',
                    text_align='center',
                    margin=32
                )
            ),
            Hr(style=dict(width=150, margin=24)),
            Div(
                A(_('Site plan'), href='#', style=dict(margin=12)),
                A(_('Legal notices'), href=reverse('legal'), style=dict(margin=12)),
                A(_('Accessibility'), href='#', style=dict(margin=12)),
                A(_('Data privacy policy'), href=reverse('policy'), style=dict(margin=12)),
                A(_('Cookies'), href=reverse('cookies'), style=dict(margin=12)),
                A(_('FAQ'), href=reverse('faq'), style=dict(margin=12)),
                A(_('Press'), href='#', style=dict(margin=12)),
                style=dict(
                    display='flex',
                    flex_flow='row wrap',
                    justify_content='center'
                )
            ),
            Hr(style=dict(width=150, margin=24)),
            Div(
                Img(
                    alt='logo neuilly',
                    src='/static/logo.png',
                    width=340,
                    style=dict(
                        filter='brightness(0)'
                    )
                ),
                style=dict(
                    margin="64 auto",
                    width='100%',
                ),
            ),
            style=dict(
                display='flex',
                flex_flow='row wrap',
                justify_content='center',
                align_items='center',
            ),
            cls='footer'
        )

class LandingApp(Html):
    body_class = Body

    def to_html(self, head, body, **ctx):
        if settings.DEBUG:
            common_style_src = sass_processor('css/common.scss')
            style_src = sass_processor('css/style.scss')
        else:
            common_style_src = '/static/css/common.css'
            style_src = '/static/css/style.css'

        head.addchild(Stylesheet(href=common_style_src))
        head.addchild(Stylesheet(href=style_src))
        head.addchild(Stylesheet(href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;700&display=swap"))
        head.addchild(
            Script(
                src='https://privacyportalde-cdn.onetrust.com/consent-receipt-scripts/scripts/otconsent-1.0.min.js',
                type="text/javascript",
                data_ot_id="40ec4ddd-1627-4efb-b428-a53e211552ad",
                charset="UTF-8",
                id="consent-receipt-script",
                data_ot_consent_register_event="document-load"
            )
        )

        return super().to_html(head, body, **ctx)


@template('landing', LandingApp)
class LandingPage(Main):
    def to_html(self, *content, view, **context):
        return super().to_html(
            Div(
                mark_safe(_('LANDING_INFO_PANEL_MSG').replace('\n', '<br>')),
                cls='info-panel',
            ),
            Div(
                H3(
                    _('Take part to an upcoming vote'),
                    style=dict(
                        font_size=32,
                        font_weight=400,
                        text_align='center',
                        margin_top=32,
                        margin_bottom=12,
                    )
                ),
                H5(
                ),
                Form(
                    MDCCheckboxField(
                        MDCCheckboxInput(
                            value='Neuilly Vote',
                            required=True,
                        ),
                        name='confirmation',
                        label=Span(
                            _('I consent to the use of my email address'),
                            style=dict(
                                font_size=18,
                                font_weight=400,
                                font_style='italic',
                                text_align='center',
                                margin=12,
                            )
                        ),
                    ),
                    MDCTextFieldOutlined(
                        Input(type='email', id='inputEmail', name='inputEmail', required=True),
                        label=_('Email address'),
                        help_text=_('Type your email to register to this service'),
                        addcls='ot-form-control',
                        style=dict(
                            max_width=520,
                            margin='0 auto',
                            margin_bottom=0,
                        )
                    ),
                    MDCButtonOutlined(
                        _('I take part'),
                        id='trigger',
                        addcls='ot-submit-button',
                        style=dict(
                            margin='50 auto',
                            font_size=32,
                            color='black',
                            padding='32 64',
                            border_radius='8px',
                            font_weight=400,
                            border='4px solid black',
                        ),
                    ),
                    action='',
                    method='POST',
                    data_ot_cp_id="cd2cd391-6c19-4ec3-bdd8-b0d024bca161-active",
                    cls='agree-form',
                    addcls='ot-form-consent',
                    id='ot-form-consent'
                ),
            )
        )


@template('legal', LandingApp)
class Legal(Div):
    def to_html(self, *content, **context):
        return super().to_html(
            Div(
                H4(
                    _('Legal notices'),
                    style=dict(
                        text_align='center'
                    )
                ),
                H5(_('Edition')),
                Div(mark_safe(
                    escape(_('LEGAL_EDITION_TEXT'))
                ).replace('\n', '<br>')),
                H5(_('Author rights')),
                Div(mark_safe(
                    escape(_('AUTHOR_RIGHTS_TEXT'))
                ).replace('\n', '<br>')),
                cls='info-panel',
            )
        )


@template('policy', LandingApp)
class Legal(Div):
    def to_html(self, *content, **context):
        return super().to_html(
            Div(
                H4(
                    _('Data privacy policy'),
                    style=dict(
                        text_align='center'
                    )
                ),
                Div(mark_safe(
                    escape(_('DATA_PRIVACY_TEXT'))
                ).replace('\n', '<br>')),
                cls='info-panel',
            )
        )


@template('cookies', LandingApp)
class Legal(Div):
    def to_html(self, *content, **context):
        return super().to_html(
            Div(
                H4(
                    _('Cookies'),
                    style=dict(
                        text_align='center'
                    )
                ),
                Div(mark_safe(
                    escape(_('COOKIES_TEXT'))
                ).replace('\n', '<br>')),
                cls='info-panel',
            )
        )


@template('faq', LandingApp)
class Legal(Div):
    def to_html(self, *content, **context):
        return super().to_html(
            Div(
                H4(
                    _('FAQ'),
                    style=dict(
                        text_align='center'
                    )
                ),
                Div(
                    mark_safe(
                        escape(
                            _('FAQ_TEXT')
                        ).replace(
                            '\n', '<br>'
                        ).replace(
                            'TITLE_START', '<h5>'
                        ).replace(
                            'TITLE_END', '</h5>'
                        )
                    )
                ),
                cls='info-panel faq',
            )
        )
