# Generated by Django 4.1 on 2023-05-04 20:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0002_facultyreviewroom"),
    ]

    operations = [
        migrations.AddField(
            model_name="review",
            name="team_progress_open",
            field=models.BooleanField(default=True),
        ),
    ]
