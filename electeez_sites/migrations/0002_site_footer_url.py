# Generated by Django 3.1 on 2021-09-09 07:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('electeez_sites', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='site',
            name='footer_url',
            field=models.CharField(default='https://electis.app', max_length=255),
        ),
    ]
