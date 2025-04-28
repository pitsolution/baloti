from django.contrib.auth.forms import AuthenticationForm
from django import forms
from django.contrib.auth.forms import (
   SetPasswordForm,
)
from django.utils.translation import gettext, gettext_lazy as _


class LoginForm(forms.Form):
    username = forms.CharField(max_length=63)
    password = forms.CharField(max_length=63, widget=forms.PasswordInput)


class PasswordChangeForm(SetPasswordForm):
    """
    A form that lets a user change their password by entering their old
    password.
    """
    error_messages = {
        **SetPasswordForm.error_messages,
        'password_incorrect': _("Your old password was entered incorrectly. Please enter it again."),
    }