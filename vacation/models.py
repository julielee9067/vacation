from django.contrib.auth import get_user_model
from django.db import models

from vacation.constants import APPROVAL_CHOICES, VACATION_CHOICES


class Vacation(models.Model):
    cat = models.CharField(max_length=1, choices=VACATION_CHOICES, default="1")
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, verbose_name="신청자"
    )
    start_at = models.DateTimeField(default=None)
    end_at = models.DateTimeField(default=None)
    approval = models.CharField(max_length=1, choices=APPROVAL_CHOICES, default="0")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    @property
    def use_days(self):
        return (self.end_at - self.start_at).days + 1

    def __str__(self):
        return f"{self.id}"
