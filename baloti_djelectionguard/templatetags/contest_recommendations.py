from django import template
from djelectionguard.models import ContestRecommender
from ..models import Recommenderi18n
from django.utils.translation import get_language

register = template.Library()

@register.filter
def getInfavourRecommenders(value):
    recommender_list = []
    current_language = get_language()
    contestrecommenders = ContestRecommender.objects.filter(
            contest=value,
            recommender_type='infavour'
            ).distinct('id')
    for record in contestrecommenders:
        recommender_list.append(record.recommender.id)
    recommenders = Recommenderi18n.objects.filter(recommender_id__in=recommender_list, language__iso=current_language)
    return recommenders

@register.filter
def getAgainstRecommenders(value):
    recommender_list = []
    current_language = get_language()
    contestrecommenders = ContestRecommender.objects.filter(
            contest=value,
            recommender_type='against'
            ).distinct('id')
    for record in contestrecommenders:
        recommender_list.append(record.recommender.id)
    recommenders = Recommenderi18n.objects.filter(recommender_id__in=recommender_list, language__iso=current_language)
    return recommenders
