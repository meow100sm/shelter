from __future__ import annotations

import os

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar, LTTextContainer, LTTextLine

try:
    import fitz  # PyMuPDF
except ModuleNotFoundError:  # pragma: no cover
    fitz = None

from reports.dogovor_overlay import DEFAULT_OVERLAY_FONT, Placement


def _iter_lines(template_path: str):
    for page_num, page_layout in enumerate(extract_pages(template_path), start=1):
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                for line in element:
                    if isinstance(line, LTTextLine):
                        yield page_num, line


def _underscore_start_x(line: LTTextLine) -> float | None:
    """Return x coordinate of the first underscore character in the line."""

    min_x: float | None = None
    for obj in getattr(line, "_objs", []):
        if isinstance(obj, LTChar):
            if obj.get_text() == "_":
                x0, _y0, _x1, _y1 = obj.bbox
                if min_x is None or x0 < min_x:
                    min_x = float(x0)
    return min_x


def _is_animal_field_line(line: LTTextLine) -> bool:
    text = line.get_text() or ""
    if text.count("_") < 8:
        return False

    x0, y0, x1, y1 = (float(v) for v in line.bbox)

    # Heuristic: these lines live in the left block and are single-line fields.
    if not (70 <= x0 <= 110):
        return False
    if (x1 - x0) < 80:
        return False
    if (y1 - y0) > 30:
        return False

    return True


def detect_animal_fields_for_pages(template_path: str, pages: list[int]) -> dict[int, list[LTTextLine]]:
    by_page: dict[int, list[LTTextLine]] = {p: [] for p in pages}
    for page_num, line in _iter_lines(template_path):
        if page_num not in by_page:
            continue
        if _is_animal_field_line(line):
            by_page[page_num].append(line)

    # Sort each page top-to-bottom and keep the top 7 lines.
    for p in list(by_page.keys()):
        lines = by_page[p]
        lines.sort(key=lambda ln: float(ln.bbox[1]), reverse=True)
        by_page[p] = lines[:7]

    return by_page


def build_default_animal_placements(template_path: str) -> list[Placement]:
    """Auto-detect placements for animal fields in the contract and act.

    This implementation is label-based (robust): it finds the exact label locations
    ("Вид:", "Порода:", etc.) on pages 1 and 4, then computes the start of the
    underline region for each field.

    Notes:
    - `dogovor.pdf` is not a fillable PDF form (no AcroForm fields).
    - We fill by overlaying text at PDF coordinates.
    """

    if not os.path.exists(template_path):
        raise FileNotFoundError(template_path)

    if fitz is None:
        raise RuntimeError("Auto-placement requires PyMuPDF (fitz). Install PyMuPDF.")

    # Build a lookup of pdfminer lines per page (bottom-left coordinates).
    lines_by_page: dict[int, list[LTTextLine]] = {1: [], 4: []}
    for page_num, line in _iter_lines(template_path):
        if page_num in lines_by_page:
            lines_by_page[page_num].append(line)

    doc = fitz.open(template_path)

    label_specs = [
        ("animal_species", "Вид:", "same"),
        ("animal_breed", "Порода:", "same"),
        ("animal_sex", "Пол:", "same"),
        ("animal_color", "Окрас:", "same"),
        ("animal_features", "Особые приметы:", "below"),
        ("animal_approx_age", "Возраст (приблизительно):", "same"),
        ("animal_name", "Кличка (на момент составления договора)", "same"),
    ]

    placements: list[Placement] = []

    for page in [1, 4]:
        fitz_page = doc.load_page(page - 1)
        page_height = float(fitz_page.rect.height)

        for key, label, mode in label_specs:
            rects = fitz_page.search_for(label)
            if not rects:
                raise RuntimeError(f"Label not found on page {page}: {label!r}")

            # Use first hit.
            r = rects[0]
            # Convert fitz (top-left origin) rect to bottom-left bbox.
            label_bbox_bl = (
                float(r.x0),
                float(page_height - r.y1),
                float(r.x1),
                float(page_height - r.y0),
            )

            # Find the pdfminer line that intersects the label rect.
            label_line: LTTextLine | None = None
            for ln in lines_by_page[page]:
                x0, y0, x1, y1 = (float(v) for v in ln.bbox)
                lx0, ly0, lx1, ly1 = label_bbox_bl
                if x1 < lx0 or x0 > lx1 or y1 < ly0 or y0 > ly1:
                    continue
                label_line = ln
                break

            if label_line is None:
                raise RuntimeError(f"Could not map label to a text line on page {page}: {label!r}")

            target_line = label_line
            underscore_x = _underscore_start_x(target_line)

            # For "Особые приметы" the underline is on the next line(s).
            if mode == "below" or underscore_x is None:
                # Find the closest underscore-heavy line below the label.
                x0, y0, x1, y1 = (float(v) for v in label_line.bbox)
                candidates: list[LTTextLine] = []
                for ln in lines_by_page[page]:
                    tx0, ty0, tx1, ty1 = (float(v) for v in ln.bbox)
                    if ty0 >= y0:
                        continue
                    if (y0 - ty0) > 80:
                        continue
                    if ln.get_text().count("_") < 8:
                        continue
                    # Keep lines roughly aligned with the label block.
                    if abs(tx0 - x0) > 20:
                        continue
                    candidates.append(ln)

                if not candidates:
                    raise RuntimeError(f"Underline line not found for {label!r} on page {page}")

                # Pick the nearest line below.
                candidates.sort(key=lambda ln: (y0 - float(ln.bbox[1])))
                target_line = candidates[0]
                underscore_x = _underscore_start_x(target_line)

            if underscore_x is None:
                # last resort: start after label
                x0, y0, x1, y1 = (float(v) for v in target_line.bbox)
                underscore_x = x0 + 80

            tx0, ty0, tx1, ty1 = (float(v) for v in target_line.bbox)
            placements.append(
                Placement(
                    key=key,
                    page=page,
                    x=float(underscore_x) + 2.0,
                    y=float(ty0) + 2.0,
                    font=DEFAULT_OVERLAY_FONT,
                    font_size=10,
                )
            )

    return placements


def placements_to_json_dict(placements: list[Placement]) -> dict:
    return {
        "comment": (
            "Auto-generated placement mapping for dogovor.pdf. "
            "Units are PDF points; origin is bottom-left of page."
        ),
        "fields": [
            {
                "key": p.key,
                "page": p.page,
                "x": p.x,
                "y": p.y,
                "font": p.font,
                "fontSize": p.font_size,
            }
            for p in placements
        ],
    }
