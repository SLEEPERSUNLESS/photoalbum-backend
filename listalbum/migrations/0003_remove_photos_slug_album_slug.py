# Generated by Django 5.1.7 on 2025-04-01 06:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('listalbum', '0002_photos_slug'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='photos',
            name='slug',
        ),
        migrations.AddField(
            model_name='album',
            name='slug',
            field=models.SlugField(blank=True, max_length=255, null=True, unique=True),
        ),
    ]
