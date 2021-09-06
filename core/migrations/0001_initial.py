# Generated by Django 3.0.2 on 2020-01-04 12:34

import django.db.models.deletion
import model_utils.fields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Attendance",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date", models.DateField(verbose_name="날짜")),
                ("start_at", models.TimeField(verbose_name="시작시간")),
                (
                    "end_at",
                    models.TimeField(blank=True, null=True, verbose_name="종료시간"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="생성일"),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="수정일")),
                (
                    "status",
                    model_utils.fields.StatusField(
                        choices=[("SUBMITTED", "제출"), ("ACCEPTED", "승인")],
                        db_index=True,
                        default="SUBMITTED",
                        max_length=100,
                        no_check_for_status=True,
                        verbose_name="상태",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="game_set_as_created",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="생성자",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="game_set_as_updated",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="수정자",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="근무자",
                    ),
                ),
            ],
        ),
    ]
