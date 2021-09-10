import json

from django.http import HttpResponse
from django.urls import path

from .models import Text


def text_view(request):
    data = list(Text.objects.order_by('id', 'key').distinct('id', 'key').values())
    return HttpResponse(json.dumps(data, ensure_ascii=False), content_type='application/json')


urlpatterns = [
    path('', text_view, name='text')
]
