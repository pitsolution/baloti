# Generated by Django 3.1.7 on 2021-04-21 11:57

from django.db import migrations, models
import timezone_field.fields


class Migration(migrations.Migration):

    dependencies = [
        ('djelectionguard', '0020_optional_about_field'),
    ]

    operations = [
        migrations.AlterField(
            model_name='candidate',
            name='description',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
