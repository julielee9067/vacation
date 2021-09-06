import datetime
import os
from datetime import timedelta

import pandas as pd
from django import template
from django.db.models import QuerySet

from vacation.constants import (
    HOLIDAY_LIST,
    VacationApproval,
    VacationTypes,
    SPECIAL_VACATION_TYPES,
)
from vacation.utils import (
    calculate_vacation_days_by_type,
)

register = template.Library()


@register.simple_tag
def relative_url(value, field_name, urlencode=None):
    url = "?{}={}".format(field_name, value)
    if urlencode:
        querystring = urlencode.split("&")
        filtered_querystring = filter(
            lambda p: p.split("=")[0] != field_name, querystring
        )
        encoded_querystring = "&".join(filtered_querystring)
        url = "{}&{}".format(url, encoded_querystring)
    return url


@register.simple_tag
def get_verbose_field_name(instance, field_name):
    """
    Returns verbose_name for a field.
    """
    return instance._meta.get_field(field_name).verbose_name.title()


@register.simple_tag
def get_duration(start_at: datetime.datetime, end_at: datetime.datetime) -> str:
    business_day_range = pd.bdate_range(start=start_at, end=end_at).to_list()
    diff = end_at - start_at
    if diff.days > 0:
        return f"{len(set(business_day_range) - set(HOLIDAY_LIST))} 일"
    elif start_at == end_at:
        return "1 일"
    return f"{int(diff.seconds / 3600)} 시간"


@register.simple_tag
def get_used_days(
    vacation_list: QuerySet,
    year: str,
    day_off_type: str = str(VacationTypes.DAY_OFF.value),
) -> float:
    if not year.strip():
        year = datetime.datetime.today().year

    vacation_list = vacation_list.filter(approval=VacationApproval.APPROVED.value)
    vacation_list = (
        vacation_list.filter(cat=day_off_type)
        if day_off_type in SPECIAL_VACATION_TYPES
        else vacation_list.exclude(cat__in=SPECIAL_VACATION_TYPES)
    )

    return calculate_vacation_days_by_type(vacation_list=vacation_list, year=int(year))


@register.simple_tag
def get_on_hold_days(vacation_list: QuerySet, year: str) -> float:
    if not year.strip():
        year = datetime.datetime.today().year

    vacation_list = vacation_list.exclude(cat__in=SPECIAL_VACATION_TYPES).filter(
        approval=VacationApproval.ON_HOLD.value
    )
    return calculate_vacation_days_by_type(vacation_list=vacation_list, year=int(year))


@register.filter
def plus_days(value, days):
    return value + timedelta(days=days)


@register.filter
def subtract(first_val: str, second_val: str = "0") -> float:
    return float(first_val) - float(second_val) if first_val else 0


@register.simple_tag
def subtract_two_vals(
    first_val: str, second_val: str = "0", third_val: str = "0"
) -> float:
    return float(first_val) - float(second_val) - float(third_val) if first_val else 0


@register.filter
def date_format(value, format="%Y-%m-%d"):
    if not value:
        return None

    return value.strftime(format)


@register.filter
def datetime_format(value: datetime, format="%Y-%m-%d %H:%M"):
    return value.strftime(format)


@register.filter
def get_item_str(dictionary, key):
    return dictionary.get(str(key))


@register.filter
def get_item(dictionary, key):
    return dictionary.get(int(key))


@register.filter
def file_ext(file_url):
    filename, file_ext = os.path.splitext(file_url)
    return file_ext.lower()


@register.filter
def split(str, splitter):
    return str.split(splitter)


@register.filter
def editable(start_at: datetime) -> bool:
    return (start_at - datetime.datetime.today()).days > 1


@register.filter
def get_approval_value_from_member_list(approval: str) -> int:
    return int(approval) % 2 + 1
