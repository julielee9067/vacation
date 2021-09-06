import datetime

from django.contrib.auth.models import User
from django.urls import reverse, reverse_lazy

from core.models import Profile
from vacation.constants import TestCaseCredentials, VacationApproval, VacationTypes
from vacation.forms import SickForm
from vacation.models import Vacation
from vacation.tests.test_integration import BaseTestCase
from vacation.tests.utils import create_half_day_off, create_two_day_offs


class TestSickForm(BaseTestCase):
    def test_is_valid(self):
        form_data = {
            "day_off_start_at": None,
            "day_off_end_at": None,
            "sick_day_off_start_at": None,
            "sick_day_off_end_at": None,
            "half_day_off_start_at": None,
            "one_fourth_day_off_start_at": datetime.datetime.now().strftime(
                "%m/%d/%Y %H:%M"
            ),
            "cat": str(VacationTypes.ONE_FOURTH_DAY_OFF.value),
            "user": self.user,
        }
        form = SickForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_is_invalid(self):
        form_data = {
            "day_off_start_at": None,
            "day_off_end_at": None,
            "sick_day_off_start_at": None,
            "sick_day_off_end_at": None,
            "half_day_off_start_at": "",
            "one_fourth_day_off_start_at": "",
            "cat": str(VacationTypes.ONE_FOURTH_DAY_OFF.value),
            "user": self.user,
        }
        form = SickForm(data=form_data)
        self.assertFalse(form.is_valid())


class TestAdminIndexView(BaseTestCase):
    def test_status_code(self):
        url = reverse_lazy("vacation:admin")
        response = self.client.get(path=url)
        self.assertRedirects(
            response=response,
            expected_url=f"{reverse('login')}?next={reverse('vacation:admin')}",
            status_code=302,
            target_status_code=200,
        )
        self.client.login(
            username=TestCaseCredentials.SUPERUSER_ID,
            password=TestCaseCredentials.SUPERUSER_PW,
        )
        response = self.client.get(path=url)
        self.assertEqual(200, response.status_code)


class TestAdminVacationUpdateView(BaseTestCase):
    def test_status_code(self):
        self.client.login(
            username=TestCaseCredentials.SUPERUSER_ID,
            password=TestCaseCredentials.SUPERUSER_PW,
        )
        url = reverse_lazy("vacation:admin_update", kwargs={"pk": 1})
        response = self.client.get(path=url)
        self.assertEqual(404, response.status_code)

        new_vacation = create_two_day_offs(user=self.user)
        url = reverse_lazy("vacation:admin_update", kwargs={"pk": new_vacation.id})
        response = self.client.get(path=url)
        self.assertEqual(200, response.status_code)

    def test_update(self):
        self.client.login(
            username=TestCaseCredentials.SUPERUSER_ID,
            password=TestCaseCredentials.SUPERUSER_PW,
        )
        new_vacation = create_two_day_offs(user=self.superuser)
        url = reverse_lazy("vacation:admin_update", kwargs={"pk": new_vacation.id})
        test_dict = {
            "cat": VacationTypes.DAY_OFF.value,
            "day_off_start_at": new_vacation.start_at.date()
            + datetime.timedelta(days=1),
            "day_off_end_at": new_vacation.end_at.date() + datetime.timedelta(days=3),
            "approval": VacationApproval.APPROVED.value,
        }
        response = self.client.post(url, test_dict)
        self.assertEqual(
            Vacation.objects.get(id=new_vacation.id).end_at.date(),
            new_vacation.end_at.date() + datetime.timedelta(days=3),
        )
        self.assertRedirects(response, reverse("vacation:member_list"))


class TestMemberListView(BaseTestCase):
    def test_status_code(self):
        self.client.login(
            username=TestCaseCredentials.SUPERUSER_ID,
            password=TestCaseCredentials.SUPERUSER_PW,
        )
        url = reverse_lazy("vacation:member_list")
        response = self.client.get(path=url)
        self.assertEqual(200, response.status_code)

    def test_get_queryset_with_member_name(self):
        self.client.login(
            username=TestCaseCredentials.SUPERUSER_ID,
            password=TestCaseCredentials.SUPERUSER_PW,
        )
        url = reverse_lazy("vacation:member_list")
        response = self.client.get(
            url,
            {
                "member_name": "test",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["vacation_list"]), 0)
        new_user = User.objects.create_user(
            username="test", password="test", first_name="test"
        )
        create_half_day_off(user=new_user)
        response = self.client.get(
            url,
            {
                "member_name": "test",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["vacation_list"]), 1)


