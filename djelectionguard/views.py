import io
import hashlib
import os
from pathlib import Path
import pickle
import shutil
import subprocess

from django import forms
from django import http
from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.db import transaction
from django.db.models import ObjectDoesNotExist, Q
from django.urls import path, reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views import generic
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import FormMixin, ProcessFormView

from electionguard.ballot import CiphertextBallot, PlaintextBallot

from pymemcache.client.base import Client

from .models import Contest, Candidate, Guardian

from datetime import datetime, date

from ryzom.views import View as RyzomView
from ryzom.components import components as html
from ryzom.py2js.decorator import JavaScript
from electeez.components import Document, BackLink
from electeez import mdc
from .components import (
    ContestPubKeyCard,
    ContestCandidateCreateCard,
    ContestForm,
    ContestCreateCard,
    ContestCard,
    ContestOpenCard,
    ContestList,
    ContestVotersUpdateCard,
    VotersDetailCard,
    GuardianVerifyCard,
)


class ContestMediator:
    def get_queryset(self):
        return self.request.user.contest_set.all()


class ContestVoter:
    def get_queryset(self):
        return Contest.objects.filter(
            voter__user=self.request.user
        )


class ContestGuardian:
    def get_queryset(self):
        return Contest.objects.filter(
            guardian__user=self.request.user
        )


class ContestAccessible:
    def get_queryset(self):
        return Contest.objects.filter(
            Q(voter__user=self.request.user)
            | Q(guardian__user=self.request.user)
            | Q(mediator=self.request.user)
        ).distinct()


class ContestCreateView(RyzomView, generic.CreateView):
    model = Contest
    form_class = ContestForm

    def form_valid(self, form):
        form.instance.mediator = self.request.user
        response = super().form_valid(form)
        form.instance.guardian_set.create(user=self.request.user)
        messages.success(
            self.request,
            f'You have created contest {form.instance}',
        )
        return response

    def render(self, request):
        context = {}
        if request.method == 'POST':
            form = ContestForm(request.POST)
            if form.is_valid():
                return self.post(form)
            context['form'] = form

        self.backlink = BackLink('my elections', reverse('contest_list'))
        return Document(self, ContestCreateCard, context)

    @classmethod
    def as_url(cls):
        return path(
            'create/',
            login_required(cls.as_view),
            name='contest_create'
        )


class ContestUpdateView(RyzomView, generic.UpdateView):
    model = Contest
    form_class = ContestForm

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'You have updated contest {form.instance}',
        )
        return response

    def render(self, request):
        context = {}
        contest = self.get_object()
        if request.method == 'POST':
            form = ContestForm(request.POST)
            if form.is_valid():
                return self.post(form)
        form = ContestForm(instance=contest)
        context['form'] = form
        self.backlink = BackLink('back', reverse('contest_detail', args=(contest.id,)))
        return Document(self, ContestCreateCard, context)

    @classmethod
    def as_url(cls):
        return path(
            '<pk>/update/',
            login_required(cls.as_view),
            name='contest_update'
        )


class ContestListView(RyzomView, ContestAccessible, generic.ListView):
    model = Contest

    def render(self, request):
        return self.get(request)

    def render_to_response(self, context):
        return Document(self, ContestList, context)

    @classmethod
    def as_url(cls):
        return path(
            '',
            login_required(cls.as_view),
            name='contest_list'
        )


