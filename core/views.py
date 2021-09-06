import datetime
import random

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView, TemplateView
from django.views.generic.edit import CreateView
from django_slack import slack_message
from ipware import get_client_ip

from core import models

# from django_filters.views import FilterView
from core.models import Profile


def is_allowed_ip(ip_str):
    allowed_client_ips = getattr(settings, "ALLOWED_CLIENT_IPS", None)

    for allowed_ip in allowed_client_ips:
        if ip_str.startswith(allowed_ip):
            return True
    return False


# Create your views here.
class IndexView(TemplateView):
    template_name = "core/index.html"

    def get(self, request, *args, **kwargs):
        try:  # 로그인 하지 않은 상태일 때, 문제
            if not Profile.objects.filter(user=request.user).exists():
                Profile.objects.create(user=request.user)
        except TypeError:
            pass
        return super().get(request, *args, **kwargs)


class AttendanceForm(forms.ModelForm):
    # type = forms.CheckboxInput()
    # type = forms.ChoiceField(choices=(('', '선택'), ('1', '출근'), ('2', '퇴근')), label='출근/퇴근')

    class Meta:
        model = models.Attendance
        fields = []


class AttendanceCreate(LoginRequiredMixin, CreateView):
    model = models.Attendance
    # fields = []
    form_class = AttendanceForm
    template_name = "core/attendance_form.html"
    client_ip = ""

    def dispatch(self, request, *args, **kwargs):
        self.client_ip, _ = get_client_ip(self.request)

        if not is_allowed_ip(self.client_ip):
            messages.error(self.request, "체크인 페이지는 외부 네트워크에서 접근하실 수 없습니다.")
            return redirect(reverse("core:index"))
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        now = timezone.datetime.now()
        return {"date": now.strftime("%Y-%m-%d")}

    def get_success_url(self):
        return reverse("core:index")

    def form_valid(self, form):
        current_user = self.request.user

        typ = (
            "1"
            if form.data.get("checkin") == "checkin"
            else "2"
            if form.data.get("checkout") == "checkout"
            else ""
        )
        now = datetime.datetime.now()

        latest = self.model.objects.filter(user=current_user).order_by("date").last()

        if typ == "1":  # 출근
            if latest and now.date() == latest.date:
                start_date = latest.date.strftime("%Y-%m-%d")
                start_time = latest.start_at.strftime("%H:%M:%S")
                error = (
                    f"이미 출근기록이 있습니다({start_date} {start_time}). 기록을 남기시려면 퇴근을 선택해 주세요."
                )
                form.add_error(None, error)
                return super().form_invalid(form)

            start_at = now.strftime("%H:%M:%S")

            instance = form.instance
            instance.date = now
            instance.start_at = start_at
            instance.user = current_user
            instance.created_by = current_user
            instance.ip_address = self.client_ip

            hello_messages = [
                "오늘 하루도 화이팅!",
                "어제 못한 것을 해보자!",
                "아 피곤해.. 커피한잔 하면서 시작해 볼까?",
                "신이나 신이나 엣헴 엣헴 신이나!",
            ]

            try:
                # Profile을 나중에 추가하여 없는 경우가 있을 수 있음.
                channel = current_user.profile.slack_channel
            except models.Profile.DoesNotExist:
                channel = getattr(settings, "SLACK_CHANNEL", None)

            if not channel:  # Profile에서 불러온 값이 None인 경우도 있음.
                channel = "random"
            if settings.DEBUG:
                channel = "git_isds"

            try:
                slack_message(
                    "core/message.slack",
                    {
                        "text": f"{current_user.first_name}님이 체크인 하였습니다. {random.choice(hello_messages)}",
                    },
                    channel=channel,
                )
            except ValueError:
                pass

            messages.success(self.request, f"출근기록을 등록하였습니다. (출근시간 : {start_at})")
            return super().form_valid(form)

        elif typ == "2":  # 퇴근
            work_time = now - datetime.datetime.combine(latest.date, latest.start_at)
            if latest.end_at:
                # 마지막 퇴근 후 8시간 이상 지난 경우 체크인이 없는 것으로 판단
                rest_time = now - datetime.datetime.combine(latest.date, latest.end_at)
                if rest_time.seconds / 3600 >= 8:
                    error = "출근기록이 제출되지 않았습니다. 제출 시 출근을 선택해 주세요."
                    form.add_error(None, error)
                    return super().form_invalid(form)

            else:  # 마지막 항목에 체크아웃 시간이 없을 때
                # 마지막 출근 후 24시간 이상 지난 경우 체크인이 없는 것으로 판단
                if work_time.days >= 1:
                    error = "출근기록이 제출되지 않았습니다. 제출 시 출근을 선택해 주세요."
                    form.add_error(None, error)
                    return super().form_invalid(form)

            end_at = now.strftime("%H:%M:%S")

            form.instance = latest
            instance = form.instance
            instance.end_at = end_at
            instance.updated_by = current_user

            goodbye_messages = [
                "고생하셨어요~",
                "수고하셨습니다~",
                "집에서 푹 쉬세요!!",
                "내일은 더 멋진 하루를 기대해 보세요!!",
            ]

            try:
                # Profile을 나중에 추가하여 없는 경우가 있을 수 있음.
                channel = current_user.profile.slack_channel
            except models.Profile.DoesNotExist:
                channel = getattr(settings, "SLACK_CHANNEL", None)

            if not channel:  # Profile에서 불러온 값이 None인 경우도 있음.
                channel = "random"
            if settings.DEBUG:
                channel = "git_isds"

            try:
                slack_message(
                    "core/message.slack",
                    {
                        "text": f"{current_user.first_name}님이 체크아웃 하였습니다. {random.choice(goodbye_messages)}",
                    },
                    channel=channel,
                )
            except ValueError:
                pass

            messages.success(self.request, f"퇴근기록을 등록하였습니다. (퇴근시간 : {end_at})")
            return super().form_valid(form)

        else:
            messages.error(self.request, "체크인/체크아웃 정보가 없습니다.")
            return super().form_invalid(form)


class AttendanceListView(LoginRequiredMixin, ListView):
    model = models.Attendance

    def get_queryset(self):
        current_user = self.request.user
        return self.model.objects.filter(user=current_user).order_by("-id").all()


def statistics(request):
    labels = [
        "1월",
        "2월",
        "3월",
        "4월",
        "5월",
        "6월",
        "7월",
        "8월",
        "9월",
        "10월",
        "11월",
        "12월",
    ]
    chartLabel = "my data"
    chartdata = [0, 10, 5, 2, 20, 30, 45]
    data = {
        "labels": labels,
        "chartLabel": chartLabel,
        "chartdata": chartdata,
    }
    return JsonResponse(data, safe=False)


class ChartView(TemplateView):
    template_name = "core/chart.html"
