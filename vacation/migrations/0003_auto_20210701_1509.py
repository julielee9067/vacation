# Generated by Django 3.0.2 on 2021-07-01 06:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vacation", "0002_auto_20210701_1357"),
    ]

    operations = [
        migrations.AlterField(
            model_name="vacation",
            name="cat",
            field=models.CharField(
                choices=[("1", "연차/휴가"), ("2", "병가")], default="1", max_length=1
            ),
        ),
    ]