class ContestDetailView(RyzomView, ContestAccessible, generic.DetailView):
    def render(self, request):
        self.backlink = BackLink('my elections', reverse('contest_list'))
        return self.get(request)

    def render_to_response(self, context):
        return Document(self, ContestCard, context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        voter = self.object.voter_set.filter(user=self.request.user).first()
        context['casted'] = voter.casted if voter else None
        context['can_vote'] = (
            self.object.actual_start
            and not self.object.actual_end
            and voter
            and not voter.casted
        )
        return context

    @classmethod
    def as_url(cls):
        return path(
            '<pk>/',
            login_required(cls.as_view),
            name='contest_detail'
        )


class ContestManifestView(ContestAccessible, generic.DetailView):
    @classmethod
    def as_url(cls):
        return path(
            '<pk>/manifest/',
            login_required(cls.as_view()),
            name='contest_manifest'
        )

    def get(self, request, *args, **kwargs):
        return http.JsonResponse(self.get_object().get_manifest())


class ContestOpenView(RyzomView, ContestMediator, generic.UpdateView):
    @classmethod
    def as_url(cls):
        return path(
            '<pk>/open/',
            login_required(cls.as_view),
            name='contest_open'
        )

    def get_queryset(self):
        return self.request.user.contest_set.exclude(
            joint_public_key=None,
        ).filter(
            actual_start=None
        )

    class form_class(forms.ModelForm):
        submit_label = 'Open votes'
        help_text = 'Create the Encrypter and BallotBox and open contest for voting'

        class Meta:
            model = Contest
            fields = []

        def save(self, *args, **kwargs):
            self.instance.prepare()
            self.instance.actual_start = timezone.now()
            return super().save(self, *args, **kwargs)

    def form_valid(self, form):
        try:
            contract = self.object.electioncontract
        except ObjectDoesNotExist:
            pass
        else:
            contract.open()
        messages.success(
            self.request,
            f'You have open contest {self.object}',
        )
        return super().form_valid(form)

    def render(self, request):
        contest = self.get_object()

        if request.method == 'POST':
            return self.post(request)

        self.backlink = BackLink('back', reverse('contest_detail', args=(contest.id,)))
        return Document(self, ContestOpenCard, dict())


class ContestCloseView(ContestMediator, generic.UpdateView):
    template_name = 'form.html'

    @classmethod
    def as_url(cls):
        return path(
            '<pk>/close/',
            login_required(cls.as_view()),
            name='contest_close'
        )

    def get_queryset(self):
        return self.request.user.contest_set.exclude(
            joint_public_key=None,
            actual_start=None,
        )

    class form_class(forms.ModelForm):
        submit_label = 'Close contest'
        help_text = 'Closing the contest will stop the voting process and start the decryption ceremony'

        class Meta:
            model = Contest
            fields = []

        def save(self, *args, **kwargs):
            self.instance.actual_end = timezone.now()
            return super().save(self, *args, **kwargs)

    def form_valid(self, form):
        try:
            contract = self.object.electioncontract
        except ObjectDoesNotExist:
            pass
        else:
            contract.close()
        messages.success(
            self.request,
            f'You have closed contest {self.object}',
        )
        return super().form_valid(form)


class ContestDecryptView(ContestMediator, generic.UpdateView):
    template_name = 'djelectionguard/contest_decrypt.html'

    class form_class(forms.ModelForm):
        ipfs = forms.BooleanField(label='Deploy on IPFS?', required=False)

        class Meta:
            model = Contest
            fields = []

    @classmethod
    def as_url(cls):
        return path(
            '<pk>/decrypt/',
            login_required(cls.as_view()),
            name='contest_decrypt'
        )

    def get_queryset(self):
        return self.request.user.contest_set.exclude(actual_end=None)

    def form_valid(self, form):
        self.object.decrypt()
        self.object.publish()

        if form.cleaned_data['ipfs']:
            if not settings.IPFS_ENABLED:
                messages.error(
                    self.request,
                    'IPFS not initialized on this node'
                )
            else:
                self.object.publish_ipfs()

        try:
            contract = self.object.electioncontract
        except ObjectDoesNotExist:
            # Contract not deployed on the blockchain
            pass
        else:
            contract.artifacts()

        return super().form_valid(form)

    def get_success_url(self):
        messages.success(
            self.request,
            f'You have decrypted tally for {self.object}',
        )
        if self.object.artifacts_ipfs:
            messages.success(
                self.request,
                f'You have published artifacts for {self.object} on IPFS '
                + self.object.artifacts_ipfs
            )
        else:
            messages.info(
                self.request,
                f'Artifacts were published for {self.object}',
            )
        messages.info(
            self.request,
            f'Guardian keys were removed from our memory for {self.object}',
        )
        return self.object.get_absolute_url()


class ContestPubkeyView(RyzomView, ContestMediator, generic.UpdateView):
    @classmethod
    def as_url(cls):
        return path(
            '<pk>/pubkey/',
            login_required(cls.as_view),
            name='contest_pubkey'
        )

    def get_queryset(self):
        return self.request.user.contest_set.filter(joint_public_key=None)

    class form_class(forms.ModelForm):
        class Meta:
            model = Contest
            fields = []

        def save(self, *args, **kwargs):
            from electionguard.key_ceremony import CeremonyDetails
            from electionguard.key_ceremony_mediator import KeyCeremonyMediator
            details = CeremonyDetails(
                self.instance.number_guardians,
                self.instance.quorum,
            )
            mediator = KeyCeremonyMediator(details)
            for guardian in self.instance.guardian_set.all():
                mediator.announce(guardian.get_guardian())
            orchestrated = mediator.orchestrate()
            verified = mediator.verify()
            self.instance.joint_public_key = mediator.publish_joint_key()
            self.instance.coefficient_validation_sets = []
            for guardian in self.instance.guardian_set.all():
                self.instance.coefficient_validation_sets.append(
                    guardian.get_guardian().share_coefficient_validation_set()
                )
            return super().save(self, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        for guardian in form.instance.guardian_set.all():
            guardian.delete_keypair()
        messages.success(
            self.request,
            f'You have completed the ceremony for {self.object}',
        )
        messages.info(
            self.request,
            f'Guardian keypairs have been deleted from our memory',
        )
        return response

    def get_success_url(self):
        return self.object.get_absolute_url()

    def render(self, request):
        contest = self.get_object()

        if request.method == 'POST':
            return self.post(request)

        self.backlink = BackLink('Back', reverse('contest_detail', args=(contest.id,)))
        return Document(self, ContestPubKeyCard, dict())


class ContestVoteMixin:
    def get_queryset(self):
        return Contest.objects.filter(
            actual_end=None,
            voter__in=self.request.user.voter_set.filter(casted=None),
        ).exclude(
            actual_start=None,
        )


class ContestVoteView(ContestVoteMixin, FormMixin, generic.DetailView):
    template_name = 'djelectionguard/contest_new_vote.html'

    def get_form(self, form_class=None):
        class FormClass(forms.Form):
            submit_label = 'Create ballot'
            selections = forms.ModelMultipleChoiceField(
                queryset=Candidate.objects.none(),
                widget=forms.CheckboxSelectMultiple,
            )
            def clean_selections(self):
                selections = self.cleaned_data['selections']
                if len(selections) > self.max_selections:
                    raise forms.ValidationError(
                        f'Max: {self.max_selections} selections'
                        f'; you have: {len(selections)} selections'
                    )
                return selections
        form = FormClass(**self.get_form_kwargs())
        form.fields['selections'].queryset = self.object.candidate_set.all()
        form.max_selections = self.object.votes_allowed
        return form

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.get(request, *args, **kwargs)

    def form_valid(self, form):
        obj = self.get_object()
        ballot = obj.get_ballot(*[
            selection.pk
            for selection in form.cleaned_data['selections']
        ])
        client = Client(settings.MEMCACHED_HOST)
        client.set(
            f'{obj.pk}-{self.request.user.pk}',
            ballot.to_json(),
        )
        return http.HttpResponseRedirect(
            reverse('contest_ballot', args=[obj.pk])
        )

    @classmethod
    def as_url(cls):
        return path(
            '<pk>/vote/',
            login_required(cls.as_view()),
            name='contest_vote'
        )


class ContestBallotMixin(ContestVoteMixin):
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        client = Client(settings.MEMCACHED_HOST)
        if not client.get(f'{self.object.pk}-{self.request.user.pk}'):
            return http.HttpResponseRedirect(
                reverse('contest_vote', args=[self.object.pk])
            )
        return super().dispatch(request, *args, **kwargs)


class ContestBallotEncryptView(RyzomView, ContestBallotMixin, FormMixin, generic.DetailView):
    class form_class(forms.Form):
        submit_label = 'Encrypt my ballot'

    def post(self, request, *args, **kwargs):
        client = Client(settings.MEMCACHED_HOST)
        ballot = PlaintextBallot.from_json(
            client.get(f'{self.object.pk}-{self.request.user.pk}')
        )
        client.set(
            f'{self.object.pk}-{self.request.user.pk}',
            self.object.encrypter.encrypt(ballot).to_json()
        )
        return http.HttpResponseRedirect(
            reverse('contest_ballot_cast', args=[self.object.pk])
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        client = Client(settings.MEMCACHED_HOST)
        context['ballot'] = PlaintextBallot.from_json(
            client.get(f'{self.object.pk}-{self.request.user.pk}')
        )
        selections = [
            s.object_id.replace('-selection', '')
            for s in context['ballot'].contests[0].ballot_selections
        ]
        context['selections'] = self.object.candidate_set.filter(pk__in=selections)
        return context

    def render(self, request):
        contest = self.get_object()

        if request.method == 'POST':
            return self.post(request)

        self.backlink = BackLink('Back', reverse('contest_detail', args=(contest.id,)))
        return Document(self, ContestBallotEncryptCard, dict())

    @classmethod
    def as_url(cls):
        return path(
            '<pk>/ballot/',
            login_required(cls.as_view),
            name='contest_ballot'
        )


class ContestBallotCastView(ContestBallotMixin, FormMixin, generic.DetailView):
    template_name = 'djelectionguard/contest_ballot_cast.html'

    class form_class(forms.Form):
        submit_label = 'Confirm my vote'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        client = Client(settings.MEMCACHED_HOST)

        ballot = CiphertextBallot.from_json(
            client.get(f'{self.object.pk}-{self.request.user.pk}')
        )

        with transaction.atomic():
            if 'spoil' in request.POST:
                self.object.ballot_box.spoil(ballot)
            else:
                self.object.ballot_box.cast(ballot)
                self.object.voter_set.update_or_create(
                    user=self.request.user,
                    defaults=dict(casted=timezone.now()),
                )
            self.object.save()

        client.delete(
            f'{self.object.pk}-{self.request.user.pk}',
        )

        if 'spoil' in request.POST:
            messages.info(
                self.request,
                f'You spoiled your ballot for {self.object}, you can make another ballot',
            )
            return http.HttpResponseRedirect(
                reverse('contest_vote', args=[self.object.pk])
            )
        else:
            messages.success(
                self.request,
                f'You casted your ballot for {self.object}',
            )
            return http.HttpResponseRedirect(self.object.get_absolute_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = Client(settings.MEMCACHED_HOST)
        context['ballot'] = CiphertextBallot.from_json(
            client.get(f'{self.object.pk}-{self.request.user.pk}')
        )
        return context

    @classmethod
    def as_url(cls):
        return path(
            '<pk>/ballot/cast/',
            login_required(cls.as_view()),
            name='contest_ballot_cast'
        )


class ContestCandidateCreateView(RyzomView, ContestMediator, FormMixin, generic.DetailView):
    class form_class(forms.ModelForm):
        def clean_name(self):
            name = self.cleaned_data['name']
            if self.instance.contest.candidate_set.filter(name=name):
                raise forms.ValidationError(
                    f'{name} already added!'
                )
            return name

        class Meta:
            model = Candidate
            fields = ['name']

    def render(self, request):
        contest = self.get_object()
        self.backlink = BackLink('Back', reverse('contest_detail', args=(contest.id,)))

        if request.method == 'POST':
            return self.post(request)

        context = {'form': self.get_form()}
        return Document(self, ContestCandidateCreateCard, context)

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.instance.contest = self.get_object()
        return form

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            context = {'form': form}
            return Document(self, ContestCandidateCreateCard, context)

    def form_valid(self, form):
        form.save()
        messages.success(
            self.request,
            f'You have added candidate {form.instance}',
        )
        return Document(self, ContestCandidateCreateCard, dict(form=form))

    @classmethod
    def as_url(cls):
        return path(
            '<pk>/candidates/create/',
            login_required(cls.as_view),
            name='contest_candidate_create'
        )


class ContestCandidateDeleteView(ContestMediator, generic.DeleteView):
    template_name = 'delete.html'

    def get_queryset(self):
        return Candidate.objects.filter(contest__mediator=self.request.user)

    def get_success_url(self):
        messages.success(
            self.request,
            f'You have removed candidate {self.object}',
        )
        return self.object.contest.get_absolute_url()

    @classmethod
    def as_url(cls):
        return path(
            'candidates/<pk>/delete/',
            login_required(cls.as_view()),
            name='contest_candidate_delete'
        )


class GuardianVerifyView(RyzomView, generic.UpdateView):

    def get_queryset(self):
        return self.request.user.guardian_set.filter(uploaded_erased=None)

    class form_class(forms.ModelForm):
        pkl_file = forms.FileField()
        submit_label = 'Verify integrity'

        class Meta:
            model = Guardian
            fields = []

        def clean_pkl_file(self):
            uploaded = self.cleaned_data['pkl_file'].read()
            inmemory = self.instance.get_keypair()
            if uploaded != inmemory:
                raise forms.ValidationError(
                    'File corrupted, please try downloading again'
                )
            return b''

        def save(self, *args, **kwargs):
            self.instance.verified = timezone.now()
            return super().save(self, *args, **kwargs)

    def get_success_url(self):
        messages.success(
            self.request,
            f'You have verified your guardian key for {self.object.contest}',
        )
        return self.object.contest.get_absolute_url()

    def render(self, request):
        self.object = self.get_object()
        contest = self.object.contest
        self.backlink = BackLink('Back', reverse('contest_detail', args=(contest.id,)))

        form = self.get_form()
        form.instance = self.object

        if request.method == 'POST':
            if form.is_valid():
                form.save()
                return http.HttpResponseRedirect(self.get_success_url())

        context = {'form': form}
        return Document(self, GuardianVerifyCard, context)

    @classmethod
    def as_url(cls):
        return path(
            'guardian/<pk>/verify/',
            login_required(cls.as_view),
            name='guardian_verify'
        )


class GuardianUploadView(generic.UpdateView):
    template_name = 'djelectionguard/contest_form_upluoad_close.html'

    def get_queryset(self):
        return self.request.user.guardian_set.filter(uploaded_erased=None)

    class form_class(forms.ModelForm):
        pkl_file = forms.FileField()
        submit_label = 'Upload'

        class Meta:
            model = Guardian
            fields = []

        def save(self, *args, **kwargs):
            self.instance.upload_keypair(self.cleaned_data['pkl_file'].read())
            return self.instance

    def get_success_url(self):
        messages.success(
            self.request,
            f'You have uploaded your guardian key for {self.object.contest}',
        )
        return self.object.contest.get_absolute_url()

    @classmethod
    def as_url(cls):
        return path(
            'guardian/<pk>/upload/',
            login_required(cls.as_view()),
            name='guardian_upload'
        )


class GuardianDownloadView(generic.DetailView):
    def get_queryset(self):
        return self.request.user.guardian_set.filter(erased=None)

    @classmethod
    def as_url(cls):
        return path(
            'guardian/<pk>/download/',
            login_required(cls.as_view()),
            name='guardian_download'
        )

    def get(self, request, *args, **kwargs):
        if 'wsgi.file_wrapper' in request.META:
            del request.META['wsgi.file_wrapper']
        obj = self.get_object()
        obj.downloaded = timezone.now()
        obj.save()
        response = http.FileResponse(
            io.BytesIO(obj.get_keypair()),
            as_attachment=True,
            filename=f"guardian-{obj.pk}.pkl",
            content_type='application/octet-stream',
        )
        return response


class ContestVotersDetailView(RyzomView, ContestMediator, generic.DetailView):
    def render(self, request):
        contest = self.get_object()
        self.backlink = BackLink('Back', reverse('contest_detail', args=(contest.id,)))
        return Document(self, VotersDetailCard, dict())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = {
            email: {
                'registered': False,
                'activated': False,
            } for email in self.object.voters_emails_list
        }
        User = apps.get_model(settings.AUTH_USER_MODEL)
        users = User.objects.filter(email__in=self.object.voters_emails_list)
        for user in users:
            context['users'][user.email]['registered'] = True
            context['users'][user.email]['activated'] = user.is_active
        return context

    @classmethod
    def as_url(cls):
        return path(
            '<pk>/voters/',
            login_required(cls.as_view),
            name='contest_voters_detail'
        )


class VotersEmailsField(forms.CharField):
    widget = forms.Textarea

    def clean(self, value):
        value = super().clean(value)
        value = value.replace(
            '\r\n', '\n'       # windows
        ).replace('\r', '\n')  # mac

        validator = EmailValidator()
        invalid = []
        emails = []
        for line in value.split('\n'):
            line = line.strip().lower()
            if not line:
                continue
            try:
                validator(line)
            except ValidationError:
                invalid.append(line)
            else:
                emails.append(line)

        if invalid:
            raise ValidationError(
                'Please remove lines containing invalid emails: '
                + ', '.join(invalid)
            )

        return emails


class VotersEmailsForm(forms.ModelForm):
    submit_label = 'Update voters'
    voters_emails = VotersEmailsField(
        help_text='The list of allowed voters with one email per line',
        required=False,
        widget=forms.Textarea(attrs=dict(cols=50, rows=20))
    )

    class Meta:
        model = Contest
        fields = []

    def save(self):
        voters_emails_list = self.cleaned_data['voters_emails']

        # delete voters who are not anymore in the email list
        self.instance.voter_set.filter(
            casted=None
        ).exclude(
            user__email__in=voters_emails_list
        ).delete()

        current = list(
            self.instance.voter_set.values_list(
                'user__email', flat=True
            )
        )

        # add new voters who have a user
        User = apps.get_model(settings.AUTH_USER_MODEL)
        users = User.objects.filter(
            email__in=voters_emails_list,
        )
        for user in users:
            if user.email.lower() in current:
                continue
            self.instance.voter_set.create(user=user)
            current.append(user.email)

        # add new voters who do not have a user
        for email in voters_emails_list:
            if email in current:
                continue
            self.instance.voter_set.create(
                user=User.objects.create(
                    email=email,
                    # consider them activated by the mediator
                    is_active=True,
                )
            )

        return self.instance


class ContestVotersUpdateView(ContestMediator, generic.UpdateView):
    template_name = 'djelectionguard/contest_add_voters_email.html'
    form_class = VotersEmailsForm

    def get_success_url(self):
        messages.success(
            self.request,
            f'You have updated voters for contest {self.object}',
        )
        return self.object.get_absolute_url()

    @classmethod
    def as_url(cls):
        return path(
            '<pk>/voters/update/',
            login_required(cls.as_view),
            name='contest_voters_update'
        )
