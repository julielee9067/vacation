# Generated by Django 3.0.2 on 2020-01-04 12:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="attendance",
            options={"verbose_name": "출근기록", "verbose_name_plural": "출근기록"},
        ),
    ]
