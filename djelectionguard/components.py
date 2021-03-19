from datetime import datetime, date
from django import forms
from django.db.models import Sum
from django.urls import reverse
from ryzom import html
from py2js import Mixin as Py2jsMixin
from py2js.renderer import JS, autoexec
from ryzom_mdc import *
from ryzom_django_mdc.components import *
from ryzom_django.forms import widget_template
from electeez.components import (
    Document,
    Card,
    BackLink,
    MDCLinearProgress
)
from .models import Contest, Candidate

from ryzom_django_mdc.components import SplitDateTimeWidget


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
            'number_elected',
            'votes_allowed',
            'start',
            'end',
            'decentralized'
        ]

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data['votes_allowed'] < cleaned_data['number_elected']:
            raise forms.ValidationError(
                'Number of elected cannot be bellow number of votes allowed'
            )
        return cleaned_data


class ContestEditForm(ContestForm):
    class Meta(ContestForm.Meta):
        fields = [
            'name',
            'number_elected',
            'votes_allowed',
            'start',
            'end',
        ]

    def clean(self):
        cleaned_data = super().clean()
        if 'decentralized' in cleaned_data:
            raise forms.ValidationError(
                'Cannot decentralize after creation'
            )
        return cleaned_data


class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = ['name']

    def clean(self):
        cleaned_data = super().clean()

        exists = Candidate.objects.filter(
            contest=self.contest,
            name=cleaned_data['name']
        ).exclude(id=self.instance.id).count()

        if exists:
            raise forms.ValidationError(
                dict(name='Candidate name must be unique for a contest')
            )
        return cleaned_data


class ContestFormComponent(CList):
    def __init__(self, view, form, edit=False):
        content = []
        content.append(html.Ul(
            *[html.Li(e) for e in form.non_field_errors()],
            cls='error-list'
        ))

        decentralized = ''
        if not edit:
            decentralized = CList(
                html.H6('Decentralize my election:'),
                MDCMultipleChoicesCheckbox(
                    'decentralized',
                    [(0, 'Decentralize with Tezos', 'true')]))

        super().__init__(
            html.H4('Edit election' if edit else 'Create an election'),
            html.Form(
                form['name'],
                html.H6('Voting settings:'),
                form['number_elected'],
                form['votes_allowed'],
                html.H6('Election starts:'),
                form['start'],
                html.H6('Election ends:'),
                form['end'],
                decentralized,
                CSRFInput(view.request),
                MDCButton('update election' if edit else 'create election'),
                method='POST',
                cls='form'),
        )


@template('djelectionguard/contest_form.html', Document, Card)
class ContestCreateCard(html.Div):
    def __init__(self, *content, view, form, **context):
        self.backlink = BackLink('back', reverse('contest_list'))

        edit = isinstance(form, ContestEditForm)
        super().__init__(
            ContestFormComponent(view, form, edit),
            cls='card',
        )


class ContestFiltersBtn(html.Button):
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
            html.Span(
                html.Span(text, cls='mdc-tab__text-label'),
                cls='mdc-tab__content'
            ),
            html.Span(
                html.Span(cls='mdc-tab-indicator__content ' +
                              'mdc-tab-indicator__content--underline'
                ),
                cls=f'mdc-tab-indicator {active_indicator}'
            ),
            html.Span(cls='mdc-tab__ripple'),
            **attrs
        )


