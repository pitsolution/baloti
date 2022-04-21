import io
import hashlib
import os
from pathlib import Path
import pickle
import re
import shutil
import subprocess
import textwrap
import json

import requests
from django import forms
from django import http
from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
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

from .models import Contest, Candidate, Guardian, Voter, ParentContest, Recommender, ContestRecommender, Initiator, ContestType
from datetime import datetime, date

from ryzom import html
from electeez_sites.models import Site
from electeez_sites.utils import (
    create_access_required,
    result_access_required
)

from electeez_common.components import Document, BackLink
from electeez_auth.models import User
from .components import (
    ParentContestForm,
    ContestForm,
    RecommenderForm,
    InitiatorForm,
    IssueTypeForm,
    ContestPubKeyCard,
    ContestCandidateCreateCard,
    ContestCandidateUpdateCard,
    ContestRecommenderCreateCard,
    ContestRecommenderUpdateCard,
    ParentContestCreateCard,
    ContestCreateCard,
    ContestCard,
    ContestOpenCard,
    ContestCloseCard,
    ContestList,
    ContestVotersUpdateCard,
    ContestVoteCard,
    ContestDecryptCard,
    ContestPublishCard,
    ContestResultCard,
    VotersDetailCard,
    GuardianCreateCard,
    GuardianVerifyCard,
    GuardianUploadKeyCard,
)

from djlang.utils import gettext as _


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
            (Q(voter__user=self.request.user) & ~Q(actual_start=None))
            | Q(guardian__user=self.request.user)
            | Q(mediator=self.request.user)
        ).distinct('id')

class ParentContestAccessible:
    def get_queryset(self):
        return ParentContest.objects.filter(
            Q(mediator=self.request.user)
        ).order_by('-end')


class ContestCreateView(generic.CreateView):
    model = Contest
    form_class = ContestForm

    def form_valid(self, form):
        form.instance.mediator = self.request.user
        form.instance.parent = ParentContest.objects.get(pk=self.kwargs['pk'])
        form.instance.start = ParentContest.objects.get(pk=self.kwargs['pk']).start
        form.instance.end = ParentContest.objects.get(pk=self.kwargs['pk']).end
        form.instance.timezone = ParentContest.objects.get(pk=self.kwargs['pk']).timezone
        response = super().form_valid(form)
        form.instance.guardian_set.create(user=self.request.user)
        form.instance.candidate_set.create(name='Yes', candidate_type='yes')
        form.instance.candidate_set.create(name='No', candidate_type='no')
        form.instance.candidate_set.create(name='Abstain', candidate_type='others')
        messages.success(
            self.request,
            _('You have created contest %(obj)s', obj=form.instance)
        )
        return response

    def get_context_data(self, **kwargs):
        context = super(ContestCreateView, self).get_context_data(**kwargs)
        context['parent'] = ParentContest.objects.get(pk=self.kwargs['pk'])
        return context

    @classmethod
    def as_url(cls):
        return path(
            '<uuid:pk>/create/',
            create_access_required(cls.as_view()),
            name='contest_create'
        )


class ContestUpdateView(generic.UpdateView):
    model = Contest
    form_class = ContestForm

    def get_queryset(self):
        return Contest.objects.filter(
            mediator=self.request.user,
            actual_start=None)

    def get_context_data(self, **kwargs):
        context = super(ContestUpdateView, self).get_context_data(**kwargs)
        context['parent'] = Contest.objects.get(pk=self.kwargs['pk']).parent
        context['contest'] = Contest.objects.get(pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('You have updated contest %(obj)s', obj=form.instance)
        )
        return response

    @classmethod
    def as_url(cls):
        return path(
            '<uuid:parentpk>/update/<uuid:pk>/',
            login_required(cls.as_view()),
            name='contest_update'
        )



class ContestListView(ContestAccessible, generic.ListView):
    model = Contest

    def get_queryset(self):
        return Contest.objects.filter(parent_id=self.kwargs['pk']).distinct('id')

    def get_context_data(self, **kwargs):
        context = super(ContestListView, self).get_context_data(**kwargs)
        context['parent'] = self.kwargs['pk']
        return context

    @classmethod
    def as_url(cls):
        return path(
            'referendum/<uuid:pk>/issues/',
            login_required(cls.as_view()),
            name='contest_list'
        )


class ContestResultView(UserPassesTestMixin, ContestAccessible, generic.DetailView):
    template_name = 'contest_result'

    def test_func(self):
        if Site.objects.get_current().all_results_are_visible:
            return True
        return self.request.user.is_authenticated

    def get_queryset(self):
        qs = Contest.objects.exclude(plaintext_tally=None)

        if Site.objects.get_current().all_results_are_visible:
            return qs

        return qs.filter(
            Q(voter__user=self.request.user)
            | Q(guardian__user=self.request.user)
            | Q(mediator=self.request.user)
        ).distinct('id')

    @classmethod
    def as_url(cls):
        return path(
            '<uuid:pk>/result',
            cls.as_view(),
            name='contest_result'
        )


