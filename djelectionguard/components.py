from datetime import datetime, date
from django import forms
from django.conf import settings
from django.db.models import Sum
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.utils import timezone
from electeez.components import *
from ryzom_django.forms import widget_template
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

    start = forms.SplitDateTimeField(
        label='',
        initial=now,
        widget=forms.SplitDateTimeWidget(
            time_attrs={'type': 'time'},
            date_attrs={'type': 'date'},
        )
    )
    end = forms.SplitDateTimeField(
        label='',
        initial=now,
        widget=forms.SplitDateTimeWidget(
            time_attrs={'type': 'time'},
            date_attrs={'type': 'date'},
        )
    )

    class Meta:
        model = Contest
        fields = [
            'name',
            'votes_allowed',
            'start',
            'end',
            'timezone',
        ]


class ContestFormComponent(CList):
    def __init__(self, view, form, edit=False):
        content = []
        content.append(Ul(
            *[Li(e) for e in form.non_field_errors()],
            cls='error-list'
        ))

        super().__init__(
            H4('Edit election' if edit else 'Create an election'),
            Form(
                form['name'],
                H6('Voting settings:'),
                form['votes_allowed'],
                H6('Election starts:'),
                form['start'],
                H6('Election ends:'),
                form['end'],
                form['timezone'],
                CSRFInput(view.request),
                MDCButton('update election' if edit else 'create election'),
                method='POST',
                cls='form'),
        )


@template('djelectionguard/contest_form.html', Document, Card)
class ContestCreateCard(Div):
    style = dict(cls='card')

    def to_html(self, *content, view, form, **context):
        self.backlink = BackLink('back', reverse('contest_list'))

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

        self.all_contests_btn = ContestFiltersBtn(1, 'all', active_btn == 'all')
        self.my_contests_btn = ContestFiltersBtn(2, 'created by me', active_btn == 'created')
        self.shared_contests_btn = ContestFiltersBtn(3, 'shared with me', active_btn == 'shared')

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
            status = 'voting ongoing'
            active_cls = 'active'
        if contest.plaintext_tally:
            active_cls = ''
            status = 'result available'

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
                Span('Create new election'),
                cls='mdc-list-item__text text-btn mdc-ripple-upgraded'
            ),
            cls='mdc-list-item contest-list-item',
            href=reverse('contest_create')
        )