class TestSickCreateView(BaseTestCase):
    def test_status_code(self):
        self.client.login(
            username=TestCaseCredentials.SUPERUSER_ID,
            password=TestCaseCredentials.SUPERUSER_PW,
        )
        url = reverse_lazy("vacation:sick")
        response = self.client.get(path=url)
        self.assertEqual(200, response.status_code)

    def test_form_invalid(self):
        self.client.login(
            username=TestCaseCredentials.SUPERUSER_ID,
            password=TestCaseCredentials.SUPERUSER_PW,
        )
        start_at = datetime.datetime.now().replace(
            second=0, microsecond=0
        ) + datetime.timedelta(days=7)
        url = reverse_lazy("vacation:sick")
        wrong_end_at = {
            "cat": "1",
            "day_off_start_at": start_at.date(),
            "day_off_end_at": start_at.date() + datetime.timedelta(days=-3),
            "half_day_off_start_at": "",
            "one_fourth_day_off_start_at": "",
            "user": self.user,
        }
        response = self.client.post(url, wrong_end_at, follow=True)
        self.assertEqual(response.status_code, 200)

        not_prenotified = {
            "cat": "1",
            "day_off_start_at": start_at.date() - datetime.timedelta(days=-7),
            "day_off_end_at": start_at.date() + datetime.timedelta(days=2),
            "sick_day_off_start_at": "",
            "sick_day_off_end_at": "",
            "half_day_off_start_at": "",
            "one_fourth_day_off_start_at": "",
            "user": self.user,
        }
        response = self.client.post(url, not_prenotified, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Vacation.objects.all().count(), 0)

    def test_form_valid(self):
        self.client.login(
            username=TestCaseCredentials.SUPERUSER_ID,
            password=TestCaseCredentials.SUPERUSER_PW,
        )
        start_at = datetime.datetime.now().replace(
            second=0, microsecond=0
        ) + datetime.timedelta(days=8)
        test_dict = {
            "day_off_start_at": "",
            "day_off_end_at": "",
            "sick_day_off_start_at": "",
            "sick_day_off_end_at": "",
            "half_day_off_start_at": "",
            "one_fourth_day_off_start_at": start_at.strftime("%m/%d/%Y %H:%M"),
            "cat": str(VacationTypes.ONE_FOURTH_DAY_OFF.value),
            "user": self.user.id,
        }
        url = reverse_lazy("vacation:sick")
        response = self.client.post(url, test_dict, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Vacation.objects.all().count(), 1)


class TestUserVacationListView(BaseTestCase):
    def test_status_code(self):
        self.client.login(
            username=TestCaseCredentials.SUPERUSER_ID,
            password=TestCaseCredentials.SUPERUSER_PW,
        )
        url = reverse_lazy("vacation:users_vacation")
        response = self.client.get(path=url)
        self.assertEqual(200, response.status_code)

    def test_get_vacation_days(self):
        self.client.login(
            username=TestCaseCredentials.SUPERUSER_ID,
            password=TestCaseCredentials.SUPERUSER_PW,
        )
        url = reverse_lazy("vacation:users_vacation")
        response = self.client.get(path=url)
        for user in response.context["user_list"].iterator():
            user_profile = Profile.objects.get(user=user)
            self.assertEqual(user_profile.total_days, 15)


class TestUserVacationDayUpdateView(BaseTestCase):
    def test_status_code(self):
        self.client.login(
            username=TestCaseCredentials.SUPERUSER_ID,
            password=TestCaseCredentials.SUPERUSER_PW,
        )
        url = reverse_lazy("vacation:vacation_update", kwargs={"pk": self.user.id})
        response = self.client.get(path=url)
        self.assertEqual(200, response.status_code)

    def test_update_vacation_days(self):
        self.client.login(
            username=TestCaseCredentials.SUPERUSER_ID,
            password=TestCaseCredentials.SUPERUSER_PW,
        )
        url = reverse_lazy("vacation:vacation_update", kwargs={"pk": self.user.id})
        test_dict = {"total_days": 10}
        response = self.client.post(url, test_dict)
        self.assertRedirects(response, reverse("vacation:users_vacation"))
        new_vac_days = Profile.objects.get(user=self.user).total_days
        self.assertEqual(new_vac_days, 10)


class TestVacationApprovalView(BaseTestCase):
    def test_status_code(self):
        self.client.login(
            username=TestCaseCredentials.SUPERUSER_ID,
            password=TestCaseCredentials.SUPERUSER_PW,
        )
        url = reverse_lazy("vacation:approval", kwargs={"pk": 1})
        response = self.client.get(path=url)
        self.assertEqual(404, response.status_code)

        new_vacation = create_two_day_offs(user=self.user)
        url = reverse_lazy("vacation:approval", kwargs={"pk": new_vacation.id})
        response = self.client.get(path=url)
        self.assertEqual(200, response.status_code)

    def test_change_approval(self):
        self.client.login(
            username=TestCaseCredentials.SUPERUSER_ID,
            password=TestCaseCredentials.SUPERUSER_PW,
        )
        new_vacation = create_two_day_offs(user=self.user)
        url = reverse_lazy("vacation:approval", kwargs={"pk": new_vacation.id})
        test_dict = {"approval": "2"}
        response = self.client.post(url, test_dict)
        self.assertRedirects(response, reverse("vacation:admin"))
        self.assertEqual(Vacation.objects.get(id=new_vacation.id).approval, "2")
