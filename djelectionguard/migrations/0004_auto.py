# Generated by Django 3.1.4 on 2021-01-26 09:37

from django.db import migrations, models
import djelectionguard.models


class Migration(migrations.Migration):

    dependencies = [
        ('djelectionguard', '0003_positiveintegers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contest',
            name='voters_emails',
            field=models.TextField(blank=True, help_text='The list of allowed voters with one email per line'),
        ),
        migrations.AlterField(
            model_name='guardian',
            name='downloaded',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='guardian',
            name='erased',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='guardian',
            name='uploaded',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='guardian',
            name='uploaded_erased',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='guardian',
            name='verified',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
