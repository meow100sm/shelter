from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from django_otp.plugins.otp_totp.models import TOTPDevice

from accounts.models import AuditLog


class AccountsSmokeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()

        self.admin = self.User.objects.create_user(
            username="admin",
            password="adminpass",
            role="admin",
        )
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

    def test_login_success_creates_audit_log(self):
        resp = self.client.post(
            reverse("accounts:login"),
            {"username": "admin", "password": "adminpass"},
            follow=False,
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(AuditLog.objects.filter(user=self.admin, action="login").exists())

    def test_admin_only_user_list_redirects_for_volunteer(self):
        self.client.login(username="volunteer", password="volpass")
        resp = self.client.get(reverse("accounts:user_list"))
        self.assertEqual(resp.status_code, 302)

    def test_admin_only_user_list_ok_for_admin(self):
        self.client.login(username="admin", password="adminpass")
        resp = self.client.get(reverse("accounts:user_list"))
        self.assertEqual(resp.status_code, 200)

    def test_admin_with_2fa_device_redirects_to_2fa(self):
        # confirmed=True so user_has_device(user) is True
        TOTPDevice.objects.create(user=self.admin, name="default", confirmed=True)

        resp = self.client.post(
            reverse("accounts:login"),
            {"username": "admin", "password": "adminpass"},
            follow=False,
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse("accounts:2fa_verify"))

    def test_vet_profile_shows_2fa_settings_section(self):
        self.client.login(username="vet", password="vetpass")
        resp = self.client.get(reverse("accounts:profile"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Настройка двухфакторной аутентификации")
