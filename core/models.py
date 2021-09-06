# Create your models here.
from django.contrib.auth.models import User
from django.db import models
from model_utils import Choices
from model_utils.fields import StatusField


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    total_days = models.FloatField(default=15.0)
    used_days = models.FloatField(default=0.0)
    sick_days = models.FloatField(default=0.0)
    comp_days = models.FloatField(default=0.0)
    slack_channel = models.CharField(max_length=50, null=True, blank=True)

    @property
    def available_days(self):
        return self.total_days - self.used_days


class Attendance(models.Model):
    STATUS = Choices(("SUBMITTED", "제출"), ("ACCEPTED", "승인"))

    user = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="근무자")
    date = models.DateField(verbose_name="날짜")
    start_at = models.TimeField(verbose_name="시작시간")
    end_at = models.TimeField(null=True, blank=True, verbose_name="종료시간")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name="생성자",
        related_name="game_set_as_created",
    )
    updated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        verbose_name="수정자",
        related_name="game_set_as_updated",
    )
    status = StatusField(choices_name="STATUS", db_index=True, verbose_name="상태")
    ip_address = models.GenericIPAddressField(verbose_name="IP주소")

    def __str__(self):
        if not self.end_at:
            end_at = "Now"
        else:
            end_at = self.end_at.strftime("%H:%M:%S")

        start_at = self.start_at.strftime("%H:%M:%S")

        return "{} : {} ({}~{})".format(self.date, self.user, start_at, end_at)

    class Meta:
        verbose_name = "출근기록"
        verbose_name_plural = "출근기록"
