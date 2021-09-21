import os

from pathlib import Path
from email.mime.image import MIMEImage
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils.safestring import mark_safe

from ryzom.html import *

from djlang.utils import gettext as _

from electeez_sites.models import Site


class EmailHtml(Html):
    def __init__(self, site, content):
        super().__init__(
            head=Head(
                Meta(charset='utf-8'),
                Style('''
                    table {
                        width: 100%%;
                        border-collapse: collapse;
                    }
                    td {
                        padding: 32px;
                    }
                    td.banner-image {
                        width: 100px;
                    }
                    td.right {
                        text-align: right;
                    }
                    td.center {
                        text-align: center;
                    }
                    h3 {
                        text-transform: uppercase;
                    }
                    .header {
                        color: %(banner_fg)s;
                        background-color: %(banner_bg)s;
                    }
                    .footer {
                        color: %(footer_fg)s;
                        background-color: %(footer_bg)s;
                    }
                    ''' % dict(
                        banner_fg=site.email_banner_fg,
                        banner_bg=site.email_banner_bg,
                        footer_fg=site.email_footer_fg,
                        footer_bg=site.email_footer_bg
                    )
                )
            ),
            body=Body(
                Table(
                    Tr(
                        Td(
                            Img(src=f'cid:{site.email_banner.name}', height=50),
                            cls='banner-image'
                        ) if site.email_banner else None,
                        Td(
                            H3(mark_safe(_('EMAIL_BANNER_TEXT').replace('\n', '<br>'))),
                            cls='center'
                        ),
                        cls='header'
                    ),
                ),
                Table(
                    Tr(
                        Td(
                            mark_safe(content.replace('\n', '<br>')),
                            cls='email-body'
                        )
                    ),
                ),
                Table(
                    Tr(
                        Td(
                            mark_safe(_('EMAIL_FOOTER_TEXT').replace('\n', '<br>')),
                        ),
                        Td(
                            Img(src=f'cid:{site.email_footer.name}', height=50),
                            cls='right'
                        ) if site.email_footer else None,
                        cls='footer'
                    )
                )
            )
        )

def attach_image(email, image):
    subtype = None
    if os.path.splitext(image.name)[1] == '.svg':
        subtype = 'svg+xml'

    to_attach = MIMEImage(image.file.read(), _subtype=subtype)
    to_attach.add_header('Content-ID', f"<{image.name}>")
    email.attach(to_attach)


def send_email(subject, body, sender, recipient):
    email = EmailMultiAlternatives(subject=subject, body=body, from_email=sender, to=recipient)

    site = Site.objects.get_current()
    if site.email_banner or site.email_footer:
        email_html = EmailHtml(site, body).to_html()
        email.attach_alternative(email_html, "text/html")
        email.content_subtype = 'html'  # set the primary content to be text/html
        email.mixed_subtype = 'related' # it is an important part that ensures embedding of an image
        if site.email_banner:
            attach_image(email, site.email_banner)
        if site.email_footer:
            attach_image(email, site.email_footer)

    email.send()
