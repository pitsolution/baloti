import html as pyhtml
import io
import subprocess
import uuid
import zipfile

from django import http, forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.urls import path, reverse
from django.utils.safestring import mark_safe
from django.views import generic

from djelectionguard.components import *
from djelectionguard.models import Contest, Voter

from djlang.utils import gettext as _


class TrackerFormView(generic.FormView):
    template_name = 'tracker_form'

    class form_class(forms.Form):
        submit_label = _('track')

        email = forms.EmailField(label=_('Email'))

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return http.HttpResponseRedirect(reverse('tracker_list'))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # send otp mail
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('tracker_success')

    @classmethod
    def as_url(cls):
        return path(
            '',
            cls.as_view(),
            name='tracker_form'
        )

@template('tracker_form', Document, Card)
class TrackerFormCard(Div):
    def to_html(self, *content, view, form, **context):
        return super().to_html(
            H4(_('Track a ballot'), style='text-align: center'),
            Form(
                CSRFInput(view.request),
                form,
                MDCButton(form.submit_label),
                method='POST',
                cls='form'
            )
        )


@template('tracker_detail', Document, Card)
class TrackerDetailCard(Div):
    def to_html(self, *content, view, **context):
        contest = view.object.contest

        self.backlink = BackLink(_('Back'), reverse('contest_detail', args=[contest.id]))

        rows = (
            (_('Election name'), contest.name),
            (_('Election ID'), contest.id),
            (_('Ballot ID'), view.object.ballot_id),
            (_('Ballot Hash'), view.object.ballot_sha1),
        )

        wiki = 'https://fr.wikipedia.org/wiki/Fonction_de_hachage'

        return super().to_html(
            H4(
                _('Tracking informations'),
                style='text-align:center;'
            ),
            Div(
                _('TRACKING_MSG'),
                style=dict(
                    text_align='center',
                    margin_top='32px',
                    margin_bottom='32px',
                    opacity='0.6'
                )
            ),
            Table(
                *(Tr(
                    Td(
                        label, ': ',
                        cls='overline',
                        style='text-align: right;'
                              'padding: 12px;'
                              'white-space: nowrap;'
                    ),
                    Td(
                        Pre(
                            value,
                            style='word-break: break-word;'
                                  'white-space: break-spaces;'
                        ),
                    )
                ) for label, value in rows),
                style='margin: 0 auto;'
            ),
            Div(
                B(
                    _('Learn more'),
                    style=dict(
                        text_align='center',
                        display='block'
                    )
                ),
                P(mark_safe(_('TRACKING_MORE_INFO', link=f'<a href={wiki}>{wiki}</a>'))),
                style=dict(
                    background='aliceblue',
                    margin_top='32px',
                    padding='12px',
                    opacity='0.6'
                )
            ),
            ArtifactsLinks(contest)
        )


class TrackerDetailView(generic.DetailView):
    template_name = 'tracker_detail'
    model = Voter

    def get_queryset(self, qs=None):
        if self.request.user.is_authenticated:
            return Voter.objects.filter(
                user=self.request.user
            ).select_related('contest')
        return []

    @classmethod
    def as_url(cls):
        return path(
            '<uuid:pk>/',
            cls.as_view(),
            name='tracker_detail'
        )


@template('tracker_success', Document, Card)
class TrackerSuccessCard(Div):
    def to_html(self, *, view, **context):
        return super().to_html(
            H4(_('An email have been sent to your address'))
        )


class TrackerSuccessView(generic.TemplateView):
    template_name = 'tracker_success'

    @classmethod
    def as_url(cls):
        return path(
            'success/',
            cls.as_view(),
            name='tracker_success'
        )


@template('tracker_list', Document, Card)
class TrackerListCard(Div):
    def to_html(self, *, view, **context):
        voters = context['object_list']

        table = MDCDataTableResponsive(
            thead=MDCDataTableThead(
                tr=MDCDataTableHeaderTr(
                    MDCDataTableTh(_('Your elections')),
                    MDCDataTableTh(_('Voted')),
                )
            ),
            style='min-width: 100%',
            view=view
        )

        for voter in voters:
            table.tbody.addchild(
                MDCDataTableTr(
                    MDCDataTableTd(
                        _('Contest %(name)s', name=voter.contest.name),
                        style='word-break: break-all; white-space: break-spaces'
                    ),
                    MDCDataTableTd(
                        CheckedIcon() if voter.casted else '--'
                    ),
                    onclick=f'document.location=\'{reverse("tracker_detail", args=[voter.id])}\'',
                    style={
                        'cursor': 'pointer'
                    }
                )
            )

        return super().to_html(

            table,
            view=view,
            **context
        )


class TrackerListView(generic.ListView):
    template_name = 'tracker_list'
    model = Voter
    title = 'tracker_contest_list'

    def get_queryset(self, qs=None):
        return Voter.objects.filter(
            user=self.request.user
        ).select_related('contest')

    @classmethod
    def as_url(cls):
        return path(
            'list/',
            login_required(cls.as_view()),
            name='tracker_list'
        )


urlpatterns = [
    # TrackerFormView.as_url(),
    # TrackerSuccessView.as_url(),
    # TrackerListView.as_url(),
    TrackerDetailView.as_url(),
]
