# Generated by Django 3.1.4 on 2021-03-19 06:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('djelectionguard', '0012_open_close_email_datetime'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contest',
            name='number_elected',
        ),
    ]