class ContestDetailView(ContestAccessible, generic.DetailView):
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
            '<uuid:pk>/',
            login_required(cls.as_view()),
            name='contest_detail'
        )


class ContestManifestView(ContestAccessible, generic.DetailView):
    @classmethod
    def as_url(cls):
        return path(
            '<uuid:pk>/manifest/',
            login_required(cls.as_view()),
            name='contest_manifest'
        )

    def get(self, request, *args, **kwargs):
        return http.JsonResponse(self.get_object().get_manifest())


class EmailForm(forms.ModelForm):
    send_email = forms.MultipleChoiceField(
        choices=(('true', 'true'), ('false', 'false')),
        required=False
    )

    email_title = forms.CharField(
        label=_('Email title'),
        help_text=_('Title of the email that will be sent to each voter'),
    )
    email_message = forms.CharField(
        widget=forms.Textarea,
        label=_('Email message'),
        help_text=_('Body of the email that will be sent, LINK will be replaced by the voting link'),
    )

    class Meta:
        model = Contest
        fields = ['send_email', 'email_title', 'email_message']


class EmailBaseView(generic.UpdateView):
    def get_form_kwargs(self):
        msg = _('Hello, '
        'Referendum %(obj)s is open for voting, you may use the link belox: '
        'LINK '
        'Happy voting!', obj=self.object
        )

        kwargs = super().get_form_kwargs()
        kwargs['initial'] = dict(
            email_title=_('Referendum %(obj)s is open for voting', obj=self.object),
            email_message=msg,
        )
        return kwargs

    def form_valid(self, form):
        if 'send_email' not in form.cleaned_data or not form.cleaned_data['send_email']:
            self.object.send_mail(
                form.cleaned_data['email_title'],
                form.cleaned_data['email_message'],
                reverse('contest_vote', args=[self.object.pk]),
                'open_email_sent',
            )
        return super().form_valid(form)


class EmailVotersView(ContestMediator, EmailBaseView):
    template_name = 'email_voters'

    @classmethod
    def as_url(cls):
        return path(
            '<uuid:pk>/email/',
            login_required(cls.as_view()),
            name='email_voters'
        )

    def get_queryset(self):
        return self.request.user.contest_set.exclude(
            joint_public_key=None,
            actual_start=None
        )

    class form_class(EmailForm):
        submit_label = _('Send invite')


class ContestOpenView(ContestMediator, EmailBaseView):
    template_name = 'contest_open'

    @classmethod
    def as_url(cls):
        return path(
            '<uuid:pk>/open/',
            login_required(cls.as_view()),
            name='contest_open'
        )

    def get_queryset(self):
        return self.request.user.contest_set.exclude(
            joint_public_key=None,
        ).filter(
            actual_start=None
        )

    class form_class(EmailForm):
        submit_label = _('Open votes')
        help_text = _('Create the Encrypter and BallotBox and open contest for voting')

        def clean(self):
            if self.instance.candidate_set.count() <= self.instance.number_elected:
                raise forms.ValidationError(
                    _('Must have more candidates than number elected')
                )

        def save(self, *args, **kwargs):
            self.instance.prepare()
            self.instance.actual_start = timezone.now()
            draft_contests = Contest.objects.filter(parent=self.instance.parent, actual_start=None).exclude(pk=self.instance.id)
            if not draft_contests:
                self.instance.parent.status = 'open'
                self.instance.parent.actual_start = timezone.now()
                self.instance.parent.save()
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
            _('You have open contest %(obj)s', obj=self.object)
        )

        return super().form_valid(form)


class ContestCloseView(ContestMediator, generic.UpdateView):
    template_name = 'contest_close'

    @classmethod
    def as_url(cls):
        return path(
            '<uuid:pk>/close/',
            login_required(cls.as_view()),
            name='contest_close'
        )

    def get_queryset(self):
        return self.request.user.contest_set.exclude(
            joint_public_key=None,
            actual_start=None,
        )

    class form_class(forms.ModelForm):
        class Meta:
            model = Contest
            fields = []

        def save(self, *args, **kwargs):
            self.instance.actual_end = timezone.now()
            closed_contests = Contest.objects.filter(parent=self.instance.parent, actual_end=None).exclude(pk=self.instance.id)
            if not closed_contests:
                self.instance.parent.status = 'closed'
                self.instance.parent.actual_end = timezone.now()
                self.instance.parent.save()
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
            _('You have closed contest %(obj)s', obj=self.object)
        )
        return super().form_valid(form)


