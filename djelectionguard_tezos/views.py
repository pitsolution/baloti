import requests
from django import forms
from django import http
from django.conf import settings
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

from electeez_common.components import Document, Card, BackLink, MDCButton

from djlang.utils import gettext as _

from .models import ElectionContract



User = get_user_model()


class BlockchainItem(Div):
    def __init__(self, account):
        blockchain = account.blockchain
        try:
            balance = account.get_balance()
        except requests.exceptions.ConnectionError:
            balance = None

        super().__init__(
            H6(_('Smart contract on %(obj)s', obj=blockchain.name)),
            Div(
                Span(_('Wallet address:'), cls='overline'),
                ' ',
                account.address
            ),
            Div(
                Span(
                    Span(_('Balance needed:'), cls='overline'),
                    ' 2Tez'
                ),
                Span(
                    Span(_('Current balance:'), cls='overline'),
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
            _('back'),
            reverse('contest_detail', args=[view.contest.id])
        )
        return super().to_html(
            H5(
                _('Choose the blockchain you want to deploy'
                ' your election results to'),
                cls='center-text'),
            Div(
                _('As a way to bring trust, this election results and parameters will be shared and stored via a Tezos smart contract and an IPFS Link. To keep it simple you have two choices, one is to chose the free / testnet contract (fine for non official elections) or the main net one (you ll need to pay a small fee / just send the needed Tez fees to the Wallet address) version that can be used for official election as the equivalent of a legal proof of the election parameters and its results.'),
                cls='center-text body-2'),
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
                H6(
                    _('This choice cannot be changed, please choose carefully'),
                    cls='red center-text',
                    style='margin-bottom: 42px;'),
                Div(
                    MDCButtonOutlined(
                        _('refresh balances'),
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
