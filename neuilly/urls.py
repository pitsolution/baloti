from electeez_common.urls import *


class LegalView(generic.TemplateView):
    template_name = 'legal'


class DataPolicyView(generic.TemplateView):
    template_name = 'policy'


class CookieView(generic.TemplateView):
    template_name = 'cookies'


class FAQView(generic.TemplateView):
    template_name = 'faq'


urlpatterns += i18n_patterns(
    path('legal/', LegalView.as_view(), name='legal'),
    path('policy/', DataPolicyView.as_view(), name='policy'),
    path('cookies/', CookieView.as_view(), name='cookies'),
    path('faq/', FAQView.as_view(), name='faq'),
)
