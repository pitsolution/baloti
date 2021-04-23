import requests
from django import forms
from django import http
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.views import generic
from django.views.generic.edit import FormMixin
from django.urls import path, reverse

from djtezos.models import Account, Blockchain
from djelectionguard.models import Contest

from ryzom.html import template
from ryzom_mdc import *
from ryzom_django_mdc.html import *
from electeez.components import Document, Card, BackLink, MDCButton
from .models import ElectionContract
from django.utils.translation import gettext_lazy as _
from django.conf import settings


User = get_user_model()


class BlockchainItem(Div):
    def __init__(self, account):
        blockchain = account.blockchain
        try:
            balance = account.get_balance()
        except requests.exceptions.ConnectionError:
            balance = None

        super().__init__(
            H6('Smart contract on ', blockchain.name),
            Div(
                Span('Wallet address: ', cls='overline'),
                account.address
            ),
            Div(
                Span(
                    Span('Balance needed:', cls='overline'),
                    ' 2Tez'
                ),
                Span(
                    Span('Current balance:', cls='overline'),
                    f' {balance/1000000 if balance else 0}Tez'
                )
                if balance is not None else None,
                style='display: flex; justify-content: space-between;'
            )
        )


@template('electioncontract_create', Document, Card)
class ElectionContractCard(Div):
    def to_html(self, *content, view, form, **context):
        self.backlink = BackLink(
            'back',
            reverse('contest_detail', args=[view.contest.id])
        )
        return super().to_html(
            H4(
                _('Choose the blockchain you want to deploy'
                ' your election results to'),
                cls='center-text'),
            H5(
                _('This choice cannot be changed, please choose carefully'),
                cls='red center-text'),
            Form(
                MDCErrorList(form.errors) if form.errors else None,
                MDCMultipleChoicesCheckbox(
                    'blockchain',
                    (
                        (i, BlockchainItem(account), account.blockchain.pk)
                        for i, account
                        in enumerate(context['accounts'])
                    ),
                    n=1),
                Div(
                    MDCButtonOutlined(
                        'refresh balances',
                        tag='a',
                        onclick='window.location.reload()'
                    ),
                    MDCButton(form.submit_label),
                    style='display: flex; justify-content: space-between'
                ),
                CSRFInput(view.request),
                method='POST',
                cls='form contract-form'),
            cls='card')


class ElectionContractCreate(generic.FormView):
    template_name = 'electioncontract_create'

    class form_class(forms.Form):
        blockchain = forms.ModelChoiceField(
            queryset=Blockchain.objects.filter(is_active=True),
        )
        submit_label = _('Confirm Smart Contract')

    def dispatch(self, request, *args, **kwargs):
        self.contest = request.user.contest_set.filter(pk=kwargs['pk']).first()
        if not self.contest:
            return http.HttpResponseBadRequest(_('Election not found'))
        if ElectionContract.objects.filter(election=self.contest).first():
            return http.HttpResponseBadRequest(_('Contract already created'))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = Blockchain.objects.filter(is_active=True)
        context['accounts'] = []
        for blockchain in qs:
            account, created = Account.objects.get_or_create(
                blockchain=blockchain,
                owner=User.objects.get_or_create(email='bank@elictis.io')[0],
            )
            context['accounts'].append(account)

        return context

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
            _(f'Blockchain contract created! Deployment in progress...'),
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
