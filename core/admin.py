from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from core import models


# Register your models here.
class ProfileInline(admin.StackedInline):
    model = models.Profile

    can_delete = False
    verbose_name_plural = "프로필"

    verbose_name = "추가정보"


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


class AttendanceAdmin(admin.ModelAdmin):
    models = models.Attendance
    short_description = "출근"

    list_display = (
        "id",
        "date",
        "username",
        "start_at",
        "end_at",
        "created_by",
        "updated_by",
        "ip_address",
    )
    readonly_fields = ("created_at", "updated_at")

    def username(self, obj):
        return obj.user.first_name

    username.short_description = "이름"


admin.site.register(models.Attendance, AttendanceAdmin)
