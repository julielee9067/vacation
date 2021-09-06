import datetime

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse, reverse_lazy

from core.models import Profile
from vacation.constants import TestCaseCredentials, VacationApproval, VacationTypes
from vacation.forms import VacationForm, VacationYearSelectForm
from vacation.models import Vacation
from vacation.tests.utils import (
    create_half_day_off,
    create_two_day_offs,
    create_vacation_objects,
)


class BaseTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username=TestCaseCredentials.SUPERUSER_ID,
            password=TestCaseCredentials.SUPERUSER_PW,
        )
        cls.user = User.objects.create_user(
            username=TestCaseCredentials.USER_ID, password=TestCaseCredentials.USER_PW
        )
        cls.superuser_profile = Profile.objects.create(user=cls.superuser)
        cls.user_profile = Profile.objects.create(user=cls.user)

    @classmethod
    def setUp(cls) -> None:
        cls.client = Client()


class TestVacationForm(TestCase):
    def test_is_valid(self):
        form_data = {
            "day_off_start_at": None,
            "day_off_end_at": None,
            "half_day_off_start_at": None,
            "one_fourth_day_off_start_at": datetime.datetime.now().strftime(
                "%m/%d/%Y %H:%M"
            ),
            "cat": str(VacationTypes.ONE_FOURTH_DAY_OFF.value),
        }
        form = VacationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_is_invalid(self):
        form_data = {
            "day_off_start_at": None,
            "day_off_end_at": None,
            "half_day_off_start_at": "",
            "one_fourth_day_off_start_at": "",
            "cat": str(VacationTypes.ONE_FOURTH_DAY_OFF.value),
        }
        form = VacationForm(data=form_data)
        self.assertFalse(form.is_valid())


class TestVacationRangeSelectForm(TestCase):
    def test_is_valid(self):
        form_data = {
            "range_start": 2020,
            "range_end": 2021,
        }
        form = VacationYearSelectForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_is_invalid(self):
        reversed_form_data = {
            "year": 1000,
        }
        form = VacationYearSelectForm(data=reversed_form_data)
        self.assertFalse(form.is_valid())


class TestIndexView(BaseTestCase):
    def test_status_code(self):
        url = reverse_lazy("vacation:index")
        response = self.client.get(path=url)
        self.assertRedirects(
            response=response,
            expected_url=f"{reverse('login')}?next={reverse('vacation:index')}",
            status_code=302,
            target_status_code=200,
        )
        self.client.login(
            username=TestCaseCredentials.USER_ID, password=TestCaseCredentials.USER_PW
        )
        response = self.client.get(path=url)
        self.assertEqual(200, response.status_code)


class TestVacationListView(BaseTestCase):
    def test_status_code(self):
        self.client.login(
            username=TestCaseCredentials.USER_ID, password=TestCaseCredentials.USER_PW
        )
        url = reverse_lazy("vacation:list", kwargs={"user_id": self.user.id})
        response = self.client.get(path=url)
        self.assertEqual(200, response.status_code)

    def test_accessing_different_user(self):
        new_user = User.objects.create_user(username="test", password="test")
        self.client.login(username="test", password="test")
        create_half_day_off(user=new_user)

        # Try to access different user's vacation profile
        url = reverse_lazy("vacation:list", kwargs={"user_id": self.user.id})
        response = self.client.get(path=url)
        self.assertEqual(response.status_code, 200)

        # Should only display new_user's vacation list no matter what
        self.assertEqual(
            set(response.context["vacation_list"]),
            set(Vacation.objects.filter(user=new_user)),
        )

    def test_get_queryset_without_year_range(self):
        create_vacation_objects(user=self.user)
        self.client.login(
            username=TestCaseCredentials.USER_ID, password=TestCaseCredentials.USER_PW
        )
        url = reverse_lazy("vacation:list", kwargs={"user_id": self.user.id})
        response = self.client.get(path=url)
        expected_qs = Vacation.objects.filter(user=self.user)
        self.assertEqual(set(expected_qs), set(response.context["vacation_list"]))

    def test_get_queryset_with_year_range(self):
        # Create vacation in year 2020
        Vacation.objects.create(
            cat=str(VacationTypes.DAY_OFF.value),
            user=self.user,
            start_at=datetime.datetime(2020, 3, 9, 0, 0, 0),
            end_at=datetime.datetime(2020, 3, 11, 0, 0, 0),
            approval=str(VacationApproval.APPROVED.value),
        )

        # Create vacation in year 2021
        create_two_day_offs(user=self.user)

        self.client.login(
            username=TestCaseCredentials.USER_ID, password=TestCaseCredentials.USER_PW
        )
        url = reverse_lazy("vacation:list", kwargs={"user_id": self.user.id})
        response = self.client.get(
            url,
            {"year": 2020},
        )
        expected_qs = Vacation.objects.filter(
            user=self.user,
            start_at__gt=datetime.datetime(2020, 1, 1),
            start_at__lt=datetime.datetime(2020, 12, 31),
        )
        self.assertEqual(set(expected_qs), set(response.context["vacation_list"]))


