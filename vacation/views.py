import datetime
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)
from django.views.generic.edit import BaseUpdateView, ModelFormMixin
from django_slack import slack_message

from core.models import Profile
from isds.exception import print_exception
from vacation.constants import (
    DATE_FORMAT,
    DATETIME_FORMAT,
    VacationApproval,
    VacationMessages,
    VacationTypes,
)
from vacation.forms import (
    AdminUpdateForm,
    SickForm,
    VacationApprovalForm,
    VacationDayForm,
    VacationForm,
    VacationYearSelectForm,
)
from vacation.mixins import IsSuperuserMixin
from vacation.models import Vacation
from vacation.utils import (
    convert_start_and_end_at,
    does_vacation_overlap,
    get_start_and_end_at,
    get_total_used_days,
    has_enough_vacation_days_left,
    is_category_day_off,
    is_vacation_prenotified,
    get_vacation_days,
)

logging.root.setLevel(logging.INFO)


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "vacation/index.html"


class VacationManagementView(LoginRequiredMixin, TemplateView):
    template_name = "vacation/admin_index.html"


class VacationListView(LoginRequiredMixin, ListView, ModelFormMixin):
    template_name = "vacation/user/list.html"
    context_object_name = "vacation_list"
    form_class = VacationYearSelectForm

    def get_queryset(self):
        if self.start is not None and self.end is not None:
            return (
                Vacation.objects.select_related("user")
                .filter(
                    user=self.user, start_at__gte=self.start, start_at__lte=self.end
                )
                .order_by("-start_at")
            )
        return (
            Vacation.objects.select_related("user")
            .filter(user=self.user)
            .order_by("-start_at")
        )

    def get(self, request, *args, **kwargs):
        year = request.GET.get("year")
        user_id = (
            self.kwargs["user_id"]
            if self.request.user.is_superuser
            else self.request.user.id
        )
        self.user = User.objects.get(id=user_id)
        self.start = datetime.date(int(year), 1, 1) if year is not None else None
        self.end = datetime.date(int(year), 12, 31) if year is not None else None
        self.object = None
        profile = Profile.objects.get_or_create(user_id=user_id)[0]
        get_vacation_days(user_profile=profile)
        return ListView.get(self, request, *args, **kwargs)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(VacationListView, self).get_context_data(**kwargs)
        if self.request.GET.get("year") is not None:
            self.get_form(self.form_class).base_fields.get(
                "year"
            ).initial = self.request.GET.get("year")
        context["form"] = self.get_form(self.form_class)
        return context


class VacationCreateView(LoginRequiredMixin, CreateView):
    queryset = Vacation.objects.all()
    template_name = "vacation/user/register.html"
    form_class = VacationForm

    def get_success_url(self):
        return reverse("vacation:index")

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["available_day"] = (
            self.request.user.profile.total_days - self.request.user.profile.used_days
        )
        return context

    def form_invalid(self, form):
        return super().form_invalid(form)

    def form_valid(self, form):
        form.instance.user = self.request.user
        start_at, end_at = get_start_and_end_at(
            data=form.cleaned_data, vacation_type=int(form.instance.cat)
        )

        if has_enough_vacation_days_left(
            user=self.request.user,
            vacation_type=int(form.instance.cat),
            start_at=start_at,
            end_at=end_at,
        ):
            messages.error(self.request, VacationMessages.NOT_ENOUGH_DAYS_LEFT)
            return super().form_invalid(form)

        if start_at < datetime.datetime.now():
            messages.error(self.request, VacationMessages.START_LESS_THAN_NOW)
            return super().form_invalid(form)

        if start_at > end_at:
            messages.error(self.request, VacationMessages.START_GREATER_THAN_END)
            return super().form_invalid(form)

        if does_vacation_overlap(user=self.request.user, start=start_at, end=end_at):
            messages.error(self.request, VacationMessages.OVERLAPPED_VACATION)
            return super().form_invalid(form)

        if not is_category_day_off(vacation_type=int(form.instance.cat)):
            form.instance.approval = str(VacationApproval.APPROVED.value)

        elif not is_vacation_prenotified(date=start_at):
            messages.error(self.request, VacationMessages.PRENOTICE_WARNING)
            return super().form_invalid(form)

        form.instance.start_at = start_at
        form.instance.end_at = end_at

        vacation = form.save(commit=False)
        vacation.save()
        user_profile = Profile.objects.get(user_id=form.instance.user.id)
        get_vacation_days(user_profile=user_profile)

        channel = getattr(settings, "SLACK_VACATION_CHANNEL", None)
        try:
            slack_message(
                "core/message.slack",
                {
                    "text": (
                        f"{form.instance.user.first_name}님이 {form.instance.get_cat_display()}: "
                        f"{start_at} 부터 {end_at} 까지 휴가를 신청하였습니다. "
                        f"상태: {form.instance.get_approval_display()}"
                    )
                },
                channel=channel,
            )
        except ValueError:
            print_exception()
            pass

        messages.success(self.request, VacationMessages.SUCCESSFUL_SUBMISSION)
        return super().form_valid(form)


