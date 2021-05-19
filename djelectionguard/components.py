from datetime import datetime, date
from django import forms
from django.conf import settings
from django.db.models import Sum
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.utils import timezone
from electeez.components import *
from ryzom_django.forms import widget_template
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from electeez.components import (
    Document,
    Card,
    BackLink,
    MDCLinearProgress,
    MDCButton
)
from .models import Contest, Candidate


@widget_template('django/forms/widgets/splitdatetime.html')
class SplitDateTimeWidget(SplitDateTimeWidget):
    date_style = 'margin-top: 0; margin-bottom: 32px;'
    time_style = 'margin: 0;'


class ContestForm(forms.ModelForm):
    def now():
        now = datetime.now()
        return now.replace(second=0, microsecond=0)

    about = forms.CharField(
        label=_('FORM_ABOUT_ELECTION_CREATE'),
        widget=forms.Textarea,
        required=False
    )

    votes_allowed = forms.IntegerField(
        label=_('FORM_VOTES_ALLOWED_ELECTION_CREATE'),
        initial=1,
        help_text=_('The maximum number of choice a voter can make for this election')
    )

    start = forms.SplitDateTimeField(
        label='',
        initial=now,
        widget=forms.SplitDateTimeWidget(
            date_format='%Y-%m-%d',
            date_attrs={'type': 'date'},
            time_attrs={'type': 'time'},
        ),
    )
    end = forms.SplitDateTimeField(
        label='',
        initial=now,
        widget=forms.SplitDateTimeWidget(
            date_format='%Y-%m-%d',
            date_attrs={'type': 'date'},
            time_attrs={'type': 'time'},
        )
    )

    class Meta:
        model = Contest
        fields = [
            'name',
            'about',
            'votes_allowed',
            'start',
            'end',
            'timezone',
        ]
        labels = {
            'name': _('FORM_TITLE_ELECTION_CREATE'),
            'about': _('FORM_ABOUT_ELECTION_CREATE'),
            'votes_allowed': _('FORM_VOTES_ALLOWED_ELECTION_CREATE'),
            'start': _('FORM_START_ELECTION_CREATE'),
            'end': _('FORM_END_ELECTION_CREATE'),
            'timezone': _('FORM_TIMEZONE_ELECTION_CREATE')
        }


class ContestFormComponent(CList):
    def __init__(self, view, form, edit=False):
        content = []
        content.append(Ul(
            *[Li(e) for e in form.non_field_errors()],
            cls='error-list'
        ))

        super().__init__(
            H4(_('Edit election') if edit else _('Create an election')),
            Form(
                form['name'],
                form['about'],
                H6(_('Voting settings:')),
                form['votes_allowed'],
                H6(_('Election starts:')),
                form['start'],
                H6(_('Election ends:')),
                form['end'],
                form['timezone'],
                CSRFInput(view.request),
                MDCButton(_('update election') if edit else _('create election')),
                method='POST',
                cls='form'),
        )


@template('djelectionguard/contest_form.html', Document, Card)
class ContestCreateCard(Div):
    style = dict(cls='card')

    def to_html(self, *content, view, form, **context):
        self.backlink = BackLink(_('back'), reverse('contest_list'))

        edit = view.object is not None
        return super().to_html(
            ContestFormComponent(view, form, edit),
        )


class ContestFiltersBtn(Button):
    def __init__(self, pos, text, active=False):
        active_cls_name = 'mdc-tab--active' if active else ''
        active_indicator = 'mdc-tab-indicator--active' if active else ''

        attrs = {
            'class': f'contest-filter-btn mdc-tab {active_cls_name}',
            'role': 'tab',
            'aria-selected': 'true',
            'tabindex': pos
        }
        super().__init__(
            Span(
                Span(text, cls='mdc-tab__text-label'),
                cls='mdc-tab__content'
            ),
            Span(
                Span(cls='mdc-tab-indicator__content ' +
                              'mdc-tab-indicator__content--underline'
                ),
                cls=f'mdc-tab-indicator {active_indicator}'
            ),
            Span(cls='mdc-tab__ripple'),
            **attrs
        )


class ContestFilters(Div):
    def __init__(self, view):
        active_btn = view.request.GET.get('q', 'all')

        self.all_contests_btn = ContestFiltersBtn(1, _('all'), active_btn == 'all')
        self.my_contests_btn = ContestFiltersBtn(2, _('created by me'), active_btn == 'created')
        self.shared_contests_btn = ContestFiltersBtn(3, _('shared with me'), active_btn == 'shared')

        super().__init__(
            Div(
                Div(
                    self.all_contests_btn,
                    self.my_contests_btn,
                    self.shared_contests_btn,
                    cls='mdc-tab-scroller__scroll-content'
                ),
                cls='mdc-tab-scroller__scroll-area ' +
                    'mdc-tab-scroller__scroll-area--scroll'
            ),
            cls='mdc-tab-bar contest-filter'
        )


class ContestItem(A):
    def __init__(self, contest, *args, **kwargs):
        active_cls = ''
        status = ''
        if contest.actual_start:
            status = _('voting ongoing')
            active_cls = 'active'
        if contest.plaintext_tally:
            active_cls = ''
            status = _('result available')

        super().__init__(
            Span(cls='mdc-list-item__ripple'),
            Span(
                Span(cls=f'contest-indicator'),
                Span(
                    Span(status, cls='contest-status overline'),
                    Span(contest.name, cls='contest-name'),
                    cls='list-item__text-container'
                ),
                cls='mdc-list-item__text'
            ),
            cls=f'contest-list-item mdc-list-item mdc-ripple-upgraded {active_cls}',
            href=reverse('contest_detail', args=[contest.id])
        )


class Separator(Li):
    def __init__(self, inset=False):
        cls = 'mdc-list-divider'
        if inset:
            cls += ' mdc-list-divider--inset'
        super().__init__(role='separator', cls=cls)


class ListItem(CList):
    def __init__(self, component, separator=True):
        content = [component]
        if separator:
            content.append(Separator())
        super().__init__(*content)


class ContestListItem(ListItem):
    def __init__(self, obj, **kwargs):
        super().__init__(ContestItem(obj))


class ListAction(ListItem):
    def __init__(self, title, txt, icon_comp, btn_comp, **kwargs):
        self.action_btn = btn_comp

        subitem_cls = 'mdc-list-item__primary-text list-action-row'
        if not txt:
            subitem_cls = 'list-action-row'
        subitem = Span(cls=subitem_cls)

        if icon_comp:
            subitem.addchild(icon_comp)
        subitem.addchild(H6(title))
        if btn_comp:
            subitem.addchild(btn_comp)

        item = Span(subitem, cls='mdc-list-item__text list-action-column')
        if txt:
            item.addchild(Span(txt, cls='mdc-list-item__secondary-text ' +
                                             'list-action-text body-2'))

        super().__init__(Li(item, cls='mdc-list-item list-action-item'), **kwargs)


class ContestListCreateBtn(A):
    def __init__(self):
        super().__init__(
            Span(
                Span(cls='mdc-list-item__ripple'),
                Span(
                    Span('+', cls='new-contest-icon'),
                    cls='new-contest-icon-container'
                ),
                Span(_('Create new election')),
                cls='mdc-list-item__text text-btn mdc-ripple-upgraded'
            ),
            cls='mdc-list-item contest-list-item',
            href=reverse('contest_create')
        )


