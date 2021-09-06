from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Tuple, Set

import pandas as pd
from dateutil import parser
from django.contrib.auth.models import User

from core.models import Profile

from vacation.constants import (
    HOLIDAY_LIST,
    NUM_PRENOTICE_DAYS,
    VacationTypes,
    VacationApproval,
    SPECIAL_VACATION_TYPES,
)
from vacation.models import Vacation


def get_dates_in_range(start: datetime, end: datetime) -> Set:
    """
    start와 end 사이에 있는 모든 날짜를 set으로 리턴합니다.
    """
    delta = end - start
    return set([start.date() + timedelta(days=i) for i in range(delta.days + 1)])


def get_valid_vacation_dates(
    vacation_list: Any, year: int = datetime.today().year
) -> List:
    """
    지정한 년도에 쓰인 연차/휴가 중 중복되는 휴가를 삭제하고, 주말을 제외한 후 List로 리턴합니다.
    """
    year_dates = get_dates_in_range(datetime(year, 1, 1), datetime(year, 12, 31))

    total_day_off_list = list()
    for day_off in vacation_list:
        day_off_dates = get_dates_in_range(day_off.start_at, day_off.end_at)
        day_off_in_same_year = year_dates & day_off_dates
        if len(day_off_in_same_year) > 0:
            total_day_off_list.extend(
                pd.bdate_range(
                    start=min(day_off_in_same_year), end=max(day_off_in_same_year)
                ).to_list()
            )

    return total_day_off_list


def calculate_vacation_days_by_type(vacation_list: Any, year: int) -> float:
    """
    주어진 휴가 리스트를 가지고 쓰인 총 연차, 반차, 반반차의 수를 더해 계산합니다.
    """
    day_off_list = vacation_list.filter(
        cat__in=[
            VacationTypes.DAY_OFF.value,
            VacationTypes.SICK_DAY.value,
            VacationTypes.COMP_DAY.value,
        ]
    )
    total_day_off_list = get_valid_vacation_dates(vacation_list=day_off_list, year=year)
    num_half_day_offs = len(
        vacation_list.filter(cat=str(VacationTypes.HALF_DAY_OFF.value))
    )
    num_one_fourth_day_offs = len(
        vacation_list.filter(cat=str(VacationTypes.ONE_FOURTH_DAY_OFF.value))
    )

    total_used_days = (
        len(set(total_day_off_list) - set(HOLIDAY_LIST))
        + num_half_day_offs * 0.5
        + num_one_fourth_day_offs * 0.25
    )
    return total_used_days


def get_total_used_days(
    user_profile: Profile,
    approval: List[str] = ["1"],
    year: int = datetime.today().year,
) -> float:
    """
    User profile을 가지고 쓰인 총 휴가(연차, 반차, 반반차)의 수를 계산합니다.
    """
    vacation_list = Vacation.objects.exclude(cat__in=SPECIAL_VACATION_TYPES).filter(
        user_id=user_profile.user_id,
        approval__in=approval,
    )
    total_used_days = calculate_vacation_days_by_type(
        vacation_list=vacation_list, year=year
    )
    user_profile.used_days = total_used_days
    user_profile.save()

    return total_used_days


def get_total_sick_days(
    user_profile: Profile, year: int = datetime.today().year
) -> float:
    """
    User profile을 가지고 쓰인 총 병가의 수를 계산합니다.
    """
    vacation_list = Vacation.objects.filter(
        approval=str(VacationApproval.APPROVED.value),
        user_id=user_profile.user_id,
        cat=str(VacationTypes.SICK_DAY.value),
    )
    total_sick_day_list = get_valid_vacation_dates(
        vacation_list=vacation_list, year=year
    )
    total_sick_days = len(set(total_sick_day_list) - set(HOLIDAY_LIST))
    user_profile.sick_days = total_sick_days
    user_profile.save()

    return total_sick_days


def get_total_comp_days(
    user_profile: Profile, year: int = datetime.today().year
) -> float:
    """
    User profile을 가지고 쓰인 총 대체 휴가의 수를 계산합니다.
    """
    vacation_list = Vacation.objects.filter(
        approval=str(VacationApproval.APPROVED.value),
        user_id=user_profile.user_id,
        cat=str(VacationTypes.COMP_DAY.value),
    )
    total_comp_day_list = get_valid_vacation_dates(
        vacation_list=vacation_list, year=year
    )
    total_comp_days = len(set(total_comp_day_list) - set(HOLIDAY_LIST))
    user_profile.comp_days = total_comp_days
    user_profile.save()

    return total_comp_days


