from django import template
from djelectionguard.models import Contest, Voter
from django.db.models import Sum

register = template.Library()

@register.simple_tag
def checkResultStatus(contest, user):
    issues = Contest.objects.filter(parent=contest)
    for issue in issues:
        if issue.candidate_set.aggregate(total=Sum('score'))['total'] == None:
            return False
    return True

@register.simple_tag
def checkVotingStatus(contest, user):
    action = ''
    issues = Contest.objects.filter(parent=contest)
    if not user.is_anonymous:
        for issue in issues:
            voter = issue.voter_set.filter(user=user)
            if voter and voter.first().casted and action != True:
                action = False
            else:
                action = True
    else:
        action = True
    return action

@register.simple_tag
def displayIssuesCount(contest, user):
    issues = Contest.objects.filter(parent=contest)
    return len(issues)

@register.filter
def getContestIssues(value):
    issues = Contest.objects.filter(parent=value)
    return issues
