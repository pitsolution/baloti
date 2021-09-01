import json

from django.http import JsonResponse
from django.urls import path

from .models import Text


def text_view(request):
    data = list(Text.objects.values())
    return JsonResponse(data, safe=False)


urlpatterns = [
    path('', text_view, name='text')
]
