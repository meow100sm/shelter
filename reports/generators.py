import io
from datetime import datetime, date
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from openpyxl import Workbook
from animals.models import Animal, VetRecord, Movement, Photo
from reportlab.lib.units import mm
import os
from django.conf import settings
from openpyxl.styles import Font
from django.db.models import Count
from PIL import Image as PILImage
from openpyxl.utils import get_column_letter

from reports.dogovor_overlay import render_dogovor_from_template

try:
    from pypdf import PdfReader, PdfWriter
except ModuleNotFoundError:  # optional dependency for template-based contracts
    PdfReader = None
    PdfWriter = None


def _merge_pdf_template(*, template_path: str, generated_pdf: io.BytesIO) -> bytes | None:
    """Return merged PDF bytes (template pages + generated pages) or None.

    This is intentionally tolerant: if `pypdf` isn't installed or template parsing
    fails, callers can fall back to returning the generated PDF.
    """

    if PdfReader is None or PdfWriter is None:
        return None

    if not os.path.exists(template_path):
        return None

    try:
        generated_pdf.seek(0)
        template_reader = PdfReader(template_path)
        generated_reader = PdfReader(generated_pdf)

        writer = PdfWriter()
        for page in template_reader.pages:
            writer.add_page(page)
        for page in generated_reader.pages:
            writer.add_page(page)

        out = io.BytesIO()
        writer.write(out)
        out.seek(0)
        return out.getvalue()
    except Exception:
        return None

# Регистрация шрифта
try:
    pdfmetrics.registerFont(TTFont('DejaVuSans', 'static/fonts/DejaVuSans.ttf'))
    FONT_NAME = 'DejaVuSans'
except Exception:
    print("Шрифт DejaVuSans.ttf не найден, русские буквы не отобразятся.")
    FONT_NAME = 'Helvetica'

# Стили
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='RussianTitle', parent=styles['Title'], fontName=FONT_NAME, fontSize=16, alignment=1, spaceAfter=12))
styles.add(ParagraphStyle(name='RussianNormal', parent=styles['Normal'], fontName=FONT_NAME, fontSize=10))
styles.add(ParagraphStyle(name='RussianHeading', parent=styles['Heading2'], fontName=FONT_NAME, fontSize=12, alignment=1))
styles.add(ParagraphStyle(name='RussianTableHeader', parent=styles['Normal'], fontName=FONT_NAME, fontSize=9, alignment=1, textColor=colors.whitesmoke, backColor=colors.grey))
styles.add(ParagraphStyle(name='RussianTableCell', parent=styles['Normal'], fontName=FONT_NAME, fontSize=8, alignment=0))

def resize_image_to_fixed(img_path, target_size=(200, 200)):
    try:
        with PILImage.open(img_path) as img:
            # Переводим в RGB (на случай CMYK или RGBA)
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            # Пропорционально масштабируем до минимального целевого размера
            img.thumbnail((target_size[0], target_size[1]), PILImage.Resampling.LANCZOS)
            # Создаём белый холст нужного размера и вклеиваем по центру
            new_img = PILImage.new('RGB', target_size, (255, 255, 255))
            x = (target_size[0] - img.width) // 2
            y = (target_size[1] - img.height) // 2
            new_img.paste(img, (x, y))
            # Сохраняем в буфер
            buffer = io.BytesIO()
            new_img.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)
            return buffer
    except Exception:
        return None
    
def _make_paragraph(text, style_name='RussianTableCell'):
    """Оборачивает текст в Paragraph, переносит длинные строки"""
    if not text:
        text = '—'
    # Замена переносов строк на пробелы
    text = str(text).replace('\n', ' ')
    return Paragraph(text, styles[style_name])

def _build_table(data, col_widths=None):
    """Строит таблицу с автоматическим переносом текста"""
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('FONTSIZE', (0,1), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('WORDWRAP', (0,0), (-1,-1), True),
    ]))
    return t

