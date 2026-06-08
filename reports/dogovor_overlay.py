from __future__ import annotations

import io
import json
import os
from dataclasses import dataclass
from typing import Any

from django.conf import settings

try:
    from pypdf import PdfReader, PdfWriter
except ModuleNotFoundError:  # pragma: no cover
    PdfReader = None
    PdfWriter = None

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def _try_register_ttf(font_name: str, candidates: list[str]) -> bool:
    for path in candidates:
        if not path:
            continue
        try:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont(font_name, path))
                return True
        except Exception:
            continue
    return False


# Register a Unicode font for overlays.
# Goal: match the template's Times New Roman when available.
# Fallback: DejaVuSans (Cyrillic-safe) or Helvetica.
_DOGOVOR_FONT_REGULAR = "DogovorTimesNewRoman"
_DOGOVOR_FONT_BOLD = "DogovorTimesNewRoman-Bold"

_times_regular_ok = _try_register_ttf(
    _DOGOVOR_FONT_REGULAR,
    [
        os.environ.get("DOGOVOR_TTF_REGULAR", ""),
        os.path.join(settings.BASE_DIR, "static", "fonts", "TimesNewRoman.ttf"),
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "times.ttf"),
    ],
)

_try_register_ttf(
    _DOGOVOR_FONT_BOLD,
    [
        os.environ.get("DOGOVOR_TTF_BOLD", ""),
        os.path.join(settings.BASE_DIR, "static", "fonts", "TimesNewRoman-Bold.ttf"),
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "timesbd.ttf"),
    ],
)

_dejavu_ok = _try_register_ttf(
    "DejaVuSans",
    [os.path.join(settings.BASE_DIR, "static", "fonts", "DejaVuSans.ttf")],
)

if _times_regular_ok:
    DEFAULT_OVERLAY_FONT = _DOGOVOR_FONT_REGULAR
elif _dejavu_ok:
    DEFAULT_OVERLAY_FONT = "DejaVuSans"
else:
    DEFAULT_OVERLAY_FONT = "Helvetica"


@dataclass(frozen=True)
class Placement:
    key: str
    page: int
    x: float
    y: float
    font: str = "Times-Roman"
    font_size: float = 10


def _set_font_safe(c: canvas.Canvas, font_name: str, font_size: float) -> None:
    try:
        c.setFont(font_name, font_size)
    except Exception:
        c.setFont("Helvetica", font_size)


def _placements_path() -> str:
    return os.path.join(os.path.dirname(__file__), "dogovor_placements.json")


def load_placements() -> list[Placement]:
    path = _placements_path()
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    placements: list[Placement] = []
    for item in raw.get("fields", []):
        placements.append(
            Placement(
                key=str(item["key"]),
                page=int(item["page"]),
                x=float(item["x"]),
                y=float(item["y"]),
                font=str(item.get("font", DEFAULT_OVERLAY_FONT)),
                font_size=float(item.get("fontSize", 10)),
            )
        )
    return placements


def build_overlay_pdf(*, page_count: int, page_size: tuple[float, float], placements: list[Placement], values: dict[str, str]) -> io.BytesIO:
    """Build a same-size overlay PDF with text at specific coordinates.

    Coordinates use PDF points: origin bottom-left.
    """

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=page_size)

    placements_by_page: dict[int, list[Placement]] = {}
    for p in placements:
        placements_by_page.setdefault(p.page, []).append(p)

    for page in range(1, page_count + 1):
        for placement in placements_by_page.get(page, []):
            text = values.get(placement.key, "")
            if text is None:
                text = ""
            text = str(text)
            if not text.strip():
                continue
            _set_font_safe(c, placement.font, placement.font_size)
            c.drawString(placement.x, placement.y, text)
        c.showPage()

    c.save()
    buf.seek(0)
    return buf


def merge_template_with_overlay(*, template_path: str, overlay_pdf: io.BytesIO) -> bytes:
    if PdfReader is None or PdfWriter is None:
        raise RuntimeError("PDF template filling requires 'pypdf'. Install it in your environment.")

    reader = PdfReader(template_path)
    overlay_reader = PdfReader(overlay_pdf)

    if len(overlay_reader.pages) != len(reader.pages):
        raise ValueError("Overlay page count must match template")

    writer = PdfWriter()
    for base_page, overlay_page in zip(reader.pages, overlay_reader.pages):
        base_page.merge_page(overlay_page)
        writer.add_page(base_page)

    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out.getvalue()


def get_dogovor_template_path() -> str:
    return os.path.join(settings.BASE_DIR, "dogovor.pdf")


def get_template_page_size(template_path: str) -> tuple[int, tuple[float, float]]:
    if PdfReader is None:
        raise RuntimeError("Reading PDF template requires 'pypdf'.")

    reader = PdfReader(template_path)
    if not reader.pages:
        raise ValueError("Template has no pages")

    mb = reader.pages[0].mediabox
    page_size = (float(mb.width), float(mb.height))
    return len(reader.pages), page_size


def render_dogovor_from_template(*, values: dict[str, Any]) -> bytes:
    """Render final contract PDF by overlaying values onto the template.

    Requires a coordinate mapping in reports/dogovor_placements.json.
    """

    template_path = get_dogovor_template_path()
    if not os.path.exists(template_path):
        raise FileNotFoundError("dogovor.pdf not found in project root")

    page_count, page_size = get_template_page_size(template_path)
    placements = load_placements()
    if not placements:
        raise RuntimeError(
            "dogovor.pdf has no fillable fields. Configure coordinates in reports/dogovor_placements.json "
            "(use `python manage.py dogovor_grid` to generate a coordinate grid PDF)."
        )

    str_values = {k: "" if v is None else str(v) for k, v in values.items()}
    overlay = build_overlay_pdf(
        page_count=page_count,
        page_size=page_size,
        placements=placements,
        values=str_values,
    )
    return merge_template_with_overlay(template_path=template_path, overlay_pdf=overlay)
