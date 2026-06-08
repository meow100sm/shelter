from django.core.management.base import BaseCommand

from animals.reminders import send_vet_due_reminders

class Command(BaseCommand):
    help = 'Отправляет напоминания о предстоящих обработках'

    def handle(self, *args, **_options):
        result = send_vet_due_reminders(days_before=3)
        self.stdout.write(
            f'Обработано: {result.processed}; отправлено: {result.sent}; без email: {result.skipped_no_email}'
        )