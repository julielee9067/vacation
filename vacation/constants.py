from datetime import datetime
from enum import Enum

NUM_PRENOTICE_DAYS = 3
DATETIME_FORMAT = "%Y-%m-%d %H:%M"
DATE_FORMAT = "%Y-%m-%d"

APPROVAL_CHOICES = [("0", "대기"), ("1", "승인"), ("2", "거부")]
VACATION_CHOICES = [
    ("1", "연차/휴가"),
    ("2", "병가"),
    ("3", "반차"),
    ("4", "반반차"),
    ("5", "대체휴가"),
]


class VacationApproval(Enum):
    ON_HOLD = 0
    APPROVED = 1
    DENIED = 2


class VacationTypes(Enum):
    DAY_OFF = 1
    SICK_DAY = 2
    HALF_DAY_OFF = 3
    ONE_FOURTH_DAY_OFF = 4
    COMP_DAY = 5


class VacationMessages(object):
    START_GREATER_THAN_END = "시작 기간은 끝 기간보다 더 작아야 합니다. 다시 시도해주세요."
    START_LESS_THAN_NOW = "이전 시간은 선택하실 수 없습니다. 다시 시도해주세요."
    INVALID_DATES = "유효하지 않은 기간입니다. 기간을 정확히 입력하세요."
    PRENOTICE_WARNING = f"휴가 신청은 최소 {NUM_PRENOTICE_DAYS}일전 신청이 가능합니다."
    SUCCESSFUL_SUBMISSION = "휴가 신청이 완료되었습니다."
    NOT_ENOUGH_DAYS_LEFT = "잔여 휴가 일수가 부족합니다. "
    OVERLAPPED_VACATION = "선택하신 날짜에 이미 휴가가 존재합니다. 다시 선택해주세요."


class TestCaseCredentials(object):
    SUPERUSER_ID = "superuser"
    SUPERUSER_PW = "superuserpwd"
    USER_ID = "user"
    USER_PW = "password"


HOLIDAY_LIST = [
    datetime(2021, 8, 15),
    datetime(2021, 9, 20),
    datetime(2021, 9, 21),
    datetime(2021, 9, 22),
    datetime(2021, 10, 3),
    datetime(2021, 10, 9),
    datetime(2021, 12, 25),
]

SPECIAL_VACATION_TYPES = [
    str(VacationTypes.SICK_DAY.value),
    str(VacationTypes.COMP_DAY.value),
]
