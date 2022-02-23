from django import template
from djelectionguard.models import Contest, Voter
from django.db.models import Sum

register = template.Library()

@register.simple_tag
def displayBalotiResult(contest, user):
    votes = contest.candidate_set.aggregate(total=Sum('score'))
    yes = 0
    no = 0
    yes_score = 0
    no_score = 0
    for i, yes_candidate in enumerate(contest.candidate_set.filter(candidate_type='yes').order_by('-score')):
        yes_score = yes_candidate.score

    for i, no_candidate in enumerate(contest.candidate_set.filter(candidate_type='no').order_by('-score')):
        no_score = no_candidate.score

    if (yes_score + no_score) > 0:
        yes = 100 * yes_score / (yes_score + no_score)
        yes = round(yes, 2)
        no = 100 * no_score / (yes_score + no_score)
        no = round(no, 2)

    if yes > no:
        baloti_result = yes_candidate
        result_label = 'yes'
    elif yes < no:
        baloti_result = no_candidate
        result_label = 'no'
    else:
        baloti_result = 'no'
        result_label = ''
    return yes, no, baloti_result, result_label

@register.simple_tag
def displayGovtResult(contest, user):
    votes = contest.candidate_set.aggregate(total=Sum('score'))
    yes = contest.govt_infavour_percent or 0
    no = contest.govt_against_percent or 0
    result = 'no'
    if yes and no:
        if yes > no:
            result = 'yes'
        elif yes < no:
            result = 'no'
        else:
            result = 'no'
    return yes, no, result
