from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from animals.models import VetRecord


@dataclass(frozen=True)
class RemindersResult:
    processed: int
    sent: int
    skipped_no_email: int


def send_vet_due_reminders(*, days_before: int = 3, today: date | None = None) -> RemindersResult:
    """Send email reminders exactly `days_before` days before next_due_date.

    Uses VetRecord.vet_email as the recipient.

    Returns basic counters for logging/monitoring.
    """

    if today is None:
        # Use local date in configured TIME_ZONE (important when USE_TZ=True).
        today = timezone.localdate()

    target_date = today + timedelta(days=days_before)
    qs = VetRecord.objects.select_related("animal").filter(next_due_date=target_date)

    processed = 0
    sent = 0
    skipped_no_email = 0

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@shelter.local")

    for record in qs:
        processed += 1
        to_email = (record.vet_email or "").strip()
        if not to_email:
            skipped_no_email += 1
            continue

        subject = "Напоминание о предстоящей обработке"
        message = (
            f"Напоминание: через {days_before} дн. ({record.next_due_date}) запланировано: {record.get_type_display()}.\n"
            f"Животное: {record.animal.unique_id}.\n"
        )

        num_sent = send_mail(
            subject,
            message,
            from_email,
            [to_email],
            fail_silently=False,
        )
        sent += int(num_sent or 0)

    return RemindersResult(processed=processed, sent=sent, skipped_no_email=skipped_no_email)
