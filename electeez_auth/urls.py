from django.urls import include, path
from django.conf.urls import url

from electeez_auth.views import (
    LogoutView,
    EmailLoginView,
    RegistrationView,
    RegistrationCompleteView,
    PasswordResetView,
    PasswordResetDoneView,
    ActivationCompleteView,
    ActivationFailureView,
)

urlpatterns = [
    path('login/', EmailLoginView.as_view, name='login'),
    path('logout/', LogoutView.as_view, name='logout'),
    path('register/', RegistrationView.as_view, name='signup'),
    path('register/complete/', RegistrationCompleteView.as_view, name='signup_complete'),
    path('password_reset/', PasswordResetView.as_view, name='password_reset'),
    path('password_reset/done/', PasswordResetDoneView.as_view, name='password_reset_done'),
    path('activate/complete/', ActivationCompleteView.as_view, name='django_registration_activation_complete'),
    path('activate/<str:activation_key>/', ActivationFailureView.as_view, name='django_registration_activate'),
    path('', include('django_registration.backends.activation.urls')),
    path('', include('django.contrib.auth.urls')),
]
