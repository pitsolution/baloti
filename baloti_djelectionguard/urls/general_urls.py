from django.urls import path
from ..views import *

urlpatterns = [
    path('news', BalotiNewsView.as_view()),
    path('disclaimer', BalotiDisclaimerView.as_view()),
    path('about-us', BalotiAboutUsView.as_view()),
    path('info/', BalotiInfoView.as_view()),
    path('info/submit', BalotiInfoView.as_view(), name='info'),
]
