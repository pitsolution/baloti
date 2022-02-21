from django import template
from djelectionguard.models import Contest, Voter
from django.db.models import Sum

register = template.Library()


@register.simple_tag
def checkReferendumResultPublished(contest, user):
    issues = Contest.objects.filter(parent=contest)
    for issue in issues:
        if issue.candidate_set.aggregate(total=Sum('score'))['total'] == None:
            return False
    return True

@register.simple_tag
def checkReferendumVotingStatus(contest, user):
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
def getReferendumIssues(contest):
    child_contests = Contest.objects.filter(
                parent=contest.first()
                ).distinct('id')
    return child_contests.count()
   

@register.simple_tag
def getUserVotedData(contest, user):
    if user.is_anonymous:
        voted_count = 0
        non_voted_count = 0
        voted_percent = 0
        non_voted_percent = 0
    else:
        child_contests = Contest.objects.filter(
                parent=contest
                ).distinct('id')
        voted_count =  Voter.objects.filter(contest__in=child_contests, user=user, casted=True).count()
        non_voted_count = child_contests.count() - voted_count
        total_count = voted_count + non_voted_count
        voted_percent = (voted_count/total_count) * 100 if (total_count != 0) else 0
        non_voted_percent = (non_voted_count/total_count) * 100 if (total_count != 0) else 0
    return voted_count, non_voted_count, voted_percent, non_voted_percent