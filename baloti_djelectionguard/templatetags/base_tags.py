from django import template
from electeez_common.settings import BASE_URL

register = template.Library()

@register.simple_tag
def getOGImage():
    print('BASE_URL======================', BASE_URL)
    thumbnail_url = BASE_URL + '/static/images/thumbnail.png'
    print('thumbnail_url======================', thumbnail_url)
    return thumbnail_url