from django.urls import path
from ..views import *

app_name = "baloti_djelectionguard"
urlpatterns = [
    path('illustrations', BalotiNewsView.as_view()),
    path('imprint', BalotiImprintView.as_view(), name="imprint"),
    path('data-privacy', BalotiDataPrivacyView.as_view(), name="data-privacy"),
    path('disclaimer', BalotiDisclaimerView.as_view()),
    path('about-us', BalotiAboutUsView.as_view()),
    path('', BalotiInfoView.as_view()),
    path('info/', BalotiInfoView.as_view()),
    path('info/submit', BalotiInfoView.as_view(), name='info'),
]
