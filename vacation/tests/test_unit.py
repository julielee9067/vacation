import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from core.models import Profile
from vacation.constants import NUM_PRENOTICE_DAYS, TestCaseCredentials, VacationTypes
from vacation.tests.utils import create_two_day_offs, create_vacation_objects
from vacation.utils import (
    convert_date_to_datetime,
    convert_start_and_end_at,
    convert_str_to_datetime,
    does_vacation_overlap,
    get_end_at,
    get_start_and_end_at,
    get_total_used_days,
    is_category_day_off,
    is_vacation_prenotified,
)


class TestUtils(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username=TestCaseCredentials.USER_ID, password=TestCaseCredentials.USER_PW
        )
        cls.user_profile = Profile.objects.create(user=cls.user)

    def test_get_total_used_vacation_days(self):
        create_vacation_objects(user=self.user)
        self.user.save()
        self.assertEqual(2.25, get_total_used_days(self.user_profile))

    def test_convert_date_to_datetime(self):
        original_date = datetime.date(2021, 7, 21)
        self.assertEqual(
            datetime.datetime(2021, 7, 21, 0, 0),
            convert_date_to_datetime(original_date=original_date),
        )

    def test_does_vacation_overlap(self):
        create_two_day_offs(user=self.user)
        start = datetime.datetime(2021, 12, 27, 11, 00)
        end = datetime.datetime(2021, 12, 28, 11, 00)
        self.assertFalse(does_vacation_overlap(user=self.user, start=start, end=end))

        start = datetime.datetime(2021, 12, 29, 11, 00)
        end = datetime.datetime(2021, 12, 31, 11, 00)
        self.assertTrue(does_vacation_overlap(user=self.user, start=start, end=end))

    def test_is_category_day_off(self):
        self.assertTrue(is_category_day_off(vacation_type=VacationTypes.DAY_OFF.value))
        self.assertTrue(is_category_day_off(vacation_type=VacationTypes.SICK_DAY.value))
        self.assertFalse(
            is_category_day_off(vacation_type=VacationTypes.HALF_DAY_OFF.value)
        )
        self.assertFalse(
            is_category_day_off(vacation_type=VacationTypes.ONE_FOURTH_DAY_OFF.value)
        )

    def test_is_vacation_prenotified(self):
        prenotified = datetime.datetime.now() + datetime.timedelta(
            days=NUM_PRENOTICE_DAYS + 2
        )
        not_prenotified = datetime.datetime.now() + datetime.timedelta(hours=5)
        self.assertTrue(is_vacation_prenotified(date=prenotified))
        self.assertFalse(is_vacation_prenotified(date=not_prenotified))

    def test_convert_str_to_datetime(self):
        date_type_obj = datetime.datetime.now()
        str_type_obj = date_type_obj.isoformat()
        self.assertEqual(date_type_obj, convert_str_to_datetime(date=date_type_obj))
        self.assertEqual(date_type_obj, convert_str_to_datetime(date=str_type_obj))

    def test_get_end_at(self):
        start_at = datetime.datetime.now()
        expected_half_day_end_at = start_at + datetime.timedelta(hours=4)
        self.assertEqual(
            expected_half_day_end_at,
            get_end_at(
                vacation_type=VacationTypes.HALF_DAY_OFF.value, start_at=start_at
            ),
        )
        expected_one_fourth_day_end_at = start_at + datetime.timedelta(hours=2)
        self.assertEqual(
            expected_one_fourth_day_end_at,
            get_end_at(
                vacation_type=VacationTypes.ONE_FOURTH_DAY_OFF.value, start_at=start_at
            ),
        )
        self.assertRaises(
            ValueError,
            get_end_at,
            vacation_type=VacationTypes.DAY_OFF.value,
            start_at=start_at,
        )

    def test_convert_start_and_end_at(self):
        start_at = datetime.datetime.now()
        self.assertEqual(
            (start_at, start_at + datetime.timedelta(hours=2)),
            convert_start_and_end_at(
                start_at=start_at,
                vacation_type=VacationTypes.ONE_FOURTH_DAY_OFF.value,
                end_at=None,
            ),
        )
        sick_day_start_at = start_at.date()
        self.assertEqual(
            (
                start_at.replace(hour=0, minute=0, second=0, microsecond=0),
                start_at.replace(hour=0, minute=0, second=0, microsecond=0)
                + datetime.timedelta(days=2),
            ),
            convert_start_and_end_at(
                start_at=sick_day_start_at,
                vacation_type=VacationTypes.SICK_DAY.value,
                end_at=sick_day_start_at + datetime.timedelta(days=2),
            ),
        )

    def test_get_start_and_end_at(self):
        start_at = datetime.datetime.now().replace(second=0, microsecond=0)
        day_off_test_dict = {
            "user": self.user,
            "cat": "1",
            "day_off_start_at": start_at.date(),
            "day_off_end_at": start_at.date() + datetime.timedelta(days=3),
            "sick_day_off_start_at": None,
            "half_day_off_start_at": "",
            "one_fourth_day_off_start_at": "",
        }
        self.assertEqual(
            (
                start_at.replace(hour=0, minute=0),
                start_at.replace(hour=0, minute=0) + datetime.timedelta(days=3),
            ),
            get_start_and_end_at(
                data=day_off_test_dict, vacation_type=VacationTypes.DAY_OFF.value
            ),
        )

        one_fourth_day_off_test_dict = {
            "user": self.user,
            "cat": "4",
            "day_off_start_at": None,
            "day_off_end_at": None,
            "sick_day_off_start_at": None,
            "sick_day_off_end_at": None,
            "half_day_off_start_at": "",
            "one_fourth_day_off_start_at": start_at.strftime("%m/%d/%Y %H:%M"),
        }
        self.assertEqual(
            (start_at, start_at + datetime.timedelta(hours=2)),
            get_start_and_end_at(
                data=one_fourth_day_off_test_dict,
                vacation_type=VacationTypes.ONE_FOURTH_DAY_OFF.value,
            ),
        )
