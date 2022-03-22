from django.db import models

class BalotiUser(models.Model):
    STATUS = (
        ('draft', 'DRAFT'),
        ('done', 'DONE')
    )

    username = models.CharField(max_length=63)
    password = models.CharField(max_length=63)
    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default='draft',
        null=True
    )

    def __str__(self):
        return self.username
