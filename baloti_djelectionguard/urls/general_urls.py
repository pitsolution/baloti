from django.urls import path
from ..views import *

app_name = "balotidjelectionguard"
urlpatterns = [
    path('illustrations', BalotiNewsView.as_view(), name='Illustration'),
    path('imprint', BalotiImprintView.as_view(), name="imprint"),
    path('data-privacy', BalotiDataPrivacyView.as_view(), name="data-privacy"),
    path('disclaimer', BalotiDisclaimerView.as_view(), name='Disclaimer'),
    # path('about-us', BalotiAboutUsView.as_view()),
    path('', BalotiInfoView.as_view()),
    path('info/', BalotiInfoView.as_view()),
    path('info/submit', BalotiInfoView.as_view(), name='info'),
]
