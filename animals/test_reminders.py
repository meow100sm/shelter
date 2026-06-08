from __future__ import annotations

from datetime import date

from django.core import mail
from django.test import TestCase, override_settings

from animals.models import Animal, VetRecord
from animals.reminders import send_vet_due_reminders


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="test-from@shelter.local",
)
class TestVetDueReminders(TestCase):
    def test_sends_reminder_exactly_days_before(self):
        today = date(2026, 5, 27)
        target_date = date(2026, 5, 30)  # today + 3

        animal = Animal.objects.create(species="cat", sex="U", intake_date=today)

        # Due on target date -> should be processed and sent
        due_with_email = VetRecord.objects.create(
            animal=animal,
            date=today,
            type="vaccination",
            vet_email="vet@example.com",
            next_due_date=target_date,
        )

        # Due on target date but without email -> processed but skipped
        VetRecord.objects.create(
            animal=animal,
            date=today,
            type="exam",
            vet_email="",
            next_due_date=target_date,
        )

        # Not due on target date -> ignored
        VetRecord.objects.create(
            animal=animal,
            date=today,
            type="exam",
            vet_email="vet@example.com",
            next_due_date=date(2026, 5, 29),
        )

        # No next_due_date -> ignored
        VetRecord.objects.create(
            animal=animal,
            date=today,
            type="exam",
            vet_email="vet@example.com",
            next_due_date=None,
        )

        result = send_vet_due_reminders(days_before=3, today=today)

        self.assertEqual(result.processed, 2)
        self.assertEqual(result.sent, 1)
        self.assertEqual(result.skipped_no_email, 1)

        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.subject, "Напоминание о предстоящей обработке")
        self.assertEqual(msg.from_email, "test-from@shelter.local")
        self.assertEqual(msg.to, ["vet@example.com"])
        self.assertIn(str(due_with_email.next_due_date), msg.body)
        self.assertIn(due_with_email.get_type_display(), msg.body)
        self.assertIn(animal.unique_id, msg.body)
