from django.shortcuts import render
from django.http import HttpResponseBadRequest
from datetime import datetime

from accounts.permissions import role_required
from .generators import (
    generate_animal_report_pdf,
    generate_animal_excel,
    generate_vet_report_pdf,
    generate_vet_excel,
    generate_movement_report_pdf,
    generate_movement_excel,
    generate_yearly_report_pdf,
    generate_yearly_excel
)

@role_required('admin', 'vet')
def report_form(request):
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        format_type = request.POST.get('format')
        year = request.POST.get('year')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        if report_type == 'yearly':
            if not year:
                return HttpResponseBadRequest('Укажите год')
            year = int(year)
            if format_type == 'pdf':
                return generate_yearly_report_pdf(year)
            elif format_type == 'excel':
                return generate_yearly_excel(year)
            else:
                return HttpResponseBadRequest('Неверный формат')
        else:
            if not start_date or not end_date:
                return HttpResponseBadRequest('Укажите период')
            if report_type == 'animals' and format_type == 'pdf':
                return generate_animal_report_pdf(start_date, end_date)
            elif report_type == 'animals' and format_type == 'excel':
                return generate_animal_excel(start_date, end_date)
            elif report_type == 'vet' and format_type == 'excel':
                return generate_vet_excel(start_date, end_date)
            elif report_type == 'vet' and format_type == 'pdf':
                return generate_vet_report_pdf(start_date, end_date)
            elif report_type == 'movements' and format_type == 'pdf':
                return generate_movement_report_pdf(start_date, end_date)
            elif report_type == 'movements' and format_type == 'excel':
                return generate_movement_excel(start_date, end_date)
            else:
                return HttpResponseBadRequest('Неверный тип отчёта или формата')
    current_year = datetime.now().year
    default_year = current_year - 1
    # Сформируем список годов (например, последние 10 лет)
    years = range(default_year - 10, default_year + 3)  # можно настроить диапазон
    return render(request, 'reports/report_form.html', {'default_year': default_year, 'years': years})
    # years = range(2015, current_year + 2)
    # return render(request, 'reports/report_form.html', {'years': years})