import datetime

from django.contrib.auth.models import User

from vacation.constants import VacationApproval, VacationTypes
from vacation.models import Vacation
from vacation.utils import get_end_at


def create_vacation_objects(user: User):
    create_two_day_offs(user=user)
    create_half_day_off(user=user)
    create_one_fourth_day_off(user=user)


def create_two_day_offs(user: User) -> Vacation:
    return Vacation.objects.create(
        cat=str(VacationTypes.DAY_OFF.value),
        user=user,
        start_at=datetime.datetime(2021, 12, 30, 11, 00),
        end_at=datetime.datetime(2021, 12, 31, 11, 00),
        approval=str(VacationApproval.APPROVED.value),
    )


def create_half_day_off(user: User) -> Vacation:
    return Vacation.objects.create(
        cat=str(VacationTypes.HALF_DAY_OFF.value),
        user=user,
        start_at=datetime.datetime(2021, 7, 30, 11, 00),
        end_at=get_end_at(
            vacation_type=VacationTypes.HALF_DAY_OFF.value,
            start_at=datetime.datetime(2021, 7, 30, 11, 00),
        ),
        approval=str(VacationApproval.DENIED.value),
    )


def create_one_fourth_day_off(user: User) -> Vacation:
    return Vacation.objects.create(
        cat=str(VacationTypes.ONE_FOURTH_DAY_OFF.value),
        user=user,
        start_at=datetime.datetime(2021, 8, 3, 14, 50),
        end_at=get_end_at(
            vacation_type=VacationTypes.ONE_FOURTH_DAY_OFF.value,
            start_at=datetime.datetime(2021, 8, 3, 14, 50),
        ),
        approval=str(VacationApproval.APPROVED.value),
    )
