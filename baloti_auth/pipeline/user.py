from django.http import HttpResponseRedirect
from django.urls import reverse
import urllib

# This is initially from https://github.com/python-social-auth/social-core/blob/master/social_core/pipeline/user.py
def get_username(strategy, details, backend, user=None, *args, **kwargs):
    # Get the logged in user (if any)
    logged_in_user = strategy.storage.user.get_username(user)

    # Custom: check for email being provided
    if not details.get('email'):
        error = "Sorry, but your social network (Facebook or Google) needs to provide us your email address."
        return HttpResponseRedirect(reverse('repairs-social-network-error') + "?error=" + urllib.quote_plus(error))

    # Custom: if user is already logged in, double check his email matches the social network email
    if logged_in_user:
        if logged_in_user.lower() != details.get('email').lower():
            error = "Sorry, but you are already logged in with another account, and the email addresses do not match. Try logging out first, please."
            return HttpResponseRedirect(reverse('repairs-social-network-error') + "?error=" + urllib.quote_plus(error))

    return {
        'username': details.get('email').lower(),
    }