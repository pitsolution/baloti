from django.urls import path
from .views import *

urlpatterns = [
    path('disclaimer', baloti_disclaimer, name='baloti_disclaimer'),
]