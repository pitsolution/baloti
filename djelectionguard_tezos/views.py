from django import forms
from django import http
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.views import generic
from django.views.generic.edit import FormMixin
from django.urls import path, reverse

from djblockchain.models import Account, Blockchain
from djelectionguard.models import Contest

from .models import ElectionContract


User = get_user_model()


class ElectionContractCreate(generic.FormView):
    template_name = 'form.html'

    class form_class(forms.Form):
        blockchain = forms.ModelChoiceField(
            queryset=Blockchain.objects.filter(is_active=True),
            widget=forms.RadioSelect,
        )
        submit_label = 'Choose blockchain'

    def dispatch(self, request, *args, **kwargs):
        self.contest = request.user.contest_set.filter(pk=kwargs['pk']).first()
        if not self.contest:
            return http.HttpResponseBadRequest('Election not found')
        if ElectionContract.objects.filter(election=self.contest).first():
            return http.HttpResponseBadRequest('Contract already created')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        blockchain = form.cleaned_data['blockchain']
        account, created = Account.objects.get_or_create(
            blockchain=blockchain,
            owner=User.objects.get_or_create(email='bank@elictis.io')[0],
        )
        contract = ElectionContract.objects.create(
            sender=account,
            election=self.contest,
            state='deploy',
        )
        messages.success(
            self.request,
            f'Blockchain contract created! Deployment in progress...',
        )
        return http.HttpResponseRedirect(
            reverse('contest_detail', args=[self.contest.pk])
        )

    @classmethod
    def as_url(cls):
        return path(
            '<pk>/create/',
            login_required(cls.as_view()),
            name='electioncontract_create'
        )


urlpatterns = [
    ElectionContractCreate.as_url(),
]