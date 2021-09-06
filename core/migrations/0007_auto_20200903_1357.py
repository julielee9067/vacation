# Generated by Django 3.0.2 on 2020-09-03 04:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_profile_vacation_days"),
    ]

    operations = [
        migrations.RenameField(
            model_name="profile",
            old_name="vacation_days",
            new_name="total_days",
        ),
        migrations.AddField(
            model_name="profile",
            name="used_days",
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]