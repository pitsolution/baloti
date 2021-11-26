from django import template
from djelectionguard.models import ContestRecommender

register = template.Library()

@register.filter
def getInfavourRecommenders(value):
    recommenders = ContestRecommender.objects.filter(
            contest=value,
            recommender_type='infavour'
            ).distinct('id')
    return recommenders

@register.filter
def getAgainstRecommenders(value):
    recommenders = ContestRecommender.objects.filter(
            contest=value,
            recommender_type='against'
            ).distinct('id')
    return recommenders
