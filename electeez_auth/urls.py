from django.urls import include, path
from django.conf.urls import url

from electeez_auth.views import (
    LogoutView,
    EmailLoginView,
    RegistrationView,
    RegistrationCompleteView,
    PasswordResetView,
    PasswordResetDoneView
)

urlpatterns = [
    path('login/', EmailLoginView.as_view, name='login'),
    path('logout/', LogoutView.as_view, name='logout'),
    path('register/', RegistrationView.as_view, name='signup'),
    path('register/complete/', RegistrationCompleteView.as_view, name='signup_complete'),
    path('password_reset/', PasswordResetView.as_view, name='password_reset'),
    path('password_reset/done/', PasswordResetDoneView.as_view, name='password_reset_done'),
    path('', include('django_registration.backends.activation.urls')),
    path('', include('django.contrib.auth.urls')),
]
