from functools import wraps
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from .models import Site


def site_passes_test(test_func):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_decorator(view_func):
            if test_func(request.user, Site.get_current()):
                return login_required(view_func)
            return staff_member_required(view_func)
        return _wrapped_decorator
    return decorator


def create_access_required(function):
    try:
        Site.objects.clear_cache()
        site = Site.objects.get_current()
    except Exception:
        return staff_member_required(*args, **kwargs)

    actual_decorator = site_passes_test(
        lambda s: s.all_users_can_create
    )

    return actual_decorator(function)


def result_access_required(*args, **kwargs):
    return True
