from datetime import datetime, date
from django import forms
from django.urls import reverse
from ryzom.components import components as html
from ryzom.py2js.decorator import JavaScript
from electeez import mdc
from .models import Contest


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
        active_cls = 'active'
        super().__init__(
            html.Span(cls='mdc-list-item__ripple'),
            html.Span(
                html.Span(cls=f'contest-indicator'),
                html.Span(
                    html.Span('status', cls='contest-status overline'),
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

        subitem = html.Span(cls='mdc-list-item__primary-text list-action-row')
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
            cls='mdc-list-item'
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
                ContestListCreateBtn(),
                *(
                    ContestListItem(contest)
                    for contest in ctx['contest_list']
                ),
                cls='mdc-list contest-list'
            ),
            cls='card'
        )


class CircleIcon(html.Span):
    def __init__(self, icon, color='', small=False):
        base_cls = f'icon {icon} {"small" if small else ""}'
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
        btn_comp = mdc.MDCButtonOutlined('add', False, 'add')
        num_candidates = obj.candidate_set.count()
        icon = DoneIcon() if num_candidates else TodoIcon()
        super().__init__(
            'Add candidates',
            f'{num_candidates} candidates',
            icon, btn_comp,
            reverse('contest_candidate_create', args=(obj.id,))
        )


class AddVoterAction(ListAction):
    def __init__(self, obj):
        btn_comp = mdc.MDCButtonOutlined('add', False, 'add')
        emails = obj.voters_emails.split('\n')
        num_emails = len(emails)
        if emails[0] == '':
            num_emails = 0
        icon = DoneIcon() if num_emails else TodoIcon()
        super().__init__(
            'Add voters',
            f'{num_emails} voters',
            icon, btn_comp,
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

        if guardian.downloaded and not guardian.verified:
            cls = 'bold'
        elif guardian.verified:
            cls = 'line'
        else:
            cls = ''
        todo_list.addchild(html.Li('Confirm possession of an uncompromised private key', cls=cls))

        #todo_list.addchild(html.Li(
        #    'All guardians confirm possession of uncompromised private keys',
        #    html.Br(), '(1/4 confirmed)'))

        if guardian.verified and not guardian.contest.joint_public_key:
            cls = 'bold'
        elif guardian.contest.joint_public_key:
            cls = 'line'
        todo_list.addchild(html.Li('Lock the ballot box / erase private keys from server memory', cls=cls))

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
        else:
            self.action_btn = mdc.MDCButtonOutlined(
                'Open the election', False)
            self.action_url = reverse('contest_open', args=(guardian.contest.id,))

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
    def __init__(self, obj):
        super().__init__(
            'Secure the election',
            SecureElectionInner(obj),
            TodoIcon(), None, None,
            separator=False
        )


class ContestSettingsCard(html.Div):
    def __init__(self, view, ctx):
        contest = view.get_object()
        super().__init__(
            html.H4(contest.name),
            html.Ul(
                BasicSettingsAction(view.get_object()),
                AddCandidateAction(view.get_object()),
                AddVoterAction(view.get_object()),
                SecureElectionAction(view.get_object()),
                cls='mdc-list action-list'
            ),
            cls='card'
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
            cls='card', style='background-color: aliceblue;'
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
        super().__init__(table)


class GuardiansSettingsCard(html.Div):
    def __init__(self, view, ctx):
        super().__init__(
            html.H6('Guardians'),
            GuardianTable(view, ctx),
            mdc.MDCButtonOutlined('Add', False, 'person_add_alt_1'),
            cls='card setting-section'
        )


class CandidatesSettingsCard(html.Div):
    def __init__(self, view, ctx):
        contest = view.get_object()
        super().__init__(
            html.H6('Candidates'),
            CandidateList(contest),
            mdc.MDCButtonOutlined('view all/edit', False),
            cls='card setting-section'
        )


class VotersSettingsCard(html.Div):
    def __init__(self, view, ctx):
        self.contest = contest = view.get_object()
        emails = contest.voters_emails.split('\n')
        num_emails = len(emails)
        if emails[0] == '':
            num_emails = 0
        self.btn = mdc.MDCButtonOutlined('view/edit', False)
        super().__init__(
            html.H6('Voters'),
            html.Span(num_emails, ' voters added'),
            self.btn,
            cls='card setting-section'
        )

    def render_js(self):
        def click_event():
            def voters_details(event):
                route(url)
            getElementByUuid(btn_id).addEventListener('click', voters_details)

        return JavaScript(click_event, dict(
            btn_id=self.btn._id,
            url=reverse('contest_voters_detail', args=(self.contest.id,))
        ))


class ContestCard(html.Div):
    def __init__(self, view, ctx):
        super().__init__(
            html.Div(
                html.Div(
                    ContestSettingsCard(view, ctx),
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


class CandidateList(html.Ul):
    def __init__(self, contest):
        super().__init__(
            *(
                mdc.MDCListItem(candidate.name)
                for candidate
                in contest.candidate_set.all()
            ) if contest.candidate_set.count()
            else 'No candidate yet.',
            cls='mdc-list'
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
            cls='mdc-list'
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
        super().__init__(
            html.H6(len(raw_emails), ' Voters', cls='center-text'),
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

            getElementByUuid(edit_btn).addEventListener('click', edit_voters)
            getElementByUuid(email_btn).addEventListener('click', email_voters)

        return JavaScript(click_events, dict(
            edit_btn=self.edit_btn._id,
            edit_url=reverse('contest_voters_update', args=(self.contest.id,)),
            email_btn=self.email_btn._id,
            email_url=''
        ))


class ContestCandidateCreateCard(html.Div):
    def __init__(self, view, ctx):
        form = ctx.get('form')
        name_field = mdc.MDCTextFieldOutlined('Name', name='name', required=True)
        if form.errors:
            err = form.errors.get('name', None)
            if err:
                name_field.set_error(err)

        super().__init__(
            html.H6(
                form.instance.contest.candidate_set.count(), ' Candidates',
                style='text-align: center;'
            ),
            html.Form(
                mdc.CSRFInput(view),
                name_field,
                mdc.MDCButton('Add candidate', True, 'add'),
                method='POST',
                cls='candidate-create-form'
            ),
            CandidateList(form.instance.contest),
            cls='card'
        )


class ContestVotersUpdateCard(html.Div):
    def __init__(self, view, ctx):
        form = ctx.get('form')
        contest = view.get_object()
        emails_field = mdc.MDCTextareaFieldOutlined(
            contest.voters_emails,
            'voters Emails',
            rows='10',
            name='voters_emails',
            type='textarea')
        if form.errors:
            err = form.errors.get('voters_emails', None)
            if err:
                emails_field.set_error(err)

        emails = contest.voters_emails.split('\n')
        num_emails = len(emails)
        if emails[0] == '':
            num_emails = 0

        super().__init__(
            html.H6(num_emails, ' Voters', style='text-align: center;'),
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
            html.H6('Confirm possession of an uncompromised private key', cls='center-text'),
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
            html.H6('Lock the ballot box', cls='center-text'),
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
            html.H6('Open the election for voting', cls='center-text'),
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
