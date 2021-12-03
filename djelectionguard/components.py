import random

from datetime import datetime, date, timedelta
from django import forms
from django.conf import settings
from django.db.models import Sum
from django.core.exceptions import ObjectDoesNotExist
from django.template.defaultfilters import date as _date
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import get_language
from django.utils.safestring import mark_safe
from django.utils.html import escape

from electeez_common.components import *
from ryzom_django.forms import widget_template
from django.conf import settings

from djlang.utils import gettext as _
from electeez_sites.models import Site
from .models import Contest, Candidate, ParentContest, Recommender
from ckeditor.widgets import CKEditorWidget


@widget_template('django/forms/widgets/splitdatetime.html')
class SplitDateTimeWidget(SplitDateTimeWidget):
    date_label = _('Date')
    date_style = 'margin-top: 0; margin-bottom: 32px;'
    time_label = _('Time')
    time_style = 'margin: 0;'


class ContestForm(forms.ModelForm):
    def now():
        now = datetime.now()
        return now.replace(second=0, microsecond=0)

    def tomorow():
        tomorow = datetime.now() + timedelta(days=1)
        return tomorow.replace(second=0, microsecond=0)

    referendum_type = forms.CharField(
        label=_('FORM_REFERENDUM_TYPE'),
        required=False
    )
    parent = forms.ModelChoiceField(queryset=ParentContest.objects.filter(), empty_label="(Parent)")
    initiator = forms.ModelChoiceField(queryset=Recommender.objects.filter(), empty_label="(Initiator)")
    infavour_arguments = forms.CharField(widget=CKEditorWidget())
    against_arguments = forms.CharField(widget=CKEditorWidget())

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
            date_attrs={'type': 'date', 'label': 'date'},
            time_attrs={'type': 'time', 'label': 'heure'},
        ),
    )
    end = forms.SplitDateTimeField(
        label='',
        initial=tomorow,
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
            'referendum_type',
            'parent',
            'initiator',
            'infavour_arguments',
            'against_arguments',
            'about',
            'votes_allowed',
            'start',
            'end',
            'timezone',
        ]
        labels = {
            'name': _('FORM_TITLE_ELECTION_CREATE'),
            'referendum_type': _('FORM_TITLE_REFERENDUM_TYPE'),
            'parent': _('FORM_TITLE_PARENT'),
            'initiator': _('FORM_TITLE_INITIATOR'),
            'infavour_arguments': _('FORM_TITLE_INFAVOUR_ARGUMENTS'),
            'against_arguments': _('FORM_TITLE_AGAINST_ARGUMENTS'),
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
            H4(_('Edit referendum') if edit else _('Create a referendum')),
            Form(
                form['name'],
                form['referendum_type'],
                form['parent'],
                form['initiator'],
                form['infavour_arguments'],
                form['against_arguments'],
                form['about'],
                H6(_('Voting settings:')),
                form['votes_allowed'],
                H6(_('Referendum starts:')),
                form['start'],
                H6(_('Referendum ends:')),
                form['end'],
                form['timezone'],
                CSRFInput(view.request),
                MDCButton(_('update referendum') if edit else _('create referendum')),
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
    def __init__(self, contest, user, *args, **kwargs):
        active_cls = ''
        status = ''
        voter = contest.voter_set.filter(user=user).first()
        voted = voter and voter.casted
        if contest.actual_start:
            status = _('voting ongoing')
            active_cls = 'active'
        if contest.actual_end:
            status = _('voting closed')
        if contest.plaintext_tally:
            active_cls = ''
            status = _('result available')

        status_2 = _(', voted') if voted else ''

        super().__init__(
            Span(cls='mdc-list-item__ripple'),
            Span(
                Span(cls=f'contest-indicator'),
                Span(
                    Span(status, status_2, cls='contest-status overline'),
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
    def __init__(self, obj, user, **kwargs):
        super().__init__(ContestItem(obj, user))


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
                Span(_('Create new referendum')),
                cls='mdc-list-item__text text-btn mdc-ripple-upgraded'
            ),
            cls='mdc-list-item contest-list-item',
            href=reverse('contest_create')
        )


@template('djelectionguard/contest_list.html', Document, Card)
class ContestList(Div):
    def to_html(self, *content, view, **context):
        site = Site.objects.get_current()
        can_create = (site.all_users_can_create
            or view.request.user.is_staff
            or view.request.user.is_superuser
        )
        return super().to_html(
            H4(_('Referendums'), style='text-align: center;'),
            # ContestFilters(view),
            Ul(
                ListItem(ContestListCreateBtn())
                if can_create else None,
                *(
                    ContestListItem(contest, view.request.user)
                    for contest in context['contest_list']
                ) if len(context['contest_list'])
                else (
                    Li(
                        _('There are no referendums yet'),
                        cls='mdc-list-item body-1'
                    ),
                ),
                cls='mdc-list contest-list'
            ),
            cls='card'
        )


class CircleIcon(Span):
    def __init__(self, icon, color='', small=False, **kw):
        base_cls = f'icon {icon} {"small " if small else ""}'
        super().__init__(
            cls=base_cls + color,
            **kw
        )


class TodoIcon(CircleIcon):
    def __init__(self, **kw):
        super().__init__('empty-icon', 'yellow', **kw)


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
        txt = _('%(candidates)d candidates, minimum: %(elected)d',
            n=num_candidates,
            candidates=num_candidates,
            elected=number
        )

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
            txt = _('%(num_voters)d voters', n=num_voters, num_voters=num_voters)
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
        text = _('All guardians must possess a private key so that the ballot box is secure and the referendum can be opened for voting.')
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
                    _('%(confirmed)d/%(gardiens)d confirmed',
                        n=n_confirmed,
                        confirmed=n_confirmed,
                        gardiens=n_guardians
                    ),
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
            todo_list.addchild(Li(_('Open the referendum for voting'), cls=cls))

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
        title = _('Secure the referendum')

        if obj.mediator == user:
            if obj.joint_public_key:
                title = _('Ballot box securely locked. Referendum can be open for voting.')
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
            head = _('Voted')
            s = voter.casted
            txt = Span(
                _('You casted your vote!'
                  ' The results will be published after the referendum is closed.'
                ),
                Br(),
                A(_('Track my vote'), href=reverse('tracker_detail', args=[voter.id])) if voter.casted else None,
            )
            icon = DoneIcon()
            btn_comp = None
        elif not obj.actual_end:
            head = _('Cast my vote')
            txt = ''
            icon = TodoIcon()
            url = reverse('contest_vote', args=(obj.id,))
            btn_comp = MDCButtonOutlined(_('vote'), False, tag='a', href=url)
        else:
            head = _('You did not vote')
            txt = _('The vote is closed, sorry you missed it.')
            icon = TodoIcon(style=dict(filter='brightness(0.5)'))
            btn_comp = None

        super().__init__( head, txt, icon, btn_comp, separator=True)


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
            txt = _('Choose the blockchain you want to deploy your referendum smart contract to')
            icon = TodoIcon()

        try:
            has_contract = obj.electioncontract is not None
        except Contest.electioncontract.RelatedObjectDoesNotExist:
            has_contract = False

        super().__init__(
            _('Add the referendum smart contract'),
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
    def __init__(self, contest, user, view):
        close_url = reverse('contest_close', args=[contest.id])
        close_btn = MDCButtonOutlined(_('close'), False, tag='a', href=close_url)
        start_time = '<b>' + _date(contest.actual_start, 'd F, G\hi') + '</b>'
        sub_txt = None
        if contest.actual_end:
            end_time = '<b>' + _date(contest.actual_end, 'd F, G\hi') + '</b>'
            title = _('Voting closed')
            txt = _('The voting started on %(start)s and was open till %(end)s. '
                    'Timezone: %(timezone)s.',
                        start=start_time,
                        end=end_time,
                        timezone=str(contest.timezone)
                    )
            txt = mark_safe(txt)
            icon = SimpleCheckIcon()
        else:
            vote_link = reverse('otp_send') + f'?redirect=' + reverse('contest_vote', args=[contest.id])
            vote_link = view.request.build_absolute_uri(vote_link)
            end_time = '<b>' + _date(contest.end, 'd F, G\hi') + '</b>'
            title = _('The voting process is currently ongoing')
            txt = _('The voting started on %(time_start)s and will be closed at %(time_end)s. '
                    'Timezone: %(timezone)s',
                        time_start=start_time,
                        time_end=end_time,
                        timezone=str(contest.timezone)
                    )
            if contest.mediator == user:
                sub_txt = _('Vote link: %(link)s',
                    link=f'<a href={vote_link}>{vote_link}</a>'
                )

            icon = OnGoingIcon()

        inner = Span(
            txt,
            CList(Br(), Br(), sub_txt) if sub_txt else None,
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
            txt = _('All guardians upload their keys %(uploaded)s/%(guardian)s uploaded',
                n=n_uploaded,
                uploaded=n_uploaded,
                guardian=n_guardian
            )
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
                P(_('When the referendum is over the guardians use their keys to open the ballot box and count the results.')),
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
        if contest.decrypting:
            icon = OnGoingIcon()
            title = _('Tallying in progress')
            if contest.mediator == user:
                subtext.addchild(
                    Div(_('An email will be sent when finished'))
                )
        else:
            icon = DoneIcon()
            title = _('Results available')
            if contest.mediator == user:
                subtext.addchild(
                    Div(_('Congratulations! You have been the mediator of a secure referendum.')))

            url=reverse('contest_result', args=[contest.id])
            result_btn = MDCButton(_('view result table'), tag='a', href=url)
            subtext.addchild(result_btn)

        super().__init__(
            title,
            subtext,
            icon,
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
            actions.append('vote')

        if contest.mediator == user:
            actions.append('close')

        guardian = contest.guardian_set.filter(user=user).first()
        if guardian:
            actions.append('upload')

        if 'vote' in actions:
            list_content.append(CastVoteAction(contest, user))

        list_content.append(OnGoingElectionAction(contest, user, view))

        if 'upload' in actions:
            list_content.append(UploadPrivateKeyAction(contest, user))
            if contest.mediator == user:
                list_content.append(UnlockBallotAction(contest, user))
            elif guardian.uploaded:
                if contest.mediator != user:
                    list_content.append(WaitForEmailAction(contest, user))

        if not len(actions):
            list_content.append(WaitForEmailAction(contest, user))

        about = mark_safe(escape(contest.about).replace('\n', '<br>'))

        super().__init__(
            H4(contest.name, style='word-break: break-all;'),
            Div(
                about,
                style='padding: 12px; word-break: break-all;',
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
                AddRecommenderAction(contest),
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

        about = mark_safe(escape(contest.about).replace('\n', '<br>'))

        super().__init__(
            H4(contest.name, style='word-break: break-all;'),
            Div(
                about,
                style='padding: 12px; word-break: break-all;',
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
        blockchain = None
        if contest.publish_state != contest.PublishStates.ELECTION_NOT_DECENTRALIZED:
            try:
                contract = contest.electioncontract
                blockchain = contract.blockchain
                link = A(
                    contract.contract_address,
                    href=getattr(contract, 'explorer_link', ''),
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
                        _('Your referendum data and results will be published'
                          ' on Tezos’ %(blockchain)s blockchain.',
                            blockchain=blockchain
                        ),
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
            Span(_('%(voters)s voters added', n=num_emails, voters=num_emails), cls='voters_count'),
            btn,
            cls='setting-section'
        )


class ContestFinishedCard(Div):
    def __init__(self, view, **context):
        contest = view.get_object()

        is_voter = False
        if contest.voter_set.filter(user=view.request.user).count():
            is_voter = True

        about = mark_safe(escape(contest.about).replace('\n', '<br>'))
        super().__init__(
            H4(contest.name, style='word-break: break-all'),
            Div(
                about,
                style='padding: 12px; word-break: break-all;',
                cls='subtitle-2'
            ),
            Ul(
                CastVoteAction(contest, view.request.user)
                if is_voter else None,
                ResultAction(contest, view.request.user),
                cls='mdc-list action-list'
            ),
            cls='setting-section main-setting-section'
        )


@template('djelectionguard/contest_detail.html', Document)
class ContestCard(Div):
    def to_html(self, *content, view, **context):
        contest = view.get_object()
        if contest.plaintext_tally or contest.decrypting:
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
        # sub_section.addchild(RecommendersSettingsCard(view, **context))


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
                style='margin-top: 6px; margin-bottom: 6px; word-break: break-all;'
            ),
            I(
                candidate.subtext,
                style=dict(
                    font_size='small',
                    font_weight='initial',
                    word_break='break-all',
                )
            ),
            style='flex: 1 1 65%; padding: 12px;'
        )

        if candidate.description:
            description = mark_safe(escape(candidate.description).replace('\n', '<br>'))
            subcontent.addchild(
                Div(
                    description,
                    style='margin-top: 24px; word-break: break-all;'
                )
            )

        content.append(subcontent)

        if editable and not candidate.description:
            content.append(
                MDCButtonOutlined(_('edit'), False, 'edit', **kwargs)
            )
        elif editable:
            subcontent.addchild(
                MDCButtonOutlined(_('edit'), False, 'edit', **kwargs)
            )

        if 'style' not in kwargs:
            kwargs['style'] = ''

        super().__init__(
            *content,
            style='padding: 12px;'
                  'display: flex;'
                  'flex-flow: row wrap;'
                  'justify-content: center;'
                  + kwargs.pop('style')
                  + extra_style,
            cls='candidate-detail',
        )


class CandidateAccordionItem(MDCAccordionSection):
    tag = 'candidate-list-item'

    def __init__(self, candidate, editable=False):
        super().__init__(
            CandidateDetail(candidate, editable),
            label=candidate.name,
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
        self.backlink = BackLink(_('back'), reverse('contest_detail', args=[contest.id]))

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
            H4(
                _('%(count)s Voters', n=voters.count(), count=voters.count()),
                cls='center-text'
            ),
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
        counter.innerHTML = count + '/300'

    def update_counter(event):
        field = event.currentTarget
        current_count = field.value.length
        if current_count > 300:
            field.value = field.value.substr(0, 300)
            current_count = 300
        parent = field.parentElement.parentElement.parentElement
        counter = parent.querySelector('.mdc-text-field-character-counter')
        counter.innerHTML = current_count + '/300'

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
        count = contest.candidate_set.count()
        return super().to_html(
            H4(
                _('%(count)s Candidates', n=count, count=count),
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
            _('delete'),
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
                    MDCButton(_('Save'), True),
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
        count = voters.count()

        return super().to_html(
            H4(_('%(count)s Voters', n=count, count=count), style='text-align: center;'),
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
                Span(_("Your privacy key is a file with '.pkl' extension."), cls='body-2'),
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
                Div(
                    MDCButton(_('create')),
                    style='width: fit-content; margin: 0 auto;'
                ),
                method='POST',
                cls='form',
            ),
            cls='card'
        )

@template('email_voters', Document, Card)
class ContestEmailVoters(Div):
    def to_html(self, *content, view, **context):
        contest = view.get_object()
        self.backlink = BackLink(
            _('back'),
            reverse('contest_voters_detail', args=[contest.id]))

        return super().to_html(
            H4(_('Send an invite to the newly added voters'), cls='center-text'),
            Form(
                context['form']['email_title'],
                context['form']['email_message'],
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
            H4(_('Open the referendum for voting'), cls='center-text'),
            Div(
                P(_('Once you open the referendum for voting you can’t make changes to it.')),
                cls='center-text'
            ),
            Form(
                context['form']['email_title'],
                context['form']['email_message'],
                MDCMultipleChoicesCheckbox(
                    'send_email',
                    ((0, B(_('Do not alert voters by email')), 'true'),),
                    n=1
                ),
                CSRFInput(view.request),
                MDCButton(_('open')),
                method='POST',
                cls='form'
            ),
            cls='card'
        )


class DialogConfirmForm(Form):
    def __init__(self, *content, selections=[], max_selections=1, **attrs):
        def hidden_selections():
            for s in selections:
                candidate = CandidateDetail(s)
                candidate.style.display = 'none'
                candidate.attrs['data-candidate-id'] = s.id
                yield candidate

        self.max_selections = max_selections

        actions = MDCDialogActions(
            MDCDialogCloseButtonOutlined(_('modify')),
            MDCDialogAcceptButton(
                _('confirm'),
                addcls='mdc-button--raised black-button',
            ),
            style={
                'display': 'flex',
                'justify-content': 'space-around'
            }
        )

        self.remaining_text_start = str(_('If you want it, you have'))
        self.remaining_text_end = str(_('choice left'))
        self.remaining_text_end_plural = str(_('choices left'))

        super().__init__(
            *content,
            MDCDialog(
                _('Confirm your selection'),
                Div(
                    _('Be careful, once confirmed,'
                    ' your choice is definitive and cannot be changed'),
                    *hidden_selections(),
                ),
                actions=Div(
                    actions,
                    Div(
                        Span(id='remaining'),
                        style=dict(
                            background='aliceblue',
                            text_align='center',
                            padding='12px',
                            margin='24px',
                            margin_top='0'
                        ),
                    ),
                )
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

        remaining = this.max_selections - len(selections)
        self.update_remaining(this, remaining)
        this.dialog.onclosing = self.ondialogclosing
        this.dialog.onclosed = self.ondialogclosed
        this.dialog.open()

    def update_remaining(form, remaining):
        elem = document.querySelector('#remaining')
        remaining_text = (
            form.remaining_text_start + ' ' + remaining + ' '
        )
        if remaining > 1:
            remaining_text += form.remaining_text_end_plural
        else:
            remaining_text += form.remaining_text_end

        if remaining == 0:
            elem.parentElement.style.display = 'none'
        else:
            elem.innerHTML = remaining_text
            elem.parentElement.style.display = 'block'

    def py2js(self):
        form = getElementByUuid(self.id)
        form.max_selections = self.max_selections
        form.remaining_text_start = self.remaining_text_start
        form.remaining_text_end = self.remaining_text_end
        form.remaining_text_end_plural = self.remaining_text_end_plural
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

        candidates = list(contest.candidate_set.all())
        random.shuffle(candidates)

        choices = (
            (i, CandidateDetail(candidate), candidate.id)
             for i, candidate
             in enumerate(candidates))

        about = mark_safe(escape(contest.about).replace('\n', '<br>'))

        return super().to_html(
            H4(contest.name, cls='center-text', style='word-break: break-all'),
            Div(
                about,
                cls='center-text body-2',
                style='word-break: break-all'
            ),
            Div(
                _('You have up to a total of %(vote_allowed)s choice',
                    n=max_selections,
                    vote_allowed=max_selections
                ),
                style='opacity: 0.6'
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
                max_selections=max_selections,
                method='POST',
                cls='form vote-form',
            ),
            cls='card'
        )


@template('djelectionguard/vote_success', Document, Card)
class ContestVoteSuccessCard(Div):
    def to_html(self, *content, view, **context):
        voter = view.get_object()
        self.backlink = BackLink(
            _('back'),
            reverse('contest_detail', args=[voter.contest.id])
        )

        track_link = reverse('tracker_detail', args=[voter.id])

        return super().to_html(
            H4(
                DoneIcon(),
                _('Your vote has been validated!'),
                style='text-align:center;'
            ),
            Div(
                _('Thank you for your participation.'
                  ' Your secret vote has been taken in account.'
                  ' You can, if you want, close this page.'),
                style=dict(
                    margin_top='50px'
                )
            ),
            Div(
                B(
                    _('How does electronic voting work?'),
                    style=dict(
                        text_align='center',
                        display='block'
                    )
                ),
                P(
                    _('ELECTRONIC_VOTE_EXPLAINATION'),
                    ' ',
                    A(_('here'), href=track_link)
                ),
                style=dict(
                    background='aliceblue',
                    margin_top='50px',
                    padding='12px',
                    opacity='0.6'
                )
            )
        )


@template('contest_close', Document, Card)
class ContestCloseCard(Div):
    def to_html(self, *content, view, **context):
        contest = view.get_object()
        self.backlink = BackLink(
            _('back'),
            reverse('contest_detail', args=[contest.id]))

        return super().to_html(
            H4(_('Manual closing of the referendum'), cls='center-text'),
            Div(
                P(_('This will stop the voting process and it can\'t be undone.')),
                cls='center-text body-2'),
            Form(
                CSRFInput(view.request),
                Div(
                    MDCButtonOutlined(_('close the referendum now'), False),
                    style='margin: 0 auto; width: fit-content',
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
                Span(_("Your privacy key is a file with '.pkl' extension."), cls='body-2'),
                MDCErrorList(form.non_field_errors()),
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
                context['form']['email_title'],
                context['form']['email_message'],
                MDCMultipleChoicesCheckbox(
                    'send_email',
                    ((0, B(_('Do not alert voters by email')), 'true'),),
                    n=1
                ),
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
            H4(_('Publish your referendum results'), cls='center-text'),
            Div(
                P(_('This will decentralize your referendum results.')),
                cls='center-text body-2'),
            Form(
                CSRFInput(view.request),
                Div(
                    MDCButton(_('publish results')),
                    style='width: fit-content; margin: 0 auto;'
                ),
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


class ArtifactsLinks(Div):
    def __init__(self, contest):
        links = Div(style=dict(display='flex', flex_flow='row nowrap', justify_content='space-around'))

        if contest.electioncontract.blockchain.explorer:
            links.addchild(
                Div(
                    A(_('Referendum report'), href=contest.electioncontract.explorer_link),
                    Br(),
                    _('On Tezos\' blockchain'),
                    style=dict(text_align='center', color='#888', margin='12px')
                )
            )

        if contest.plaintext_tally:
            links.addchild(
                Div(
                    A(_('Referendum datas'), href=contest.artifacts_local_url),
                    Br(),
                    _('Local data'),
                    style=dict(text_align='center', color='#888', margin='12px')
                )
            )

        if contest.artifacts_ipfs_url:
            links.addchild(
                Div(
                    A(_('Referendum datas'), href=contest.artifacts_ipfs_url),
                    Br(),
                    _('On IPFS, decentralized'),
                    style=dict(text_align='center', color='#888', margin='12px')
                )
            )

        super().__init__(links, style=dict(margin_top='32px'))


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
                score_percent = f'{round(score_percent, 2)} %'
            else:
                score_percent = '--'

            table_content.addchild(
                Tr(
                    Td(
                        num + candidate.name,
                        cls=cls,
                        style='word-break: break-all; white-space: normal'
                    ),
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

        about = mark_safe(escape(contest.about).replace('\n', '<br>'))

        return super().to_html(
            H4(_('Results'), cls='center-text'),
            Div(
                H5(contest.name, style='word-break: break-all'),
                Div(
                    about,
                    style='padding: 12px; word-break: break-all;',
                    cls='subtitle-2'
                ),
                publish_btn,
                score_table,
                cls='table-container score-table center-text'
            ),
            ArtifactsLinks(contest),
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


class AddRecommenderAction(ListAction):
    def __init__(self, obj):
        num_recommender = obj.contestrecommender_set.count()
        kwargs = dict(
            tag='a',
            href=reverse('contest_recommender_create', args=[obj.id]))
        if num_recommender:
            btn_comp = MDCButtonOutlined(_('edit'), False, **kwargs)
            icon = DoneIcon()
        else:
            btn_comp = MDCButtonOutlined(_('add'), False, 'add', **kwargs)
            icon = TodoIcon()

        infavour_recommender = obj.contestrecommender_set.filter(recommender_type='infavour').count()
        against_recommender = obj.contestrecommender_set.filter(recommender_type='against').count()
        # txt = _('%(candidates)d candidates, minimum: %(elected)d',
        #     n=against_recommender,
        #     candidates=infavour_recommender,
        #     elected=against_recommender
        # )
        txt = _('Infavour Recommenders, Against Recommenders')

        super().__init__(
            _('Add recommender'), txt, icon, btn_comp,
        )

class ContestRecommenderForm(Div):
    def __init__(self, form):
        self.form = form
        # self.count = 0
        # if form.instance and form.instance.recommender:
        #     self.count = len(form.instance.recommender)
        super().__init__(form)

    def init_counter(form_id, count):
        form = getElementByUuid(form_id)
        counter = form.querySelector('.mdc-text-field-character-counter')
        counter.innerHTML = count + '/300'

    def update_counter(event):
        field = event.currentTarget
        current_count = field.value.length
        if current_count > 300:
            field.value = field.value.substr(0, 300)
            current_count = 300
        parent = field.parentElement.parentElement.parentElement
        counter = parent.querySelector('.mdc-text-field-character-counter')
        counter.innerHTML = current_count + '/300'

    def py2js(self):
        self.init_counter(self.id, self.count)
        field = document.getElementById('id_description')
        field.addEventListener('keyup', self.update_counter)


@template('djelectionguard/recommender_form.html', Document, Card)
class ContestRecommenderCreateCard(Div):
    def to_html(self, *content, view, form, **context):
        contest = view.get_object()
        editable = (view.request.user == contest.mediator
                    and not contest.actual_start)
        self.backlink = BackLink(_('back'), reverse('contest_detail', args=[contest.id]))
        form_component = ''
        if editable:
            form_component = Form(
                ContestRecommenderForm(form),
                CSRFInput(view.request),
                MDCButton(_('Add recommender'), icon='person_add_alt_1'),
                method='POST',
                cls='form')
        count = contest.contestrecommender_set.count()
        return super().to_html(
            H4(
                _('%(count)s Recommeders', n=count, count=count),
                cls='center-text'
            ),
            RecommenderAccordion(contest, editable),
            H5(_('Add a recommender'), cls='center-text'),
            form_component,
            cls='card'
        )



@template('djelectionguard/recommender_update.html', Document, Card)
class ContestRecommenderUpdateCard(Div):
    def to_html(self, *content, view, form, **context):
        recommender = view.get_object()
        contest = recommender.contest
        self.backlink = BackLink(
            _('back'),
            reverse('contest_recommender_create', args=[contest.id]))
        delete_btn = MDCTextButton(
            _('delete'),
            'delete',
            tag='a',
            href=reverse('contest_recommender_delete', args=[recommender.id]))

        return super().to_html(
            H4(
                _('Edit recommender'),
                style='text-align: center;'
            ),
            Form(
                CSRFInput(view.request),
                ContestRecommenderForm(form),
                Div(
                    Div(delete_btn, cls='red-button-container'),
                    MDCButton(_('Save'), True),
                    style='display: flex; justify-content: space-between'),
                method='POST',
                cls='form'),
            cls='card'
        )

class RecommenderDetail(Div):
    def __init__(self, recommender, editable=False, **kwargs):
        if editable:
            kwargs['tag'] = 'a'
            kwargs['href'] = reverse('contest_recommender_update', args=[recommender.id])
            kwargs['style'] = 'margin-left: auto; margin-top: 12px;'

        extra_style = 'align-items: baseline;'
        content = []

        if recommender.recommender.picture:
            extra_style = ''
            content.append(
                Div(
                    Image(
                        loading='eager',
                        src=recommender.recommender.picture.url,
                        style='width: 100%;'
                              'display: block;'
                    ),
                    style='width: 150px; padding: 12px;'
                )
            )

        subcontent = Div(
            H5(
                recommender.recommender,
                style='margin-top: 6px; margin-bottom: 6px; word-break: break-all;'
            ),
            I(
                recommender.recommender,
                style=dict(
                    font_size='small',
                    font_weight='initial',
                    word_break='break-all',
                )
            ),
            style='flex: 1 1 65%; padding: 12px;'
        )

        if recommender.recommender_type:
            recommender_type = recommender.recommender_type
            subcontent.addchild(
                Div(
                    recommender_type,
                    style='margin-top: 24px; word-break: break-all;'
                )
            )

        content.append(subcontent)

        if editable and not recommender.recommender:
            content.append(
                MDCButtonOutlined(_('edit'), False, 'edit', **kwargs)
            )
        elif editable:
            subcontent.addchild(
                MDCButtonOutlined(_('edit'), False, 'edit', **kwargs)
            )

        if 'style' not in kwargs:
            kwargs['style'] = ''

        super().__init__(
            *content,
            style='padding: 12px;'
                  'display: flex;'
                  'flex-flow: row wrap;'
                  'justify-content: center;'
                  + kwargs.pop('style')
                  + extra_style,
            cls='recommender-detail',
        )

class RecommenderAccordionItem(MDCAccordionSection):
    tag = 'recommender-list-item'

    def __init__(self, recommender, editable=False):
        super().__init__(
            RecommenderDetail(recommender, editable),
            label=recommender.recommender,
        )


class RecommenderAccordion(MDCAccordion):
    tag = 'recommender-accordion'
    def __init__(self, contest, editable=False):
        super().__init__(
            *(
                RecommenderAccordionItem(recommender, editable)
                for recommender
                in contest.contestrecommender_set.all()
            ) if contest.contestrecommender_set.count()
            else [_('No recommender yet.')]
        )

class RecommenderListComp(MDCList):
    tag = 'recommender-list'
    def __init__(self, contest, editable=False):
        qs = contest.contestrecommender_set.all()[:]
        def recommenders(qs):
            for recommender in qs:
                attrs = dict()
                if editable:
                    attrs['tag'] = 'a'
                    attrs['href'] = reverse(
                        'contest_recommender_update',
                        args=[recommender.id]
                    )
                yield (recommender, attrs)

        super().__init__(
            *(
                MDCListItem(recommender, **attrs)
                for recommender, attrs in recommenders(qs)
            ) if qs.count()
            else [_('No recommender yet.')]
        )

class RecommendersSettingsCard(Div):
    def __init__(self, view, **context):
        contest = view.get_object()
        editable = (view.request.user == contest.mediator
                    and not contest.actual_start)
        kwargs = dict(p=False, tag='a')
        if contest.contestrecommender_set.count():
            if editable:
                kwargs['href'] = reverse('contest_recommender_create', args=[contest.id])
                btn = MDCButtonOutlined(_('view all/edit'), **kwargs)
            else:
                kwargs['href'] = reverse('contest_recommender_list', args=[contest.id])
                btn = MDCButtonOutlined(_('view all'), **kwargs)
        else:
            if editable:
                kwargs['href'] = reverse('contest_recommender_create', args=[contest.id])
                btn = MDCButtonOutlined(_('add'), icon='add', **kwargs)
            else:
                btn = None

        super().__init__(
            H5(_('Recommeders')),
            RecommenderListComp(contest, editable),
            btn,
            cls='setting-section'
        )




class ParentContestForm(forms.ModelForm):
    def now():
        now = datetime.now()
        return now.replace(second=0, microsecond=0)

    def tomorow():
        tomorow = datetime.now() + timedelta(days=1)
        return tomorow.replace(second=0, microsecond=0)

    start = forms.SplitDateTimeField(
        label='',
        initial=now,
        widget=forms.SplitDateTimeWidget(
            date_format='%Y-%m-%d',
            date_attrs={'type': 'date', 'label': 'date'},
            time_attrs={'type': 'time', 'label': 'heure'},
        ),
    )
    end = forms.SplitDateTimeField(
        label='',
        initial=tomorow,
        widget=forms.SplitDateTimeWidget(
            date_format='%Y-%m-%d',
            date_attrs={'type': 'date'},
            time_attrs={'type': 'time'},
        )
    )

    class Meta:
        model = ParentContest
        fields = [
            'name',
            'start',
            'end',
            'timezone',
        ]
        labels = {
            'name': _('FORM_TITLE_ELECTION_CREATE'),
            'start': _('FORM_START_ELECTION_CREATE'),
            'end': _('FORM_END_ELECTION_CREATE'),
            'timezone': _('FORM_TIMEZONE_ELECTION_CREATE')
        }


class ParentContestFormComponent(CList):
    def __init__(self, view, form, edit=False):
        content = []
        content.append(Ul(
            *[Li(e) for e in form.non_field_errors()],
            cls='error-list'
        ))

        super().__init__(
            H4(_('Edit referendum') if edit else _('Create a referendum')),
            Form(
                form['name'],
                H6(_('Referendum starts:')),
                form['start'],
                H6(_('Referendum ends:')),
                form['end'],
                form['timezone'],
                CSRFInput(view.request),
                MDCButton(_('update referendum') if edit else _('create referendum')),
                method='POST',
                cls='form'),
        )


@template('djelectionguard/parentcontest_form.html', Document, Card)
class ParentContestCreateCard(Div):
    style = dict(cls='card')

    def to_html(self, *content, view, form, **context):
        self.backlink = BackLink(_('back'), reverse('parentcontest_list'))

        edit = view.object is not None
        return super().to_html(
            ParentContestFormComponent(view, form, edit),
        )


class ParentContestFiltersBtn(Button):
    def __init__(self, pos, text, active=False):
        active_cls_name = 'mdc-tab--active' if active else ''
        active_indicator = 'mdc-tab-indicator--active' if active else ''

        attrs = {
            'class': f'parentcontest-filter-btn mdc-tab {active_cls_name}',
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


class ParentContestFilters(Div):
    def __init__(self, view):
        active_btn = view.request.GET.get('q', 'all')

        self.all_parentcontests_btn = ParentContestFiltersBtn(1, _('all'), active_btn == 'all')
        self.my_parentcontests_btn = ParentContestFiltersBtn(2, _('created by me'), active_btn == 'created')
        self.shared_parentcontests_btn = ParentContestFiltersBtn(3, _('shared with me'), active_btn == 'shared')

        super().__init__(
            Div(
                Div(
                    self.all_parentcontests_btn,
                    self.my_parentcontests_btn,
                    self.shared_parentcontests_btn,
                    cls='mdc-tab-scroller__scroll-content'
                ),
                cls='mdc-tab-scroller__scroll-area ' +
                    'mdc-tab-scroller__scroll-area--scroll'
            ),
            cls='mdc-tab-bar parentcontest-filter'
        )


class ParentContestItem(A):
    def __init__(self, parentcontest, user, *args, **kwargs):
        active_cls = ''
        status = ''
        status_2 = ''
        # voter = parentcontest.voter_set.filter(user=user).first()
        # voted = voter and voter.casted
        if parentcontest.actual_start:
            status = _('voting ongoing')
            active_cls = 'active'
        if parentcontest.actual_end:
            status = _('voting closed')
        # if parentcontest.plaintext_tally:
        #     active_cls = ''
        #     status = _('result available')

        super().__init__(
            Span(cls='mdc-list-item__ripple'),
            Span(
                Span(cls=f'parentcontest-indicator'),
                Span(
                    Span(status, status_2, cls='parentcontest-status overline'),
                    Span(parentcontest.name, cls='parentcontest-name'),
                    cls='list-item__text-container'
                ),
                cls='mdc-list-item__text'
            ),
            cls=f'parentcontest-list-item mdc-list-item mdc-ripple-upgraded {active_cls}',
            href=reverse('parentcontest_detail', args=[parentcontest.uid])
        )



class ParentContestListItem(ListItem):
    def __init__(self, obj, user, **kwargs):
        super().__init__(ParentContestItem(obj, user))


class ParentListAction(ListItem):
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


class ParentContestListCreateBtn(A):
    def __init__(self):
        super().__init__(
            Span(
                Span(cls='mdc-list-item__ripple'),
                Span(
                    Span('+', cls='new-parentcontest-icon'),
                    cls='new-parentcontest-icon-container'
                ),
                Span(_('Create new referendum')),
                cls='mdc-list-item__text text-btn mdc-ripple-upgraded'
            ),
            cls='mdc-list-item parentcontest-list-item',
            href=reverse('parentcontest_create')
        )


@template('djelectionguard/parentcontest_list.html', Document, Card)
class ParentContestList(Div):
    def to_html(self, *content, view, **context):
        site = Site.objects.get_current()
        can_create = (site.all_users_can_create
            or view.request.user.is_staff
            or view.request.user.is_superuser
        )
        return super().to_html(
            H4(_('Referendums'), style='text-align: center;'),
            # ContestFilters(view),
            Ul(
                ListItem(ParentContestListCreateBtn())
                if can_create else None,
                *(
                    ParentContestListItem(parentcontest, view.request.user)
                    for parentcontest in context['parentcontest_list']
                ) if len(context['parentcontest_list'])
                else (
                    Li(
                        _('There are no referendums yet'),
                        cls='mdc-list-item body-1'
                    ),
                ),
                cls='mdc-list parentcontest-list'
            ),
            cls='card'
        )


class ParentBasicSettingsAction(ListAction):
    def __init__(self, obj):
        btn_comp = MDCButtonOutlined(
            _('edit'),
            False,
            tag='a',
            href=reverse('parentcontest_update', args=[obj.uid]))
        super().__init__(
            _('Basic settings'),
            _('Name, votes allowed, time and date, etc.'),
            DoneIcon(), btn_comp
        )

class AddIssuesAction(ListAction):
    def __init__(self, obj):
        btn_comp = MDCButtonOutlined(
            _('edit'),
            False,
            tag='a',
            href=reverse('contest_list'))
        super().__init__(
            _('Add Issues'),
            _('Name, votes allowed, time and date, etc.'),
            DoneIcon(), btn_comp
        )

class ParentContestSettingsCard(Div):
    def __init__(self, view, **context):
        parentcontest = view.get_object()
        user = view.request.user
        list_content = []
        # if contest.mediator == view.request.user:
        list_content += [
            ParentBasicSettingsAction(parentcontest),
            AddIssuesAction(parentcontest)
        ]

        #     if (
        #         contest.voter_set.count()
        #         and contest.candidate_set.count()
        #         and contest.candidate_set.count() > contest.number_elected
        #     ):
        #         if contest.publish_state != contest.PublishStates.ELECTION_NOT_DECENTRALIZED:
        #             list_content.append(SecureElectionAction(contest, user))
        # else:
        #     list_content.append(SecureElectionAction(contest, user))

        # about = mark_safe(escape(contest.about).replace('\n', '<br>'))

        super().__init__(
            H4(parentcontest.name, style='word-break: break-all;'),
            Div(
                parentcontest.name,
                style='padding: 12px; word-break: break-all;',
                cls='subtitle-2'
            ),
            Ul(
                *list_content,
                cls='mdc-list action-list'
            ),
            cls='setting-section main-setting-section'
        )

class IssuesSettingsCard(Div):
    def __init__(self, view, **context):
        parentcontest = view.get_object()
        user = view.request.user
        list_content = []
        # if contest.mediator == view.request.user:
        list_content += [
            ParentBasicSettingsAction(parentcontest),
            # AddIssuesAction(parentcontest)
        ]

        super().__init__(
            H4(parentcontest.name, style='word-break: break-all;'),
            Div(
                parentcontest.name,
                style='padding: 12px; word-break: break-all;',
                cls='subtitle-2'
            ),
            Ul(
                *list_content,
                cls='mdc-list action-list'
            ),
            cls='setting-section main-setting-section'
        )


@template('djelectionguard/parentcontest_detail.html', Document)
class ParentContestCard(Div):
    def to_html(self, *content, view, **context):
        parentcontest = view.get_object()
        # if parentcontest.status == 'closed':
        #     main_section = ContestFinishedCard(view, **context)
        # elif parentcontest.status == 'open':
        #     main_section = ContestVotingCard(view, **context)
        # else:
        #     main_section = ContestSettingsCard(view, **context)

        main_section = ParentContestSettingsCard(view, **context)

        action_section = Div(
            main_section,
            cls='main-container')
        sub_section = Div(
            IssuesSettingsCard(view, **context),
            cls='side-container')

        # if (
        #     contest.mediator == view.request.user
        #     or contest.guardian_set.filter(user=view.request.user).count()
        # ):
        #     action_section.addchild(GuardiansSettingsCard(view, **context))

        # if contest.mediator == view.request.user:
            # sub_section.addchild(VotersSettingsCard(view, **context))
        # sub_section.addchild(RecommendersSettingsCard(view, **context))


        return super().to_html(
            Div(
                Div(
                    BackLink(_('my elections'), reverse('contest_list')),
                    cls='main-container'),
                Div(cls='side-container'),
                action_section,
                # sub_section,
                cls='flex-container'
            )
        )