def get_vacation_days(
    user_profile: Profile, year: int = datetime.today().year
) -> Tuple[float, float, float]:
    """
    User profile을 가지고 쓰인 총 휴가, 병가, 대체 휴가의 수를 계산합니다.
    """
    used_days = get_total_used_days(user_profile=user_profile, year=year)
    sick_days = get_total_sick_days(user_profile=user_profile, year=year)
    comp_days = get_total_comp_days(user_profile=user_profile, year=year)
    return used_days, sick_days, comp_days


def get_end_at(vacation_type: int, start_at: Any) -> datetime:
    """
    휴가 종류(반차, 반반차)에 따라 종료 시간을 계산합니다.
    """
    if vacation_type == VacationTypes.HALF_DAY_OFF.value:
        return get_half_day_off_end_at(start_at)
    elif vacation_type == VacationTypes.ONE_FOURTH_DAY_OFF.value:
        return get_one_fourth_day_off_end_at(start_at)
    else:
        raise ValueError(
            f"Cannot calculate end_at for given vacation type: {vacation_type}"
        )


def convert_date_to_datetime(original_date: date) -> datetime:
    """
    Date type을 datetime type으로 변환합니다.
    """
    return datetime.combine(original_date, datetime.min.time())


def convert_start_and_end_at(
    start_at: Any, end_at: Any, vacation_type: int
) -> Tuple[datetime, datetime]:
    """
    휴가 종류에 따라 start_at과 end_at을 각각 계산해 datetime type으로 변환합니다.
    """
    if is_category_day_off(vacation_type=vacation_type):
        start_at = convert_date_to_datetime(original_date=start_at)
        end_at = convert_date_to_datetime(original_date=end_at)
    else:
        end_at = get_end_at(vacation_type=vacation_type, start_at=start_at)
        start_at = convert_str_to_datetime(start_at)

    return start_at, end_at


def get_start_and_end_at(data: Dict, vacation_type: int) -> Tuple[datetime, datetime]:
    """
    Form에서 가져온 정보를 통해 start_at과 end_at을 계산합니다.
    """
    start_at, end_at = None, None

    for key, val in data.items():
        if val:
            if "start" in key:
                start_at = val
            elif "end" in key:
                end_at = val

    return convert_start_and_end_at(
        start_at=start_at, end_at=end_at, vacation_type=vacation_type
    )


def is_category_day_off(vacation_type: int) -> bool:
    return vacation_type in [
        VacationTypes.DAY_OFF.value,
        VacationTypes.SICK_DAY.value,
        VacationTypes.COMP_DAY.value,
    ]


def is_vacation_prenotified(date: datetime) -> bool:
    return (date - datetime.now()).days >= NUM_PRENOTICE_DAYS


def does_vacation_overlap(
    user: User, start: datetime, end: datetime, vacation_id: int = None
) -> bool:
    """
    휴가 신청 시 겹치는 휴가가 이미 존재하는지 확인합니다.
    """
    vacation_list = Vacation.objects.exclude(id=vacation_id).filter(
        user=user, cat=str(VacationTypes.DAY_OFF.value)
    )
    for vac in vacation_list:
        latest_start = max(vac.start_at, start)
        earliest_end = min(vac.end_at, end)
        delta = (earliest_end - latest_start).days + 1
        if max(0, delta) > 0:
            return True
    return False


def has_enough_vacation_days_left(
    user: User, vacation_type: int, start_at: datetime, end_at: datetime
) -> bool:
    """
    휴가 신청 시 사용 가능한 휴가를 초과하는지 확인합니다.
    """
    user_profile = Profile.objects.get(user=user)

    vacation_days = 0
    if is_category_day_off(vacation_type=vacation_type):
        vacation_days = (end_at - start_at).days
    elif vacation_type == VacationTypes.HALF_DAY_OFF.value:
        vacation_days = 0.5
    elif vacation_type == VacationTypes.ONE_FOURTH_DAY_OFF.value:
        vacation_days = 0.25

    if user_profile.total_days >= vacation_days + get_total_used_days(
        user_profile=user_profile, approval=["0", "1"]
    ):
        return False
    return True


def convert_str_to_datetime(date: Any) -> datetime:
    return (
        parser.isoparse(parser.parse(date).isoformat()) if type(date) == str else date
    )


def get_datetime_obj(date: Any) -> datetime:
    return (
        parser.isoparse(parser.parse(date).isoformat()) if type(date) == str else date
    )


def get_half_day_off_end_at(start_at: str) -> datetime:
    return get_datetime_obj(start_at) + timedelta(hours=4)


def get_one_fourth_day_off_end_at(start_at: str) -> datetime:
    return get_datetime_obj(start_at) + timedelta(hours=2)
