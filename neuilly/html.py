from django.conf import settings
from django.urls import reverse

from sass_processor.processor import sass_processor

from ryzom_django_mdc.html import *

from djlang.utils import gettext as _


class LandingApp(Html):
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

class Footer(Footer):
    sass = '''
    footer.Footer
        font-size: 22
        a, a:visited
            color: black
            text-decoration: underline
    '''

@template('landing', LandingApp)
class LandingPage(Main):
    def to_html(self, *content, view, **context):
        welcome = _(
            'Welcome to %(app)s',
            app=Span(_('NeuillyVote'), cls='red').to_html()
        )
        return super().to_html(
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
            ),
            Div(
                mark_safe(_('LANDING_INFO_PANEL_MSG').replace('\n', '<br>')),
                cls='info-panel',
                style=dict(
                    border='5px solid lightgray',
                    boder_radius=1,
                    margin='0 auto',
                    margin_top=-50,
                    padding='50 20',
                    width='60%',
                    min_width=340,
                    max_width='80%',
                    font_family='Open Sans',
                    font_size='1.5em',
                    font_weight=100,
                    background='white',
                    color='#000b'
                )
            ),
            Div(
                H3(
                    _('Take part to an upcoming vote'),
                    style=dict(
                        font_size=32,
                        font_weight=400,
                        text_align='center',
                        margin_top=150,
                        margin_bottom=12,
                    )
                ),
                H5(
                    _('I consent to the use of my email address'),
                    style=dict(
                        font_size=18,
                        font_weight=400,
                        font_style='italic',
                        text_align='center',
                        margin=12,
                    )
                ),
                Form(
                    MDCTextFieldOutlined(
                        Input(type='email', name='email'),
                        label=_('Email address'),
                        help_text=_('Type your email to register to this service'),
                        style=dict(
                            max_width=450,
                            margin='64 auto',
                            margin_bottom=0,
                        )
                    ),
                    MDCButtonOutlined(
                        _('I take part'),
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
                    data_ot_cp_id="cd2cd391-6c19-4ec3-bdd8-b0d024bca161-draft",
                    cls='agree-form',
                    addcls='ot-form-consent'
                ),
            ),
            Footer(
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
                    A(_('Site plan'), style=dict(margin=12)),
                    A(_('Legal notices'), style=dict(margin=12)),
                    A(_('Accessibility'), style=dict(margin=12)),
                    A(_('Data privacy policy'), style=dict(margin=12)),
                    A(_('Cookies'), style=dict(margin=12)),
                    A(_('FAQ'), style=dict(margin=12)),
                    A(_('Press'), style=dict(margin=12)),
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
            ),
            **context
        )