# ---------- Отчёт по поступлению животных (PDF) ----------
def generate_animal_report_pdf(start_date, end_date):
    animals = Animal.objects.filter(intake_date__range=[start_date, end_date])
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="animals_{start_date}_{end_date}.pdf"'
    doc = SimpleDocTemplate(response, pagesize=A4, topMargin=50, bottomMargin=50)
    elements = []
    elements.append(Paragraph(f"Журнал поступления животных с {start_date} по {end_date}", styles['RussianTitle']))
    elements.append(Spacer(1, 12))

    data = [[
        Paragraph("Уник. №", styles['RussianTableHeader']),
        Paragraph("Вид", styles['RussianTableHeader']),
        Paragraph("Порода", styles['RussianTableHeader']),
        Paragraph("Дата", styles['RussianTableHeader']),
        Paragraph("Статус", styles['RussianTableHeader'])
    ]]
    for a in animals:
        data.append([
            _make_paragraph(a.unique_id),
            _make_paragraph(a.get_species_display()),
            _make_paragraph(a.breed or '—'),
            _make_paragraph(str(a.intake_date)),
            _make_paragraph(a.get_status_display())
        ])
    col_widths = [60, 60, 80, 70, 80]
    elements.append(_build_table(data, col_widths))
    doc.build(elements)
    return response


def _autosize_columns(ws):
    for col_cells in ws.columns:
        max_len = 0
        col_letter = col_cells[0].column_letter
        for cell in col_cells:
            value = cell.value
            if value is None:
                continue
            max_len = max(max_len, len(str(value)))
        ws.column_dimensions[col_letter].width = min(max_len + 2, 45)


# ---------- Отчёт по поступлению животных (Excel) ----------
def generate_animal_excel(start_date, end_date):
    animals = Animal.objects.filter(intake_date__range=[start_date, end_date]).order_by('intake_date', 'id')
    wb = Workbook()
    ws = wb.active
    ws.title = 'Поступления'
    ws.append(['Уник. №', 'Кличка', 'Вид', 'Порода', 'Пол', 'Дата поступления', 'Источник', 'Статус'])
    for a in animals:
        ws.append([
            a.unique_id,
            a.name or '',
            a.get_species_display(),
            a.breed or '',
            a.get_sex_display(),
            str(a.intake_date),
            a.intake_source or '',
            a.get_status_display(),
        ])
    _autosize_columns(ws)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="animals_{start_date}_{end_date}.xlsx"'
    wb.save(response)
    return response

# ---------- Ветеринарные мероприятия (Excel) ----------
def generate_vet_excel(start_date, end_date):
    records = VetRecord.objects.filter(date__range=[start_date, end_date])
    wb = Workbook()
    ws = wb.active
    ws.title = 'Ветеринария'
    ws.append(['ID животного', 'Дата', 'Тип', 'Описание', 'Ветеринар', 'След. обработка'])
    for r in records:
        ws.append([
            r.animal.unique_id,
            str(r.date),
            r.get_type_display(),
            r.description or '',
            r.vet_name or '',
            str(r.next_due_date) if r.next_due_date else ''
        ])
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = 15
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="vet_{start_date}_{end_date}.xlsx"'
    wb.save(response)
    return response


# ---------- Ветеринарные мероприятия (PDF) ----------
def generate_vet_report_pdf(start_date, end_date):
    records = VetRecord.objects.filter(date__range=[start_date, end_date]).select_related('animal').order_by('date', 'id')
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="vet_{start_date}_{end_date}.pdf"'
    doc = SimpleDocTemplate(response, pagesize=landscape(A4), topMargin=50, bottomMargin=50)
    elements = []
    elements.append(Paragraph(f"Журнал ветеринарных мероприятий с {start_date} по {end_date}", styles['RussianTitle']))
    elements.append(Spacer(1, 12))

    data = [[
        Paragraph('Дата', styles['RussianTableHeader']),
        Paragraph('Животное', styles['RussianTableHeader']),
        Paragraph('Тип', styles['RussianTableHeader']),
        Paragraph('Описание', styles['RussianTableHeader']),
        Paragraph('Ветеринар', styles['RussianTableHeader']),
        Paragraph('След. обработка', styles['RussianTableHeader']),
    ]]

    for r in records:
        data.append([
            _make_paragraph(str(r.date)),
            _make_paragraph(f"{r.animal.unique_id} ({r.animal.name or '—'})"),
            _make_paragraph(r.get_type_display()),
            _make_paragraph(r.description or '—'),
            _make_paragraph(r.vet_name or '—'),
            _make_paragraph(str(r.next_due_date) if r.next_due_date else '—'),
        ])

    col_widths = [65, 80, 80, 180, 90, 85]
    elements.append(_build_table(data, col_widths))
    doc.build(elements)
    return response