@template('djelectionguard/contest_list.html', Document, Card)
class ContestList(Div):
    def to_html(self, *content, view, **context):
        return super().to_html(
            H4(_('Elections'), style='text-align: center;'),
            # ContestFilters(view),
            Ul(
                ListItem(ContestListCreateBtn()),
                *(
                    ContestListItem(contest)
                    for contest in context['contest_list']
                ) if len(context['contest_list'])
                else (
                    Li(
                        _('There are no elections yet'),
                        cls='mdc-list-item body-1'
                    ),
                ),
                cls='mdc-list contest-list'
            ),
            cls='card'
        )


class CircleIcon(Span):
    def __init__(self, icon, color='', small=False):
        base_cls = f'icon {icon} {"small " if small else ""}'
        super().__init__(
            cls=base_cls + color
        )


class TodoIcon(CircleIcon):
    def __init__(self):
        super().__init__('empty-icon', 'yellow')


class DoneIcon(CircleIcon):
    def __init__(self):
        super().__init__('check-icon', 'green')


class TezosIcon(CircleIcon):
    def __init__(self):
        super().__init__('tezos-icon', 'white')


class OnGoingIcon(CircleIcon):
    def __init__(self):
        super().__init__('ongoing-icon', 'yellow')


class EmailIcon(CircleIcon):
    def __init__(self):
        super().__init__('email-icon', 'yellow')


class SimpleCheckIcon(CircleIcon):
    def __init__(self):
        super().__init__('simple-check-icon', 'green')


class WorldIcon(CircleIcon):
    def __init__(self):
        super().__init__('world-icon', 'black', small=True)


class BasicSettingsAction(ListAction):
    def __init__(self, obj):
        btn_comp = MDCButtonOutlined(
            _('edit'),
            False,
            tag='a',
            href=reverse('contest_update', args=[obj.id]))
        super().__init__(
            _('Basic settings'),
            _('Name, votes allowed, time and date, etc.'),
            DoneIcon(), btn_comp
        )


class AddCandidateAction(ListAction):
    def __init__(self, obj):
        num_candidates = obj.candidate_set.count()
        kwargs = dict(
            tag='a',
            href=reverse('contest_candidate_create', args=[obj.id]))
        if num_candidates and num_candidates > obj.number_elected:
            btn_comp = MDCButtonOutlined(_('edit'), False, **kwargs)
            icon = DoneIcon()
        else:
            btn_comp = MDCButtonOutlined(_('add'), False, 'add', **kwargs)
            icon = TodoIcon()

        number = obj.number_elected + 1
        txt = _('%(candidates)d candidates, minimum: %(elected)d') % {'candidates': num_candidates, 'elected': number}


        super().__init__(
            _('Add candidates'), txt, icon, btn_comp,
        )


class AddVoterAction(ListAction):
    def __init__(self, obj):
        num_voters = obj.voter_set.all().count()
        num_candidates = obj.candidate_set.all().count()

        kwargs = dict(
            tag='a',
            href=reverse('contest_voters_update', args=[obj.id]))
        if num_voters:
            btn_comp = MDCButtonOutlined(_('edit'), False, **kwargs)
            icon = DoneIcon()
            txt = _('%(num_voters)d voters') % {'num_voters': num_voters}
        else:
            btn_comp = MDCButtonOutlined(_('add'), False, 'add', **kwargs)
            icon = TodoIcon()
            txt = ''

        super().__init__(
            _('Add voters'),
            txt, icon, btn_comp,
            separator=True
        )


class DownloadBtnMixin:
    async def get_file(event):
        event.preventDefault()
        elem = event.currentTarget
        file_response = await fetch(elem.href).then(
            lambda res: res.blob()
        )
        url = URL.createObjectURL(file_response)
        link = document.createElement('a')
        link.download = elem.dataset.filename
        link.href = url
        link.click()
        URL.revokeObjectURL(url)
        setTimeout(
            lambda: document.location.reload()
        , 2000)

    def py2js(self):
        elem = getElementByUuid(self.id)
        elem.onclick = self.get_file


class DownloadBtnOutlined(DownloadBtnMixin, MDCButtonOutlined):
    pass


class DownloadBtn(DownloadBtnMixin, MDCTextButton):
    pass


class SecureElectionInner(Span):
    def __init__(self, obj, user):
        text = _('All guardians must possess a private key so that the ballot box is secure and the election can be opened for voting.')
        todo_list = Ol()

        #todo_list.addchild(Li('Add guardians', cls='line'))
        guardian = obj.guardian_set.filter(user=user).first()
        if guardian:
            cls = 'line' if guardian.downloaded else 'bold'
            todo_list.addchild(Li(_('Download my private key'), cls=cls))

            cls = ''
            if guardian.downloaded and not guardian.verified:
                cls = 'bold'
            elif guardian.verified:
                cls = 'line'
            todo_list.addchild(Li(_('Confirm possession of an uncompromised private key'), cls=cls))

        if user == obj.mediator:
            n_confirmed = obj.guardian_set.exclude(verified=None).count()
            n_guardians = obj.guardian_set.count()
            cls = ''
            if guardian and guardian.verified:
                cls = 'bold'
            if n_guardians == n_confirmed:
                cls = 'line'
            todo_list.addchild(
                Li(
                    _('All guardians confirm possession of uncompromised private keys'),
                    Br(),
                    _('%(confirmed)d/%(gardiens)d confirmed') % {'confirmed': n_confirmed, 'gardiens': n_guardians},
                    cls=cls))

            cls = ''
            if n_confirmed == n_guardians and not obj.joint_public_key:
                cls = 'bold'
            elif obj.joint_public_key:
                cls = 'line'
            todo_list.addchild(Li(_('Lock the ballot box / erase private keys from server memory'), cls=cls))

            cls = ''
            if guardian.contest.joint_public_key:
                cls = 'bold'
            todo_list.addchild(Li(_('Open the election for voting'), cls=cls))

        subtext = _('Guardians must NOT loose their PRIVATE keys and they must keep them SECRET.')

        action_btn = None
        if not guardian.downloaded:
            action_btn = DownloadBtnOutlined(
                _('download private key'),
                p=False,
                icon='file_download',
                data_filename=f'guardian-{guardian.id}.pkl',
                tag='a',
                href=reverse('guardian_download', args=[guardian.id]))
        elif not guardian.verified:
            action_btn = MDCButtonOutlined(
                _('confirm key integrity'),
                p=False,
                tag='a',
                href=reverse('guardian_verify', args=[guardian.id]))
        elif user == obj.mediator:
            if n_guardians == n_confirmed and not obj.joint_public_key:
                action_btn = MDCButtonOutlined(
                    _('Lock the ballot box'),
                    p=False,
                    tag='a',
                    href=reverse('contest_pubkey', args=[guardian.contest.id]))
            elif obj.joint_public_key and not obj.actual_start:
                action_btn = MDCButton(
                    _('Open for voting'),
                    tag='a',
                    href=reverse('contest_open', args=[guardian.contest.id]))

        super().__init__(
            text,
            P(todo_list),
            subtext,
            action_btn,
            cls='body-2'
        )


class SecureElectionAction(ListAction):
    def __init__(self, obj, user):
        title = _('Secure the election')

        if obj.mediator == user:
            if obj.joint_public_key:
                title = _('Ballot box securely locked. Election can be open for voting.')
                icon = DoneIcon()
            else:
                icon = TodoIcon()

        elif guardian := obj.guardian_set.filter(user=user).first():
            if guardian.verified:
                icon = DoneIcon()
            else:
                icon = TodoIcon()

        super().__init__(
            title,
            SecureElectionInner(obj, user),
            icon,
            None,
            separator=False
        )