class ContestFilters(html.Div):
    def __init__(self, view):
        active_btn = view.request.GET.get('q', 'all')

        self.all_contests_btn = ContestFiltersBtn(1, 'all', active_btn == 'all')
        self.my_contests_btn = ContestFiltersBtn(2, 'created by me', active_btn == 'created')
        self.shared_contests_btn = ContestFiltersBtn(3, 'shared with me', active_btn == 'shared')

        super().__init__(
            html.Div(
                html.Div(
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


class ContestItem(html.A):
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
            html.Span(cls='mdc-list-item__ripple'),
            html.Span(
                html.Span(cls=f'contest-indicator'),
                html.Span(
                    html.Span(status, cls='contest-status overline'),
                    html.Span(contest.name, cls='contest-name'),
                    cls='list-item__text-container'
                ),
                cls='mdc-list-item__text'
            ),
            cls=f'contest-list-item mdc-list-item mdc-ripple-upgraded {active_cls}',
            href=reverse('contest_detail', args=[contest.id])
        )


class Separator(html.Li):
    def __init__(self, inset=False):
        cls = 'mdc-list-divider'
        if inset:
            cls += ' mdc-list-divider--inset'
        super().__init__(role='separator', cls=cls)


class ListItem(html.CList):
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
        subitem = html.Span(cls=subitem_cls)

        if icon_comp:
            subitem.addchild(icon_comp)
        subitem.addchild(html.H6(title))
        if btn_comp:
            subitem.addchild(btn_comp)

        item = html.Span(subitem, cls='mdc-list-item__text list-action-column')
        if txt:
            item.addchild(html.Span(txt, cls='mdc-list-item__secondary-text ' +
                                             'list-action-text body-2'))

        super().__init__(html.Li(item, cls='mdc-list-item list-action-item'), **kwargs)


class ContestListCreateBtn(html.A):
    def __init__(self):
        super().__init__(
            html.Span(
                html.Span(cls='mdc-list-item__ripple'),
                html.Span(
                    html.Span('+', cls='new-contest-icon'),
                    cls='new-contest-icon-container'
                ),
                html.Span('Create new election'),
                cls='mdc-list-item__text text-btn mdc-ripple-upgraded'
            ),
            cls='mdc-list-item contest-list-item',
            href=reverse('contest_create')
        )


@template('djelectionguard/contest_list.html', Document, Card)
class ContestList(html.Div):
    def __init__(self, *content, view, **context):
        super().__init__(
            html.H4('Elections', style='text-align: center;'),
            # ContestFilters(view),
            html.Ul(
                ListItem(ContestListCreateBtn()),
                *(
                    ContestListItem(contest)
                    for contest in context['contest_list']
                ) if view.get_queryset().count()
                else (
                    html.Li(
                        'There are no elections yet',
                        cls='mdc-list-item body-1'
                    ),
                ),
                cls='mdc-list contest-list'
            ),
            cls='card'
        )


class CircleIcon(html.Span):
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
        )


class DownloadBtnMixin(Py2jsMixin):
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


class SecureElectionInner(html.Span):
    def __init__(self, obj, user):
        text = 'All guardians must possess a private key so that the ballot box is secure and the election can be opened for voting.'
        todo_list = html.Ol()

        #todo_list.addchild(html.Li('Add guardians', cls='line'))
        guardian = obj.guardian_set.filter(user=user).first()
        if guardian:
            cls = 'line' if guardian.downloaded else 'bold'
            todo_list.addchild(html.Li('Download my private key', cls=cls))

            cls = ''
            if guardian.downloaded and not guardian.verified:
                cls = 'bold'
            elif guardian.verified:
                cls = 'line'
            todo_list.addchild(html.Li('Confirm possession of an uncompromised private key', cls=cls))

        if user == obj.mediator:
            n_confirmed = obj.guardian_set.exclude(verified=None).count()
            n_guardians = obj.guardian_set.count()
            cls = ''
            if guardian and guardian.verified:
                cls = 'bold'
            if n_guardians == n_confirmed:
                cls = 'line'
            todo_list.addchild(
                html.Li(
                    'All guardians confirm possession of uncompromised private keys',
                    html.Br(),
                    f'({n_confirmed}/{n_guardians} confirmed)',
                    cls=cls))

            cls = ''
            if n_confirmed == n_guardians and not obj.joint_public_key:
                cls = 'bold'
            elif obj.joint_public_key:
                cls = 'line'
            todo_list.addchild(html.Li('Lock the ballot box / erase private keys from server memory', cls=cls))

            cls = ''
            if guardian.contest.joint_public_key:
                cls = 'bold'
            todo_list.addchild(html.Li('Open the election for voting', cls=cls))

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
            html.P(todo_list),
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
        if obj.publish_status:
            txt = ''
            icon = DoneIcon()
        else:
            txt = 'Choose the blockchain you want to deploy your election to'
            icon = TodoIcon()

        super().__init__(
            'Choose a blockchain',
            txt, icon, None,
            separator=obj.publish_status > 0
        )


class OnGoingElectionAction(ListAction):
    def __init__(self, contest, user):
        contest = contest
        user = user
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
            txt = f'The voting started on {start_time} and will close automatically on {end_time}.'
            icon = OnGoingIcon()

        inner = html.Span(
            txt,
            cls='body-2 red-button-container'
        )

        if contest.mediator == user and not contest.actual_end:
            inner.addchild(close_btn)

        super().__init__(
            title,
            inner,
            icon,
            None,
            separator=True
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
            task_list = html.Ol()
            txt = f'All guardians upload their keys ({n_uploaded}/{n_guardian} uploaded)'
            cls='bold'
            if n_uploaded == n_guardian:
                cls = 'line'

            task_list.addchild(html.Li(txt, cls=cls))

            cls = 'bold' if cls == 'line' else ''
            txt = 'Unlock the ballot box with encrypted ballots and reveal the results'
            task_list.addchild(html.Li(txt, cls=cls))

            content = html.Span(
                html.P(
                    'All guardians need to upload their private keys so that the ballot box can be opened to reveal the results.'
                ),
                task_list,
                cls='body-2'
            )
        else:
            content = html.Span(
                html.P('When the election is over the guardians use their keys to open the ballot box and count the results.'),
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
        subtext = html.Div()
        if contest.mediator == user:
            subtext.addchild(
                html.Div('Congratulations! You have been the mediator of a secure election.'))
        if contest.number_elected > 1:
            winners = html.Ol(cls='winners')
            winner_item = html.Li
            winner_text = 'the winners are:'
        else:
            winners = html.Div(cls='winners')
            winner_item = html.Span
            winner_text = 'the winner is:'

        subtext.addchild(html.Span(winner_text, cls='winner-caption overline'))

        candidates = contest.candidate_set.order_by('-score')
        candidates = candidates[:contest.number_elected]

        prefix = ''
        for i, candidate in enumerate(candidates):
            if contest.number_elected > 1:
                prefix = f'{i + 1}. '
            winners.addchild(
                winner_item(
                    html.H6(f'{prefix}{candidate.name}', cls='winner')))

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


class ContestVotingCard(html.Div):
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
            html.H4(contest.name),
            html.Ul(
                *list_content,
                cls='mdc-list action-list'
            ),
            cls='setting-section main-setting-section'
        )


class ContestSettingsCard(html.Div):
    def __init__(self, view, **context):
        contest = view.get_object()
        user = view.request.user
        list_content = []
        if contest.mediator == view.request.user:
            list_content += [
                BasicSettingsAction(contest),
                AddCandidateAction(contest),
                AddVoterAction(contest),
            ]
            if contest.decentralized:
                list_content.append(ChooseBlockchainAction(contest, user)),

            if (
                contest.voter_set.count()
                and contest.candidate_set.count()
                and contest.candidate_set.count() > contest.number_elected
            ):
                if contest.decentralized:
                    if contest.publish_status:
                        list_content.append(SecureElectionAction(contest, user))
                else:
                    list_content.append(SecureElectionAction(contest, user))
        else:
            list_content.append(SecureElectionAction(contest, user))

        super().__init__(
            html.H4(contest.name),
            html.Ul(
                *list_content,
                cls='mdc-list action-list'
            ),
            cls='setting-section main-setting-section'
        )


class Section(html.Div):
    pass


class TezosSecuredCard(Section):
    def __init__(self, contest, user):
        if (
            contest.decentralized
            and contest.publish_status == 0
            and contest.mediator == user
        ):
            btn = MDCButton(
                'choose blockchain',
                tag='a',
                href=reverse('electioncontract_create', args=[contest.id]))
        else:
            btn = MDCTextButton('Here\'s how', 'info_outline')

        super().__init__(
            html.Ul(
                ListAction(
                    'Secure and decentralised with Tezos',
                    html.Span(
                        'Your election data and results will be published on Tezos’ test blockchain.',
                        PublishProgressBar([
                            'Election contract created',
                            'Election opened',
                            'Election closed',
                            'Election Results available',
                            'Election contract updated'
                        ], contest.publish_status - 1)
                        if contest.decentralized and contest.publish_status
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
        super().__init__('check_circle', cls='icon green2')


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


class GuardianTable(html.Div):
    def __init__(self, view, **context):
        table_head_row = html.Tr(cls='mdc-data-table__header-row')
        for th in ('email', 'key downloaded', 'key verified'):
            table_head_row.addchild(
                html.Th(
                    th,
                    role='columnheader',
                    scope='col',
                    cls='mdc-data-table__header-cell overline',
                    style='width: 50%' if th == 'email' else 'text-align: center;'
                )
            )

        table_content = html.Tbody(cls='mdc-data-table__content')
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
                table_content.addchild(html.Tr(
                    html.Td(guardian.user.email, cls=cls),
                    html.Td(
                        dl_elem,
                        cls=cls + ' center'),
                    html.Td(
                        ul_elem,
                        cls=cls + ' center'),
                    cls='mdc-data-table__row'
                ))
            else:
                table_content.addchild(html.Tr(
                    html.Td(guardian.user.email, cls=cls),
                    html.Td(
                        CheckedIcon() if guardian.downloaded else 'No',
                        cls=cls + ' center'),
                    html.Td(
                        CheckedIcon() if guardian.verified else 'No',
                        cls=cls + ' center'),
                    cls='mdc-data-table__row'
                ))

        table = html.Table(
            html.Thead(table_head_row),
            table_content,
            **{
                'class': 'mdc-data-table__table',
                'aria-label': 'Guardians'
            }
        )
        super().__init__(table, cls='table-container guardian-table')


class GuardiansSettingsCard(html.Div):
    def __init__(self, view, **context):
        contest = view.get_object()
        super().__init__(
            html.H5('Guardians'),
            GuardianTable(view, **context),
            cls='setting-section'
        )


class CandidatesSettingsCard(html.Div):
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
            html.H5('Candidates'),
            CandidateList(contest, editable),
            btn,
            cls='setting-section'
        )


class VotersSettingsCard(html.Div):
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
            html.H5('Voters'),
            html.Span(num_emails, ' voters added', cls='voters_count'),
            btn,
            cls='setting-section'
        )


class ContestFinishedCard(html.Div):
    def __init__(self, view, **context):
        super().__init__(
            html.H4(view.get_object().name),
            html.Ul(
                ResultAction(view.get_object(), view.request.user),
                cls='mdc-list action-list'
            ),
            cls='setting-section main-setting-section'
        )


@template('djelectionguard/contest_detail.html', Document)
class ContestCard(html.Div):
    def __init__(self, *content, view, **context):
        contest = view.get_object()
        if contest.plaintext_tally:
            main_section = ContestFinishedCard(view, **context)
        elif contest.actual_start:
            main_section = ContestVotingCard(view, **context)
        else:
            main_section = ContestSettingsCard(view, **context)

        action_section = html.Div(
            main_section,
            TezosSecuredCard(contest, view.request.user),
            cls='main-container')
        sub_section = html.Div(
            CandidatesSettingsCard(view, **context),
            cls='side-container')

        if (
            contest.mediator == view.request.user
            or contest.guardian_set.filter(user=view.request.user).count()
        ):
            action_section.addchild(GuardiansSettingsCard(view, **context))

        if contest.mediator == view.request.user:
            sub_section.addchild(VotersSettingsCard(view, **context))


        super().__init__(
            html.Div(
                html.Div(
                    BackLink('my elections', reverse('contest_list')),
                    cls='main-container'),
                html.Div(cls='side-container'),
                action_section,
                sub_section,
                cls='flex-container'
            )
        )


class CandidateListItem(MDCListItem):
    def __init__(self, contest, candidate, editable=False):
        kwargs = dict()
        if editable:
            kwargs['tag'] = 'a'
            kwargs['href'] = reverse('contest_candidate_update', args=[candidate.id])

        super().__init__(
            candidate.name,
            addcls='candidate-list-item',
            **kwargs
        )


class CandidateList(html.Ul):
    def __init__(self, contest, editable=False):
        super().__init__(
            *(
                CandidateListItem(contest, candidate, editable)
                for candidate
                in contest.candidate_set.all()
            ) if contest.candidate_set.count()
            else 'No candidate yet.',
            cls='mdc-list candidate-list'
        )


class VoterList(html.Ul):
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


@template('djelectionguard/contest_voters_detail.html', Document, Card)
class VotersDetailCard(html.Div):
    def __init__(self, *content, view, **context):
        contest = view.get_object()
        self.backlink = BackLink('back', reverse('contest_detail', args=[contest.id]))
        voters = contest.voter_set.all()
        table_head_row = html.Tr(cls='mdc-data-table__header-row')
        for th in ('email', 'vote email sent', 'voted', 'tally email sent'):
            table_head_row.addchild(
                html.Th(
                    th,
                    role='columnheader',
                    scope='col',
                    cls='mdc-data-table__header-cell overline',
                    style='width: 50%' if th == 'email' else 'text-align: center;'
                )
            )

        table_content = html.Tbody(cls='mdc-data-table__content')
        cls = 'mdc-data-table__cell'
        for voter in voters:
            activated = voter.user and voter.user.is_active
            table_content.addchild(html.Tr(
                html.Td(voter.user.email, cls=cls),
                html.Td(
                    voter.open_email_sent or '',
                    cls=cls + ' center',
                ),
                html.Td(CheckedIcon() if voter.casted else 'No', cls=cls + ' center'),
                html.Td(
                    voter.close_email_sent or '',
                    cls=cls + ' center',
                ),
                cls='mdc-data-table__row',
                style='opacity: 0.5;' if not activated else ''
            ))

        table = html.Table(
            html.Thead(table_head_row),
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

        super().__init__(
            html.H4(voters.count(), ' Voters', cls='center-text'),
            html.Div(self.edit_btn, cls='center-button'),
            table,
            cls='card'
        )


@template('djelectionguard/candidate_list.html', Document, Card)
class ContestCandidateCreateCard(html.Div):
    def __init__(self, *content, view, **context):
        contest = view.get_object()
        self.backlink = BackLink('back', reverse('contest_detail', args=[contest.id]))
        super().__init__(
            html.H4(
                contest.candidate_set.count(), ' Candidates',
                style='text-align: center;'),
            CandidateList(contest),
            cls='card'
        )


@template('djelectionguard/candidate_form.html', Document, Card)
class ContestCandidateCreateCard(html.Div):
    def __init__(self, *content, view, form, **context):
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
        super().__init__(
            html.H4(
                contest.candidate_set.count(), ' Candidates',
                style='text-align: center;'),
            form_component,
            CandidateList(contest, editable),
            cls='card'
        )


@template('djelectionguard/candidate_update.html', Document, Card)
class ContestCandidateUpdateCard(html.Div):
    def __init__(self, *content, view, form, **context):
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

        super().__init__(
            html.H4(
                'Edit candidate',
                style='text-align: center;'
            ),
            html.Form(
                CSRFInput(view.request),
                form,
                html.Div(
                    html.Div(delete_btn, cls='red-button-container'),
                    MDCButton('Save', True),
                    style='display: flex; justify-content: space-between'),
                method='POST',
                cls='form'),
            cls='card'
        )


@template('djelectionguard/voters_update.html', Document, Card)
class ContestVotersUpdateCard(html.Div):
    def __init__(self, *content, view, form, **context):
        contest = view.get_object()
        self.backlink = BackLink(
            'back',
            reverse('contest_detail', args=[contest.id]))
        voters = contest.voter_set.all()

        super().__init__(
            html.H4(voters.count(), ' Voters', style='text-align: center;'),
            html.Div('The list of allowed voters with one email per line (sparated by Enter/Return ⏎)', cls='body-2', style='margin-bottom: 24px;text-align: center;'),
            html.Form(
                CSRFInput(view.request),
                form,
                MDCButton('Save'),
                method='POST',
                cls='form'
            ),
            cls='card'
        )


@template('djelectionguard/guardian_form.html', Document, Card)
class GuardianVerifyCard(Py2jsMixin, html.Div):
    def __init__(self, *content, view, form, **context):
        guardian = view.get_object()
        contest = guardian.contest
        self.backlink = BackLink(
            'back',
            reverse('contest_detail', args=[contest.id]))

        self.submit_btn = MDCButton('confirm', True, disabled=True)
        self.submit_btn_id = self.submit_btn.id

        super().__init__(
            html.H4('Confirm possession of an uncompromised private key', cls='center-text'),
            html.Div('You need to upload your private key to confirm that you posses a valid key that hasn’t been temepered with.', cls='center-text'),
            html.Form(
                MDCFileField(
                    Input(id='file_input', type='file', name='pkl_file'),
                    label='Choose file'),
                html.Span("Your privacy key is a file with '.pkl' extension. ", cls='body-2'),
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
class ContestPubKeyCard(html.Div):
    def __init__(self, *content, view, form, **context):
        contest = view.get_object()
        self.backlink = BackLink(
            'back',
            reverse('contest_detail', args=[contest.id]))
        super().__init__(
            html.H4('Lock the ballot box', cls='center-text'),
            html.Div(
                html.P('This will remove all guardians’ private keys from the server memory.'),
                html.P('When the voting is over the ballot box can only be opened when all guardians upload their private keys.'),
                html.P('This is what makes the governing of the election decentralised.')
            ),
            html.Form(
                CSRFInput(view.request),
                MDCButton('create'),
                method='POST',
                cls='form'
            ),
            cls='card'
        )


@template('contest_open', Document, Card)
class ContestOpenCard(html.Div):
    def __init__(self, *content, view, **context):
        contest = view.get_object()
        self.backlink = BackLink(
            'back',
            reverse('contest_detail', args=[contest.id]))

        super().__init__(
            html.H4('Open the election for voting', cls='center-text'),
            html.Div(
                html.P('Once you open the election for voting you can’t make changes to it.'),
                cls='center-text'
            ),
            html.Form(
                context['form'],
                CSRFInput(view.request),
                MDCButton('open'),
                method='POST',
                cls='form'
            ),
            cls='card'
        )


@template('contest_vote', Document, Card)
class ContestVoteCard(html.Div):
    def __init__(self, *content, view, form, **context):
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

        super().__init__(
            html.H4('Make your choice', cls='center-text'),
            html.Div(
                html.P(f'You may choose up to {max_selections} ' +
                        'candidates. In the end of the election ' +
                        f'{number_elected} winner will be announced.'),
                cls='center-text body-2'
            ),
            html.Ul(
                *[html.Li(e) for e in form.non_field_errors()],
                cls='error-list'
            ),
            html.Form(
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
class ContestBallotEncryptCard(html.Div):
    def __init__(self, *content, view, form, **context):
        contest = view.get_object()
        url = reverse('contest_vote', args=[contest.id])
        self.backlink = BackLink('back', url)
        selections = context.get('selections', [])
        ballot = context.get('ballot', '')
        change_btn = MDCButtonOutlined('change', False, tag='a', href=url)
        encrypt_btn = MDCButton('encrypt ballot')

        super().__init__(
            html.H4('Review your ballot', cls='center-text'),
            html.Div(
                html.P('This is an ecrypted election. Once your ballot is encrypted, it will always stay that way – no one can see who voted for whom. However, you will be able to check that your vote has been properly counted.  Learn how'),
                cls='center-text'),
            html.H6('Your selection'),
            html.Ul(*(
                MDCListItem(candidate.name)
                for candidate in selections),
                cls='mdc-list'),
            change_btn,
            html.Form(
                CSRFInput(view.request),
                encrypt_btn,
                method='POST',
                cls='form'),
            cls='card',
        )


@template('ballot_cast', Document, Card)
class ContestBallotCastCard(Py2jsMixin, html.Div):
    def __init__(self, *content, view, **context):
        self.contest = view.get_object()
        self.backlink = BackLink(
            'back',
            reverse('contest_ballot', args=[self.contest.id]))

        self.ballot = context['ballot']
        self.download_btn = MDCButtonOutlined(
            'download ballot file', False, 'file_download', tag='a')
        cast_btn = MDCButton('confirm my vote')

        super().__init__(
            html.H4('Encrypted ballot', cls='center-text'),
            html.Div(
                html.P('This is an ecrypted election. Once your ballot is encrypted, it will always stay that way – no one can see who voted for whom. However, you will be able to check that your vote has been properly counted. Learn more'),
                cls='center-text body-2'),
            html.Form(
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
class ContestCloseCard(html.Div):
    def __init__(self, *content, view, **context):
        contest = view.get_object()
        self.backlink = BackLink(
            'back',
            reverse('contest_detail', args=[contest.id]))

        super().__init__(
            html.H4('Manual closing of the election', cls='center-text'),
            html.Div(
                html.P('This will stop the voting process and it can\'t be undone.'),
                cls='center-text body-2'),
            html.Form(
                CSRFInput(view.request),
                html.Div(
                    MDCButtonOutlined('close the election now', False),
                    style='margin: 0 auto;',
                    cls='red-button-container'),
                method='POST',
                cls='form'),
            cls='card',
        )


@template('guardian_upload', Document, Card)
class GuardianUploadKeyCard(Py2jsMixin, html.Div):
    def __init__(self, *content, view, form, **context):
        guardian = view.get_object()
        contest = guardian.contest
        self.backlink = BackLink(
            'back',
            reverse('contest_detail', args=[contest.id]))

        self.submit_btn = MDCButton('confirm', True, disabled=True)
        self.submit_btn_id = self.submit_btn.id

        super().__init__(
            html.H4('Verify your private key', cls='center-text'),
            html.Div('All guardians’ must upload their valid private keys to unlock the ballot box.', cls='center-text'),
            html.Form(
                MDCFileField(
                    Input(id='file_input', type='file', name='pkl_file'),
                    label='Choose file'),
                html.Span("Your privacy key is a file with '.pkl' extension. ", cls='body-2'),
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
class ContestDecryptCard(html.Div):
    def __init__(self, *content, view, **context):
        contest = view.get_object()
        self.backlink = BackLink(
            'back',
            reverse('contest_detail', args=[contest.id]))
        super().__init__(
            html.H4('Open ballot box', cls='center-text'),
            html.Div(
                html.P('This process will erase all guardian keys from server memory.'),
                cls='center-text body-2'),
            html.Form(
                context['form'],
                CSRFInput(view.request),
                MDCButton('open and view results'),
                method='POST',
                cls='form'),
            cls='card',
        )


@template('contest_publish', Document, Card)
class ContestPublishCard(html.Div):
    def __init__(self, *content, view, form , **ctx):
        super().__init__(
            html.H4('Publish your election results', cls='center-text'),
            html.Div(
                html.P('This will decentralize your election results.'),
                cls='center-text body-2'),
            html.Form(
                CSRFInput(view.request),
                MDCButton('publish results'),
                method='POST',
                cls='form'),
            cls='card',
        )


class PublishProgressBar(Py2jsMixin, html.Div):
    def __init__(self, _steps, step=0):
        self.nsteps = len(_steps)
        self.step = step
        steps = [
            html.Span(
                cls=f'progress-step progress-step--disabled',
                **{'data-step': s})
            for s in range(0, self.nsteps)
        ]
        if 0 <= step < self.nsteps:
            steps[step].attrs['class'] += ' progress-step--active'

        super().__init__(
            MDCLinearProgress(),
            html.Div(
                *steps,
                cls='progress-bar__steps'
            ),
            html.Span(_steps[step], cls='center-text overline'),
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
class ContestResultCard(html.Div):
    def __init__(self, *content, view, **context):
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

        table_content = html.Tbody(cls='mdc-data-table__content')
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
        if contest.publish_status == 4 and contest.decentralized:
            publish_btn = MDCButton(
                'publish results',
                p=True,
                icon=WorldIcon(),
                tag='a',
                href=reverse('contest_publish', args=[contest.id]),
                style='margin: 0 auto;')

        super().__init__(
            html.H4('Results', cls='center-text'),
            html.Div(
                publish_btn,
                score_table,
                cls='table-container score-table'),
            cls='card',
        )


class GuardianDeleteBtn(html.A):
    def __init__(self, guardian):
        self.guardian = guardian

        super().__init__(
            MDCIcon(
                'delete',
                cls='delete-icon'),
            tag='a',
            href=reverse('contest_guardian_delete', args=[guardian.id]))


@template('guardian_create', Document, Card)
class GuardianCreateCard(html.Div):
    def __init__(self, *content, view, form, **context):
        contest = view.get_object()
        self.backlink = BackLink('back', reverse('contest_detail', args=[contest.id]))
        table_head_row = html.Tr(cls='mdc-data-table__header-row')
        for th in ('guardians', ''):
            table_head_row.addchild(
                html.Th(
                    th,
                    role='columnheader',
                    scope='col',
                    cls='mdc-data-table__header-cell overline',
                )
            )

        table_content = html.Tbody(cls='mdc-data-table__content')
        cls = 'mdc-data-table__cell'
        for guardian in contest.guardian_set.all():
            activated = guardian.user and guardian.user.is_active
            table_content.addchild(html.Tr(
                html.Td(guardian.user.email, cls=cls),
                html.Td(
                    GuardianDeleteBtn(guardian),
                    cls=cls,
                    style='text-align:right'),
                cls='mdc-data-table__row',
                style='opacity: 0.5;' if not activated else '',
            ))

        table = html.Table(
            html.Thead(table_head_row),
            table_content,
            **{
                'class': 'mdc-data-table__table',
                'aria-label': 'Voters'
            }
        )

        super().__init__(
            html.H4('Add guardians', cls='center-text'),
            html.Div(
                'Guardians are responsible for locking and unlocking of the ballot box with their private keys.',
                cls='center-text body-1'
            ),
            html.Div(
                html.B('No guardians for speed and simplicity (default).'),
                ' Electis App will technically be your guardian and can secure your ballot box.',
                cls='red-section'),
            html.Div(
                html.B('With guardians for greater security (recommended).'),
                ' You can distribute control over the closing/opening of the',
                ' ballot box between multiple guardians. All of their keys will',
                ' be necessary to conduct an election – from opening for voting',
                ' to revealing the results.',
                cls='red-section'),
            html.Form(
                form['email'],
                CSRFInput(view.request),
                MDCButtonOutlined('add guardian', p=False, icon='person_add'),
                table,
                html.Div(
                    form['quorum'],
                    html.Span(
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
