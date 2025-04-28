from django import template
from electeez_common.settings import BASE_URL
import json
import ast

register = template.Library()

@register.simple_tag
def getOGImage():
    print('BASE_URL======================', BASE_URL)
    thumbnail_url = BASE_URL + '/static/images/thumbnail.png'
    print('thumbnail_url======================', thumbnail_url)
    return thumbnail_url

@register.simple_tag
def displayLanguageCode(code):
    with open("baloti_djelectionguard/static/languages.json") as data_file:
        myJson = data_file.read()
        myJson = ast.literal_eval(myJson)
        if code in myJson:
            code = myJson[code][0]['display_code']
    return code

@register.simple_tag
def displayLanguageName(code, name):
    with open("baloti_djelectionguard/static/languages.json") as data_file:
        myJson = data_file.read()
        myJson = ast.literal_eval(myJson)
        if code in myJson:
            name = myJson[code][0]['display_name']
    return name