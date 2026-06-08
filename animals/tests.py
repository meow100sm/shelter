from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from animals.models import Animal


class AnimalsSmokeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.volunteer = self.User.objects.create_user(
            username="volunteer",
            password="volpass",
            role="volunteer",
        )

    def test_dashboard_ok_for_anonymous(self):
        resp = self.client.get(reverse("animals:dashboard"))
        self.assertEqual(resp.status_code, 200)

    def test_animal_list_ok_for_anonymous(self):
        resp = self.client.get(reverse("animals:animal_list"))
        self.assertEqual(resp.status_code, 200)

    def test_animal_create_requires_login(self):
        resp = self.client.get(reverse("animals:animal_create"))
        self.assertEqual(resp.status_code, 302)

    def test_volunteer_can_create_animal_min_fields(self):
        self.client.login(username="volunteer", password="volpass")

        resp = self.client.post(
            reverse("animals:animal_create"),
            {
                "species": "cat",
                "sex": "U",
                "intake_date": "2026-05-25",
            },
            follow=False,
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Animal.objects.count(), 1)
        animal = Animal.objects.first()
        self.assertTrue(animal.unique_id.startswith("AN-"))

    def test_movement_list_requires_login(self):
        resp = self.client.get(reverse("animals:movement_list"))
        self.assertEqual(resp.status_code, 302)

        self.client.login(username="volunteer", password="volpass")
        resp2 = self.client.get(reverse("animals:movement_list"))
        self.assertEqual(resp2.status_code, 200)
