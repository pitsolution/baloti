from datetime import datetime, date
from django import forms
from django.db.models import Sum
from django.urls import reverse
from ryzom.components import components as html
from ryzom.py2js.decorator import JavaScript
from electeez import mdc
from electeez.components import BackLink
from .models import Contest, Candidate


class ContestForm(forms.ModelForm):
    now = datetime.now()
    current_time = now.strftime("%H:%M")

    start = forms.SplitDateTimeField(
        widget=forms.SplitDateTimeWidget(
            time_attrs={'type': 'time', 'value': current_time},
            date_attrs={'type': 'date', 'value': date.today()},
        )
    )
    end = forms.SplitDateTimeField(
        widget=forms.SplitDateTimeWidget(
            time_attrs={'type': 'time', 'value': current_time},
            date_attrs={'type': 'date', 'value': date.today()},
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

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data['votes_allowed'] < cleaned_data['number_elected']:
            raise forms.ValidationError(
                'Number of elected cannot be bellow number of votes allowed'
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


class ContestCreateCard(html.Div):
    def __init__(self, view, ctx):
        form = ctx.get('form', None)
        if form is None:
            form = ContestForm()

        content = []
        self.fields = {}
        content.append(html.Ul(
            *[html.Li(e) for e in form.non_field_errors()],
            cls='error-list'
        ))
        for field_name in form.fields:
            value = (
                getattr(form.instance, field_name, '')
                if form.instance
                else ''
            )
            if field_name in ('start', 'end'):
                content.append(html.H6(
                    f'Election {field_name}s',
                    cls='section')),
                self.fields[field_name] = mdc.MDCSplitDateTime(
                    form.fields[field_name].label,
                    name=field_name, required=True,
                    value=value)
                content.append(self.fields[field_name])
            elif field_name in ('votes_allowed', 'number_elected'):
                self.fields[field_name] = mdc.MDCTextFieldOutlined(
                    form.fields[field_name].label,
                    name=field_name, type='number', required=True,
                    value=value)
                content.append(self.fields[field_name])
            else:
                self.fields[field_name] = mdc.MDCTextFieldOutlined(
                    form.fields[field_name].label,
                    name=field_name, required=True,
                    value=value)
                content.append(self.fields[field_name])
                content.append(html.H6('Vote settings', cls='section'))

        self.submit_btn = mdc.MDCButton('Save')
        content.append(html.Div(
            self.submit_btn,
            style='display: flex; justify-content: flex-end'
        ))
        content.append(mdc.CSRFInput(view))

        self.form_component = html.Form(*content, method='POST')

        super().__init__(
            html.H4('Create an election'),
            self.form_component,
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


class ContestItem(html.Li):
    def __init__(self, obj, *args, **kwargs):
        self.obj = obj
        active_cls = ''
        status = ''
        if obj.actual_start:
            status = 'voting ongoing'
            active_cls = 'active'
        if obj.plaintext_tally:
            active_cls = ''
            status = 'result available'

        super().__init__(
            html.Span(cls='mdc-list-item__ripple'),
            html.Span(
                html.Span(cls=f'contest-indicator'),
                html.Span(
                    html.Span(status, cls='contest-status overline'),
                    html.Span(obj.name, cls='contest-name'),
                    cls='list-item__text-container'
                ),
                cls='mdc-list-item__text'
            ),
            cls=f'contest-list-item mdc-list-item mdc-ripple-upgraded {active_cls}'
        )

    def render_js(self):
        def click_event():
            def contest_detail(event):
                route(contest_url)

            getElementByUuid(list_item_id).addEventListener('click', contest_detail)

        return JavaScript(
            click_event,
            dict(
                list_item_id=self._id,
                contest_url=reverse('contest_detail', args=[self.obj.id]))
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
    def __init__(self, title, txt, icon_comp, btn_comp, url, **kwargs):
        self.action_btn = btn_comp
        self.action_url = url

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

    def render_js(self):
        if not self.action_btn:
            return ''

        def click_event():
            def action(event):
                route(url)
            getElementByUuid(btn_id).addEventListener('click', action)

        return JavaScript(click_event, dict(
            btn_id=self.action_btn._id,
            url=self.action_url
        ))


class ContestListCreateBtn(html.Li):
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
            cls='mdc-list-item contest-list-item'
        )

    def render_js(self):
        def click_event():
            def contest_detail(event):
                route(contest_url)

            getElementByUuid(list_item_id).addEventListener('click', contest_detail)

        return JavaScript(
            click_event,
            dict(
                list_item_id=self._id,
                contest_url=reverse('contest_create')
            )
        )


class ContestList(html.Div):
    def __init__(self, view, ctx):
        super().__init__(
            html.H4('Elections', style='text-align: center;'),
            ContestFilters(view),
            html.Ul(
                ListItem(ContestListCreateBtn()),
                *(
                    ContestListItem(contest)
                    for contest in ctx['contest_list']
                ) if view.get_queryset().count()
                else (
                    html.Li(
                        'There are no elections yet',
                        cls='mdc-list-item body-1'
                    )
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


class BasicSettingsAction(ListAction):
    def __init__(self, obj):
        btn_comp = mdc.MDCButtonOutlined('edit', False)
        super().__init__(
            'Basic settings',
            'Name, votes allowed, time and date, etc.',
            DoneIcon(), btn_comp,
            reverse('contest_update', args=(obj.id,)),
        )


class AddCandidateAction(ListAction):
    def __init__(self, obj):
        num_candidates = obj.candidate_set.count()
        if num_candidates:
            btn_comp = mdc.MDCButtonOutlined('edit', False)
            icon = DoneIcon()
            txt = f'{num_candidates} candidates'
        else:
            btn_comp = mdc.MDCButtonOutlined('add', False, 'add')
            icon = TodoIcon()
            txt = ''

        super().__init__(
            'Add candidates',
            txt, icon, btn_comp,
            reverse('contest_candidate_create', args=(obj.id,))
        )


class AddVoterAction(ListAction):
    def __init__(self, obj):
        emails = obj.voters_emails.split('\n')
        num_emails = len(emails)
        if emails[0] == '':
            num_emails = 0

        if num_emails:
            btn_comp = mdc.MDCButtonOutlined('edit', False)
            icon = DoneIcon()
            txt = f'{num_emails} voters'
        else:
            btn_comp = mdc.MDCButtonOutlined('add', False, 'add')
            icon = TodoIcon()
            txt = ''

        super().__init__(
            'Add voters',
            txt, icon, btn_comp,
            reverse('contest_voters_update', args=(obj.id,))
        )


class SecureElectionInner(html.Span):
    def __init__(self, obj):
        text = 'All guardians must possess a private key so that the ballot box is secure and the election can be opened for voting.'
        todo_list = html.Ol()

        #todo_list.addchild(html.Li('Add guardians', cls='line'))
        guardian = obj.guardian_set.first()
        cls = 'line' if guardian.downloaded else 'bold'
        todo_list.addchild(html.Li('Download my private key', cls=cls))

        cls = ''
        if guardian.downloaded and not guardian.verified:
            cls = 'bold'
        elif guardian.verified:
            cls = 'line'
        todo_list.addchild(html.Li('Confirm possession of an uncompromised private key', cls=cls))

        #todo_list.addchild(html.Li(
        #    'All guardians confirm possession of uncompromised private keys',
        #    html.Br(), '(1/4 confirmed)'))

        cls = ''
        if guardian.verified and not guardian.contest.joint_public_key:
            cls = 'bold'
        elif guardian.contest.joint_public_key:
            cls = 'line'
        todo_list.addchild(html.Li('Lock the ballot box / erase private keys from server memory', cls=cls))

        cls = ''
        if guardian.contest.joint_public_key:
            cls = 'bold'
        todo_list.addchild(html.Li('Open the election for voting', cls=cls))

        subtext = 'Guardians must NOT loose their PRIVATE keys and they must keep them SECRET.'
        if not guardian.downloaded:
            self.action_btn = mdc.MDCButtonOutlined(
                'download private key', False, 'file_download')
            self.action_url = reverse('guardian_download', args=(guardian.id,))
        elif not guardian.verified:
            self.action_btn = mdc.MDCButtonOutlined(
                'confirm key integrity', False)
            self.action_url = reverse('guardian_verify', args=(guardian.id,))
        elif not guardian.contest.joint_public_key:
            self.action_btn = mdc.MDCButtonOutlined(
                'Lock the ballot box', False)
            self.action_url = reverse('contest_pubkey', args=(guardian.contest.id,))
        elif not guardian.contest.actual_start:
            self.action_btn = mdc.MDCButton(
                'Open for voting')
            self.action_url = reverse('contest_open', args=(guardian.contest.id,))
        else:
            self.action_btn = None

        super().__init__(
            text,
            html.P(todo_list),
            subtext,
            self.action_btn,
            cls='body-2'
        )

    def render_js(self):
        if not self.action_btn:
            return ''

        def click_event():
            def action(event):
                route(action_url)
            getElementByUuid(action_btn).addEventListener('click', action)

        return JavaScript(click_event, dict(
            action_btn=self.action_btn._id,
            action_url=self.action_url
        ))


class SecureElectionAction(ListAction):
    def __init__(self, obj, user):
        if obj.joint_public_key:
            icon = DoneIcon()
            title = 'Ballot box securely locked. Election can be open for voting.'
        else:
            icon = TodoIcon()
            title = 'Secure the election'

        super().__init__(
            title,
            SecureElectionInner(obj),
            icon, None, None,
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
            btn_comp = url = None
        else:
            txt = ''
            icon = TodoIcon()
            btn_comp = mdc.MDCButtonOutlined('vote', False)
            url = reverse('contest_vote', args=(obj.id,))

        super().__init__(
            'Cast my vote',
            txt, icon, btn_comp, url,
            separator=True
        )


class OnGoingElectionAction(ListAction):
    def __init__(self, contest, user):
        self.contest = contest
        self.user = user
        self.close_btn = mdc.MDCButtonOutlined('close', False)
        self.close_url = reverse('contest_close', args=(contest.id,))
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
            inner.addchild(self.close_btn)

        super().__init__(
            title,
            inner,
            icon,
            None, None,
            separator=True
        )

    def render_js(self):
        def click_event():
            def close_contest(event):
                route(url)

            getElementByUuid(close_btn).addEventListener('click', close_contest)

        if self.contest.actual_end or self.contest.mediator != self.user:
            return ''

        return JavaScript(click_event, dict(
            close_btn=self.close_btn._id,
            url=self.close_url
        ))


class UploadPrivateKeyAction(ListAction):
    def __init__(self, contest, user):
        self.contest = contest
        self.user = user
        self.has_action = False

        guardian = contest.guardian_set.filter(user=user).first()
        n_guardian = contest.guardian_set.count()
        n_uploaded = contest.guardian_set.exclude(uploaded=None).count()

        if contest.actual_end:
            task_list = html.Ol()
            if guardian:
                cls = 'line' if guardian.uploaded else 'bold'
                task_list.addchild(html.Li('Upload your private key', cls=cls))

            txt = f'All guardians upload their keys ({n_uploaded}/{n_guardian} uploaded)'
            cls=''
            if not guardian or guardian.uploaded:
                cls = 'bold'
            if n_uploaded == n_guardian:
                cls = 'line'

            task_list.addchild(html.Li(txt, cls=cls))

            if contest.mediator == user:
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
                html.P(
                    'Do NOT loose yout PRIVATE key and keep it SECRET.'
                ),
                html.P('When the election is over the guardians use their keys to open the ballot box and count the results.'),
                cls='body-2'
            )

        title = ''
        if guardian:
            title = 'Upload my private key'
            icon = DoneIcon()
            if contest.actual_end and not guardian.uploaded:
                self.has_action = True
                self.action_url_ = reverse('guardian_upload', args=(guardian.id,))
                self.action_btn_ = mdc.MDCButtonOutlined(
                    'upload my private key',
                    False)
                content.addchild(self.action_btn_)

        if contest.mediator == user:
            title = 'Unlocking the ballot box and revealing the resluts'
            if contest.actual_end and not self.has_action:
                self.has_action = True
                self.action_url_ = reverse('contest_decrypt', args=(contest.id,))
                self.action_btn_ = mdc.MDCButton(
                    'reveal results',
                    True,
                    n_guardian != n_uploaded)
                content.addchild(self.action_btn_)

            icon = TodoIcon()

        super().__init__(
            title,
            content,
            icon,
            None, None, separator=False
        )

    def render_js(self):
        def click_event():
            def upload_key(event):
                route(url)

            getElementByUuid(action_btn).addEventListener('click', upload_key)

        if self.has_action:
            return JavaScript(click_event, dict(
                action_btn=self.action_btn_._id,
                url=self.action_url_,
            ))

        return ''


class WaitForEmailAction(ListAction):
    def __init__(self, contest, user):
        super().__init__(
            'Once the ballots are counted you will be notified by email',
            '',
            EmailIcon(), None, None, separator=False
        )


class ResultAction(ListAction):
    def __init__(self, contest, user):
        self.contest = contest

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

        self.result_btn = mdc.MDCButton('view result table')
        subtext.addchild(self.result_btn)

        super().__init__(
            'Results available', subtext,
            DoneIcon(), None, None, separator=False
        )

    def render_js(self):
        def click_event():
            def get_results(event):
                route(url)

            getElementByUuid(result_btn).addEventListener('click', get_results)

        return JavaScript(click_event, dict(
            result_btn=self.result_btn._id,
            url=reverse('contest_result', args=(self.contest.id,))
        ))


class ContestVotingCard(html.Div):
    def __init__(self, view, ctx):
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
            if guardian.uploaded:
                if contest.mediator != user:
                    list_content.append(WaitForEmailAction(contest, user))
                else:
                    list_content

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
    def __init__(self, view, ctx):
        contest = view.get_object()
        user = view.request.user
        list_content = []
        if contest.mediator == view.request.user:
            list_content += [
                BasicSettingsAction(contest),
                AddCandidateAction(contest),
                AddVoterAction(contest),
            ]

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
    def __init__(self):
        super().__init__(
            html.Ul(
                ListAction(
                    'Secure and decentralised with Tezos',
                    html.Span(
                        'Your election data and results will be published on Tezos’ test blockchain.',
                        mdc.MDCTextButton("here's how", 'info_outline'),
                    ),
                    TezosIcon(), None, '',
                    separator=False
                ),
                cls='mdc-list action-list',
            ),
            cls='setting-section', style='background-color: aliceblue;'
        )


class CheckedIcon(mdc.MDCIcon):
    def __init__(self):
        super().__init__('check_circle', cls='icon green2')


class DownloadButton(mdc.MDCTextButton):
    def __init__(self):
        super().__init__('Download', 'file_download')


class UploadButton(mdc.MDCTextButton):
    def __init__(self):
        super().__init__('Upload', 'file_upload')


class GuardianTable(html.Div):
    def __init__(self, view, ctx):
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
                table_content.addchild(html.Tr(
                    html.Td(guardian.user.email, cls=cls),
                    html.Td(
                        CheckedIcon() if guardian.downloaded else DownloadButton(),
                        cls=cls + ' center'),
                    html.Td(
                        CheckedIcon() if guardian.verified else UploadButton(),
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
    def __init__(self, view, ctx):
        super().__init__(
            html.H5('Guardians'),
            GuardianTable(view, ctx),
            #mdc.MDCButtonOutlined('Add', False, 'person_add_alt_1'),
            cls='setting-section'
        )


class CandidatesSettingsCard(html.Div):
    def __init__(self, view, ctx):
        self.contest = view.get_object()
        if self.contest.actual_start:
            self.btn = mdc.MDCButtonOutlined('view all', False)
        elif self.contest.candidate_set.count():
            self.btn = mdc.MDCButtonOutlined('view all/edit', False)
        else:
            self.btn = mdc.MDCButtonOutlined('add', False, 'add')
        super().__init__(
            html.H5('Candidates'),
            CandidateList(self.contest),
            self.btn,
            cls='setting-section'
        )

    def render_js(self):
        def click_event():
            def candidate_create(event):
                route(url)
            getElementByUuid(btn_id).addEventListener('click', candidate_create)

        return JavaScript(click_event, dict(
            btn_id=self.btn._id,
            url=reverse('contest_candidate_create', args=(self.contest.id,))
        ))


class VotersSettingsCard(html.Div):
    def __init__(self, view, ctx):
        self.contest = contest = view.get_object()
        emails = contest.voters_emails.split('\n')
        num_emails = len(emails)
        if emails[0] == '':
            num_emails = 0

        if self.contest.actual_start:
            self.btn = mdc.MDCButtonOutlined('view all', False)
            self.url = reverse('contest_voters_detail', args=(self.contest.id,))
        elif num_emails:
            self.btn = mdc.MDCButtonOutlined('view all/edit', False)
            self.url = reverse('contest_voters_detail', args=(self.contest.id,))
        else:
            self.btn = mdc.MDCButtonOutlined('add', False, 'add')
            self.url = reverse('contest_voters_update', args=(self.contest.id,))

        super().__init__(
            html.H5('Voters'),
            html.Span(num_emails, ' voters added', cls='voters_count'),
            self.btn,
            cls='setting-section'
        )

    def render_js(self):
        def click_event():
            def voters_details(event):
                route(url)
            getElementByUuid(btn_id).addEventListener('click', voters_details)

        return JavaScript(click_event, dict(
            btn_id=self.btn._id,
            url=self.url
        ))


class ContestFinishedCard(html.Div):
    def __init__(self, view, ctx):
        super().__init__(
            html.H4(view.get_object().name),
            html.Ul(
                ResultAction(view.get_object(), view.request.user),
                cls='mdc-list action-list'
            ),
            cls='setting-section main-setting-section'
        )


class ContestCard(html.Div):
    def __init__(self, view, ctx):
        contest = view.get_object()
        if contest.plaintext_tally:
            main_section = ContestFinishedCard(view, ctx)
        elif contest.actual_start:
            main_section = ContestVotingCard(view, ctx)
        else:
            main_section = ContestSettingsCard(view, ctx)

        super().__init__(
            html.Div(
                BackLink('my elections', reverse('contest_list')),
                html.Div(
                    main_section,
                    TezosSecuredCard(),
                    GuardiansSettingsCard(view, ctx),
                    cls='main-container'
                ),
                html.Div(
                    CandidatesSettingsCard(view, ctx),
                    VotersSettingsCard(view, ctx),
                    cls='side-container'
                ),
                cls='flex-container'
            )
        )


class CandidateListItem(mdc.MDCListItem):
    def __init__(self, contest, candidate):
        self.contest = contest
        self.candidate = candidate
        super().__init__(
            candidate.name,
            cls='candidate-list-item'
        )

    def render_js(self):
        def click_event():
            def edit_candidate(event):
                route(url)

            getElementByUuid(_id).addEventListener('click', edit_candidate)

        if self.contest.actual_start:
            return ''

        return JavaScript(click_event, dict(
            _id=self._id,
            url=reverse('contest_candidate_update', args=(self.candidate.id,))
        ))


class CandidateList(html.Ul):
    def __init__(self, contest):
        super().__init__(
            *(
                CandidateListItem(contest, candidate)
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
                mdc.MDCListItem(voter)
                for voter
                in emails
            ) if num_emails
            else 'No voter yet.',
            cls='mdc-list voters-list'
        )


class VotersDetailCard(html.Div):
    def __init__(self, view, ctx):
        self.contest = contest = view.get_object()
        raw_emails = contest.voters_emails.split('\n')
        if raw_emails[0] == '':
            raw_emails = []

        table_head_row = html.Tr(cls='mdc-data-table__header-row')
        for th in ('email', 'activated', 'voted'):
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
        for email in raw_emails:
            activated = casted = False
            voter = contest.voter_set.filter(user__email=email).first()
            if voter:
                activated = True
                if voter.casted:
                    casted = True

            table_content.addchild(html.Tr(
                html.Td(email, cls=cls),
                html.Td(CheckedIcon() if activated else 'No', cls=cls + ' center'),
                html.Td(CheckedIcon() if casted else 'No', cls=cls + ' center'),
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
        self.edit_btn = mdc.MDCButtonOutlined('edit voters', False, 'edit')
        self.email_btn = mdc.MDCButtonOutlined('email voters', False, 'mail')

        if contest.actual_start:
            self.edit_btn = ''

        super().__init__(
            html.H4(len(raw_emails), ' Voters', cls='center-text'),
            html.Div(self.edit_btn, self.email_btn, cls='center-button'),
            table,
            cls='card'
        )

    def render_js(self):
        def click_events():
            def edit_voters(event):
                route(edit_url)

            def email_voters(event):
                pass

            getElementByUuid(email_btn).addEventListener('click', email_voters)

            if edit_btn:
                getElementByUuid(edit_btn).addEventListener('click', edit_voters)

        return JavaScript(click_events, dict(
            edit_btn=self.edit_btn._id if self.edit_btn else '',
            edit_url=reverse('contest_voters_update', args=(self.contest.id,)),
            email_btn=self.email_btn._id,
            email_url=''
        ))


class ContestCandidateCreateCard(html.Div):
    def __init__(self, view, ctx):
        contest = view.get_object()

        if not contest.actual_start:
            form = ctx.get('form')
            name_field = mdc.MDCTextFieldOutlined('Name', name='name', required=True)
            if form.errors:
                err = form.errors.get('name', None)
                if err:
                    name_field.set_error(err)

            form_component = html.Form(
                mdc.CSRFInput(view),
                name_field,
                mdc.MDCButton('Add', True),
                method='POST',
                cls='candidate-create-form'
            )
        else:
            form_component = ''

        super().__init__(
            html.H4(
                contest.candidate_set.count(), ' Candidates',
                style='text-align: center;'
            ),
            form_component,
            CandidateList(contest),
            cls='card'
        )


class ContestCandidateUpdateCard(html.Div):
    def __init__(self, view, ctx):
        form = ctx.get('form')
        name_field = mdc.MDCTextFieldOutlined(
            'Name',
            name='name',
            value=view.get_object().name,
            required=True)
        if form.errors:
            err = form.errors.get('name', None)
            if err:
                name_field.set_error(err)

        self.candidate = view.get_object()
        self.delete_btn = mdc.MDCTextButtonLabel('delete', 'delete')
        super().__init__(
            html.H4(
                'Edit candidate',
                style='text-align: center;'
            ),
            html.Form(
                mdc.CSRFInput(view),
                name_field,
                html.Div(
                    html.Div(self.delete_btn, cls='red-button-container'),
                    mdc.MDCButton('Save', True),
                    style='display: flex; justify-content: space-between'
                ),
                method='POST',
                cls='candidate-create-form'
            ),
            cls='card'
        )

    def render_js(self):
        def click_event():
            def delete_candidate(event):
                route(url)

            getElementByUuid(btn_id).addEventListener('click', delete_candidate)

        return JavaScript(click_event, dict(
            url=reverse('contest_candidate_delete', args=(self.candidate.id,)),
            btn_id=self.delete_btn._id
        ))


class ContestVotersUpdateCard(html.Div):
    def __init__(self, view, ctx):
        form = ctx.get('form')
        contest = view.get_object()
        emails_field = mdc.MDCTextareaFieldOutlined(
            contest.voters_emails,
            'voters Emails',
            name='voters_emails',
            rows='10')
        if form.errors:
            err = form.errors.get('voters_emails', None)
            if err:
                emails_field.set_error(err)

        emails = contest.voters_emails.split('\n')
        num_emails = len(emails)
        if emails[0] == '':
            num_emails = 0

        super().__init__(
            html.H4(num_emails, ' Voters', style='text-align: center;'),
            html.Div('The list of allowed voters with one email per line (sparated by Enter/Return ⏎)', cls='body-2', style='margin-bottom: 24px;text-align: center;'),
            html.Form(
                mdc.CSRFInput(view),
                emails_field,
                mdc.MDCButton('Save'),
                method='POST',
                cls='voters-update-form'
            ),
            cls='card'
        )


class GuardianVerifyCard(html.Div):
    def __init__(self, view, ctx):
        form = ctx.get('form')
        guardian = view.get_object()
        contest = guardian.contest

        self.submit_btn = mdc.MDCButton('confirm', True, disabled=True)

        super().__init__(
            html.H4('Confirm possession of an uncompromised private key', cls='center-text'),
            html.Div('You need to upload your private key to confirm that you posses a valid key that hasn’t been temepered with.', cls='center-text'),
            html.Form(
                mdc.MDCFileInput('Choose file', 'file_input', name='pkl_file'),
                html.Span("Your privacy key is a file with '.pkl' extension. ", cls='body-2'),
                self.submit_btn,
                mdc.CSRFInput(view),
                enctype='multipart/form-data',
                method='POST',
                cls='guardian-verify-form',
            ),
            cls='card'
        )

    def render_js(self):
        def change_event():
            def enable_post(event):
                file_name = document.querySelector('#file_input')
                if file_name != '':
                    setattr(getElementByUuid(submit_btn), 'disabled', False)
                else:
                    setattr(getElementByUuid(submit_btn), 'disabled', True)
            file_input = document.querySelector('#file_input')
            file_input.addEventListener('change', enable_post)

        return JavaScript(change_event, dict(submit_btn=self.submit_btn._id))


class ContestPubKeyCard(html.Div):
    def __init__(self, view, ctx):
        self.encrypt_btn = mdc.MDCButton('create')
        super().__init__(
            html.H4('Lock the ballot box', cls='center-text'),
            html.Div(
                html.P('This will remove all guardians’ private keys from the server memory.'),
                html.P('When the voting is over the ballot box can only be opened when all guardians upload their private keys.'),
                html.P('This is what makes the governing of the election decentralised.')
            ),
            html.Form(
                mdc.CSRFInput(view),
                html.Div(self.encrypt_btn,
                    style='display:flex; justify-content: center'),
                method='POST'
            ),
            cls='card'
        )


class ContestOpenCard(html.Div):
    def __init__(self, view, ctx):
        self.open_btn = mdc.MDCButton('Open')
        super().__init__(
            html.H4('Open the election for voting', cls='center-text'),
            html.Div(
                html.P('Once you open the election for voting you can’t make changes to it.'),
                cls='center-text'
            ),
            html.Form(
                mdc.CSRFInput(view),
                html.Div(self.open_btn,
                    style='display:flex; justify-content: center'),
                method='POST'
            ),
            cls='card'
        )


class ContestVoteCard(html.Div):
    def __init__(self, view, ctx):
        choices = []
        for i, candidate in enumerate(view.form.fields['selections'].queryset):
            choices.append((i, candidate.name, candidate.id))

        multiple_choices_field = mdc.MDCMultipleChoicesCheckbox(
            name='selections',
            choices=choices,
            n=view.form.max_selections,
            **{'aria-label': 'Make your choice'}
        )

        self.create_ballot_btn = mdc.MDCButton('create ballot')
        super().__init__(
            html.H4('Make your choice', cls='center-text'),
            html.Div(
                html.P(f'You may choose up to {view.form.max_selections} ' +
                        'candidates. In the end of the election ' +
                        f'{view.object.number_elected} winner will be announced.'),
                cls='center-text body-2'
            ),
            html.Form(
                mdc.CSRFInput(view),
                multiple_choices_field,
                self.create_ballot_btn,
                method='POST',
                cls='vote-form',
            ),
            cls='card'
        )


class ContestBallotEncryptCard(html.Div):
    def __init__(self, view, ctx):
        self.contest = ctx.get('object', None)
        self.selections = ctx.get('selections', [])
        self.ballot = ctx.get('ballot', '')
        self.change_btn = mdc.MDCButtonOutlined('change', False)
        self.encrypt_btn = mdc.MDCButton('encrypt ballot')

        super().__init__(
            html.H4('Review your ballot', cls='center-text'),
            html.Div(
                html.P('This is an ecrypted election. Once your ballot is encrypted, it will always stay that way – no one can see who voted for whom. However, you will be able to check that your vote has been properly counted.  Learn how'),
                cls='center-text'),
            html.H6('Your selection'),
            html.Ul(*(
                mdc.MDCListItem(candidate.name)
                for candidate in self.selections),
                cls='mdc-list'),
            self.change_btn,
            html.H6('Plain text ballot'),
            html.Div(
                html.P('For reference, this is your ballot before encryption:'),
                cls='body-2'),
            html.Form(
                mdc.MDCTextareaFieldOutlined(self.ballot, rows=15, readonly=True),
                mdc.CSRFInput(view),
                self.encrypt_btn,
                method='POST',
                cls='encrypt-form'),
            cls='card',
        )

    def render_js(self):
        def click_event():
            def change_selections(event):
                route(url)

            getElementByUuid(change_btn).addEventListener('click', change_selections)

        return JavaScript(click_event, dict(
            change_btn=self.change_btn._id,
            url=reverse('contest_vote', args=(self.contest.id,))
        ))


class ContestBallotCastCard(html.Div):
    def __init__(self, view, ctx):
        self.contest = ctx.get('object', None)
        self.ballot = ctx.get('ballot', '')
        self.download_btn = mdc.MDCButtonLabelOutlined(
            'download ballot file', False, 'file_download')
        self.cast_btn = mdc.MDCButton('confirm my vote')

        super().__init__(
            html.H4('Encrypted ballot', cls='center-text'),
            html.Div(
                html.P('This is an ecrypted election. Once your ballot is encrypted, it will always stay that way – no one can see who voted for whom. However, you will be able to check that your vote has been properly counted. Learn more'),
                cls='center-text body-2'),
            html.Form(
                mdc.MDCTextareaFieldOutlined(
                    self.ballot.to_json(),
                    rows=15,
                    readonly=True),
                mdc.CSRFInput(view),
                self.download_btn,
                self.cast_btn,
                method='POST',
                cls='encrypt-form'),
            cls='card',
        )

    def render_js(self):
        def click_event():
            def download_file(event):
                blob = _new(Blob, Array(ballot), {'type': 'application/json'})
                url = URL.createObjectURL(blob)
                link = document.createElement('a')
                setattr(link, 'href', url)
                setattr(link, 'download', file_name)
                link.click()
                URL.revokeObjectURL(url)

            getElementByUuid(download_btn).addEventListener('click', download_file)

        return JavaScript(click_event, dict(
            download_btn=self.download_btn._id,
            ballot=self.ballot.to_json().replace('"', '\\"'),
            file_name=self.contest.name + '_encrypted_ballot.json'
        ))


class ContestCloseCard(html.Div):
    def __init__(self, view, ctx):
        self.contest = view.get_object()
        self.close_btn = mdc.MDCButtonOutlined('close the election now', False)

        super().__init__(
            html.H4('Manual closing of the election', cls='center-text'),
            html.Div(
                html.P('This will stop the voting process and it can\'t be undone.'),
                cls='center-text body-2'),
            html.Form(
                mdc.CSRFInput(view),
                html.Div(
                    self.close_btn,
                    style='margin: 0 auto;',
                    cls='red-button-container'),
                method='POST',
                cls='close-form'),
            cls='card',
        )

    def render_js(self):
        def click_event():
            def close_election(event):
                route(url)

            getElementByUuid(close_btn).addEventListener('click', close_election)

        return JavaScript(click_event, dict(
            close_btn=self.close_btn._id,
            url=reverse('contest_close', args=(self.contest.id,))
        ))


class GuardianUploadKeyCard(html.Div):
    def __init__(self, view, ctx):
        form = ctx.get('form')
        guardian = view.get_object()
        contest = guardian.contest

        self.submit_btn = mdc.MDCButton('confirm', True, disabled=True)

        super().__init__(
            html.H4('Verify your private key', cls='center-text'),
            html.Div('All guardians’ must upload their valid private keys to unlock the ballot box.', cls='center-text'),
            html.Form(
                mdc.MDCFileInput('Choose file', 'file_input', name='pkl_file'),
                html.Span("Your privacy key is a file with '.pkl' extension. ", cls='body-2'),
                self.submit_btn,
                mdc.CSRFInput(view),
                enctype='multipart/form-data',
                method='POST',
                cls='guardian-verify-form',
            ),
            cls='card'
        )

    def render_js(self):
        def change_event():
            def enable_post(event):
                file_name = document.querySelector('#file_input')
                if file_name != '':
                    setattr(getElementByUuid(submit_btn), 'disabled', False)
                else:
                    setattr(getElementByUuid(submit_btn), 'disabled', True)
            file_input = document.querySelector('#file_input')
            file_input.addEventListener('change', enable_post)

        return JavaScript(change_event, dict(submit_btn=self.submit_btn._id))


class ContestDecryptCard(html.Div):
    def __init__(self, view, ctx):
        self.contest = view.get_object()
        self.decrypt_btn = mdc.MDCButton('open and view results')

        super().__init__(
            html.H4('Open ballot box', cls='center-text'),
            html.Div(
                html.P('This process will erase all guardian keys from server memory.'),
                cls='center-text body-2'),
            html.Form(
                mdc.CSRFInput(view),
                mdc.MDCMultipleChoicesCheckbox(
                    'ipfs',
                    [(0, 'Deploy on IPFS?', 1)]),
                self.decrypt_btn,
                method='POST',
                cls='decrypt-form'),
            cls='card',
        )

    def render_js(self):
        def click_event():
            def decrypt_election(event):
                route(url)

            getElementByUuid(decrypt_btn).addEventListener('click', decrypt_election)

        return JavaScript(click_event, dict(
            decrypt_btn=self.decrypt_btn._id,
            url=reverse('contest_decrypt', args=(self.contest.id,))
        ))


class ContestResultCard(html.Div):
    def __init__(self, view, ctx):
        self.contest = view.get_object()

        votes = self.contest.candidate_set.aggregate(total=Sum('score'))

        table_head_row = html.Tr(cls='mdc-data-table__header-row')
        kwargs = dict(
            role='columnheader',
            scope='col',
            cls='mdc-data-table__header-cell overline'
        )
        table_head_row.addchild(html.Th('candidate', **kwargs))

        kwargs['style'] = 'text-align: right;'
        table_head_row.addchild(html.Th('votes', **kwargs))

        table_content = html.Tbody(cls='mdc-data-table__content')
        cls = 'mdc-data-table__cell'

        for i, candidate in enumerate(self.contest.candidate_set.order_by('-score')):
            num = f'{i + 1}. '
            score_percent = 100 * candidate.score / votes['total']
            table_content.addchild(
                html.Tr(
                    html.Td(num + candidate.name, cls=cls),
                    html.Td(
                        html.Span(f'{candidate.score}', cls='body-2'),
                        html.Span(f' {score_percent} %', cls='text-btn'),
                        style='text-align: right'),
                    cls='mdc-data-table__row'))

        score_table = html.Table(
            html.Thead(table_head_row),
            table_content,
            **{
                'class': 'mdc-data-table__table',
                'aria-label': 'Scores'
            }
        )

        super().__init__(
            html.H4('Results', cls='center-text'),
            html.Div(
                score_table,
                cls='table-container score-table'),
            cls='card',
        )
