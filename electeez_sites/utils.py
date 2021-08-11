from functools import wraps
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import resolve_url

from .models import Site


def site_passes_test():
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            site = Site.objects.get_current()
            url = resolve_url(settings.LOGIN_URL)
            if user.is_authenticated:
                if (site.all_users_can_create
                        or user.is_staff
                        or user.is_superuser):
                    return view_func(request, *args, **kwargs)
                else:
                    url = resolve_url('admin:login')

            from django.contrib.auth.views import redirect_to_login
            path = request.get_full_path()
            return redirect_to_login(path, url, REDIRECT_FIELD_NAME)
        return _wrapped_view
    return decorator


def create_access_required(function):
    try:
        Site.objects.clear_cache()
        site = Site.objects.get_current()
    except Exception:
        return staff_member_required(function)

    actual_decorator = site_passes_test()
    return actual_decorator(function)


def result_access_required(*args, **kwargs):
    return True
