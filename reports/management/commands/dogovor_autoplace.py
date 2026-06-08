from __future__ import annotations

import json
import os

from django.core.management.base import BaseCommand

from reports.dogovor_autoplace import build_default_animal_placements, placements_to_json_dict
from reports.dogovor_overlay import get_dogovor_template_path


class Command(BaseCommand):
    help = "Auto-detect animal field coordinates in dogovor.pdf and write reports/dogovor_placements.json"

    def handle(self, *args, **options):
        template_path = get_dogovor_template_path()
        placements = build_default_animal_placements(template_path)
        payload = placements_to_json_dict(placements)

        out_path = os.path.join(os.path.dirname(__file__), "..", "..", "dogovor_placements.json")
        out_path = os.path.normpath(out_path)

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        self.stdout.write(self.style.SUCCESS(f"Wrote {out_path}"))
        for p in placements:
            self.stdout.write(f"- page {p.page}: {p.key} @ ({p.x:.1f}, {p.y:.1f})")
