from django.db import models
from djelectionguard.models import ParentContest, Contest, Initiator, ContestType, Recommender
from djlang.models import Language
from ckeditor.fields import RichTextField


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

    def __str__(self):
        return self.name

class Initiatori18n(models.Model):
    name = models.CharField(max_length=255)
    initiator_id = models.ForeignKey(
        Initiator,
        related_name='initiator',
        on_delete=models.CASCADE,
        null=True
    )
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now_add=True, null=True)
    language = models.ForeignKey(
        Language,
        related_name='initiator',
        on_delete=models.CASCADE,
        null=True
    )

    def __str__(self):
        return self.name

class ContestTypei18n(models.Model):
    name = models.CharField(max_length=255)
    contest_type_id = models.ForeignKey(
        ContestType,
        related_name='contest_type',
        on_delete=models.CASCADE,
        null=True
    )
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now_add=True, null=True)
    language = models.ForeignKey(
        Language,
        related_name='contest_type',
        on_delete=models.CASCADE,
        null=True
    )

    def __str__(self):
        return self.name

class Recommenderi18n(models.Model):
    name = models.CharField(max_length=255)
    recommender_type = models.CharField(max_length=255, blank=True)
    recommender_id = models.ForeignKey(
        Recommender,
        related_name='recommender',
        on_delete=models.CASCADE,
        null=True
    )
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now_add=True, null=True)
    language = models.ForeignKey(
            Language,
            related_name='recommender',
            on_delete=models.CASCADE,
            null=True
        )

    def __str__(self):
        return self.name


class Contesti18n(models.Model):
    name = models.CharField(max_length=255)
    contest_id = models.ForeignKey(
        Contest,
        related_name='contest_data',
        on_delete=models.CASCADE,
        null=True
    )
    about = models.CharField(
        max_length=2048,
        blank=True,
        null=True
    )
    type = models.CharField(default='school', max_length=100)
    decrypting = models.BooleanField(default=False)
    parent = models.ForeignKey(
        ParentContest,
        related_name='parent_con',
        on_delete=models.CASCADE,
        null=True
    )
    infavour_arguments = RichTextField(
        null=True
    )
    against_arguments = RichTextField(
        null=True
    )
    language = models.ForeignKey(
        Language,
        related_name='contest',
        on_delete=models.CASCADE,
        null=True
    )

    def __str__(self):
        return self.name
