import io
import os
import pickle
import shutil

from django import forms
from django import http
from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.urls import path, reverse
from django.utils import timezone
from django.views import generic
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import FormMixin, ProcessFormView

from electionguard.ballot import CiphertextBallot, PlaintextBallot

from pymemcache.client.base import Client

from .models import Contest, Candidate, Guardian


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
        )


class ContestCreateView(generic.CreateView):
    model = Contest

    class form_class(forms.ModelForm):
        start = forms.SplitDateTimeField(
            widget=forms.SplitDateTimeWidget(
                time_attrs={'type': 'time'},
                date_attrs={'type': 'date'},
            )
        )
        end = forms.SplitDateTimeField(
            widget=forms.SplitDateTimeWidget(
                time_attrs={'type': 'time'},
                date_attrs={'type': 'date'},
            )
        )

        class Meta:
            model = Contest
            fields = [
                'name',
                'number_elected',
                'votes_allowed',
                'start',
                'end',
            ]

    def form_valid(self, form):
        form.instance.mediator = self.request.user
        response = super().form_valid(form)
        form.instance.guardian_set.create(user=self.request.user)
        messages.success(
            self.request,
            f'You have created contest {form.instance}',
        )
        return response

    @classmethod
    def as_url(cls):
        return path(
            'create/',
            login_required(cls.as_view()),
            name='contest_create'
        )


