from django.urls import include, path
from django_registration.forms import RegistrationForm
from django_registration.backends.activation.views import RegistrationView

from .models import User


class EmailRegistrationForm(RegistrationForm):
    class Meta(RegistrationForm.Meta):
        model = User


urlpatterns = [
    path('register/',
        RegistrationView.as_view(
            form_class=EmailRegistrationForm,
        ),
        name='django_registration_register',
    ),
    path('', include('django_registration.backends.activation.urls')),
    path('', include('django.contrib.auth.urls')),
]