class CastVoteAction(ListAction):
    def __init__(self, obj, user):
        voter = obj.voter_set.filter(user=user).first()
        if voter.casted:
            s = voter.casted
            txt = (
                _('You casted your vote on %(time)s'
                  ' The results will be published after the election is closed.')
                % {'time': f'<b>{s.strftime("%a %d %b at %H:%M")}</b>.'}
            )
            icon = DoneIcon()
            btn_comp = None
        else:
            txt = ''
            icon = TodoIcon()
            url = reverse('contest_vote', args=(obj.id,))
            btn_comp = MDCButtonOutlined(_('vote'), False, tag='a', href=url)

        super().__init__(
            _('Cast my vote'),
            txt, icon, btn_comp,
            separator=True
        )


class ChooseBlockchainAction(ListAction):
    def __init__(self, obj, user):
        num_voters = obj.voter_set.all().count()
        num_candidates = obj.candidate_set.all().count()
        separator = (
            obj.publish_state != obj.PublishStates.ELECTION_NOT_DECENTRALIZED
            and num_voters
            and num_candidates > obj.votes_allowed
        )
        if obj.publish_state != obj.PublishStates.ELECTION_NOT_DECENTRALIZED:
            txt = ''
            icon = DoneIcon()
        else:
            txt = _('Choose the blockchain you want to deploy your election smart contract to')
            icon = TodoIcon()

        try:
            has_contract = obj.electioncontract is not None
        except Contest.electioncontract.RelatedObjectDoesNotExist:
            has_contract = False

        super().__init__(
            _('Add the election smart contract'),
            txt, icon,
            MDCButtonOutlined(
                _('add'),
                icon='add',
                tag='a',
                p=False,
                href=reverse('electioncontract_create', args=[obj.id])
            ) if not has_contract else None,
            separator=separator
        )


class OnGoingElectionAction(ListAction):
    def __init__(self, contest, user):
        close_url = reverse('contest_close', args=[contest.id])
        close_btn = MDCButtonOutlined(_('close'), False, tag='a', href=close_url)
        start_time = '<b>' + contest.actual_start.strftime('%a %d at %H:%M') + '</b>'
        if contest.actual_end:
            end_time = '<b>' + contest.actual_end.strftime('%a %d at %H:%M') + '</b>'
            title = 'Voting closed'
            txt = _('The voting started on %(start)s and was open till %(end)s.') % {'start': start_time, 'end': end_time}
            icon = SimpleCheckIcon()
        else:
            end_time = '<b>' + contest.end.strftime('%a %d at %H:%M') + '</b>'
            title = _('The voting process is currently ongoing')
            txt = _('The voting started on %(time_start)s and will be closed at %(time_end)s.') % {'time_start': start_time, 'time_end': end_time}
            icon = OnGoingIcon()
        txt += ' Timezone: ' + str(contest.timezone)

        inner = Span(
            txt,
            cls='body-2 red-button-container'
        )

        if contest.mediator == user and not contest.actual_end:
            inner.addchild(close_btn)

        separator = (
            contest.actual_end
            or contest.mediator == user
            or contest.guardian_set.filter(user=user).count()
        )

        super().__init__(
            title,
            inner,
            icon,
            None,
            separator=separator
        )


class UploadPrivateKeyAction(ListAction):
    def __init__(self, contest, user):

        guardian = contest.guardian_set.filter(user=user).first()
        title = _('Upload my private key')
        icon = TodoIcon()
        content = Div(
            _('All guardians need to upload their private keys so that'
            ' the ballot box can be opened to reveal the results.'))
        if contest.actual_end and not guardian.uploaded:
            action_url_ = reverse('guardian_upload', args=[guardian.id])
            action_btn_ = MDCButtonOutlined(
                _('upload my private key'),
                False,
                tag='a',
                href=action_url_)
            content.addchild(action_btn_)
        elif guardian.uploaded:
            icon = DoneIcon()

        super().__init__(
            title,
            content,
            icon,
            None,
            separator=user == contest.mediator
        )


class UnlockBallotAction(ListAction):
    def __init__(self, contest, user):
        self.contest = contest
        self.user = user
        self.has_action = False

        guardian = contest.guardian_set.filter(user=user).first()
        n_guardian = contest.guardian_set.count()
        n_uploaded = contest.guardian_set.exclude(uploaded=None).count()

        if contest.actual_end:
            task_list = Ol()
            txt = _('All guardians upload their keys %(uploaded)d/%(guardian)d uploaded') % {'uploaded': n_uploaded, 'guardian': n_guardian}
            cls='bold'
            if n_uploaded == n_guardian:
                cls = 'line'

            task_list.addchild(Li(txt, cls=cls))

            cls = 'bold' if cls == 'line' else ''
            txt = _('Unlock the ballot box with encrypted ballots and reveal the results')
            task_list.addchild(Li(txt, cls=cls))

            content = Span(
                P(
                    _('All guardians need to upload their private keys so that the ballot box can be opened to reveal the results.')
                ),
                task_list,
                cls='body-2'
            )
        else:
            content = Span(
                P(_('When the election is over the guardians use their keys to open the ballot box and count the results.')),
                cls='body-2'
            )

        title = _('Unlocking the ballot box and revealing the results')
        if (contest.actual_end
            and not self.has_action
            and n_guardian == n_uploaded
        ):
            action_url_ = reverse('contest_decrypt', args=(contest.id,))
            action_btn_ = MDCButton(
                _('reveal results'),
                True,
                tag='a',
                href=action_url_,
                disabled=n_guardian != n_uploaded)
            content.addchild(action_btn_)

        icon = TodoIcon()

        super().__init__(
            title,
            content,
            icon,
            None,
            separator=False,
        )

class WaitForEmailAction(ListAction):
    def __init__(self, contest, user):
        super().__init__(
            _('Once the ballots are counted you will be notified by email'),
            '',
            EmailIcon(), None, separator=False
        )


class ResultAction(ListAction):
    def __init__(self, contest, user):
        subtext = Div()
        if contest.mediator == user:
            subtext.addchild(
                Div(_('Congratulations! You have been the mediator of a secure election.')))

        url=reverse('contest_result', args=[contest.id])
        result_btn = MDCButton(_('view result table'), tag='a', href=url)
        subtext.addchild(result_btn)

        super().__init__(
            _('Results available'),
            subtext,
            DoneIcon(),
            None,
            separator=False
        )


class ContestVotingCard(Div):
    def __init__(self, view, **context):
        contest = view.get_object()
        user = view.request.user
        list_content = []

        actions = []
        if contest.voter_set.filter(user=user).count():
            if not contest.actual_end:
                actions.append('vote')

        if contest.mediator == user:
            actions.append('close')

        guardian = contest.guardian_set.filter(user=user).first()
        if guardian:
            actions.append('upload')

        if 'vote' in actions:
            list_content.append(CastVoteAction(contest, user))

        list_content.append(OnGoingElectionAction(contest, user))

        if 'upload' in actions:
            list_content.append(UploadPrivateKeyAction(contest, user))
            if contest.mediator == user:
                list_content.append(UnlockBallotAction(contest, user))
            elif guardian.uploaded:
                if contest.mediator != user:
                    list_content.append(WaitForEmailAction(contest, user))

        if not len(actions):
            list_content.append(WaitForEmailAction(contest, user))

        super().__init__(
            H4(contest.name),
            Div(
                *contest.about.split('\n'),
                style='padding: 12px;',
                cls='subtitle-2'
            ),
            Ul(
                *list_content,
                cls='mdc-list action-list'
            ),
            cls='setting-section main-setting-section'
        )