@template('djelectionguard/contest_list.html', Document, Card)
class ContestList(Div):
    def to_html(self, *content, view, **context):
        return super().to_html(
            H4('Elections', style='text-align: center;'),
            # ContestFilters(view),
            Ul(
                ListItem(ContestListCreateBtn()),
                *(
                    ContestListItem(contest)
                    for contest in context['contest_list']
                ) if len(context['contest_list'])
                else (
                    Li(
                        'There are no elections yet',
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
            'edit',
            False,
            tag='a',
            href=reverse('contest_update', args=[obj.id]))
        super().__init__(
            'Basic settings',
            'Name, votes allowed, time and date, etc.',
            DoneIcon(), btn_comp
        )


class AddCandidateAction(ListAction):
    def __init__(self, obj):
        num_candidates = obj.candidate_set.count()
        kwargs = dict(
            tag='a',
            href=reverse('contest_candidate_create', args=[obj.id]))
        if num_candidates and num_candidates > obj.number_elected:
            btn_comp = MDCButtonOutlined('edit', False, **kwargs)
            icon = DoneIcon()
        else:
            btn_comp = MDCButtonOutlined('add', False, 'add', **kwargs)
            icon = TodoIcon()
        txt = f'{num_candidates} candidates, minimum: {obj.number_elected + 1}'

        super().__init__(
            'Add candidates', txt, icon, btn_comp,
        )


class AddVoterAction(ListAction):
    def __init__(self, obj):
        num_voters = obj.voter_set.all().count()
        num_candidates = obj.candidate_set.all().count()

        kwargs = dict(
            tag='a',
            href=reverse('contest_voters_update', args=[obj.id]))
        if num_voters:
            btn_comp = MDCButtonOutlined('edit', False, **kwargs)
            icon = DoneIcon()
            txt = f'{num_voters} voters'
        else:
            btn_comp = MDCButtonOutlined('add', False, 'add', **kwargs)
            icon = TodoIcon()
            txt = ''

        super().__init__(
            'Add voters',
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
        text = 'All guardians must possess a private key so that the ballot box is secure and the election can be opened for voting.'
        todo_list = Ol()

        #todo_list.addchild(Li('Add guardians', cls='line'))
        guardian = obj.guardian_set.filter(user=user).first()
        if guardian:
            cls = 'line' if guardian.downloaded else 'bold'
            todo_list.addchild(Li('Download my private key', cls=cls))

            cls = ''
            if guardian.downloaded and not guardian.verified:
                cls = 'bold'
            elif guardian.verified:
                cls = 'line'
            todo_list.addchild(Li('Confirm possession of an uncompromised private key', cls=cls))

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
                    'All guardians confirm possession of uncompromised private keys',
                    Br(),
                    f'({n_confirmed}/{n_guardians} confirmed)',
                    cls=cls))

            cls = ''
            if n_confirmed == n_guardians and not obj.joint_public_key:
                cls = 'bold'
            elif obj.joint_public_key:
                cls = 'line'
            todo_list.addchild(Li('Lock the ballot box / erase private keys from server memory', cls=cls))

            cls = ''
            if guardian.contest.joint_public_key:
                cls = 'bold'
            todo_list.addchild(Li('Open the election for voting', cls=cls))

        subtext = 'Guardians must NOT loose their PRIVATE keys and they must keep them SECRET.'

        action_btn = None
        if not guardian.downloaded:
            action_btn = DownloadBtnOutlined(
                'download private key',
                p=False,
                icon='file_download',
                data_filename=f'guardian-{guardian.id}.pkl',
                tag='a',
                href=reverse('guardian_download', args=[guardian.id]))
        elif not guardian.verified:
            action_btn = MDCButtonOutlined(
                'confirm key integrity',
                p=False,
                tag='a',
                href=reverse('guardian_verify', args=[guardian.id]))
        elif user == obj.mediator:
            if n_guardians == n_confirmed and not obj.joint_public_key:
                action_btn = MDCButtonOutlined(
                    'Lock the ballot box',
                    p=False,
                    tag='a',
                    href=reverse('contest_pubkey', args=[guardian.contest.id]))
            elif obj.joint_public_key and not obj.actual_start:
                action_btn = MDCButton(
                    'Open for voting',
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
        title = 'Secure the election'

        if obj.mediator == user:
            if obj.joint_public_key:
                title = 'Ballot box securely locked. Election can be open for voting.'
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
                f'You casted your vote on <b>{s.strftime("%a %d %b at %H:%M")}</b>.' +
                ' The results will be published after the election is closed.'
            )
            icon = DoneIcon()
            btn_comp = None
        else:
            txt = ''
            icon = TodoIcon()
            url = reverse('contest_vote', args=(obj.id,))
            btn_comp = MDCButtonOutlined('vote', False, tag='a', href=url)

        super().__init__(
            'Cast my vote',
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
            txt = 'Choose the blockchain you want to deploy your election to'
            icon = TodoIcon()

        super().__init__(
            'Choose a blockchain',
            txt, icon,
            MDCButtonOutlined(
                'choose blockchain',
                tag='a',
                p=False,
                href=reverse('electioncontract_create', args=[obj.id])
            ),
            separator=separator
        )


class OnGoingElectionAction(ListAction):
    def __init__(self, contest, user):
        close_url = reverse('contest_close', args=[contest.id])
        close_btn = MDCButtonOutlined('close', False, tag='a', href=close_url)
        start_time = '<b>' + contest.actual_start.strftime('%a %d at %H:%M') + '</b>'
        if contest.actual_end:
            end_time = '<b>' + contest.actual_end.strftime('%a %d at %H:%M') + '</b>'
            title = 'Voting closed'
            txt = f'The voting started on {start_time} and was open till {end_time}.'
            icon = SimpleCheckIcon()
        else:
            end_time = '<b>' + contest.end.strftime('%a %d at %H:%M') + '</b>'
            title = 'The voting process is currently ongoing'
            txt = f'The voting started on {start_time} and will be closed at {end_time}.'
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
        title = 'Upload my private key'
        icon = TodoIcon()
        content = Div(
            'All guardians need to upload their private keys so that'
            ' the ballot box can be opened to reveal the results.')
        if contest.actual_end and not guardian.uploaded:
            action_url_ = reverse('guardian_upload', args=[guardian.id])
            action_btn_ = MDCButtonOutlined(
                'upload my private key',
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
            txt = f'All guardians upload their keys ({n_uploaded}/{n_guardian} uploaded)'
            cls='bold'
            if n_uploaded == n_guardian:
                cls = 'line'

            task_list.addchild(Li(txt, cls=cls))

            cls = 'bold' if cls == 'line' else ''
            txt = 'Unlock the ballot box with encrypted ballots and reveal the results'
            task_list.addchild(Li(txt, cls=cls))

            content = Span(
                P(
                    'All guardians need to upload their private keys so that the ballot box can be opened to reveal the results.'
                ),
                task_list,
                cls='body-2'
            )
        else:
            content = Span(
                P('When the election is over the guardians use their keys to open the ballot box and count the results.'),
                cls='body-2'
            )

        title = 'Unlocking the ballot box and revealing the results'
        if (contest.actual_end
            and not self.has_action
            and n_guardian == n_uploaded
        ):
            action_url_ = reverse('contest_decrypt', args=(contest.id,))
            action_btn_ = MDCButton(
                'reveal results',
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
            'Once the ballots are counted you will be notified by email',
            '',
            EmailIcon(), None, separator=False
        )


class ResultAction(ListAction):
    def __init__(self, contest, user):
        subtext = Div()
        if contest.mediator == user:
            subtext.addchild(
                Div('Congratulations! You have been the mediator of a secure election.'))
        if contest.number_elected > 1:
            winners = Ol(cls='winners')
            winner_item = Li
            winner_text = 'the winners are:'
        else:
            winners = Div(cls='winners')
            winner_item = Span
            winner_text = 'the winner is:'

        subtext.addchild(Span(winner_text, cls='winner-caption overline'))

        candidates = contest.candidate_set.order_by('-score')
        candidates = candidates[:contest.number_elected]

        prefix = ''
        for i, candidate in enumerate(candidates):
            if contest.number_elected > 1:
                prefix = f'{i + 1}. '
            winners.addchild(
                winner_item(
                    H6(f'{prefix}{candidate.name}', cls='winner')))

        subtext.addchild(winners)

        url=reverse('contest_result', args=[contest.id])
        result_btn = MDCButton('view result table', tag='a', href=url)
        subtext.addchild(result_btn)

        super().__init__(
            'Results available',
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
        if (
            contest.publish_state == contest.PublishStates.ELECTION_NOT_DECENTRALIZED
            and contest.mediator == user
        ):
            btn = MDCButton(
                'choose blockchain',
                tag='a',
                href=reverse('electioncontract_create', args=[contest.id]))
        else:
            btn = MDCTextButton('Here\'s how', 'info_outline')

        links = []

        if contest.publish_state != contest.PublishStates.ELECTION_NOT_DECENTRALIZED:
            try:
                links.append(contest.electioncontract.contract_address)
            except ObjectDoesNotExist:
                pass  # no contract

        if contest.publish_state == contest.PublishStates.ELECTION_PUBLISHED:
            links.append(A('Download artifacts', href=contest.artifacts_local_url))
            if contest.artifacts_ipfs_url:
                links.append(A('Download from IPFS', href=contest.artifacts_ipfs_url))

        def step(s):
            return Span(Span(s), *links, style='display: flex; flex-flow: column wrap')

        super().__init__(
            Ul(
                ListAction(
                    'Secure and decentralised with Tezos',
                    Span(
                        'Your election data and results will be published on Tezos’ test blockchain.',
                        PublishProgressBar([
                            step('Election contract created'),
                            step('Election opened'),
                            step('Election closed'),
                            step('Election Results available'),
                            step('Election contract updated'),
                        ], contest.publish_state - 1)
                        if contest.publish_state
                        else btn
                    ),
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
                'Download',
                'file_download',
                tag='a',
                href=url,
                data_filename=f'guardian-{guardian.id}.pkl')

        elif action == 'verify':
            btn = MDCTextButton('Upload', 'file_upload', tag='a', href=url)

        super().__init__(btn)


class GuardianTable(Div):
    def __init__(self, view, **context):
        table_head_row = Tr(cls='mdc-data-table__header-row')
        for th in ('email', 'key downloaded', 'key verified'):
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
            H5('Guardians'),
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
                btn = MDCButtonOutlined('view all/edit', **kwargs)
            else:
                kwargs['href'] = reverse('contest_candidate_list', args=[contest.id])
                btn = MDCButtonOutlined('view all', **kwargs)
        else:
            if editable:
                kwargs['href'] = reverse('contest_candidate_create', args=[contest.id])
                btn = MDCButtonOutlined('add', icon='add', **kwargs)
            else:
                btn = None

        super().__init__(
            H5('Candidates'),
            CandidateList(contest, editable),
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
            btn = MDCButtonOutlined('view all', **kwargs)
        elif num_emails:
            btn = MDCButtonOutlined('view all/edit', **kwargs)
        else:
            kwargs['href'] = reverse('contest_voters_update', args=[contest.id])
            btn = MDCButtonOutlined('add', icon='add', **kwargs)

        super().__init__(
            H5('Voters'),
            Span(num_emails, ' voters added', cls='voters_count'),
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
                    BackLink('my elections', reverse('contest_list')),
                    cls='main-container'),
                Div(cls='side-container'),
                action_section,
                sub_section,
                cls='flex-container'
            )
        )



class CandidateAccordionItem(MDCAccordionSection):
    tag = 'candidate-list-item'

    def __init__(self, contest, candidate, editable=False):
        kwargs = dict()
        if editable:
            kwargs['tag'] = 'a'
            kwargs['href'] = reverse('contest_candidate_update', args=[candidate.id])
            kwargs['style'] = 'margin-left: auto; margin-top: 12px;'

        super().__init__(
            Div(
                Div(
                    Image(
                        loading='eager',
                        src=candidate.picture.url,
                        style='max-height: 300px;'
                            'max-width: 100%;'
                            'display: block;'
                            'margin: 0 auto;'
                    ) if candidate.picture else None,
                ),
                Div(
                    H4(candidate.name),
                    Div(candidate.description.replace('\n', '<br>')),
                    MDCButtonOutlined( 'Edit', False, 'edit', **kwargs),
                ),
                style='margin-bottom: 32px; padding: 12px'
            ),
            label=candidate.name,
            icon='add'
        )


class CandidateAccordion(MDCAccordion):
    tag = 'candidate-accordion'
    def __init__(self, contest, editable=False):
        super().__init__(
            *(
                CandidateAccordionItem(contest, candidate, editable)
                for candidate
                in contest.candidate_set.all()
            ) if contest.candidate_set.count()
            else ['No candidate yet.']
        )


class CandidateList(MDCList):
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
            else ['No candidate yet.']
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
            else 'No voter yet.',
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
            H4('Candidates', cls='center-text'),
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
        self.backlink = BackLink('back', reverse('contest_detail', args=[contest.id]))
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
                    ClipboardCopy('Copy link', icon='content_copy'),
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
        self.edit_btn = MDCButtonOutlined(
            'edit voters',
            False,
            'edit',
            tag='a',
            href=reverse('contest_voters_update', args=[contest.id]))

        if contest.actual_start:
            self.edit_btn = ''

        return super().to_html(
            H4(voters.count(), ' Voters', cls='center-text'),
            Div(self.edit_btn, cls='center-button'),
            Div(
                table,
                cls='table-container'),
        )


@template('djelectionguard/candidate_form.html', Document, Card)
class ContestCandidateCreateCard(Div):
    def to_html(self, *content, view, form, **context):
        contest = view.get_object()
        editable = (view.request.user == contest.mediator
                    and not contest.actual_start)
        self.backlink = BackLink('back', reverse('contest_detail', args=[contest.id]))
        form_component = ''
        if editable:
            form_component = Form(
                form,
                CSRFInput(view.request),
                MDCButton('Add candidate', icon='person_add_alt_1'),
                method='POST',
                cls='form')
        return super().to_html(
            H4(
                contest.candidate_set.count(),
                ' Candidates',
                cls='center-text'
            ),
            CandidateAccordion(contest, editable),
            H5('Add a candidate', cls='center-text'),
            form_component,
            cls='card'
        )


@template('djelectionguard/candidate_update.html', Document, Card)
class ContestCandidateUpdateCard(Div):
    def to_html(self, *content, view, form, **context):
        candidate = view.get_object()
        contest = candidate.contest
        self.backlink = BackLink(
            'back',
            reverse('contest_candidate_create', args=[contest.id]))
        delete_btn = MDCTextButton(
            'delete',
            'delete',
            tag='a',
            href=reverse('contest_candidate_delete', args=[candidate.id]))

        return super().to_html(
            H4(
                'Edit candidate',
                style='text-align: center;'
            ),
            Form(
                CSRFInput(view.request),
                form,
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
            'back',
            reverse('contest_detail', args=[contest.id]))
        voters = contest.voter_set.all()

        return super().to_html(
            H4(voters.count(), ' Voters', style='text-align: center;'),
            Div('The list of allowed voters with one email per line (sparated by Enter/Return ⏎)', cls='body-2', style='margin-bottom: 24px;text-align: center;'),
            Form(
                CSRFInput(view.request),
                form,
                MDCButton('Save'),
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
            'back',
            reverse('contest_detail', args=[contest.id]))

        self.submit_btn = MDCButton('confirm', True, disabled=True)
        self.submit_btn_id = self.submit_btn.id

        return super().to_html(
            H4('Confirm possession of an uncompromised private key', cls='center-text'),
            Div('You need to upload your private key to confirm that you posses a valid key that hasn’t been temepered with.', cls='center-text'),
            Form(
                MDCFileField(
                    Input(id='file_input', type='file', name='pkl_file'),
                    label='Choose file'),
                Span("Your privacy key is a file with '.pkl' extension. ", cls='body-2'),
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
            'back',
            reverse('contest_detail', args=[contest.id]))
        return super().to_html(
            H4('Lock the ballot box', cls='center-text'),
            Div(
                P('This will remove all guardians’ private keys from the server memory.'),
                P('When the voting is over the ballot box can only be opened when all guardians upload their private keys.'),
                P('This is what makes the governing of the election decentralised.')
            ),
            Form(
                CSRFInput(view.request),
                MDCButton('create'),
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
            'back',
            reverse('contest_detail', args=[contest.id]))

        return super().to_html(
            H4('Open the election for voting', cls='center-text'),
            Div(
                P('Once you open the election for voting you can’t make changes to it.'),
                cls='center-text'
            ),
            Form(
                context['form'],
                CSRFInput(view.request),
                MDCButton('open'),
                method='POST',
                cls='form'
            ),
            cls='card'
        )


@template('contest_vote', Document, Card)
class ContestVoteCard(Div):
    def to_html(self, *content, view, form, **context):
        contest = view.get_object()
        self.backlink = BackLink(
            'back',
            reverse('contest_detail', args=[contest.id]))

        max_selections = contest.votes_allowed
        number_elected = contest.number_elected

        candidates = contest.candidate_set.all()
        choices = (
            (i, candidate.name, candidate.id)
             for i, candidate
             in enumerate(candidates))

        return super().to_html(
            H4('Make your choice', cls='center-text'),
            Div(
                P(f'You may choose up to {max_selections} ' +
                        'candidates. In the end of the election ' +
                        f'{number_elected} winner will be announced.'),
                cls='center-text body-2'
            ),
            Ul(
                *[Li(e) for e in form.non_field_errors()],
                cls='error-list'
            ),
            Form(
                CSRFInput(view.request),
                MDCMultipleChoicesCheckbox(
                    'selections',
                    choices,
                    n=max_selections),
                MDCButton('create ballot'),
                method='POST',
                cls='form',
            ),
            cls='card'
        )


@template('ballot_encrypt', Document, Card)
class ContestBallotEncryptCard(Div):
    def to_html(self, *content, view, form, **context):
        contest = view.get_object()
        url = reverse('contest_vote', args=[contest.id])
        self.backlink = BackLink('back', url)
        selections = context.get('selections', [])
        ballot = context.get('ballot', '')
        change_btn = MDCButtonOutlined('change', False, tag='a', href=url)
        encrypt_btn = MDCButton('encrypt ballot')

        return super().to_html(
            H4('Review your ballot', cls='center-text'),
            Div(
                P('This is an ecrypted election. Once your ballot is encrypted, it will always stay that way – no one can see who voted for whom. However, you will be able to check that your vote has been properly counted.  Learn how'),
                cls='center-text'),
            H6('Your selection'),
            Ul(*(
                MDCListItem(candidate.name)
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
            'back',
            reverse('contest_ballot', args=[self.contest.id]))

        self.ballot = context['ballot']
        self.download_btn = MDCButtonOutlined(
            'download ballot file', False, 'file_download', tag='a')
        cast_btn = MDCButton('confirm my vote')

        return super().to_html(
            H4('Encrypted ballot', cls='center-text'),
            Div(
                P('This is an ecrypted election. Once your ballot is encrypted, it will always stay that way – no one can see who voted for whom. However, you will be able to check that your vote has been properly counted. Learn more'),
                cls='center-text body-2'),
            Form(
                Div(
                    MDCTextareaFieldOutlined(
                        Textarea(
                            self.ballot.to_json(),
                            rows=15,
                            name='encrypted',
                        ),
                    ),
                    style='margin-bottom: 24px;'
                ),
                CSRFInput(view.request),
                Div(
                    self.download_btn,
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
            'back',
            reverse('contest_detail', args=[contest.id]))

        return super().to_html(
            H4('Manual closing of the election', cls='center-text'),
            Div(
                P('This will stop the voting process and it can\'t be undone.'),
                cls='center-text body-2'),
            Form(
                CSRFInput(view.request),
                Div(
                    MDCButtonOutlined('close the election now', False),
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
            'back',
            reverse('contest_detail', args=[contest.id]))

        self.submit_btn = MDCButton('confirm', True, disabled=True)
        self.submit_btn_id = self.submit_btn.id

        return super().to_html(
            H4('Verify your private key', cls='center-text'),
            Div('All guardians’ must upload their valid private keys to unlock the ballot box.', cls='center-text'),
            Form(
                MDCFileField(
                    Input(id='file_input', type='file', name='pkl_file'),
                    label='Choose file'),
                Span("Your privacy key is a file with '.pkl' extension. ", cls='body-2'),
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
            'back',
            reverse('contest_detail', args=[contest.id]))
        return super().to_html(
            H4('Open ballot box', cls='center-text'),
            Div(
                P('This process will erase all guardian keys from server memory.'),
                cls='center-text body-2'),
            Form(
                context['form'],
                CSRFInput(view.request),
                MDCButton('open and view results'),
                method='POST',
                cls='form'),
            cls='card',
        )


@template('contest_publish', Document, Card)
class ContestPublishCard(Div):
    def to_html(self, *content, view, form , **ctx):
        return super().to_html(
            H4('Publish your election results', cls='center-text'),
            Div(
                P('This will decentralize your election results.'),
                cls='center-text body-2'),
            Form(
                CSRFInput(view.request),
                MDCButton('publish results'),
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
            'back',
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
                'publish results',
                p=True,
                icon=WorldIcon(),
                tag='a',
                href=reverse('contest_publish', args=[contest.id]),
                style='margin: 0 auto;')

        return super().to_html(
            H4('Results', cls='center-text'),
            Div(
                publish_btn,
                score_table,
                cls='table-container score-table'),
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
        self.backlink = BackLink('back', reverse('contest_detail', args=[contest.id]))
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
                'aria-label': 'Voters'
            }
        )

        return super().to_html(
            H4('Add guardians', cls='center-text'),
            Div(
                'Guardians are responsible for locking and unlocking of the ballot box with their private keys.',
                cls='center-text body-1'
            ),
            Div(
                B('No guardians for speed and simplicity (default).'),
                ' Electis App will technically be your guardian and can secure your ballot box.',
                cls='red-section'),
            Div(
                B('With guardians for greater security (recommended).'),
                ' You can distribute control over the closing/opening of the',
                ' ballot box between multiple guardians. All of their keys will',
                ' be necessary to conduct an election – from opening for voting',
                ' to revealing the results.',
                cls='red-section'),
            Form(
                form['email'],
                CSRFInput(view.request),
                MDCButtonOutlined('add guardian', p=False, icon='person_add'),
                table,
                Div(
                    form['quorum'],
                    Span(
                        MDCButton('Save'),
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