class ContestDecryptView(ContestMediator, generic.UpdateView):
    template_name = 'contest_decrypt'

    class form_class(forms.ModelForm):
        send_email = forms.MultipleChoiceField(
            choices=(('true', 'true'), ('false', 'false')),
            required=False
        )

        email_title = forms.CharField(
            help_text=_('Title of the email that will be sent to each voter'),
            label=_('Email title')
        )
        email_message = forms.CharField(
            widget=forms.Textarea,
            label=_('Email message'),
            help_text=_('Body of the email that will be sent, LINK will be replaced by the result link'),
        )
        class Meta:
            model = Contest
            fields = ['send_email', 'email_title', 'email_message']

    def get_form_kwargs(self):
        msg = _('Hello, '
        'Referendum %(obj)s has been tallied, you may use this link below to check the results: '
        'LINK '
        'Thank you for voting on %(obj)s', obj=self.object
        )

        kwargs = super().get_form_kwargs()
        kwargs['initial'] = dict(
            email_title= _('Referendum %(obj)s is has been tallied', obj=self.object),
            email_message=msg
        )
        return kwargs

    @classmethod
    def as_url(cls):
        return path(
            '<uuid:pk>/decrypt/',
            login_required(cls.as_view()),
            name='contest_decrypt'
        )

    def get_queryset(self):
        return self.request.user.contest_set.exclude(
            actual_end=None, decrypting=True
        ).filter(
            plaintext_tally=None
        )

    def form_valid(self, form):
        email_voters = (
            'send_email' not in form.cleaned_data
            or not form.cleaned_data['send_email']
        )
        self.object.launch_decryption(
            email_voters,
            form.cleaned_data['email_title'],
            form.cleaned_data['email_message']
        )

        return http.HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        messages.success(
            self.request,
            _('You have started tallying for %(obj)s', obj=self.object)
        )
        return self.object.get_absolute_url()


class ContestDecentralized(ContestMediator):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.exclude(actual_end=None)


class ContestPublishView(ContestDecentralized, generic.UpdateView):
    template_name = 'contest_publish'

    class form_class(forms.ModelForm):
        class Meta:
            model = Contest
            fields = []

    def form_valid(self, form):
        if not settings.IPFS_ENABLED:
            messages.error(
                self.request,
                _('IPFS not initialized on this node')
            )
        else:
            self.object.publish_ipfs()
            if self.object.artifacts_ipfs:
                try:
                    contract = self.object.electioncontract
                except ObjectDoesNotExist:
                    # Contract not deployed on the blockchain
                    pass
                else:
                    contract.artifacts()

        return super().form_valid(form)

    def get_success_url(self):
        if self.object.artifacts_ipfs:
            messages.success(
                self.request,
                _('You have published artifacts for %(obj)s on IPFS', obj=self.object)
            )
        return self.object.get_absolute_url()

    @classmethod
    def as_url(cls):
        return path(
            '<uuid:pk>/publish/',
            login_required(cls.as_view()),
            name='contest_publish'
        )


