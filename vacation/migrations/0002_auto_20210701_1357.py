# Generated by Django 3.0.2 on 2021-07-01 04:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vacation", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="vacation",
            name="approval",
            field=models.CharField(
                choices=[("0", "대기"), ("1", "승인"), ("2", "거부")],
                default="0",
                max_length=1,
            ),
        ),
    ]
