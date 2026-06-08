from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse


class ReportsSmokeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.volunteer = self.User.objects.create_user(
            username="volunteer",
            password="volpass",
            role="volunteer",
        )
        self.vet = self.User.objects.create_user(
            username="vet",
            password="vetpass",
            role="vet",
        )

    def test_report_form_requires_login(self):
        resp = self.client.get(reverse("reports:report_form"))
        self.assertEqual(resp.status_code, 302)

    def test_report_form_ok_when_logged_in(self):
        # FR-19: отчёты доступны только admin/vet
        self.client.login(username="volunteer", password="volpass")
        resp_forbidden = self.client.get(reverse("reports:report_form"))
        self.assertEqual(resp_forbidden.status_code, 302)

        self.client.login(username="vet", password="vetpass")
        resp = self.client.get(reverse("reports:report_form"))
        self.assertEqual(resp.status_code, 200)
