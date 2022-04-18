from django.urls import path
from .views import *
from django.contrib.auth import views as auth_views

app_name = "baloti_auth"
urlpatterns = [
    path('login/', BalotiLoginView.as_view(
        ), name="login"),
    path('logout/', auth_views.LogoutView.as_view(
                    ), name='logout'),
    path('signup/', BalotiSignupView.as_view(
        ), name="signup"),
    path('signup/mailsent/', BalotiSignupMailView.as_view(
        ), name="signup_mail"),
    path('modalsignup/mailsent/', BalotiModalSignupMailView.as_view(
        ), name="modalsignup_mail"),
    path(
        'change-password/',
        auth_views.PasswordChangeView.as_view(
            template_name='change_password.html',
            success_url = '/baloti/success/changepassword'
        ),
        name='change-password'
    ),
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='password_reset.html',
             email_template_name='password_reset_email.html',
             html_email_template_name="password_reset_email.html",
             success_url='/baloti/password-reset/done/'
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='password_reset_confirm.html',
             success_url='/baloti/password-reset/complete/'
         ),
         name='password_reset_confirm'),
    path('password-reset/complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='password_reset_complete.html'
         ),
         name='password_reset_complete'),
    path('delete/profile', BalotiDeleteProfileView.as_view(), name='deleteProfile'),
]
