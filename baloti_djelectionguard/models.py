from django.db import models
from djelectionguard.models import ParentContest, Contest
from djlang.models import Language

# Create your models here.


class ParentContesti18n(models.Model):

    STATUS = (
        ('draft', 'DRAFT'),
        ('open', 'OPEN'),
        ('closed', 'CLOSED')
    )
    parent_contest_id = models.ForeignKey(
        ParentContest,
        related_name='parent_contest',
        on_delete=models.CASCADE,
        null=True
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default='draft',
        null=True
    )
    language = models.ForeignKey(
        Language,
        related_name='parent_contest',
        on_delete=models.CASCADE,
        null=True
    )