class VacationUpdateView(LoginRequiredMixin, UpdateView):
    queryset = Vacation.objects.all()
    form_class = VacationForm
    template_name = "vacation/user/update.html"
    context_object_name = "vacation"

    def get_success_url(self):
        return reverse_lazy("vacation:list", args=(self.request.user.id,))

    def form_valid(self, form):
        start_at, end_at = get_start_and_end_at(
            data=form.cleaned_data, vacation_type=int(form.instance.cat)
        )
        form.instance.start_at = start_at
        form.instance.end_at = end_at

        if has_enough_vacation_days_left(
            user=self.request.user,
            vacation_type=int(form.instance.cat),
            start_at=start_at,
            end_at=end_at,
        ):
            messages.error(self.request, VacationMessages.NOT_ENOUGH_DAYS_LEFT)
            return super().form_invalid(form)

        if start_at < datetime.datetime.now():
            messages.error(self.request, VacationMessages.START_LESS_THAN_NOW)
            return super().form_invalid(form)

        if start_at > end_at:
            messages.error(self.request, VacationMessages.START_GREATER_THAN_END)
            return super().form_invalid(form)

        if does_vacation_overlap(
            user=self.request.user,
            start=start_at,
            end=end_at,
            vacation_id=form.instance.id,
        ):
            messages.error(self.request, VacationMessages.OVERLAPPED_VACATION)
            return super().form_invalid(form)

        if not is_category_day_off(vacation_type=int(form.instance.cat)):
            form.instance.approval = str(VacationApproval.APPROVED.value)

        elif not is_vacation_prenotified(date=start_at):
            messages.error(self.request, VacationMessages.PRENOTICE_WARNING)
            return super().form_invalid(form)
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)


class VacationDeleteView(LoginRequiredMixin, DeleteView):
    queryset = Vacation.objects.all()

    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        channel = getattr(settings, "SLACK_VACATION_CHANNEL", None)
        vacation = self.get_object()
        try:
            slack_message(
                "core/message.slack",
                {
                    "text": (
                        f"{self.request.user.first_name}님이 "
                        f"{vacation.start_at} 부터 {vacation.end_at} 까지 휴가를 삭제하였습니다. "
                    )
                },
                channel=channel,
            )
        except ValueError:
            print_exception()
            pass
        return super(VacationDeleteView, self).delete(request, *args, **kwargs)

    def get_success_url(self):
        if self.request.user.is_superuser:
            return reverse("vacation:member_list")
        return reverse("vacation:list", args=(self.request.user.id,))


# ---- admin ---- #
class AdminIndexView(IsSuperuserMixin, ListView):
    template_name = "vacation/admin/list.html"
    context_object_name = "vacation_list"

    def get_queryset(self):
        query = Q()
        query.add(Q(approval=f"{VacationApproval.ON_HOLD.value}"), query.AND)
        query.add(Q(cat=f"{VacationTypes.DAY_OFF.value}"), query.AND)

        return Vacation.objects.select_related("user").filter(query)


class AdminVacationUpdateView(IsSuperuserMixin, UpdateView):
    template_name = "vacation/admin/update.html"
    queryset = Vacation.objects.all()
    form_class = AdminUpdateForm
    context_object_name = "vacation"

    def get_success_url(self):
        return reverse_lazy("vacation:member_list")

    def form_valid(self, form):
        logging.info(form)
        logging.info(form.cleaned_data)
        start_at, end_at = get_start_and_end_at(
            data=form.cleaned_data, vacation_type=int(form.instance.cat)
        )
        form.instance.start_at = start_at
        form.instance.end_at = end_at

        if start_at > end_at:
            messages.error(self.request, VacationMessages.START_GREATER_THAN_END)
            return super().form_invalid(form)

        if does_vacation_overlap(
            user=form.instance.user,
            start=start_at,
            end=end_at,
            vacation_id=form.instance.id,
        ):
            messages.error(self.request, VacationMessages.OVERLAPPED_VACATION)
            return super().form_invalid(form)

        return super().form_valid(form)

    def form_invalid(self, form):
        logging.info(form)
        return super().form_invalid(form)


