from django import template
from djelectionguard.models import Contest, Voter
from ..models import Contesti18n
from django.db.models import Sum
from django.utils.translation import get_language

register = template.Library()

@register.simple_tag
def displayIssuesCount(contest, user):
    issues = Contest.objects.filter(parent=contest)
    return len(issues)

@register.filter
def getContestIssues(value):
    current_language = get_language()
    issues = Contesti18n.objects.filter(parent=value, language__iso=current_language)
    return issues

@register.simple_tag
def checkIssueVotingStatus(contest, user):
    contest = Contest.objects.filter(id=contest.contest_id.id).first()
    if not contest.actual_start or not contest.parent.actual_start:
        return False
    if contest.actual_end or contest.parent.actual_end:
        return False
    if not user.is_anonymous:
        voter = contest.voter_set.filter(user=user).first()
        if voter and voter.casted:
            return False
    return True

@register.simple_tag
def displayIssueVotedFlag(contest, user):
    if not user.is_anonymous and contest.contest_id.actual_start and not contest.contest_id.actual_end:
        voter = contest.contest_id.voter_set.filter(user=user).first()
        if voter and voter.casted:
            return True
    return False

@register.simple_tag
def displayReferendumVotedFlag(contest, user):
    if not user.is_anonymous:
        issues = Contest.objects.filter(parent=contest)
        for issue in issues:
            voter = issue.voter_set.filter(user=user).first()
            if voter and voter.casted:
                pass
            else:
                return False
        return True
    return False

@register.simple_tag
def displayIssueViewResult(contest, user):
    contest = Contest.objects.filter(id=contest.contest_id.id).first()
    if contest.candidate_set.aggregate(total=Sum('score'))['total'] == None:
        return False
    return True
