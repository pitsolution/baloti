from django import template
from djelectionguard.models import Contest, Voter
from django.db.models import Sum

register = template.Library()

@register.simple_tag
def displayIssuesCount(contest, user):
    issues = Contest.objects.filter(parent=contest)
    return len(issues)

@register.filter
def getContestIssues(value):
    issues = Contest.objects.filter(parent=value)
    return issues

@register.simple_tag
def checkIssueVotingStatus(contest, user):
    contest = Contest.objects.filter(id=contest.id).first()
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
    if not user.is_anonymous and contest.actual_start and not contest.actual_end:
        voter = contest.voter_set.filter(user=user).first()
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
    contest = Contest.objects.filter(id=contest.id).first()
    if contest.candidate_set.aggregate(total=Sum('score'))['total'] == None:
        return False
    return True
