from django.urls import path
from .views import *
from baloti_auth.forms import UserLoginForm
from django.contrib.auth.views import LogoutView, PasswordChangeView, PasswordChangeDoneView

urlpatterns = [
    path('login/', BalotiLoginView.as_view(
                    template_name="login.html",
                    authentication_form=UserLoginForm
                    ), name='login'),
    path('logout/', LogoutView.as_view(
                    ), name='logout'),
    path('signup/', BalotiSignupView.as_view(
        ), name="signup"),
    path('signup/mailsent/', BalotiSignupMailView.as_view(
        ), name="signup_mail"),
    path('modalsignup/mailsent/', BalotiModalSignupMailView.as_view(
        ), name="modalsignup_mail"),
    path(
        'change-password/',
        BalotiPasswordChangeView.as_view(
            template_name='change_password.html',
            success_url = '/en/baloti/contest/list/'
        ),
        name='change-password'
    ),
    # path('password_change/done/',
    #      PasswordChangeDoneView.as_view(template_name="change_password.html"),
    #      name='password_change_done'),
]