class ContestSettingsCard(Div):
    def __init__(self, view, **context):
        contest = view.get_object()
        user = view.request.user
        list_content = []
        if contest.mediator == view.request.user:
            list_content += [
                BasicSettingsAction(contest),
                AddCandidateAction(contest),
                AddVoterAction(contest),
                ChooseBlockchainAction(contest, user),
            ]

            if (
                contest.voter_set.count()
                and contest.candidate_set.count()
                and contest.candidate_set.count() > contest.number_elected
            ):
                if contest.publish_state != contest.PublishStates.ELECTION_NOT_DECENTRALIZED:
                    list_content.append(SecureElectionAction(contest, user))
        else:
            list_content.append(SecureElectionAction(contest, user))

        super().__init__(
            H4(contest.name),
            Div(
                *contest.about.split('\n'),
                style='padding: 12px;',
                cls='subtitle-2'
            ),
            Ul(
                *list_content,
                cls='mdc-list action-list'
            ),
            cls='setting-section main-setting-section'
        )


class Section(Div):
    pass


class TezosSecuredCard(Section):
    def __init__(self, contest, user):
        link = None
        if contest.publish_state != contest.PublishStates.ELECTION_NOT_DECENTRALIZED:
            try:
                contract = contest.electioncontract
                link = A(
                    contract.contract_address,
                    href=contract.explorer_link,
                    style='text-overflow: ellipsis; overflow: hidden; width: 100%;'
                )
            except ObjectDoesNotExist:
                pass  # no contract

        def step(s):
            return Span(
                Span(s, style='width: 100%'),
                link,
                style='display: flex; flex-flow: column wrap'
            )

        super().__init__(
            Ul(
                ListAction(
                    _('Secured and decentralised with Tezos'),
                    Span(
                        str(_('Your election data and results will be published on Tezos’ '))
                            + str(contract.blockchain)
                            + str(_(' blockchain.')),
                        PublishProgressBar([
                            step(_('Election contract created')),
                            step(_('Election opened')),
                            step(_('Election closed')),
                            step(_('Election Results available')),
                            step(_('Election contract updated')),
                        ], contest.publish_state - 1),
                    ) if contest.publish_state else None,
                    TezosIcon(),
                    None,
                    separator=False
                ),
                cls='mdc-list action-list',
            ),
            cls='setting-section', style='background-color: aliceblue;'
        )


class CheckedIcon(MDCIcon):
    def __init__(self):
        super().__init__('check_circle', cls='material-icons icon green2')


class GuardianActionButton(CList):
    def __init__(self, guardian, action):
        url = reverse(f'guardian_{action}', args=[guardian.id])
        if action == 'download':
            btn = DownloadBtn(
                _('Download'),
                'file_download',
                tag='a',
                href=url,
                data_filename=f'guardian-{guardian.id}.pkl')

        elif action == 'verify':
            btn = MDCTextButton(_('Upload'), 'file_upload', tag='a', href=url)

        super().__init__(btn)


class GuardianTable(Div):
    def __init__(self, view, **context):
        table_head_row = Tr(cls='mdc-data-table__header-row')
        for th in (_('email'), _('key downloaded'), _('key verified')):
            table_head_row.addchild(
                Th(
                    th,
                    role='columnheader',
                    scope='col',
                    cls='mdc-data-table__header-cell overline',
                    style='width: 50%' if th == 'email' else 'text-align: center;'
                )
            )

        table_content = Tbody(cls='mdc-data-table__content')
        contest = view.get_object()
        cls = 'mdc-data-table__cell'
        for guardian in contest.guardian_set.all():
            if guardian.user == view.request.user:
                if not guardian.downloaded:
                    dl_elem = GuardianActionButton(guardian, 'download')
                    ul_elem = '--'
                else:
                    if not guardian.verified:
                        dl_elem = GuardianActionButton(guardian, 'download')
                        ul_elem = GuardianActionButton(guardian, 'verify')
                    else:
                        dl_elem = CheckedIcon()
                        ul_elem = CheckedIcon()
                table_content.addchild(Tr(
                    Td(guardian.user.email, cls=cls),
                    Td(
                        dl_elem,
                        cls=cls + ' center'),
                    Td(
                        ul_elem,
                        cls=cls + ' center'),
                    cls='mdc-data-table__row'
                ))
            else:
                table_content.addchild(Tr(
                    Td(guardian.user.email, cls=cls),
                    Td(
                        CheckedIcon() if guardian.downloaded else 'No',
                        cls=cls + ' center'),
                    Td(
                        CheckedIcon() if guardian.verified else 'No',
                        cls=cls + ' center'),
                    cls='mdc-data-table__row'
                ))

        table = Table(
            Thead(table_head_row),
            table_content,
            **{
                'class': 'mdc-data-table__table',
                'aria-label': 'Guardians'
            }
        )
        super().__init__(table, cls='table-container guardian-table')


class GuardiansSettingsCard(Div):
    def __init__(self, view, **context):
        contest = view.get_object()
        super().__init__(
            H5(_('Guardians')),
            GuardianTable(view, **context),
            cls='setting-section'
        )


class CandidatesSettingsCard(Div):
    def __init__(self, view, **context):
        contest = view.get_object()
        editable = (view.request.user == contest.mediator
                    and not contest.actual_start)
        kwargs = dict(p=False, tag='a')
        if contest.candidate_set.count():
            if editable:
                kwargs['href'] = reverse('contest_candidate_create', args=[contest.id])
                btn = MDCButtonOutlined(_('view all/edit'), **kwargs)
            else:
                kwargs['href'] = reverse('contest_candidate_list', args=[contest.id])
                btn = MDCButtonOutlined(_('view all'), **kwargs)
        else:
            if editable:
                kwargs['href'] = reverse('contest_candidate_create', args=[contest.id])
                btn = MDCButtonOutlined(_('add'), icon='add', **kwargs)
            else:
                btn = None

        super().__init__(
            H5(_('Candidates')),
            CandidateListComp(contest, editable),
            btn,
            cls='setting-section'
        )


class VotersSettingsCard(Div):
    def __init__(self, view, **context):
        contest = view.get_object()
        num_emails = contest.voter_set.all().count()

        kwargs = dict(
            p=False,
            tag='a',
            href=reverse('contest_voters_detail', args=[contest.id]))
        if contest.actual_start:
            btn = MDCButtonOutlined(_('view all'), **kwargs)
        elif num_emails:
            btn = MDCButtonOutlined(_('view all/edit'), **kwargs)
        else:
            kwargs['href'] = reverse('contest_voters_update', args=[contest.id])
            btn = MDCButtonOutlined(_('add'), icon='add', **kwargs)

        super().__init__(
            H5(_('Voters')),
            Span(num_emails, _(' voters added'), cls='voters_count'),
            btn,
            cls='setting-section'
        )


class ContestFinishedCard(Div):
    def __init__(self, view, **context):
        super().__init__(
            H4(view.get_object().name),
            Ul(
                ResultAction(view.get_object(), view.request.user),
                cls='mdc-list action-list'
            ),
            cls='setting-section main-setting-section'
        )