class TestVacationCreateView(BaseTestCase):
    def test_status_code(self):
        self.client.login(
            username=TestCaseCredentials.USER_ID, password=TestCaseCredentials.USER_PW
        )
        url = reverse_lazy("vacation:register")
        response = self.client.get(path=url)
        self.assertEqual(200, response.status_code)

    def test_form_invalid(self):
        self.client.login(
            username=TestCaseCredentials.USER_ID, password=TestCaseCredentials.USER_PW
        )
        start_at = datetime.datetime.now().replace(
            second=0, microsecond=0
        ) + datetime.timedelta(days=7)
        url = reverse_lazy("vacation:register")
        wrong_end_at = {
            "cat": "1",
            "day_off_start_at": start_at.date(),
            "day_off_end_at": start_at.date() + datetime.timedelta(days=-3),
            "half_day_off_start_at": "",
            "one_fourth_day_off_start_at": "",
        }
        response = self.client.post(url, wrong_end_at, follow=True)
        self.assertEqual(response.status_code, 200)

        not_prenotified = {
            "cat": "1",
            "day_off_start_at": start_at.date() - datetime.timedelta(days=-7),
            "day_off_end_at": start_at.date() + datetime.timedelta(days=2),
            "half_day_off_start_at": "",
            "one_fourth_day_off_start_at": "",
        }
        response = self.client.post(url, not_prenotified, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Vacation.objects.all().count(), 0)

    def test_form_valid(self):
        self.client.login(
            username=TestCaseCredentials.USER_ID, password=TestCaseCredentials.USER_PW
        )
        start_at = datetime.datetime.now().replace(
            second=0, microsecond=0
        ) + datetime.timedelta(days=8)
        test_dict = {
            "cat": "1",
            "day_off_start_at": start_at.date(),
            "day_off_end_at": start_at.date() + datetime.timedelta(days=2),
            "half_day_off_start_at": "",
            "one_fourth_day_off_start_at": "",
        }
        url = reverse_lazy("vacation:register")
        response = self.client.post(url, test_dict, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Vacation.objects.all().count(), 1)


class TestVacationUpdateView(BaseTestCase):
    def test_status_code(self):
        self.client.login(
            username=TestCaseCredentials.USER_ID, password=TestCaseCredentials.USER_PW
        )
        url = reverse_lazy("vacation:update", kwargs={"pk": 1})
        response = self.client.get(path=url)
        self.assertEqual(404, response.status_code)

        new_vacation = create_two_day_offs(user=self.user)
        url = reverse_lazy("vacation:update", kwargs={"pk": new_vacation.id})
        response = self.client.get(path=url)
        self.assertEqual(200, response.status_code)

    def test_update(self):
        self.client.login(
            username=TestCaseCredentials.USER_ID, password=TestCaseCredentials.USER_PW
        )
        new_vacation = create_two_day_offs(user=self.user)
        url = reverse_lazy("vacation:update", kwargs={"pk": new_vacation.id})
        test_dict = {
            "cat": VacationTypes.DAY_OFF.value,
            "day_off_start_at": new_vacation.start_at.date()
            + datetime.timedelta(days=1),
            "day_off_end_at": new_vacation.end_at.date() + datetime.timedelta(days=3),
        }
        response = self.client.post(url, test_dict)
        self.assertRedirects(
            response, reverse("vacation:list", kwargs={"user_id": self.user.id})
        )
        self.assertEqual(
            Vacation.objects.get(id=new_vacation.id).end_at.date(),
            new_vacation.end_at.date() + datetime.timedelta(days=3),
        )


class TestVacationDeleteView(BaseTestCase):
    def test_status_code(self):
        self.client.login(
            username=TestCaseCredentials.USER_ID, password=TestCaseCredentials.USER_PW
        )
        url = reverse_lazy("vacation:delete", kwargs={"pk": 1})
        response = self.client.get(path=url)
        self.assertEqual(404, response.status_code)

        new_vacation = create_two_day_offs(user=self.user)
        url = reverse_lazy("vacation:delete", kwargs={"pk": new_vacation.id})
        response = self.client.get(path=url)
        self.assertEqual(200, response.status_code)

    def test_delete(self):
        self.client.login(
            username=TestCaseCredentials.USER_ID, password=TestCaseCredentials.USER_PW
        )
        new_vacation = create_two_day_offs(user=self.user)
        original_length = Vacation.objects.all().count()
        url = reverse_lazy("vacation:delete", kwargs={"pk": new_vacation.id})
        response = self.client.post(url)
        self.assertRedirects(
            response, reverse("vacation:list", kwargs={"user_id": self.user.id})
        )
        self.assertEqual(Vacation.objects.all().count(), original_length - 1)