# ---------- Договор передачи/усыновления (PDF) ----------
def generate_movement_contract_pdf(movement: Movement):
    """FR-12: договор передачи/усыновления (PDF) строго по шаблону dogovor.pdf.

    Важно: dogovor.pdf не является PDF-формой (в нём нет AcroForm-полей), поэтому
    заполнение делается наложением текста (overlay) в заранее настроенных координатах.
    Координаты задаются в reports/dogovor_placements.json.
    """

    animal = movement.animal
    values = {
        # Animal
        "animal_unique_id": animal.unique_id,
        "animal_name": animal.name or "",
        "animal_species": animal.get_species_display(),
        "animal_sex": animal.get_sex_display(),
        "animal_breed": animal.breed or "",
        "animal_color": animal.color or "",
        "animal_features": animal.features or "",
        "animal_approx_age": animal.approx_age or "",
        # Movement
        "movement_date": movement.date.strftime('%d.%m.%Y'),
        "movement_reason": movement.get_reason_display(),
        "movement_from_location": movement.from_location or "",
        "movement_to_location": movement.to_location or "",
        "movement_notes": movement.notes or "",
    }

    try:
        pdf_bytes = render_dogovor_from_template(values=values)
    except Exception as e:
        return HttpResponse(
            f"Не настроено автозаполнение шаблона dogovor.pdf: {e}\n"
            "Сгенерируй сетку координат: python manage.py dogovor_grid\n"
            "и заполни reports/dogovor_placements.json",
            content_type="text/plain; charset=utf-8",
            status=500,
        )

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="contract_{animal.unique_id}_{movement.date}.pdf"'
    )
    return response


def generate_adoption_contract_pdf(animal: Animal):
    """Договор усыновления строго по шаблону dogovor.pdf (overlay заполнение)."""

    values = {
        "animal_unique_id": animal.unique_id,
        "animal_name": animal.name or "",
        "animal_species": animal.get_species_display(),
        "animal_sex": animal.get_sex_display(),
        "animal_breed": animal.breed or "",
        "animal_color": animal.color or "",
        "animal_features": animal.features or "",
        "animal_approx_age": animal.approx_age or "",
        "contract_date": datetime.now().strftime('%d.%m.%Y'),
    }

    try:
        pdf_bytes = render_dogovor_from_template(values=values)
    except Exception as e:
        return HttpResponse(
            f"Не настроено автозаполнение шаблона dogovor.pdf: {e}\n"
            "Сгенерируй сетку координат: python manage.py dogovor_grid\n"
            "и заполни reports/dogovor_placements.json",
            content_type="text/plain; charset=utf-8",
            status=500,
        )

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="adoption_contract_{animal.unique_id}.pdf"'
    return response

# ---------- Журнал перемещений (PDF) ----------
def generate_movement_report_pdf(start_date, end_date):
    movements = Movement.objects.filter(date__range=[start_date, end_date])
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="movements_{start_date}_{end_date}.pdf"'
    doc = SimpleDocTemplate(response, pagesize=landscape(A4), topMargin=50, bottomMargin=50)
    elements = []
    elements.append(Paragraph(f"Журнал перемещений с {start_date} по {end_date}", styles['RussianTitle']))
    elements.append(Spacer(1, 12))

    data = [[
        Paragraph("Дата", styles['RussianTableHeader']),
        Paragraph("Животное", styles['RussianTableHeader']),
        Paragraph("Откуда", styles['RussianTableHeader']),
        Paragraph("Куда", styles['RussianTableHeader']),
        Paragraph("Причина", styles['RussianTableHeader']),
        Paragraph("Примечания", styles['RussianTableHeader'])
    ]]
    for m in movements:
        data.append([
            _make_paragraph(str(m.date)),
            _make_paragraph(f"{m.animal.unique_id} ({m.animal.name or '—'})"),
            _make_paragraph(m.from_location or '—'),
            _make_paragraph(m.to_location or '—'),
            _make_paragraph(m.get_reason_display()),
            _make_paragraph(m.notes or '—')
        ])
    col_widths = [65, 70, 80, 80, 90, 100]
    elements.append(_build_table(data, col_widths))
    doc.build(elements)
    return response