@template('djelectionguard/contest_detail.html', Document)
class ContestCard(Div):
    def to_html(self, *content, view, **context):
        contest = view.get_object()
        if contest.plaintext_tally:
            main_section = ContestFinishedCard(view, **context)
        elif contest.actual_start:
            main_section = ContestVotingCard(view, **context)
        else:
            main_section = ContestSettingsCard(view, **context)

        action_section = Div(
            main_section,
            TezosSecuredCard(contest, view.request.user),
            cls='main-container')
        sub_section = Div(
            CandidatesSettingsCard(view, **context),
            cls='side-container')

        if (
            contest.mediator == view.request.user
            or contest.guardian_set.filter(user=view.request.user).count()
        ):
            action_section.addchild(GuardiansSettingsCard(view, **context))

        if contest.mediator == view.request.user:
            sub_section.addchild(VotersSettingsCard(view, **context))


        return super().to_html(
            Div(
                Div(
                    BackLink(_('my elections'), reverse('contest_list')),
                    cls='main-container'),
                Div(cls='side-container'),
                action_section,
                sub_section,
                cls='flex-container'
            )
        )


class CandidateDetail(Div):
    def __init__(self, candidate, editable=False, **kwargs):
        if editable:
            kwargs['tag'] = 'a'
            kwargs['href'] = reverse('contest_candidate_update', args=[candidate.id])
            kwargs['style'] = 'margin-left: auto; margin-top: 12px;'

        extra_style = 'align-items: baseline;'
        content = []

        if candidate.picture:
            extra_style = ''
            content.append(
                Div(
                    Image(
                        loading='eager',
                        src=candidate.picture.url,
                        style='width: 100%;'
                              'display: block;'
                    ),
                    style='width: 150px; padding: 12px;'
                )
            )

        subcontent = Div(
            H5(
                candidate.name,
                style='margin-top: 6px; margin-bottom: 6px;'
            ),
            style='flex: 1 1 65%; padding: 12px;'
        )

        if candidate.description:
            subcontent.addchild(
                Div(
                    *candidate.description.split('\n'),
                    style='margin-top: 24px;'
                )
            )

        content.append(subcontent)

        if editable and not candidate.description:
            content.append(
                MDCButtonOutlined('Edit', False, 'edit', **kwargs)
            )
        elif editable:
            subcontent.addchild(
                MDCButtonOutlined('Edit', False, 'edit', **kwargs)
            )

        super().__init__(
            *content,
            style='padding: 12px;'
                  'display: flex;'
                  'flex-flow: row wrap;'
                  'justify-content: center;'
                  + extra_style,
            cls='candidate-detail',
            **kwargs
        )


class CandidateAccordionItem(MDCAccordionSection):
    tag = 'candidate-list-item'

    def __init__(self, candidate, editable=False):
        super().__init__(
            CandidateDetail(candidate, editable),
            label=candidate.name,
            icon='add'
        )


class CandidateAccordion(MDCAccordion):
    tag = 'candidate-accordion'
    def __init__(self, contest, editable=False):
        super().__init__(
            *(
                CandidateAccordionItem(candidate, editable)
                for candidate
                in contest.candidate_set.all()
            ) if contest.candidate_set.count()
            else [_('No candidate yet.')]
        )


class CandidateListComp(MDCList):
    tag = 'candidate-list'
    def __init__(self, contest, editable=False):
        qs = contest.candidate_set.all()[:]
        def candidates(qs):
            for candidate in qs:
                attrs = dict()
                if editable:
                    attrs['tag'] = 'a'
                    attrs['href'] = reverse(
                        'contest_candidate_update',
                        args=[candidate.id]
                    )
                yield (candidate, attrs)

        super().__init__(
            *(
                MDCListItem(candidate, **attrs)
                for candidate, attrs in candidates(qs)
            ) if qs.count()
            else [_('No candidate yet.')]
        )


class VoterList(Ul):
    def __init__(self, contest):
        emails = contest.voters_emails.split('\n')
        num_emails = len(emails)
        if emails[0] == '':
            num_emails = 0
        super().__init__(
            *(
                MDCListItem(voter)
                for voter
                in emails
            ) if num_emails
            else _('No voter yet.'),
            cls='mdc-list voters-list'
        )


class ClipboardCopy(MDCTextButton):
    def onclick(target):
        target.previousElementSibling.select()
        document.execCommand('copy')


@template('djelectionguard/candidate_list.html', Document, Card)
class CandidateList(Div):
    def to_html(self, *content, view, **context):
        contest = view.get_object()
        self.backlink = BackLink('back', reverse('contest_detail', args=[contest.id]))

        return super().to_html(
            H4(_('Candidates'), cls='center-text'),
            CandidateAccordion(
                contest,
                view.request.user == contest.mediator and not contest.actual_start
            )
        )


@template('djelectionguard/contest_voters_detail.html', Document)
class VotersDetailCard(Div):
    style = dict(cls='card')

    def to_html(self, *content, view, **context):
        contest = view.object
        self.backlink = BackLink(_('back'), reverse('contest_detail', args=[contest.id]))
        voters = contest.voter_set.select_related('user')
        table_head_row = Tr(cls='mdc-data-table__header-row')
        for th in ('email', 'vote email sent', 'voted', 'tally email sent'):
            table_head_row.addchild(
                Th(
                    th,
                    role='columnheader',
                    scope='col',
                    cls='mdc-data-table__header-cell overline',
                    style='' if th == 'email' else 'text-align: center;'
                )
            )
        table_head_row.addchild(Th('OTP'))

        table_content = Tbody(cls='mdc-data-table__content')
        cls = 'mdc-data-table__cell'
        for voter in voters:
            otp_link = None
            if not voter.casted:
                redirect = reverse('contest_vote', args=[contest.pk])
            else:
                redirect = reverse('contest_detail', args=[contest.pk])

            token = voter.user.token_set.filter(
                redirect=redirect,
                used=None,
                expiry__gt=timezone.now(),
            ).first()

            if token:
                otp_link = CList(
                    Input(
                        value=token.url,
                        style='opacity: 0; position: absolute',
                    ),
                    ClipboardCopy(_('Copy link'), icon='content_copy'),
                )
            else:
                otp_link = MDCTextButton(
                    'Request OTP',
                    href=''.join([
                        reverse('otp_send'),
                        '?email=',
                        voter.user.email,
                        '&redirect=',
                        redirect,
                        '&next=',
                        view.request.path_info,
                    ]),
                    tag='a',
                    icon='shield',
                )
            activated = voter.user and voter.user.is_active

            open_email_sent = (
                voter.open_email_sent.strftime("%d/%m/%Y %H:%M")
                if voter.open_email_sent else ''
            )
            close_email_sent = (
                voter.close_email_sent.strftime("%d/%m/%Y %H:%M")
                if voter.close_email_sent else ''
            )

            table_content.addchild(Tr(
                Td(voter.user.email, cls=cls),
                Td(
                    open_email_sent,
                    cls=cls + ' center',
                ),
                Td(CheckedIcon() if voter.casted else 'No', cls=cls + ' center'),
                Td(
                    close_email_sent,
                    cls=cls + ' center',
                ),
                Td(
                    otp_link,
                    cls=cls + ' center',
                ),
                cls='mdc-data-table__row',
                style='opacity: 0.5;' if not activated else ''
            ))

        table = Table(
            Thead(table_head_row),
            table_content,
            **{
                'class': 'mdc-data-table__table',
                'aria-label': 'Voters'
            }
        )
        edit_btn = MDCButtonOutlined(
            _('edit voters'),
            False,
            'edit',
            tag='a',
            href=reverse('contest_voters_update', args=[contest.id]))

        email_btn = MDCButtonOutlined(
            _('invite new voters'),
            False,
            'email',
            tag='a',
            href=reverse('email_voters', args=[contest.id]))

        if contest.actual_end:
            edit_btn = ''
            email_btn = ''

        if not voters.filter(open_email_sent=None).count():
            email_btn = ''

        return super().to_html(
            H4(voters.count(), _(' Voters'), cls='center-text'),
            Div(edit_btn, email_btn, cls='center-button'),
            Div(
                table,
                cls='table-container'),
        )


