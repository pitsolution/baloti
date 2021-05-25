import html as pyhtml
import io
import subprocess
import uuid
import zipfile

from django import http, forms
from django.core.exceptions import ValidationError
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.views import generic
from djelectionguard.components import *


def validate_ipfs_hash(h):
    out = subprocess.check_output(
        ['ipfs', 'cid', 'format', h]
    )
    # convert to str and remove \n
    out = bytes.decode(out)[0:-1]
    return out == h


class TrackerFormView(generic.FormView):
    template_name = 'tracker_form'

    class form_class(forms.Form):
        submit_label = _('track')

        contest_id = forms.CharField(label=_('Election ID or IPFS Hash'))
        ballot_id = forms.CharField(label=_('Ballot ID'))

        def clean(self):
            pk_or_hash = self.cleaned_data['contest_id']
            ballot_id = self.cleaned_data['ballot_id']

            # clean pk_or_hash
            try:
                uuid.UUID(pk_or_hash)
            except ValueError:
                if not validate_ipfs_hash(pk_or_hash):
                    raise ValidationError(
                        f'"{pk_or_hash}" is not a valid UUID nor IPFS hash'
                    )

            try:
                uuid.UUID(ballot_id)
            except ValueError:
                    raise ValidationError(
                        f'"{ballot_id}" is not a valid UUID'
                    )

            return self.cleaned_data

    def form_valid(self, form):
        return http.HttpResponseRedirect(
            reverse('tracker_detail', kwargs={
                'pk_or_hash': form.cleaned_data['contest_id'],
                'ballot_id': form.cleaned_data['ballot_id']
            })
        )

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
        self.backlink = BackLink(_('Back'), reverse('tracker_form'))

        rows = (
            # (_('Election IPFS hash'), context['contest_hash']),
            (_('Election ID'), context['contest_id']),
            (_('Ballot ID'), context['ballot_id'])
        )

        return super().to_html(
            H4(
                _('Tracking informations'),
                style='text-align:center;'
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
            H5(
                _('Ballot found!')
                if context['ballot']
                else _('Ballot not found.'),
                style='text-align: center'
            ),
        )


class TrackerDetailView(generic.DetailView):
    template_name = 'tracker_detail'
    model = Contest

    def get_object(self, queryset=None):
        pk_or_hash = self.kwargs.get('pk_or_hash')
        try:
            try:
                return Contest.objects.get(pk=pk_or_hash)
            except ValidationError as e:
                if 'UUID' in e.message:
                    # Try to find by ipfs hash
                    out = subprocess.check_output(
                        ['ipfs', 'cid', 'format', pk_or_hash]
                    )
                    # convert to str and remove \n
                    out = bytes.decode(out)[0:-1]
                    if out == pk_or_hash:
                        return Contest.objects.get(artifacts_ipfs=pk_or_hash)
                    else:
                        raise ValidationError(
                            f'"{pk_or_hash}" is not a valid UUID nor IPFS hash'
                        )
                raise e
        except self.model.DoesNotExist:
            raise http.Http404('Contest not found')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(dict(
            contest_id=self.object.id,
            contest_hash=self.object.artifacts_ipfs,
            ballot_id=self.kwargs.get('ballot_id'),
            ballot=None,
        ))

        exists, ballot = self.object.store.exists(str(context['ballot_id']))
        context['ballot'] = ballot

        return context

    @classmethod
    def as_url(cls):
        return path(
            '<pk_or_hash>/<uuid:ballot_id>/',
            cls.as_view(),
            name='tracker_detail'
        )


urlpatterns = [
    TrackerFormView.as_url(),
    TrackerDetailView.as_url(),
]