# ---------- Журнал перемещений (Excel) ----------
def generate_movement_excel(start_date, end_date):
    movements = Movement.objects.filter(date__range=[start_date, end_date])
    wb = Workbook()
    ws = wb.active
    ws.title = 'Перемещения'
    ws.append(['Дата', 'Животное', 'Откуда', 'Куда', 'Причина', 'Примечания'])
    for m in movements:
        ws.append([
            str(m.date),
            f"{m.animal.unique_id} ({m.animal.name or '—'})",
            m.from_location or '—',
            m.to_location or '—',
            m.get_reason_display(),
            m.notes or '—'
        ])
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = 18
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="movements_{start_date}_{end_date}.xlsx"'
    wb.save(response)
    return response

# ---------- ГОДОВОЙ ОТЧЁТ (PDF) ----------
def generate_yearly_report_pdf(year):
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    # ---- Случайные фотографии животных за год ----
    sample_photos = []
    photos_queryset = Photo.objects.filter(
        animal__intake_date__range=[start_date, end_date]
    ).select_related('animal').order_by('?')[:6]  # до 6 случайных
    for photo in photos_queryset:
        sample_photos.append({
            'img_path': os.path.join(settings.MEDIA_ROOT, photo.image.name),
            'caption': f"{photo.animal.unique_id} – {photo.animal.name or 'без клички'}",
            'exists': os.path.exists(os.path.join(settings.MEDIA_ROOT, photo.image.name))
        })

    # ---- Статистика ----
    total_animals = Animal.objects.filter(intake_date__range=[start_date, end_date]).count()
    vet_count = VetRecord.objects.filter(date__range=[start_date, end_date]).count()
    movements_count = Movement.objects.filter(date__range=[start_date, end_date]).count()
    adoptions = Movement.objects.filter(date__range=[start_date, end_date], reason='adoption').count()

    # ---- Распределение по видам (с процентами) ----
    total = total_animals if total_animals > 0 else 1
    species_data = []
    for code, name in Animal.SPECIES_CHOICES:
        cnt = Animal.objects.filter(species=code, intake_date__range=[start_date, end_date]).count()
        if cnt > 0:
            species_data.append([name, cnt, f"{cnt/total*100:.1f}%"])

    # ---- Статусы ----
    status_data = []
    for code, name in Animal.STATUS_CHOICES:
        cnt = Animal.objects.filter(status=code, intake_date__range=[start_date, end_date]).count()
        if cnt > 0:
            status_data.append([name, cnt])

    # ---- Поступление по месяцам ----
    months_ru = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
    monthly_data = []
    max_month_count = 0
    for month in range(1, 13):
        cnt = Animal.objects.filter(intake_date__year=year, intake_date__month=month).count()
        monthly_data.append((months_ru[month-1], cnt))
        if cnt > max_month_count:
            max_month_count = cnt
    max_month_count = max_month_count if max_month_count > 0 else 1

    # ---- Топ пород ----
    top_breeds = list(Animal.objects.filter(
        intake_date__year=year,
        species__in=['cat', 'dog']
    ).exclude(breed='').values('species', 'breed').annotate(
        cnt=Count('id')
    ).order_by('-cnt')[:5])

    # ---- Типы процедур ----
    proc_by_type = VetRecord.objects.filter(date__range=[start_date, end_date]).values('type').annotate(
        cnt=Count('id')).order_by('-cnt')
    proc_labels = dict(VetRecord.TYPE_CHOICES)

    # ---- Причины перемещений ----
    mov_by_reason = Movement.objects.filter(date__range=[start_date, end_date]).values('reason').annotate(
        cnt=Count('id')).order_by('-cnt')
    reason_labels = dict(Movement.REASON_CHOICES)

    # ---- Создаём PDF ----
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="yearly_report_{year}.pdf"'
    doc = SimpleDocTemplate(response, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=25*mm, bottomMargin=20*mm)
    elements = []

    # ---- Заголовок ----
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'icons', 'logo.png')
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=40*mm, height=15*mm, kind='proportional')
        header_data = [[logo, Paragraph(f"<font color='#2E7D32'><b>Годовой отчёт</b></font><br/><font size=10>{year} год</font>", styles['RussianTitle'])]]
        header_table = Table(header_data, colWidths=[50*mm, 100*mm])
        header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ALIGN', (1,0), (1,0), 'CENTER')]))
        elements.append(header_table)
    else:
        elements.append(Paragraph(f"<font color='#2E7D32'><b>Годовой отчёт {year}</b></font>", styles['RussianTitle']))
    elements.append(Spacer(1, 10*mm))

    # ---- KPI (4 блока) ----
    kpi_data = [
        [Paragraph(f"<font size=18><b>{total_animals}</b></font>", styles['RussianNormal']),
         Paragraph(f"<font size=18><b>{vet_count}</b></font>", styles['RussianNormal']),
         Paragraph(f"<font size=18><b>{movements_count}</b></font>", styles['RussianNormal']),
         Paragraph(f"<font size=18><b>{adoptions}</b></font>", styles['RussianNormal'])],
        [Paragraph("Поступило", styles['RussianNormal']),
         Paragraph("Процедур", styles['RussianNormal']),
         Paragraph("Перемещений", styles['RussianNormal']),
         Paragraph("Усыновлено", styles['RussianNormal'])],
    ]
    kpi_table = Table(kpi_data, colWidths=[45*mm, 45*mm, 45*mm, 45*mm])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.Color(0.18, 0.49, 0.196)),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
        ('FONTSIZE', (0,0), (-1,0), 14),
        ('FONTSIZE', (0,1), (-1,1), 11),
        ('TOPPADDING', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BOTTOMPADDING', (0,1), (-1,1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 8*mm))

    # ---- Поступление по месяцам (русские названия, диаграмма) ----
    elements.append(Paragraph("<b>Поступление по месяцам</b>", styles['RussianHeading']))
    month_table_data = [["Месяц", "Кол-во", "Доля (%)", "Диаграмма"]]
    for month_label, cnt in monthly_data:
        percent = cnt / total_animals * 100 if total_animals > 0 else 0
        bar_len = int(cnt / total_animals * 20) if total_animals > 0 else 0
        bar = "█" * bar_len + "░" * (20 - bar_len)
        month_table_data.append([month_label, str(cnt), f"{percent:.1f}%", bar])
    month_table = Table(month_table_data, colWidths=[40*mm, 30*mm, 30*mm, 60*mm])
    month_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('ALIGN', (1,0), (3,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    elements.append(month_table)
    elements.append(Spacer(1, 6*mm))

    # ---- Распределение по видам ----
    if species_data:
        elements.append(Paragraph("<b>Распределение по видам</b>", styles['RussianHeading']))
        spp_table_data = [["Вид", "Кол-во", "Доля"]] + species_data
        spp_table = Table(spp_table_data, colWidths=[60*mm, 40*mm, 50*mm])
        spp_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('ALIGN', (1,0), (2,0), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ]))
        elements.append(spp_table)
        elements.append(Spacer(1, 6*mm))

    # ---- Распределение по статусам ----
    if status_data:
        elements.append(Paragraph("<b>Распределение по статусам</b>", styles['RussianHeading']))
        stat_table_data = [["Статус", "Кол-во"]] + status_data
        stat_table = Table(stat_table_data, colWidths=[100*mm, 50*mm])
        stat_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('ALIGN', (1,0), (1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ]))
        elements.append(stat_table)
        elements.append(Spacer(1, 6*mm))

    # ---- Топ пород ----
    if top_breeds:
        elements.append(Paragraph("<b>Топ пород (кошки и собаки)</b>", styles['RussianHeading']))
        breed_table_data = [["Вид", "Порода", "Кол-во"]]
        species_display = dict(Animal.SPECIES_CHOICES)
        for b in top_breeds:
            breed_table_data.append([species_display.get(b['species'], b['species']), b['breed'], str(b['cnt'])])
        breed_table = Table(breed_table_data, colWidths=[50*mm, 80*mm, 30*mm])
        breed_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('ALIGN', (2,0), (2,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ]))
        elements.append(breed_table)
        elements.append(Spacer(1, 6*mm))

    # ---- Ветеринарные процедуры по типам ----
    if proc_by_type:
        elements.append(Paragraph("<b>Ветеринарные процедуры по типам</b>", styles['RussianHeading']))
        proc_table_data = [["Тип", "Кол-во"]]
        for p in proc_by_type:
            proc_table_data.append([proc_labels.get(p['type'], p['type']), str(p['cnt'])])
        proc_table = Table(proc_table_data, colWidths=[100*mm, 50*mm])
        proc_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('ALIGN', (1,0), (1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ]))
        elements.append(proc_table)
        elements.append(Spacer(1, 6*mm))

    # ---- Причины перемещений ----
    if mov_by_reason:
        elements.append(Paragraph("<b>Причины перемещений</b>", styles['RussianHeading']))
        reason_table_data = [["Причина", "Кол-во"]]
        for r in mov_by_reason:
            reason_table_data.append([reason_labels.get(r['reason'], r['reason']), str(r['cnt'])])
        reason_table = Table(reason_table_data, colWidths=[100*mm, 50*mm])
        reason_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('ALIGN', (1,0), (1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ]))
        elements.append(reason_table)
        elements.append(Spacer(1, 6*mm))

        # ---- Галерея животных (если есть фото) ----
    photos = Photo.objects.filter(
        animal__intake_date__range=[start_date, end_date]
    ).select_related('animal').order_by('?')[:6]  # до 6 случайных фото

    if photos:
        elements.append(Paragraph("<b>Наши питомцы в этом году</b>", styles['RussianHeading']))
        elements.append(Spacer(1, 6))

        rows = []
        current_row = []
        for photo in photos:
            img_path = os.path.join(settings.MEDIA_ROOT, photo.image.name)
            buffer = resize_image_to_fixed(img_path, target_size=(200, 200))
            if buffer:
                # Создаём изображение reportlab из буфера (размер в пикселях)
                img = Image(buffer, width=50*mm, height=50*mm)  # 30x30 мм
                # Подпись под фото: уникальный номер и кличка
                caption = Paragraph(f"{photo.animal.unique_id}<br/>{photo.animal.name or ''}", styles['RussianNormal'])
                # Ячейка: картинка + подпись
                cell = Table([[img], [caption]], colWidths=[50*mm])
                cell.setStyle(TableStyle([
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ]))
                current_row.append(cell)

            if len(current_row) == 3:
                rows.append(current_row)
                current_row = []
        if current_row:
            rows.append(current_row)

        if rows:
            gallery_table = Table(rows, colWidths=[50*mm, 50*mm, 50*mm])
            gallery_table.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ]))
            elements.append(gallery_table)
            elements.append(Spacer(1, 8*mm))

    # ---- Подвал ----
    elements.append(Spacer(1, 15*mm))
    elements.append(Paragraph(f"<i>Отчёт сгенерирован {datetime.now().strftime('%d.%m.%Y в %H:%M')}</i>", styles['RussianNormal']))

    doc.build(elements)
    return response