class ContestCandidateForm(Div):
    def __init__(self, form):
        self.form = form
        self.count = 0
        if form.instance and form.instance.description:
            self.count = len(form.instance.description)
        super().__init__(form)

    def init_counter(form_id, count):
        form = getElementByUuid(form_id)
        counter = form.querySelector('.mdc-text-field-character-counter')
        counter.innerHTML = count + '/255'

    def update_counter(event):
        field = event.currentTarget
        current_count = field.value.length
        parent = field.parentElement.parentElement.parentElement
        counter = parent.querySelector('.mdc-text-field-character-counter')
        counter.innerHTML = current_count + '/255'

    def py2js(self):
        self.init_counter(self.id, self.count)
        field = document.getElementById('id_description')
        field.addEventListener('keyup', self.update_counter)


@template('djelectionguard/candidate_form.html', Document, Card)
class ContestCandidateCreateCard(Div):
    def to_html(self, *content, view, form, **context):
        contest = view.get_object()
        editable = (view.request.user == contest.mediator
                    and not contest.actual_start)
        self.backlink = BackLink(_('back'), reverse('contest_detail', args=[contest.id]))
        form_component = ''
        if editable:
            form_component = Form(
                ContestCandidateForm(form),
                CSRFInput(view.request),
                MDCButton(_('Add candidate'), icon='person_add_alt_1'),
                method='POST',
                cls='form')
        return super().to_html(
            H4(
                contest.candidate_set.count(),
                _(' Candidates'),
                cls='center-text'
            ),
            CandidateAccordion(contest, editable),
            H5(_('Add a candidate'), cls='center-text'),
            form_component,
            cls='card'
        )



@template('djelectionguard/candidate_update.html', Document, Card)
class ContestCandidateUpdateCard(Div):
    def to_html(self, *content, view, form, **context):
        candidate = view.get_object()
        contest = candidate.contest
        self.backlink = BackLink(
            _('back'),
            reverse('contest_candidate_create', args=[contest.id]))
        delete_btn = MDCTextButton(
            'delete',
            'delete',
            tag='a',
            href=reverse('contest_candidate_delete', args=[candidate.id]))

        return super().to_html(
            H4(
                _('Edit candidate'),
                style='text-align: center;'
            ),
            Form(
                CSRFInput(view.request),
                ContestCandidateForm(form),
                Div(
                    Div(delete_btn, cls='red-button-container'),
                    MDCButton('Save', True),
                    style='display: flex; justify-content: space-between'),
                method='POST',
                cls='form'),
            cls='card'
        )


@template('djelectionguard/voters_update.html', Document, Card)
class ContestVotersUpdateCard(Div):
    def to_html(self, *content, view, form, **context):
        contest = view.get_object()
        self.backlink = BackLink(
            _('back'),
            reverse('contest_detail', args=[contest.id]))
        voters = contest.voter_set.all()

        return super().to_html(
            H4(voters.count(), _(' Voters'), style='text-align: center;'),
            Div(_('The list of allowed voters with one email per line (sparated by Enter/Return ⏎)'), cls='body-2', style='margin-bottom: 24px;text-align: center;'),
            Form(
                CSRFInput(view.request),
                form,
                MDCButton(_('Save')),
                method='POST',
                cls='form'
            ),
            cls='card'
        )


@template('djelectionguard/guardian_form.html', Document, Card)
class GuardianVerifyCard(Div):
    def to_html(self, *content, view, form, **context):
        guardian = view.get_object()
        contest = guardian.contest
        self.backlink = BackLink(
            _('back'),
            reverse('contest_detail', args=[contest.id]))

        self.submit_btn = MDCButton(_('confirm'), True, disabled=True)
        self.submit_btn_id = self.submit_btn.id

        return super().to_html(
            H4(_('Confirm possession of an uncompromised private key'), cls='center-text'),
            Div(_('You need to upload your private key to confirm that you posses a valid key that hasn’t been temepered with.'), cls='center-text'),
            Form(
                MDCFileField(
                    Input(id='file_input', type='file', name='pkl_file'),
                    label=_('Choose file')),
                Span(_("Your privacy key is a file with '.pkl' extension. "), cls='body-2'),
                self.submit_btn,
                CSRFInput(view.request),
                enctype='multipart/form-data',
                method='POST',
                cls='form',
            ),
            cls='card'
        )

    def enable_post(event):
        file_input = document.querySelector('#file_input')
        file_name = file_input.value
        btn = getElementByUuid(file_input.submit_btn_id)
        btn.disabled = file_name == ''

    def py2js(self):
        file_input = document.querySelector('#file_input')
        file_input.submit_btn_id = self.submit_btn_id
        file_input.addEventListener('change', self.enable_post)


@template('djelectionguard/contest_pubkey.html', Document, Card)
class ContestPubKeyCard(Div):
    def to_html(self, *content, view, form, **context):
        contest = view.get_object()
        self.backlink = BackLink(
            _('back'),
            reverse('contest_detail', args=[contest.id]))
        return super().to_html(
            H4(_('Lock the ballot box'), cls='center-text'),
            Div(
                P(_('This will remove all guardians’ private keys from the server memory.')),
                P(_('When the voting is over the ballot box can only be opened when all guardians upload their private keys.')),
                P(_('This is what makes the governing of the election decentralised.'))
            ),
            Form(
                CSRFInput(view.request),
                MDCButton(_('create')),
                method='POST',
                cls='form'
            ),
            cls='card'
        )

@template('email_voters', Document, Card)
class ContestOpenCard(Div):
    def to_html(self, *content, view, **context):
        contest = view.get_object()
        self.backlink = BackLink(
            _('back'),
            reverse('contest_voters_detail', args=[contest.id]))

        return super().to_html(
            H4(_('Send an invite to the newly added voters'), cls='center-text'),
            Form(
                context['form'],
                CSRFInput(view.request),
                MDCButton(context['form'].submit_label),
                method='POST',
                cls='form'
            ),
            cls='card'
        )

@template('contest_open', Document, Card)
class ContestOpenCard(Div):
    def to_html(self, *content, view, **context):
        contest = view.get_object()
        self.backlink = BackLink(
            _('back'),
            reverse('contest_detail', args=[contest.id]))

        return super().to_html(
            H4(_('Open the election for voting'), cls='center-text'),
            Div(
                P(_('Once you open the election for voting you can’t make changes to it.')),
                cls='center-text'
            ),
            Form(
                context['form'],
                CSRFInput(view.request),
                MDCButton(_('open')),
                method='POST',
                cls='form'
            ),
            cls='card'
        )


class DialogConfirmForm(Form):
    def __init__(self, *content, selections=[], **attrs):
        def hidden_selections():
            for s in selections:
                candidate = CandidateDetail(s)
                candidate.style.display = 'none'
                candidate.attrs['data-candidate-id'] = s.id
                yield candidate

        super().__init__(
            *content,
            MDCDialog(
                _('Confirm your selection'),
                Div(*hidden_selections()),
            ),
            **attrs
        )

    def ondialogclosed(event):
        candidates = event.currentTarget.querySelectorAll('[data-candidate-id]')
        for candidate in candidates:
            candidate.style.display = 'none'

    def ondialogclosing(event):
        if event.detail.action == 'accept':
            form.submit()

    def handle_submit(event):
        event.preventDefault()
        this.dialog = this.querySelector('mdc-dialog')
        selections = new.FormData(this).getAll('selections')
        for selection in selections:
            candidate = this.dialog.querySelector(
                '[data-candidate-id="' + selection + '"]'
            )
            candidate.style.display = 'flex'
        this.dialog.onclosing = self.ondialogclosing
        this.dialog.onclosed = self.ondialogclosed
        this.dialog.open()

    def py2js(self):
        form = getElementByUuid(self.id)
        form.addEventListener('submit', self.handle_submit.bind(form))


