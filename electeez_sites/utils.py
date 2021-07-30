from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from .models import Site


def create_access_required(*args, **kwargs):
    try:
        site = Site.objects.get_current()
    except Exception:
        return staff_member_required(*args, **kwargs)

    if site.all_users_can_create:
        return login_required(*args, **kwargs)
    return staff_member_required(*args, **kwargs)


def result_access_required(*args, **kwargs):
    return True
