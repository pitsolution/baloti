from django.urls import include, path
from django.conf.urls import url

from electeez_auth.views import (
    LogoutRView,
    EmailLoginRView,
    RegistrationRView,
    RegistrationCompleteRView,
    PasswordResetRView,
    PasswordResetDoneRView
)

urlpatterns = [
    url(r'login/?$', EmailLoginRView.as_view, name='login'),
    url(r'logout/?$', LogoutRView.as_view, name='logout'),
    url(r'register/?$', RegistrationRView.as_view, name='signup'),
    url(r'register/complete/?$', RegistrationCompleteRView.as_view, name='signup_complete'),
    url(r'password_reset/?$', PasswordResetRView.as_view, name='password_reset'),
    url(r'password_reset/done/?$', PasswordResetDoneRView.as_view, name='password_reset_done'),
    url(r'', include('django_registration.backends.activation.urls')),
    path('', include('django.contrib.auth.urls')),
]
