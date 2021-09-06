import datetime

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from tempus_dominus.widgets import DatePicker, DateTimePicker

from core.models import Profile
from vacation.constants import APPROVAL_CHOICES, VACATION_CHOICES
from vacation.models import Vacation


class VacationForm(forms.ModelForm):
    day_off_start_at = forms.DateField(
        required=False, widget=DatePicker(), label="연차시작"
    )
    day_off_end_at = forms.DateField(required=False, widget=DatePicker(), label="연차끝")
    comp_day_off_start_at = forms.DateTimeField(
        required=False, widget=DatePicker(), label="대체휴가시작"
    )
    comp_day_off_end_at = forms.DateTimeField(
        required=False, widget=DatePicker(), label="대체휴가끝"
    )
    half_day_off_start_at = forms.CharField(
        required=False, widget=DateTimePicker(), label="반차"
    )
    one_fourth_day_off_start_at = forms.CharField(
        required=False, widget=DateTimePicker(), label="반반차"
    )
    cat = forms.ChoiceField(
        choices=VACATION_CHOICES,
        widget=forms.Select(attrs={"class": "form-control w-25"}),
        label="구분",
    )

    def clean(self):
        day_off_start_at = self.cleaned_data.get("day_off_start_at")
        comp_day_off_start_at = self.cleaned_data.get("comp_day_off_start_at")
        half_day_off_start_at = self.cleaned_data.get("half_day_off_start_at")
        one_fourth_day_off_start_at = self.cleaned_data.get(
            "one_fourth_day_off_start_at"
        )

        if (
            not day_off_start_at
            and not comp_day_off_start_at
            and not half_day_off_start_at
            and not one_fourth_day_off_start_at
        ):
            raise ValidationError("One of the four fields are required.")
        return self.cleaned_data

    class Meta:
        model = Vacation
        fields = ["cat"]


def get_year_choices():
    return [(r, r) for r in range(2020, datetime.date.today().year + 1)]


class VacationYearSelectForm(forms.ModelForm):
    year = forms.TypedChoiceField(
        required=False,
        initial=datetime.date.today().year,
        coerce=int,
        choices=get_year_choices,
        label="년도",
    )

    def clean(self):
        year = self.cleaned_data.get("year")
        if year is None:
            raise ValidationError("One of the required field is missing.")
        return self.cleaned_data

    class Meta:
        model = Vacation
        fields = []


class VacationApprovalForm(forms.ModelForm):
    class Meta:
        model = Vacation
        fields = ["approval"]


class VacationDayForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["total_days"]


class NameChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.last_name}{obj.first_name}"


class SickForm(forms.ModelForm):
    cat = forms.ChoiceField(
        choices=VACATION_CHOICES,
        widget=forms.Select(attrs={"class": "form-control w-25"}),
        label="구분",
    )
    day_off_start_at = forms.DateField(
        required=False, widget=DatePicker(), label="연차시작"
    )
    day_off_end_at = forms.DateField(required=False, widget=DatePicker(), label="연차끝")
    sick_day_off_start_at = forms.DateTimeField(
        required=False, widget=DatePicker(), label="병가시작"
    )
    sick_day_off_end_at = forms.DateTimeField(
        required=False, widget=DatePicker(), label="병가끝"
    )
    comp_day_off_start_at = forms.DateTimeField(
        required=False, widget=DatePicker(), label="대체휴가시작"
    )
    comp_day_off_end_at = forms.DateTimeField(
        required=False, widget=DatePicker(), label="대체휴가끝"
    )
    half_day_off_start_at = forms.CharField(
        required=False, widget=DateTimePicker(), label="반차"
    )
    one_fourth_day_off_start_at = forms.CharField(
        required=False, widget=DateTimePicker(), label="반반차"
    )
    user = NameChoiceField(
        queryset=User.objects.all(),
        label="직원",
        widget=forms.Select(attrs={"class": "form-control w-25"}),
    )

    def clean(self):
        day_off_start_at = self.cleaned_data.get("day_off_start_at")
        sick_day_off_start_at = self.cleaned_data.get("sick_day_off_start_at")
        comp_day_off_start_at = self.cleaned_data.get("comp_day_off_start_at")
        half_day_off_start_at = self.cleaned_data.get("half_day_off_start_at")
        one_fourth_day_off_start_at = self.cleaned_data.get(
            "one_fourth_day_off_start_at"
        )

        if (
            not day_off_start_at
            and not sick_day_off_start_at
            and not comp_day_off_start_at
            and not half_day_off_start_at
            and not one_fourth_day_off_start_at
        ):
            raise ValidationError("One of the five fields are required.")
        return self.cleaned_data

    class Meta:
        model = Vacation
        fields = ["user", "cat"]


class AdminUpdateForm(SickForm):
    approval = forms.ChoiceField(
        choices=APPROVAL_CHOICES,
        widget=forms.Select(attrs={"class": "form-control w-25"}),
    )

    def __init__(self, *args, **kwargs):
        super(AdminUpdateForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Vacation
        fields = ["user", "cat", "approval"]
