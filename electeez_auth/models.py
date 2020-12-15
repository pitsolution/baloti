from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import signals


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    username = None
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )


def user_voter(sender, instance, created, **kwargs):
    if not created:
        return
    from djelectionguard.models import Contest
    contests = Contest.objects.filter(voters_emails__icontains=instance.email)
    for contest in contests:
        contest.voter_set.create(user=instance)
signals.post_save.connect(user_voter, sender=User)
