from django import template
from djelectionguard.models import Contest, Voter
from django.db.models import Sum

register = template.Library()

@register.simple_tag
def displayResult(contest, user):
    votes = contest.candidate_set.aggregate(total=Sum('score'))
    yes = 0
    no = 0
    for i, yes_candidate in enumerate(contest.candidate_set.filter(candidate_type='yes').order_by('-score')):
        num = f'{i + 1}. '
        if votes['total']:
            yes = 100 * yes_candidate.score / votes['total']
            yes = round(yes)

    for i, no_candidate in enumerate(contest.candidate_set.filter(candidate_type='no').order_by('-score')):
        num = f'{i + 1}. '
        if votes['total']:
            no = 100 * no_candidate.score / votes['total']
            no = round(no)
            
    if yes > no:
        baloti_result = yes_candidate
    elif yes < no:
        baloti_result = no_candidate
    else:
        baloti_result = None

    return yes, no, baloti_result
