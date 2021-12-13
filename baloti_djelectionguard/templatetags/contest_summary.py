from django import template
from djelectionguard.models import Contest, Voter

register = template.Library()

@register.simple_tag
def displayVoteNow(contest, user):
    contest = Contest.objects.filter(id=contest.id).first()
    if not contest.actual_start or not contest.parent.actual_start:
        return False
    if not user.is_anonymous:
        voter = contest.voter_set.filter(user=user).first()
        if voter and voter.casted:
            return False
    return True

@register.simple_tag
def getContestIssues(contest):
    child_contests = Contest.objects.filter(
                parent=contest.first()
                ).distinct('id')
    return child_contests.count()
   
@register.simple_tag
def getContestVoted(contest, user):
    child_contests = Contest.objects.filter(
                parent=contest.first()
                ).distinct('id')
    return Voter.objects.filter(contest__in=child_contests, user=user, casted=True).count()

@register.simple_tag
def getContestNotVoted(contest, user):
    child_contests = Contest.objects.filter(
                parent=contest.first()
                ).distinct('id')
    voters =  Voter.objects.filter(contest__in=child_contests, user=user, casted=True).count()
    return child_contests.count() - voters