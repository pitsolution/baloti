from django.contrib.auth.forms import AuthenticationForm
from django import forms

class UserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs)

    username = forms.EmailField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': '', 'id': 'hello'}))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={
            'class': 'form-control',
            'placeholder': '',
            'id': 'hi',
        }
    ))

from django.contrib.auth.models import User

class ChangePasswordForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['old_password', 'confirm_password', 'password']

    old_password = forms.CharField(label='Oldpassword', widget=forms.PasswordInput(attrs={'placeholder': 'Password:'}))
    confirm_password = forms.CharField(label='ConfirmPassword', widget=forms.PasswordInput(attrs={'placeholder': 'Password:'}))
    password = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'placeholder': 'Password:'}))