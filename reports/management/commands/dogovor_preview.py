from __future__ import annotations

import os

from django.core.management.base import BaseCommand

from animals.models import Animal
from reports.dogovor_overlay import render_dogovor_from_template


class Command(BaseCommand):
    help = "Render a filled dogovor.pdf for a given Animal ID and write it to disk for visual checking."

    def add_arguments(self, parser):
        parser.add_argument("animal_id", type=int)
        parser.add_argument(
            "--out",
            default=None,
            help="Output PDF filename (default: dogovor_filled_<id>.pdf) in project root.",
        )

    def handle(self, *args, **options):
        animal = Animal.objects.get(pk=options["animal_id"])
        values = {
            "animal_unique_id": animal.unique_id,
            "animal_name": animal.name or "",
            "animal_species": animal.get_species_display(),
            "animal_sex": animal.get_sex_display(),
            "animal_breed": animal.breed or "",
            "animal_color": animal.color or "",
            "animal_features": animal.features or "",
            "animal_approx_age": animal.approx_age or "",
        }

        pdf_bytes = render_dogovor_from_template(values=values)

        out_name = options["out"] or f"dogovor_filled_{animal.pk}.pdf"
        out_path = os.path.join(os.getcwd(), out_name)
        with open(out_path, "wb") as f:
            f.write(pdf_bytes)

        self.stdout.write(self.style.SUCCESS(f"Wrote {out_path}"))