class ContestPubkeyView(ContestMediator, generic.UpdateView):
    template_name = 'djelectionguard/contest_pubkey.html'
    @classmethod
    def as_url(cls):
        return path(
            '<uuid:pk>/pubkey/',
            login_required(cls.as_view()),
            name='contest_pubkey'
        )

    def get_queryset(self):
        qs = self.request.user.contest_set.filter(joint_public_key=None)
        return qs.exclude(electioncontract=None)

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
            mediator = KeyCeremonyMediator('mediator', details)
            guardians = self.instance.guardian_set.all().order_by('sequence')

            # round 1
            for g in guardians:
                mediator.announce(g.get_guardian().share_public_keys())

            for g in guardians:
                guardian = g.get_guardian()
                other_guardian_keys = mediator.share_announced(guardian.id)
                for guardian_public_keys in other_guardian_keys:
                    guardian.save_guardian_public_keys(guardian_public_keys)

            if len(guardians) > 1:
                # round 2
                for g in guardians:
                    guardian = g.get_guardian()
                    guardian.generate_election_partial_key_backups(lambda msg, key: key)
                    mediator.receive_backups(guardian.share_election_partial_key_backups())

                for g in guardians:
                    guardian = g.get_guardian()
                    backups = mediator.share_backups(guardian.id)
                    for backup in backups:
                        guardian.save_election_partial_key_backup(backup)

                # round 3
                for g in guardians:
                    guardian = g.get_guardian()
                    for og in guardians:
                        other_guardian = og.get_guardian()
                        verifications = []
                        if guardian.id is not other_guardian.id:
                            verifications.append(
                                guardian.verify_election_partial_key_backup(
                                    other_guardian.id, lambda msg, key: key
                                )
                            )
                        mediator.receive_backup_verifications(verifications)

            self.instance.joint_public_key = mediator.publish_joint_key()

            return super().save(self, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        for guardian in form.instance.guardian_set.all():
            guardian.delete_keypair()
        messages.success(
            self.request,
            _('You have completed the ceremony for') + f'{self.object}',
        )
        messages.info(
            self.request,
            _('Guardian keypairs have been deleted from our memory'),
        )
        return response

    def get_success_url(self):
        return self.object.get_absolute_url()


class ContestVoteMixin:
    def get_queryset(self):
        return Contest.objects.filter(
            voter__user=self.request.user,
        )

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.info(request, _('Please get a magic link to proceed to secure vote'))
            return http.HttpResponseRedirect(
                reverse('otp_send')
                + '?next='
                + self.request.path_info
            )
        self.object = self.get_object()

        voter = self.object.voter_set.filter(user=request.user).first()
        redirect = http.HttpResponseRedirect(reverse('contest_list'))
        if not voter:
            messages.error(
                request,
                _('You are not registered to vote on %(obj)s', obj=self.object)
            )
            return redirect
        elif self.object.actual_end:
            messages.error(request, _('%(obj)s vote is closed', obj=self.object))
            return redirect
        elif not self.object.actual_start:
            messages.error(request, _('%(obj)s vote is not yet open', obj=self.object))
            return redirect
        elif voter and voter.casted:
            messages.error(
                request,
                _('You have already casted your vote for %(obj)s', obj=self.object)
            )
            return redirect
        return super().dispatch(request, *args, **kwargs)


class ContestVoteView(ContestVoteMixin, FormMixin, generic.DetailView):
    template_name = 'contest_vote'

    def get_form(self, form_class=None):
        class FormClass(forms.Form):
            submit_label = _('Create ballot')
            selections = forms.ModelMultipleChoiceField(
                queryset=Candidate.objects.none(),
                widget=forms.CheckboxSelectMultiple,
            )
            def clean_selections(self):
                selections = self.cleaned_data['selections']
                if len(selections) > self.max_selections:
                    raise forms.ValidationError(
                        f'Max: {self.max_selections} selections' +
                        _('; you have:') + f'{len(selections)} selections'
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
        ballot = self.object.get_ballot(*[
            selection.pk
            for selection in form.cleaned_data['selections']
        ])
        encrypted_ballot = self.object.encrypter.encrypt(ballot)

        with transaction.atomic():
            if 'spoil' in self.request.POST:
                self.object.ballot_box.spoil(encrypted_ballot)
            else:
                self.object.ballot_box.cast(encrypted_ballot)

                submitted_ballot = self.object.ballot_box._store.get(
                    encrypted_ballot.object_id
                )
                ballot_sha1 = hashlib.sha1(
                    submitted_ballot.to_json().encode('utf8'),
                ).hexdigest()

                self.object.voter_set.update_or_create(
                    user=self.request.user,
                    defaults=dict(
                        casted=True,
                        ballot_id=encrypted_ballot.object_id,
                        ballot_sha1=ballot_sha1
                    ),
                )
            self.object.save()

        if 'spoil' in self.request.POST:
            messages.info(
                self.request,
                _('You spoiled your ballot for %(obj)s you can make another ballot',
                    obj=self.object
                )
            )
            return http.HttpResponseRedirect(
                reverse('contest_vote', args=[self.object.pk])
            )
        else:
            messages.success(
                self.request,
                _('You casted your ballot for %(obj)s', obj=self.object)
            )
            uid = self.object.voter_set.get(user=self.request.user).id
            return http.HttpResponseRedirect(
                    reverse('vote_success', args=[uid])
            )

    @classmethod
    def as_url(cls):
        return path(
            '<uuid:pk>/vote/',
            cls.as_view(),
            name='contest_vote'
        )


class ContestVoteSuccessView(generic.DetailView):
    template_name = 'djelectionguard/vote_success'
    model = Voter

    def get_queryset(self):
        return Voter.objects.filter(
            user=self.request.user,
            casted=True
        )

    @classmethod
    def as_url(cls):
        return path(
            'voter/<uuid:pk>/success/',
            login_required(cls.as_view()),
            name='vote_success'
        )


class ContestCandidateListView(ContestAccessible, generic.DetailView):
    template_name = 'djelectionguard/candidate_list.html'

    @classmethod
    def as_url(cls):
        return path(
            '<uuid:pk>/candidates/',
            login_required(cls.as_view()),
            name='contest_candidate_list'
        )


class CandidateForm(forms.ModelForm):
    description = forms.CharField(
        widget=forms.Textarea(
            attrs=dict(
                rows=3,
                maxlength=300
            )
        ),
        required=False,
        help_text=html.Div(
            html.Div('0/300', cls='mdc-text-field-character-counter'),
            cls='mdc-text-field-helper-line'
        )
    )
    subtext = forms.CharField(
        required=False,
        label=_('Sous-texte'),
    )
    picture = forms.ImageField(
        widget=forms.FileInput,
        label=_('CANDIDATE_PICTURE'),
        required=False
    )

    def clean_name(self):
        name = self.cleaned_data['name']
        if self.instance.contest.candidate_set.filter(
            name=name
        ).exclude(pk=self.instance.pk):
            raise forms.ValidationError(
                f'{name} already added!'
            )

        return name

    class Meta:
        model = Candidate
        fields = [
            'name',
            'subtext',
            'description',
            'picture'
        ]

        labels = {
            'name': _('CANDIDATE_NAME'),
            'description': _('CANDIDATE_DESCRIPTION'),
            'picture': _('CANDIDATE_PICTURE')
        }


class ContestCandidateCreateView(ContestMediator, FormMixin, generic.DetailView):
    template_name = 'djelectionguard/candidate_form.html'
    form_class = CandidateForm

    def get_queryset(self):
        return Contest.objects.filter(
            mediator=self.request.user,
            actual_start=None)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.instance.contest = self.get_object()
        return form

    def form_valid(self, form):
        form.save()
        messages.success(
            self.request,
            _('You have added candidate') + f' {form.instance}',
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('contest_candidate_create', args=[self.get_object().id])

    @classmethod
    def as_url(cls):
        return path(
            '<uuid:pk>/candidates/create/',
            login_required(cls.as_view()),
            name='contest_candidate_create'
        )

class ContestCandidateUpdateView(generic.UpdateView):
    model = Candidate
    form_class = CandidateForm
    template_name = 'djelectionguard/candidate_update.html'

    def get_form(self, *args, **kwargs):
        form = super().get_form()
        form.contest = self.get_object().contest
        return form

    def get_queryset(self):
        return Candidate.objects.filter(
            contest__mediator=self.request.user,
            contest__actual_start=None)

    def get_success_url(self):
        contest = self.get_object().contest
        messages.success(
            self.request,
            _('You have updated candidate') + f'{self.object}',
        )
        return reverse('contest_candidate_create', args=(contest.id,))

    @classmethod
    def as_url(cls):
        return path(
            'candidates/<uuid:pk>/update/',
            login_required(cls.as_view()),
            name='contest_candidate_update'
        )


class ContestCandidateDeleteView(ContestMediator, generic.DeleteView):
    def dispatch(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def get_queryset(self):
        return Candidate.objects.filter(
            contest__mediator=self.request.user,
            contest__actual_start=None)

    def get_success_url(self):
        contest = self.get_object().contest
        messages.success(
            self.request,
            _('You have removed candidate') + f'{self.object}',
        )
        return reverse('contest_candidate_create', args=(contest.id,))

    @classmethod
    def as_url(cls):
        return path(
            'candidates/<uuid:pk>/delete/',
            login_required(cls.as_view()),
            name='contest_candidate_delete'
        )


class GuardianCreateView(ContestMediator, FormMixin, generic.DetailView):
    template_name = 'guardian_create'

    class form_class(forms.Form):
        email = forms.EmailField(required=False)
        quorum = forms.IntegerField(
            min_value=1,
            required=True,
            help_text=_('Minimum guardians needed to unlock the ballot box'))

        class Meta:
            fields = ['email']

        def clean(self):
            if self.cleaned_data['email']:
                email = self.cleaned_data['email']
                user = User.objects.filter(email=email).first()
                if not user:
                    raise forms.ValidationError(
                        dict(email=_('User not found'))
                    )
                if self.instance.contest.guardian_set.filter(user=user):
                    raise forms.ValidationError(
                        dict(email=f'{user}' + _('already added!'))
                    )

            n_guardians = self.instance.contest.guardian_set.count()
            if self.cleaned_data['email']:
                n_guardians += 1

            quorum = self.cleaned_data['quorum']
            if quorum > n_guardians:
                raise forms.ValidationError(
                    dict(quorum=_('Cannot be higher than the number of guardians'))
                )

            return self.cleaned_data

        def save(self):
            contest = self.instance.contest
            contest.quorum = self.cleaned_data['quorum']
            contest.save()

            if self.cleaned_data['email']:
                email = self.cleaned_data['email']
                user = User.objects.filter(email=email).first()
                self.instance.user = user
                self.instance.save()


    def get_queryset(self):
        return Contest.objects.filter(
            mediator=self.request.user,
            actual_start=None,
            joint_public_key=None
        )

    def get_context_data(self, **kwargs):
        self.object = self.get_object()
        return super().get_context_data(**kwargs)

    def get_form(self):
        contest = self.get_object()
        form = super().get_form()
        form.initial['quorum'] = contest.quorum
        form.instance = Guardian(contest=contest)
        return form

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        form.save()
        if form.cleaned_data['email']:
            messages.success(
                self.request,
                _('You have invited %(obj)s as guardian', obj=form.instance),
            )
        if 'quorum' in form.changed_data:
            messages.success(
                self.request,
                _('Quorum set to %(quorum)s', quorum=form.instance.contest.quorum)
            )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('contest_guardian_create', args=[self.get_object().id])

    @classmethod
    def as_url(cls):
        return path(
            '<uuid:pk>/guardian/create/',
            login_required(cls.as_view()),
            name='contest_guardian_create'
        )


class GuardianDeleteView(ContestMediator, generic.DeleteView):
    def dispatch(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        contest = self.get_object().contest

        response = super().delete(request, *args, **kwargs)

        if contest.quorum > contest.guardian_set.count():
            contest.quorum = contest.guardian_set.count()
            contest.save()
            messages.success(
                self.request,
                _('Quorum set to %(quorum)s to match the number of guardians',
                    quorum=contest.quorum
                )
            )
        messages.success(
            self.request,
            _('You have removed guardian %(guardian)s', guardian=self.object)
        )
        return response

    def get_queryset(self):
        return Guardian.objects.filter(
            contest__mediator=self.request.user,
            contest__joint_public_key=None,
            contest__actual_start=None,
        )

    def get_success_url(self):
        contest = self.get_object().contest
        return reverse('contest_guardian_create', args=(contest.id,))

    @classmethod
    def as_url(cls):
        return path(
            'guardian/<uuid:pk>/delete/',
            login_required(cls.as_view()),
            name='contest_guardian_delete'
        )


class GuardianVerifyView(generic.UpdateView):

    def get_queryset(self):
        return self.request.user.guardian_set.filter(uploaded_erased=None)

    class form_class(forms.ModelForm):
        pkl_file = forms.FileField()
        submit_label = _('Verify integrity')

        class Meta:
            model = Guardian
            fields = []

        def clean_pkl_file(self):
            uploaded = self.cleaned_data['pkl_file'].read()
            inmemory = self.instance.get_keypair()
            if uploaded != inmemory:
                raise forms.ValidationError(
                    _('File corrupted, please try downloading again')
                )
            return b''

        def save(self, *args, **kwargs):
            self.instance.verified = timezone.now()
            return super().save(self, *args, **kwargs)

    def get_success_url(self):
        messages.success(
            self.request,
            _('You have verified your guardian key for %(obj)s',
                obj=self.object.contest
            )
        )
        return self.object.contest.get_absolute_url()

    @classmethod
    def as_url(cls):
        return path(
            'guardian/<uuid:pk>/verify/',
            login_required(cls.as_view()),
            name='guardian_verify'
        )


class GuardianUploadView(generic.UpdateView):
    template_name = 'guardian_upload'

    def get_queryset(self):
        return self.request.user.guardian_set.filter(uploaded_erased=None)

    class form_class(forms.ModelForm):
        pkl_file = forms.FileField()
        submit_label = 'Upload'

        class Meta:
            model = Guardian
            fields = []

        def clean(self):
            file_content = self.cleaned_data['pkl_file'].read()
            self.cleaned_data['pkl_file'].seek(0)
            sha1 = hashlib.sha1(file_content).hexdigest()
            if sha1 != self.instance.key_sha1:
                raise forms.ValidationError(_("The provided guardian key is invalid"))

            return self.cleaned_data

        def save(self, *args, **kwargs):
            self.instance.upload_keypair(self.cleaned_data['pkl_file'].read())
            return self.instance

    def get_success_url(self):
        messages.success(
            self.request,
            _('You have uploaded your guardian key for %(obj)s',
                obj=self.object.contest
            )
        )
        return self.object.contest.get_absolute_url()

    @classmethod
    def as_url(cls):
        return path(
            'guardian/<uuid:pk>/upload/',
            login_required(cls.as_view()),
            name='guardian_upload'
        )


class GuardianDownloadView(generic.DetailView):
    def get_queryset(self):
        return self.request.user.guardian_set.filter(erased=None)

    @classmethod
    def as_url(cls):
        return path(
            'guardian/<uuid:pk>/download/',
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


class ContestVotersDetailView(ContestMediator, generic.DetailView):
    template_name = 'djelectionguard/contest_voters_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = {
            voter.user.email: {
                'registered': False,
                'activated': False,
            } for voter in self.object.voter_set.all()
        }
        User = apps.get_model(settings.AUTH_USER_MODEL)
        contest = self.get_object()
        users = User.objects.filter(email__in=contest.voter_set.all().values_list('user__email'))
        for user in users:
            context['users'][user.email]['registered'] = True
            context['users'][user.email]['activated'] = user.is_active
        return context

    @classmethod
    def as_url(cls):
        return path(
            '<uuid:pk>/voters/',
            login_required(cls.as_view()),
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
                _('Please remove lines containing invalid emails: ')
                + ', '.join(invalid))

        return emails


class VotersEmailsForm(forms.ModelForm):
    submit_label = _('Update voters')
    voters_emails = VotersEmailsField(
        label=_('Voters emails'),
        help_text=_('The list of allowed voters with one email per line'),
        required=False,
        widget=forms.Textarea(attrs=dict(cols=50, rows=20))
    )

    class Meta:
        model = Contest
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['voters_emails'].initial = '\n'.join(
            self.instance.voter_set.values_list('user__email', flat=True)
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
    template_name = 'djelectionguard/voters_update.html'
    form_class = VotersEmailsForm

    def get_queryset(self):
        return Contest.objects.filter(
            mediator=self.request.user,
            actual_end=None)

    def get_success_url(self):
        messages.success(
            self.request,
            _('You have updated voters for contest %(obj)s', obj=self.object)
        )
        return self.object.get_absolute_url()

    @classmethod
    def as_url(cls):
        return path(
            '<uuid:pk>/voters/update/',
            login_required(cls.as_view()),
            name='contest_voters_update'
        )


class ContestRecommenderListView(ContestAccessible, generic.DetailView):
    template_name = 'djelectionguard/recommender_list.html'

    @classmethod
    def as_url(cls):
        return path(
            '<uuid:pk>/recommenders/',
            login_required(cls.as_view()),
            name='contest_recommender_list'
        )


class ContestRecommenderForm(forms.ModelForm):

    RECOMMENDER_TYPE = (
        ('infavour', 'IN FAVOUR'),
        ('against', 'AGAINST'),
    )

    recommender = forms.ModelChoiceField(
        queryset=Recommender.objects.filter(),
        empty_label="(Recommender)",
        )
    recommender_type = forms.ChoiceField(
        choices=RECOMMENDER_TYPE
        )

    def __init__(self, *args, **kwargs):
        if kwargs.get('contest'):
            contest = kwargs.pop('contest')
            super().__init__(*args, **kwargs)
            recommenderlist = []
            recommenders = ContestRecommender.objects.filter(pk__in=contest.first().contestrecommender_set.filter())
            for rem in recommenders:
                recommenderlist.append(rem.recommender.id)
            self.fields['recommender'].queryset = Recommender.objects.filter().exclude(pk__in=recommenderlist)
        else:
            super().__init__(*args, **kwargs)

    def clean_recommender(self):
        recommender = self.cleaned_data['recommender']
        if self.instance.contest.contestrecommender_set.filter(
            recommender=recommender
            ).exclude(pk=self.instance.pk):
            raise forms.ValidationError(
                f'{recommender} already added!'
            )
        return recommender

    class Meta:
        model = ContestRecommender
        fields = [
            'recommender',
            'recommender_type'
        ]

        labels = {
            'recommender': _('RECOMMENDER_NAME'),
            'recommender_type': _('RECOMMENDER_TYPE')
        }


class ContestRecommenderCreateView(ContestMediator, FormMixin, generic.DetailView):
    template_name = 'djelectionguard/contestrecommender_form.html'
    form_class = ContestRecommenderForm

    def get_queryset(self):
        return Contest.objects.filter(
            mediator=self.request.user,
            actual_start=None)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.instance.contest = self.get_object()
        return form

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['contest'] = Contest.objects.filter(pk=self.kwargs.get('pk'))
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(
            self.request,
            _('You have added recommender') + f' {form.instance.recommender}',
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('contest_recommender_create', args=[self.get_object().id])

    @classmethod
    def as_url(cls):
        return path(
            '<uuid:pk>/recommenders/add/',
            login_required(cls.as_view()),
            name='contest_recommender_create'
        )

class ContestRecommenderUpdateView(generic.UpdateView):
    model = ContestRecommender
    form_class = ContestRecommenderForm
    template_name = 'djelectionguard/recommender_update.html'

    def get_form(self, *args, **kwargs):
        form = super().get_form()
        form.contest = self.get_object().contest
        return form

    def get_queryset(self):
        return ContestRecommender.objects.filter()

    def get_success_url(self):
        contest = self.get_object().contest
        messages.success(
            self.request,
            _('You have updated recommender') + ' ' + f'{self.object.recommender.name}',
        )
        return reverse('contest_recommender_create', args=(contest.id,))

    @classmethod
    def as_url(cls):
        return path(
            'recommenders/<pk>/update/',
            login_required(cls.as_view()),
            name='contest_recommender_update'
        )


class ContestRecommenderDeleteView(ContestMediator, generic.DeleteView):
    def dispatch(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def get_queryset(self):
        return ContestRecommender.objects.filter()

    def get_success_url(self):
        contest = self.get_object().contest
        messages.success(
            self.request,
            _('You have removed recommender') + ' ' + f'{self.object.recommender}',
        )
        return reverse('contest_recommender_create', args=(contest.id,))

    @classmethod
    def as_url(cls):
        return path(
            'recommenders/<pk>/delete/',
            login_required(cls.as_view()),
            name='contest_recommender_delete'
        )


class RecommenderCreateView(generic.CreateView):
    model = Recommender
    form_class = RecommenderForm
    template_name = 'djelectionguard/recommender_form.html'

    def form_valid(self, form):
        # form.instance.mediator = self.request.user
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('You have created recommender %(obj)s', obj=form.instance)
        )
        return response

    @classmethod
    def as_url(cls):
        return path(
            '<uuid:pk>/recommender/create/',
            create_access_required(cls.as_view()),
            name='recommender_create'
        )
    def get_context_data(self, **kwargs):
        context = super(RecommenderCreateView, self).get_context_data(**kwargs)
        context['contest'] = Contest.objects.get(pk=self.kwargs['pk'])
        return context

    def get_success_url(self):
        # return self.object.get_absolute_url()
        return reverse('contest_recommender_create', args=[self.kwargs['pk']])



class ParentContestCreateView(generic.CreateView):
    model = ParentContest
    form_class = ParentContestForm

    def form_valid(self, form):
        form.instance.mediator = self.request.user
        response = super().form_valid(form)
        from deep_translator import GoogleTranslator
        from djlang.models import Language
        from baloti_djelectionguard.models import ParentContesti18n
        queryset = Language.objects.all()
        form.save()
        print(queryset,'qsettttt', form.instance.pk)
        for each in queryset:
            trans_content_name = GoogleTranslator('auto', each.iso).translate(form.cleaned_data['name'])
            # trans_content_status = GoogleTranslator('auto', each.iso).translate(form.cleaned_data['status'])
            print(trans_content_name,'tscon')
            ParentContesti18n.objects.create(parent_contest_id=form.instance,language=each,name= trans_content_name)

        messages.success(
            self.request,
            _('You have created parentcontest %(obj)s', obj=form.instance)
        )
        return response

    @classmethod
    def as_url(cls):
        return path(
            'referendum/create/',
            create_access_required(cls.as_view()),
            name='parentcontest_create'
        )


class ParentContestUpdateView(generic.UpdateView):
    model = ParentContest
    form_class = ParentContestForm

    def get_queryset(self):
        return ParentContest.objects.filter()

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('You have updated parentcontest %(obj)s', obj=form.instance)
        )
        return response

    @classmethod
    def as_url(cls):
        return path(
            'referendum/<uuid:pk>/update/',
            login_required(cls.as_view()),
            name='parentcontest_update'
        )


class ParentContestListView(ParentContestAccessible, generic.ListView):
    model = ParentContest

    @classmethod
    def as_url(cls):
        return path(
            'referendums',
            login_required(cls.as_view()),
            name='parentcontest_list'
        )

class ParentContestDeleteView(ParentContestAccessible, generic.DeleteView):
    def dispatch(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def get_queryset(self):
        return ParentContest.objects.filter()

    def get_success_url(self):
        messages.success(
            self.request,
            _('You have removed referendum') + ' ' + f'{self.object.name}',
        )
        return reverse('parentcontest_list')

    @classmethod
    def as_url(cls):
        return path(
            'referendum/<uuid:pk>/delete/',
            login_required(cls.as_view()),
            name='parentcontest_delete'
        )


class ParentContestDetailView(ParentContestAccessible, generic.DetailView):
    model = ParentContest

    @classmethod
    def as_url(cls):
        return path(
            'referendum/<uuid:pk>/',
            login_required(cls.as_view()),
            name='parentcontest_detail'
        )

class ContestInitiatorCreateView(generic.CreateView):
    model = Initiator
    form_class = InitiatorForm
    template_name = 'djelectionguard/initiator_form.html'

    @classmethod
    def as_url(cls):
        return path(
            '<uuid:parent>/issue/<uuid:issue>initiator/create/',
            create_access_required(cls.as_view()),
            name='contest_initiator_create'
        )
    def get_context_data(self, **kwargs):
        context = super(ContestInitiatorCreateView, self).get_context_data(**kwargs)
        context['parent'] = self.kwargs['parent']
        context['issue'] = self.kwargs['issue']
        return context

    def get_success_url(self):
        return reverse('contest_update', args=[self.kwargs['parent'], self.kwargs['issue']])

class InitiatorCreateView(generic.CreateView):
    model = Initiator
    form_class = InitiatorForm
    template_name = 'djelectionguard/initiator_form.html'

    @classmethod
    def as_url(cls):
        return path(
            '<uuid:parent>/initiator/create/',
            create_access_required(cls.as_view()),
            name='initiator_create'
        )
    def get_context_data(self, **kwargs):
        context = super(InitiatorCreateView, self).get_context_data(**kwargs)
        context['parent'] = self.kwargs['parent']
        return context

    def get_success_url(self):
        return reverse('contest_list', args=[self.kwargs['parent']])


class ContestIssueTypeCreateView(generic.CreateView):
    model = ContestType
    form_class = IssueTypeForm
    template_name = 'djelectionguard/issue_type_form.html'

    @classmethod
    def as_url(cls):
        return path(
            '<uuid:parent>/issue/<uuid:issue>type/create/',
            create_access_required(cls.as_view()),
            name='contest_issue_type_create'
        )
    def get_context_data(self, **kwargs):
        context = super(ContestIssueTypeCreateView, self).get_context_data(**kwargs)
        context['parent'] = self.kwargs['parent']
        context['issue'] = self.kwargs['issue']
        return context

    def get_success_url(self):
        return reverse('contest_update', args=[self.kwargs['parent'], self.kwargs['issue']])

class IssueTypeCreateView(generic.CreateView):
    model = ContestType
    form_class = IssueTypeForm
    template_name = 'djelectionguard/issue_type_form.html'

    @classmethod
    def as_url(cls):
        return path(
            '<uuid:parent>/type/create/',
            create_access_required(cls.as_view()),
            name='issue_type_create'
        )
    def get_context_data(self, **kwargs):
        context = super(IssueTypeCreateView, self).get_context_data(**kwargs)
        context['parent'] = self.kwargs['parent']
        return context

    def get_success_url(self):
        return reverse('contest_list', args=[self.kwargs['parent']])


class GovtResultsUpdateView(generic.UpdateView):
    model = Contest
    form_class = ContestForm

    def get_context_data(self, **kwargs):
        context = super(GovtResultsUpdateView, self).get_context_data(**kwargs)
        context['parent'] = Contest.objects.get(pk=self.kwargs['pk']).parent
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        if form.instance.govt_infavour_percent and form.instance.govt_against_percent and form.instance.govt_infavour_percent + form.instance.govt_against_percent > 100:
            messages.error(
                self.request,
                _('The total percentage of results is not allowed to exceed 100')
                )

        else:
            messages.success(
                self.request,
                _('You have updated contest %(obj)s', obj=form.instance)
            )
        return response

    @classmethod
    def as_url(cls):
        return path(
            '<uuid:parentpk>/<uuid:pk>/govt/results/create/',
            login_required(cls.as_view()),
            name='govt_results_create'
        )