def generate_yearly_excel(year):
    from datetime import datetime
    start_date = datetime(year, 1, 1).date()
    end_date = datetime(year, 12, 31).date()

    wb = Workbook()

    total_animals = Animal.objects.filter(intake_date__range=[start_date, end_date]).count()
    vet_count = VetRecord.objects.filter(date__range=[start_date, end_date]).count()
    movements_count = Movement.objects.filter(date__range=[start_date, end_date]).count()
    adoptions = Movement.objects.filter(date__range=[start_date, end_date], reason='adoption').count()

    # ---- KPI ----
    ws_kpi = wb.active
    ws_kpi.title = 'KPI'
    ws_kpi['A1'] = f'Годовой отчёт {year}'
    ws_kpi['A1'].font = Font(size=14, bold=True)
    ws_kpi.merge_cells('A1:B1')
    ws_kpi.append([])
    ws_kpi.append(['Показатель', 'Значение'])
    ws_kpi.append(['Поступило животных', total_animals])
    ws_kpi.append(['Ветеринарных процедур', vet_count])
    ws_kpi.append(['Перемещений', movements_count])
    ws_kpi.append(['Усыновлено', adoptions])
    ws_kpi.append(['Погибло/усыплено', Movement.objects.filter(date__range=[start_date, end_date], reason='death').count()])
    _autosize_columns(ws_kpi)

    # ---- По видам ----
    ws_species = wb.create_sheet('Виды')
    ws_species.append(['Вид', 'Количество'])
    for code, name in Animal.SPECIES_CHOICES:
        cnt = Animal.objects.filter(species=code, intake_date__range=[start_date, end_date]).count()
        ws_species.append([name, cnt])
    _autosize_columns(ws_species)

    # ---- По статусам ----
    ws_status = wb.create_sheet('Статусы')
    ws_status.append(['Статус', 'Количество'])
    for code, name in Animal.STATUS_CHOICES:
        cnt = Animal.objects.filter(status=code, intake_date__range=[start_date, end_date]).count()
        ws_status.append([name, cnt])
    _autosize_columns(ws_status)

    # ---- Поступление по месяцам ----
    ws_months = wb.create_sheet('Месяцы')
    ws_months.append(['Месяц', 'Количество'])
    months_ru = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
    for month in range(1, 13):
        cnt = Animal.objects.filter(intake_date__year=year, intake_date__month=month).count()
        ws_months.append([months_ru[month - 1], cnt])
    _autosize_columns(ws_months)

    # ---- Топ-5 пород ----
    ws_breeds = wb.create_sheet('Топ пород')
    ws_breeds.append(['Вид', 'Порода', 'Количество'])
    top_breeds = list(
        Animal.objects.filter(intake_date__year=year, species__in=['cat', 'dog'])
        .exclude(breed='')
        .values('species', 'breed')
        .annotate(cnt=Count('id'))
        .order_by('-cnt')[:5]
    )
    species_display = dict(Animal.SPECIES_CHOICES)
    for b in top_breeds:
        ws_breeds.append([species_display.get(b['species'], b['species']), b['breed'], b['cnt']])
    _autosize_columns(ws_breeds)

    # ---- Типы ветеринарных процедур ----
    ws_proc = wb.create_sheet('Процедуры')
    ws_proc.append(['Тип', 'Количество'])
    proc_by_type = VetRecord.objects.filter(date__range=[start_date, end_date]).values('type').annotate(cnt=Count('id')).order_by('-cnt')
    proc_labels = dict(VetRecord.TYPE_CHOICES)
    for p in proc_by_type:
        ws_proc.append([proc_labels.get(p['type'], p['type']), p['cnt']])
    _autosize_columns(ws_proc)

    # ---- Причины перемещений ----
    ws_reason = wb.create_sheet('Причины движений')
    ws_reason.append(['Причина', 'Количество'])
    mov_by_reason = Movement.objects.filter(date__range=[start_date, end_date]).values('reason').annotate(cnt=Count('id')).order_by('-cnt')
    reason_labels = dict(Movement.REASON_CHOICES)
    for r in mov_by_reason:
        ws_reason.append([reason_labels.get(r['reason'], r['reason']), r['cnt']])
    _autosize_columns(ws_reason)

    # ---- Галерея фото (как список файлов) ----
    ws_photos = wb.create_sheet('Фото')
    ws_photos.append(['Животное', 'Кличка', 'Файл'])
    photos = Photo.objects.filter(animal__intake_date__range=[start_date, end_date]).select_related('animal').order_by('?')[:12]
    for p in photos:
        ws_photos.append([
            p.animal.unique_id,
            p.animal.name or '',
            p.image.name,
        ])
    _autosize_columns(ws_photos)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="yearly_report_{year}.xlsx"'
    wb.save(response)
    return response