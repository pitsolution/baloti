from django.urls import path
from .views import *
from django.contrib.auth.views import LogoutView, PasswordChangeView, PasswordChangeDoneView

urlpatterns = [
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
        PasswordChangeView.as_view(
            template_name='change_password.html',
            success_url = '/baloti/success/changepassword'
        ),
        name='change-password'
    ),
    path('login/', BalotiLoginView.as_view(
        ), name="login"),

]