class MemberListView(IsSuperuserMixin, ListView):
    template_name = "vacation/admin/member_list.html"
    context_object_name = "vacation_list"

    def get_queryset(self):
        member_name = self.request.GET.get("member_name")
        if member_name is None:
            return Vacation.objects.select_related("user").order_by(
                "-start_at", "approval"
            )
        else:
            try:
                user = User.objects.get(first_name=member_name)
            except User.DoesNotExist:
                return User.objects.none()
            return (
                Vacation.objects.select_related("user")
                .filter(user=user)
                .order_by("-start_at", "approval")
            )


class SickCreateView(IsSuperuserMixin, CreateView):
    queryset = Vacation.objects.select_related("user").all()
    template_name = "vacation/admin/register.html"
    form_class = SickForm

    def get_success_url(self):
        return reverse("vacation:member_list")

    def form_invalid(self, form):
        return super().form_invalid(form)

    def form_valid(self, form):
        form.instance.approval = f"{VacationApproval.APPROVED.value}"
        start_at, end_at = get_start_and_end_at(
            data=form.cleaned_data, vacation_type=int(form.instance.cat)
        )

        if form.instance.cat != str(
            VacationTypes.SICK_DAY.value
        ) and has_enough_vacation_days_left(
            user=self.request.user,
            vacation_type=int(form.instance.cat),
            start_at=start_at,
            end_at=end_at,
        ):
            messages.error(self.request, VacationMessages.NOT_ENOUGH_DAYS_LEFT)
            return super().form_invalid(form)

        if start_at > end_at:
            messages.error(self.request, VacationMessages.START_GREATER_THAN_END)
            return super().form_invalid(form)

        if does_vacation_overlap(user=form.instance.user, start=start_at, end=end_at):
            messages.error(self.request, VacationMessages.OVERLAPPED_VACATION)
            return super().form_invalid(form)

        if not is_category_day_off(vacation_type=int(form.instance.cat)):
            form.instance.approval = str(VacationApproval.APPROVED.value)

        form.instance.start_at = start_at
        form.instance.end_at = end_at

        vacation = form.save(commit=False)
        vacation.save()
        user_profile = Profile.objects.get(user_id=form.instance.user.id)
        get_vacation_days(user_profile=user_profile)

        messages.success(self.request, VacationMessages.SUCCESSFUL_SUBMISSION)
        return super().form_valid(form)


class UserVacationListView(IsSuperuserMixin, ListView):
    queryset = User.objects.filter(is_active=True)
    template_name = "vacation/admin/change.html"
    context_object_name = "user_list"


class UserVacationDayUpdateView(IsSuperuserMixin, BaseUpdateView):
    queryset = Profile.objects.all()
    form_class = VacationDayForm

    def get_success_url(self):
        return reverse("vacation:users_vacation")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return render(request, "vacation/blank.html", context=context)

    def form_valid(self, form):
        instance = form.instance
        messages.success(
            self.request,
            f"{instance.user.first_name}의 총 휴가를 {instance.total_days}일로 변경하였습니다.",
        )
        return super().form_valid(form)


class VacationApprovalView(IsSuperuserMixin, BaseUpdateView):
    queryset = Vacation.objects.all()
    form_class = VacationApprovalForm

    def get_success_url(self):
        return reverse("vacation:admin")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return render(request, "vacation/blank.html", context=context)

    def form_valid(self, form):
        instance = form.instance
        result = (
            "거부"
            if int(form.data.get("approval")) == VacationApproval.DENIED.value
            else "승인"
        )
        vacation = Vacation.objects.get(id=instance.id)
        vacation.approval = instance.approval
        vacation.save()
        user_profile = Profile.objects.get(user_id=instance.user.id)
        used_days = get_total_used_days(user_profile=user_profile)

        if user_profile.total_days - used_days < 0:
            instance.approval = VacationApproval.ON_HOLD.value
            messages.error(self.request, VacationMessages.NOT_ENOUGH_DAYS_LEFT)
            return super().form_valid(form)

        start_at, end_at = convert_start_and_end_at(
            start_at=instance.start_at,
            end_at=instance.end_at,
            vacation_type=int(instance.cat),
        )

        datetime_format = (
            DATE_FORMAT if is_category_day_off(int(instance.cat)) else DATETIME_FORMAT
        )
        start_at = start_at.strftime(datetime_format)
        end_at = end_at.strftime(datetime_format)

        messages.success(
            self.request,
            f"{instance.user.first_name}의 {start_at} ~ {end_at} 휴가를 {result} 처리하였습니다. "
            f"(잔여 휴가: {user_profile.total_days - used_days}일)",
        )

        return super().form_valid(form)