class ContestListView(ContestAccessible, generic.ListView):
    @classmethod
    def as_url(cls):
        return path(
            '',
            login_required(cls.as_view()),
            name='contest_list'
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


class ContestOpenView(ContestMediator, generic.UpdateView):
    template_name = 'form.html'

    @classmethod
    def as_url(cls):
        return path(
            '<pk>/open/',
            login_required(cls.as_view()),
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
        messages.success(
            self.request,
            f'You have open contest {self.object}',
        )
        return super().form_valid(form)


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
        messages.success(
            self.request,
            f'You have closed contest {self.object}',
        )
        return super().form_valid(form)


class ContestDecryptView(ContestMediator, generic.UpdateView):
    template_name = 'djelectionguard/contest_decrypt.html'

    @classmethod
    def as_url(cls):
        return path(
            '<pk>/decrypt/',
            login_required(cls.as_view()),
            name='contest_decrypt'
        )

    def get_queryset(self):
        return self.request.user.contest_set.exclude(actual_end=None)

    class form_class(forms.ModelForm):
        class Meta:
            model = Contest
            fields = []

        def save(self, *args, **kwargs):
            # Append from box to tally
            from electionguard.tally import CiphertextTally, publish_ciphertext_tally
            self.instance.ciphertext_tally = CiphertextTally(
                f'{self.instance.pk}-tally',
                self.instance.metadata,
                self.instance.context,
            )
            for ballot in self.instance.store.all():
                assert self.instance.ciphertext_tally.append(ballot)

            from electionguard.decryption_mediator import DecryptionMediator
            decryption_mediator = DecryptionMediator(
                self.instance.metadata,
                self.instance.context,
                self.instance.ciphertext_tally,
            )

            # Decrypt the tally with available guardian keys
            for guardian in self.instance.guardian_set.all():
                if decryption_mediator.announce(guardian.get_guardian()) is None:
                    break

            self.instance.plaintext_tally = decryption_mediator.get_plaintext_tally()
            plaintext_tally_contest = self.instance.plaintext_tally.contests[str(self.instance.pk)]
            for candidate in self.instance.candidate_set.all():
                candidate.score = plaintext_tally_contest.selections[f'{candidate.pk}-selection'].tally
                candidate.save()

            path = os.path.join(settings.MEDIA_ROOT, f'contest-{self.instance.pk}')
            if not os.path.exists(path):
                os.makedirs(path)
            cwd = os.getcwd()
            os.chdir(path)

            from electionguard.publish import publish
            from electionguard.election import ElectionConstants
            publish(
                self.instance.description,
                self.instance.context,
                ElectionConstants(),
                [self.instance.device],
                self.instance.store.all(),
                self.instance.ciphertext_tally.spoiled_ballots.values(),
                publish_ciphertext_tally(self.instance.ciphertext_tally),
                self.instance.plaintext_tally,
                self.instance.coefficient_validation_sets,
            )
            os.chdir(settings.MEDIA_ROOT)
            shutil.make_archive(
                f'contest-{self.instance.pk}',
                'zip',
                f'contest-{self.instance.pk}',
            )
            os.chdir(cwd)

            for guardian in self.instance.guardian_set.all():
                guardian.delete_keypair()

            return super().save(self, *args, **kwargs)

    def get_success_url(self):
        messages.success(
            self.request,
            f'You have decrypted tally for {self.object}',
        )
        messages.info(
            self.request,
            f'Artifacts were published for {self.object}',
        )
        messages.info(
            self.request,
            f'Guardian keys were removed from our memory for {self.object}',
        )
        return self.object.get_absolute_url()


class ContestPubkeyView(ContestMediator, generic.UpdateView):
    template_name = 'djelectionguard/contest_pubkey.html'

    @classmethod
    def as_url(cls):
        return path(
            '<pk>/pubkey/',
            login_required(cls.as_view()),
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


class ContestDetailView(ContestAccessible, generic.DetailView):
    @classmethod
    def as_url(cls):
        return path(
            '<pk>/',
            login_required(cls.as_view()),
            name='contest_detail'
        )

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


class ContestVoteMixin:
    def get_queryset(self):
        return Contest.objects.filter(
            actual_end=None,
            voter__in=self.request.user.voter_set.filter(casted=None),
        ).exclude(
            actual_start=None,
        )


class ContestVoteView(ContestVoteMixin, FormMixin, generic.DetailView):
    template_name = 'form.html'

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


class ContestBallotEncryptView(ContestBallotMixin, FormMixin, generic.DetailView):
    template_name = 'djelectionguard/contest_ballot.html'

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

    @classmethod
    def as_url(cls):
        return path(
            '<pk>/ballot/',
            login_required(cls.as_view()),
            name='contest_ballot'
        )


class ContestBallotCastView(ContestBallotMixin, FormMixin, generic.DetailView):
    template_name = 'djelectionguard/contest_ballot_cast.html'

    class form_class(forms.Form):
        submit_label = 'Cast my ballot'

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


class ContestCandidateCreateView(ContestMediator, FormMixin, generic.DetailView):
    template_name = 'djelectionguard/candidate_form.html'

    class form_class(forms.ModelForm):
        class Meta:
            model = Candidate
            fields = ['name']

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        form.instance.contest = self.get_object()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.get(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        messages.success(
            self.request,
            f'You have added candidate {form.instance}',
        )
        return http.HttpResponseRedirect(
            form.instance.contest.get_absolute_url()
        )

    @classmethod
    def as_url(cls):
        return path(
            '<pk>/candidates/create/',
            login_required(cls.as_view()),
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


class GuardianVerifyView(generic.UpdateView):
    template_name = 'form.html'

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

    @classmethod
    def as_url(cls):
        return path(
            'guardian/<pk>/verify/',
            login_required(cls.as_view()),
            name='guardian_verify'
        )


class GuardianUploadView(generic.UpdateView):
    template_name = 'form.html'

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
        if 'wsgi.file_wrapper' in request.environ:
            del request.environ['wsgi.file_wrapper']
        obj = self.get_object()
        obj.downloaded = timezone.now()
        obj.save()
        response = http.FileResponse(
            io.BytesIO(obj.get_keypair()),
            content_type='application/octet-stream',
        )
        response['Content-Disposition'] = f'attachment; filename="guardian-{obj.pk}.pkl"'
        return response


class ContestVotersDetailView(ContestMediator, generic.DetailView):
    template_name = 'djelectionguard/contest_voters_detail.html'

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
            login_required(cls.as_view()),
            name='contest_voters_detail'
        )


class ContestVotersUpdateView(ContestMediator, generic.UpdateView):
    template_name = 'form.html'

    class form_class(forms.ModelForm):
        submit_label = 'Update voters'
        help_text = 'Set the list of allowed voters by email'

        class Meta:
            model = Contest
            fields = ['voters_emails']
            widgets = dict(
                voters_emails=forms.Textarea(attrs=dict(cols=50, rows=30))
            )

    def form_valid(self, form):
        response = super().form_valid(form)
        form.instance.voters_update()
        return response

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
            login_required(cls.as_view()),
            name='contest_voters_update'
        )


urlpatterns = [
    GuardianDownloadView.as_url(),
    GuardianVerifyView.as_url(),
    GuardianUploadView.as_url(),
    ContestCreateView.as_url(),
    ContestVoteView.as_url(),
    ContestBallotEncryptView.as_url(),
    ContestBallotCastView.as_url(),
    ContestPubkeyView.as_url(),
    ContestDecryptView.as_url(),
    ContestOpenView.as_url(),
    ContestCloseView.as_url(),
    ContestListView.as_url(),
    ContestManifestView.as_url(),
    ContestCandidateCreateView.as_url(),
    ContestCandidateDeleteView.as_url(),
    ContestVotersUpdateView.as_url(),
    ContestVotersDetailView.as_url(),
    ContestDetailView.as_url(),
]