@template('contest_vote', Document, Card)
class ContestVoteCard(Div):
    def to_html(self, *content, view, form, **context):
        contest = view.get_object()
        self.backlink = BackLink(
            _('back'),
            reverse('contest_detail', args=[contest.id]))

        max_selections = contest.votes_allowed
        number_elected = contest.number_elected

        candidates = contest.candidate_set.all()
        choices = (
            (i, CandidateDetail(candidate), candidate.id)
             for i, candidate
             in enumerate(candidates))

        return super().to_html(
            H4(_('Make your choice'), cls='center-text'),
            Div(
                P(_('In the end of the election the results will be announced by email')),
                cls='center-text body-2'
            ),
            Ul(
                *[Li(e) for e in form.non_field_errors()],
                cls='error-list'
            ),
            DialogConfirmForm(
                CSRFInput(view.request),
                MDCMultipleChoicesCheckbox(
                    'selections',
                    choices,
                    n=max_selections),
                MDCButton(_('create ballot')),
                selections=candidates,
                method='POST',
                cls='form vote-form',
            ),
            cls='card'
        )

@template('vote_track', Document, Card)
class ContestVoteCard(Div):
    def to_html(self, *content, view, **context):
        voter = view.get_object()
        self.backlink = BackLink(
            _('back'),
            reverse('contest_detail', args=[voter.contest.id]))

        return super().to_html(
            H4(
                _('Tracking informations'),
                style='text-align:center;'
            ),
            I('Tracking hash:', cls='overline'),
            Pre(
                voter.tracking_hash,
                style='text-align:center;'
                      'word-break: break-word;'
                      'white-space: break-spaces;'
            ),
            I('Previous tracking hash:', cls='overline'),
            Pre(
                voter.previous_tracking_hash,
                style='text-align:center;'
                      'word-break: break-word;'
                      'white-space: break-spaces;'
            ),
        )

@template('ballot_encrypt', Document, Card)
class ContestBallotEncryptCard(Div):
    def to_html(self, *content, view, form, **context):
        contest = view.get_object()
        url = reverse('contest_vote', args=[contest.id])
        self.backlink = BackLink(_('back'), url)
        selections = context.get('selections', [])
        ballot = context.get('ballot', '')
        change_btn = MDCButtonOutlined(_('change'), False, tag='a', href=url)
        encrypt_btn = MDCButton(_('encrypt ballot'))

        return super().to_html(
            H4(_('Review your ballot'), cls='center-text'),
            Div(
                P(_('This is an ecrypted election. Once your ballot is encrypted, it will always stay that way – no one can see who voted for whom. However, you will be able to check that your vote has been properly counted.  Learn how')),
                cls='center-text'),
            H6(_('Your selection')),
            Ul(*(
                CandidateDetail(candidate)
                for candidate in selections),
                cls='mdc-list'),
            change_btn,
            Form(
                CSRFInput(view.request),
                encrypt_btn,
                method='POST',
                cls='form'),
            cls='card',
        )


@template('ballot_cast', Document, Card)
class ContestBallotCastCard(Div):
    def to_html(self, *content, view, **context):
        self.contest = view.get_object()
        self.backlink = BackLink(
            _('back'),
            reverse('contest_ballot', args=[self.contest.id]))

        self.ballot = context['ballot']
        self.download_btn = MDCButtonOutlined(
            _('download ballot file'), False, 'file_download', tag='a')
        cast_btn = MDCButton(_('confirm my vote'))

        return super().to_html(
            H4(_('Encrypted ballot'), cls='center-text'),
            Div(
                P(_('This is an ecrypted election. Once your ballot is encrypted, it will always stay that way – no one can see who voted for whom. However, you will be able to check that your vote has been properly counted. Learn more')),
                cls='center-text body-2'),
            Form(
                Div(
                    MDCTextareaFieldOutlined(
                        Textarea(
                            self.ballot.to_json(),
                            rows=5,
                            name='encrypted',
                        ),
                    ),
                    style='margin-bottom: 24px;'
                ),
                CSRFInput(view.request),
                Div(
                    #self.download_btn,
                    Div(cast_btn, style='margin-left: auto;'),
                    style='display: flex;'
                          'justify-content: space-between;'
                          'flex-wrap: wrap;'),
                method='POST',
                cls='encrypt-form'
            ),
            cls='card',
        )
        self.download_btn_id = self.download_btn.id
        self.ballot_json = self.ballot.to_json().replace('"', '\\"')
        self.file_name = self.contest.name + '_encrypted_ballot.json'

    def download_file(event):
        elem = event.currentTarget
        blob = new.Blob([elem.ballot], {'type': 'application/json'})
        url = URL.createObjectURL(blob)
        link = document.createElement('a')
        link.href = url
        link.download = elem.file_name
        link.click()
        URL.revokeObjectURL(url)

    def py2js(self):
        btn = getElementByUuid(self.download_btn_id)
        btn.ballot = self.ballot_json
        btn.file_name = self.file_name
        btn.addEventListener('click', self.download_file)


@template('contest_close', Document, Card)
class ContestCloseCard(Div):
    def to_html(self, *content, view, **context):
        contest = view.get_object()
        self.backlink = BackLink(
            _('back'),
            reverse('contest_detail', args=[contest.id]))

        return super().to_html(
            H4(_('Manual closing of the election'), cls='center-text'),
            Div(
                P(_('This will stop the voting process and it can\'t be undone.')),
                cls='center-text body-2'),
            Form(
                CSRFInput(view.request),
                Div(
                    MDCButtonOutlined(_('close the election now'), False),
                    style='margin: 0 auto;',
                    cls='red-button-container'),
                method='POST',
                cls='form'),
            cls='card',
        )


@template('guardian_upload', Document, Card)
class GuardianUploadKeyCard(Div):
    def to_html(self, *content, view, form, **context):
        guardian = view.get_object()
        contest = guardian.contest
        self.backlink = BackLink(
            _('back'),
            reverse('contest_detail', args=[contest.id]))

        self.submit_btn = MDCButton(_('confirm'), True, disabled=True)
        self.submit_btn_id = self.submit_btn.id

        return super().to_html(
            H4(_('Verify your private key'), cls='center-text'),
            Div(_('All guardians’ must upload their valid private keys to unlock the ballot box.'), cls='center-text'),
            Form(
                MDCFileField(
                    Input(id='file_input', type='file', name='pkl_file'),
                    label=_('Choose file')),
                Span(_("Your privacy key is a file with '.pkl' extension. "), cls='body-2'),
                self.submit_btn,
                CSRFInput(view.request),
                enctype='multipart/form-data',
                method='POST',
                cls='form',
            ),
            cls='card'
        )

    def py2js(self):
        file_input = document.querySelector('#file_input')
        file_input.submit_btn_id = self.submit_btn_id
        file_input.addEventListener('change', self.enable_post)

    def enable_post(event):
        file_input = document.querySelector('#file_input')
        file_name = file_input.value
        btn = getElementByUuid(file_input.submit_btn_id)
        btn.disabled = file_name == ''


