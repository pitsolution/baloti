from django.urls import include, path
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls import url

from .views import OTPEmailSuccess, OTPLogin, OTPSend

from .components import *


urlpatterns = [
    path('otp/success/', OTPEmailSuccess.as_view(), name='otp_email_success'),
    path('otp/<token>/', OTPLogin.as_view(), name='otp_login'),
    path('otp/', OTPSend.as_view(), name='otp_send'),
        path('', include('django_registration.backends.activation.urls')),
    path('', include('django.contrib.auth.urls'))
]