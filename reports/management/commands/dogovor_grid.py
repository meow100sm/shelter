from __future__ import annotations

import io
import os

from django.core.management.base import BaseCommand

from reportlab.pdfgen import canvas

from reports.dogovor_overlay import (
    get_dogovor_template_path,
    get_template_page_size,
    merge_template_with_overlay,
)


class Command(BaseCommand):
    help = "Generate dogovor.pdf with coordinate grid overlay (for mapping field positions)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--out",
            default="dogovor_grid.pdf",
            help="Output PDF filename (default: dogovor_grid.pdf) in project root.",
        )
        parser.add_argument(
            "--step",
            type=int,
            default=50,
            help="Grid step in points (default: 50).",
        )

    def handle(self, *args, **options):
        template_path = get_dogovor_template_path()
        page_count, page_size = get_template_page_size(template_path)
        step = int(options["step"])

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=page_size)

        width, height = page_size
        for page in range(1, page_count + 1):
            c.setFont("Helvetica", 6)

            # vertical lines
            x = 0
            while x <= width:
                c.line(x, 0, x, height)
                c.drawString(x + 2, 2, str(int(x)))
                x += step

            # horizontal lines
            y = 0
            while y <= height:
                c.line(0, y, width, y)
                c.drawString(2, y + 2, str(int(y)))
                y += step

            c.setFont("Helvetica-Bold", 10)
            c.drawString(10, height - 20, f"PAGE {page}")
            c.showPage()

        c.save()
        buf.seek(0)

        merged = merge_template_with_overlay(template_path=template_path, overlay_pdf=buf)

        out_name = options["out"]
        out_path = os.path.join(os.getcwd(), out_name)
        with open(out_path, "wb") as f:
            f.write(merged)

        self.stdout.write(self.style.SUCCESS(f"Wrote {out_path}"))