@template('contest_decrypt', Document, Card)
class ContestDecryptCard(Div):
    def to_html(self, *content, view, **context):
        contest = view.get_object()
        self.backlink = BackLink(
            _('back'),
            reverse('contest_detail', args=[contest.id]))
        return super().to_html(
            H4(_('Open ballot box'), cls='center-text'),
            Div(
                P(_('This process will erase all guardian keys from server memory.')),
                cls='center-text body-2'),
            Form(
                context['form'],
                CSRFInput(view.request),
                MDCButton(_('open and view results')),
                method='POST',
                cls='form'),
            cls='card',
        )


@template('contest_publish', Document, Card)
class ContestPublishCard(Div):
    def to_html(self, *content, view, form , **ctx):
        return super().to_html(
            H4(_('Publish your election results'), cls='center-text'),
            Div(
                P(_('This will decentralize your election results.')),
                cls='center-text body-2'),
            Form(
                CSRFInput(view.request),
                MDCButton(_('publish results')),
                method='POST',
                cls='form'),
            cls='card',
        )


class PublishProgressBar(Div):
    def __init__(self, _steps, step=0):
        self.nsteps = len(_steps)
        self.step = step
        steps = [
            Span(
                cls=f'progress-step progress-step--disabled',
                **{'data-step': s})
            for s in range(0, self.nsteps)
        ]
        if 0 <= step < self.nsteps:
            steps[step].attrs['class'] += ' progress-step--active'

        super().__init__(
            MDCLinearProgress(),
            Div(
                *steps,
                cls='progress-bar__steps'
            ),
            Span(_steps[step], cls='center-text overline'),
            cls='progress-bar',
            style='margin: 24px auto'
        )

    def set_progress(current_step, total_steps):
        bar_container = document.querySelector('.progress-bar')
        bar = bar_container.querySelector('.mdc-linear-progress')

        mdcbar = new.mdc.linearProgress.MDCLinearProgress(bar)
        bar.MDCLinearProgress = mdcbar

        def step(step):
            progress = step / (total_steps - 1)

            steps = bar_container.querySelectorAll('.progress-step')
            for n in range(total_steps):
                s = steps.item(n)
                if s.dataset.step > step:
                    s.classList.remove('progress-step--active')
                    s.classList.add('progress-step--disabled')
                elif s.dataset.step == step:
                    s.classList.remove('progress-step--disabled')
                    s.classList.add('progress-step--active')
                else:
                    s.classList.remove('progress-step--active')
                    s.classList.remove('progress-step--disabled')

            bar.MDCLinearProgress.foundation.setProgress(progress)

        bar.setStep = step
        bar.setStep(current_step)

    def py2js(self):
        self.set_progress(self.step, self.nsteps)


@template('contest_result', Document, Card)
class ContestResultCard(Div):
    def to_html(self, *content, view, **context):
        contest = view.get_object()
        self.backlink = BackLink(
            _('back'),
            reverse('contest_detail', args=[contest.id]))

        votes = contest.candidate_set.aggregate(total=Sum('score'))

        table_head_row = Tr(cls='mdc-data-table__header-row')
        kwargs = dict(
            role='columnheader',
            scope='col',
            cls='mdc-data-table__header-cell overline'
        )
        table_head_row.addchild(Th('candidate', **kwargs))

        kwargs['style'] = 'text-align: right;'
        table_head_row.addchild(Th('votes', **kwargs))

        table_content = Tbody(cls='mdc-data-table__content')
        cls = 'mdc-data-table__cell'

        for i, candidate in enumerate(contest.candidate_set.order_by('-score')):
            num = f'{i + 1}. '
            if votes['total']:
                score_percent = 100 * candidate.score / votes['total']
                score_percent = f'{score_percent} %'
            else:
                score_percent = '--'

            table_content.addchild(
                Tr(
                    Td(num + candidate.name, cls=cls),
                    Td(
                        Span(f'{candidate.score}', cls='body-2'),
                        Span(f' {score_percent}', cls='text-btn'),
                        style='text-align: right'),
                    cls='mdc-data-table__row'))

        score_table = Table(
            Thead(table_head_row),
            table_content,
            **{
                'class': 'mdc-data-table__table',
                'aria-label': 'Scores'
            }
        )

        publish_btn = ''
        if (
            contest.publish_state == contest.PublishStates.ELECTION_DECRYPTED
            and contest.mediator == view.request.user
        ):
            publish_btn = MDCButton(
                _('publish results'),
                p=True,
                icon=WorldIcon(),
                tag='a',
                href=reverse('contest_publish', args=[contest.id]),
                style='margin: 0 auto;')

        return super().to_html(
            H4(_('Results'), cls='center-text'),
            Div(
                publish_btn,
                score_table,
                A(
                    'Download artifacts',
                    tag='a',
                    href=contest.artifacts_local_url,
                ),
                Div(
                    Br(),
                    Span(
                        'Or download artifacts on IPFS:',
                        cls='body-2',
                    ),
                    Pre(
                        f'> ipfs get {contest.artifacts_ipfs}',
                        style='background-color: lightgray;'
                              'width: fit-content;'
                              'margin: 12px auto;'
                              'padding: 4px;'
                              'max-width: 90%;'
                              'white-space: break-spaces;'
                    ),
                ) if contest.artifacts_ipfs else None,
                cls='table-container score-table center-text'
            ),
            cls='card',
        )


class GuardianDeleteBtn(A):
    def __init__(self, guardian):
        self.guardian = guardian

        super().__init__(
            MDCIcon(
                'delete',
                cls='delete-icon'),
            tag='a',
            href=reverse('contest_guardian_delete', args=[guardian.id]))


@template('guardian_create', Document, Card)
class GuardianCreateCard(Div):
    def to_html(self, *content, view, form, **context):
        contest = view.get_object()
        self.backlink = BackLink(_('back'), reverse('contest_detail', args=[contest.id]))
        table_head_row = Tr(cls='mdc-data-table__header-row')
        for th in ('guardians', ''):
            table_head_row.addchild(
                Th(
                    th,
                    role='columnheader',
                    scope='col',
                    cls='mdc-data-table__header-cell overline',
                )
            )

        table_content = Tbody(cls='mdc-data-table__content')
        cls = 'mdc-data-table__cell'
        for guardian in contest.guardian_set.all():
            activated = guardian.user and guardian.user.is_active
            table_content.addchild(Tr(
                Td(guardian.user.email, cls=cls),
                Td(
                    GuardianDeleteBtn(guardian),
                    cls=cls,
                    style='text-align:right'),
                cls='mdc-data-table__row',
                style='opacity: 0.5;' if not activated else '',
            ))

        table = Table(
            Thead(table_head_row),
            table_content,
            **{
                'class': 'mdc-data-table__table',
                'aria-label': _('Voters')
            }
        )

        return super().to_html(
            H4(_('Add guardians'), cls='center-text'),
            Div(
                _('Guardians are responsible for locking and unlocking of the ballot box with their private keys.'),
                cls='center-text body-1'
            ),
            Div(
                B(_('No guardians for speed and simplicity (default).')),
                _(' Electis App will technically be your guardian and can secure your ballot box.'),
                cls='red-section'),
            Div(
                B(_('GUARDIAN_HELP_TEXT')),
                cls='red-section'),
            Form(
                form['email'],
                CSRFInput(view.request),
                MDCButtonOutlined(_('add guardian'), p=False, icon='person_add'),
                table,
                Div(
                    form['quorum'],
                    Span(
                        MDCButton(_('Save')),
                        style='margin: 32px 12px'),
                    style='display:flex;'
                          'flex-flow: row nowrap;'
                          'justify-content: space-between;'
                          'align-items: baseline;'),
                method='POST',
                cls='form'
            ),
            cls='card'
        )
