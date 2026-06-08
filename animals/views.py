from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Animal, Photo, VetRecord, Movement
from .forms import AnimalForm, VetRecordForm, MovementForm, PhotoForm
from .filters import AnimalFilter
import calendar
from datetime import datetime, timedelta
from django.http import JsonResponse
from accounts.utils import log_action
from django.urls import reverse
from .view_utils import get_next_url, redirect_next_or
from accounts.permissions import role_required
from reports.generators import generate_movement_contract_pdf, generate_adoption_contract_pdf
from django.db.models import Q

def dashboard(request):
    # Основные карточки
    context = {
        'total_animals': Animal.objects.count(),
        'quarantine_count': Animal.objects.filter(status='quarantine').count(),
        'treatment_count': Animal.objects.filter(status='treatment').count(),
        'ready_count': Animal.objects.filter(status='ready').count(),
    }
    # Для ветеринара – количество пациентов на сегодня
    if request.user.is_authenticated and request.user.role == 'vet':
        context['today_patients'] = VetRecord.objects.filter(date=timezone.now().date()).count()

    # ========== 1. Последние поступления (5 штук) ==========
    context['recent_animals'] = Animal.objects.all().order_by('-intake_date')[:5]

    # ========== 2. Предстоящие обработки ==========
    today = timezone.now().date()
    next_week = today + timedelta(days=7)
    upcoming = VetRecord.objects.filter(
        Q(date__gte=today, date__lte=next_week) |
        Q(next_due_date__gte=today, next_due_date__lte=next_week)
    ).select_related('animal').order_by('date', 'next_due_date')
    context['upcoming_vet_records'] = upcoming

    return render(request, 'animals/dashboard.html', context)

def animal_list(request):
    f = AnimalFilter(request.GET, queryset=Animal.objects.prefetch_related('photos').all())
    paginator = Paginator(f.qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    query_params.pop('page', None)
    querystring = query_params.urlencode()
    return render(request, 'animals/animal_list.html', {
        'filter': f,
        'page_obj': page_obj,
        'search_query': request.GET.get('search', ''),
        'querystring': querystring,
    })

def animal_detail(request, pk):
    animal = get_object_or_404(Animal, pk=pk)
    photos = animal.photos.all()
    vet_records = animal.vet_records.all()
    movements = animal.movements.all()
    
    # Активная вкладка (по умолчанию 'basic')
    active_tab = request.GET.get('tab', 'basic')
    
    # Сохраняем текущие GET-параметры для ссылок (кроме tab)
    get_params = request.GET.copy()
    get_params.pop('tab', None)
    filter_query = get_params.urlencode()
    
    return render(request, 'animals/animal_detail.html', {
        'animal': animal,
        'photos': photos,
        'vet_records': vet_records,
        'movements': movements,
        'active_tab': active_tab,
        'filter_query': filter_query,
    })

@role_required('admin', 'vet', 'volunteer')
def animal_create(request):
    if request.method == 'POST':
        form = AnimalForm(request.POST, user=request.user)
        if form.is_valid():
            animal = form.save(commit=False)
            if request.user.is_authenticated:
                animal.created_by = request.user
            animal.save()
            log_action(request.user, 'animal_create', f'Создано животное {animal.unique_id}')
            return redirect('animals:animal_detail', pk=animal.pk)
        else:
            messages.error(request, 'Исправьте ошибки в форме')
    else:
        form = AnimalForm(user=request.user)
    return render(request, 'animals/animal_form.html', {'form': form})

@role_required('admin', 'vet', 'volunteer')
def animal_edit(request, pk):
    animal = get_object_or_404(Animal, pk=pk)
    if request.method == 'POST':
        form = AnimalForm(request.POST, instance=animal, user=request.user)
        if form.is_valid():
            form.save()
            log_action(request.user, 'animal_edit', f'Изменено животное {animal.unique_id}')
            return redirect('animals:animal_detail', pk=animal.id)
    else:
        form = AnimalForm(instance=animal, user=request.user)
    return render(request, 'animals/animal_form.html', {'form': form, 'animal': animal})

@role_required('admin')
def animal_delete(request, pk):
    animal = get_object_or_404(Animal, pk=pk)
    if request.method == 'POST':
        log_action(request.user, 'animal_delete', f'Удалено животное {animal.unique_id}')
        animal.delete()
        return redirect('animals:animal_list')
    return render(request, 'animals/animal_confirm_delete.html', {'animal': animal})

@role_required('admin', 'vet')
def vet_record_create(request, animal_pk):
    animal = get_object_or_404(Animal, pk=animal_pk)
    next_url = get_next_url(request)
    if request.method == 'POST':
        form = VetRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.animal = animal  # принудительно привязываем к нужному животному
            record.save()
            log_action(request.user, 'vet_record_create', f'Добавлена {record.get_type_display()} для {animal.unique_id}')
            messages.success(request, 'Запись добавлена')
            return redirect(next_url) if next_url else redirect('animals:animal_detail', pk=animal.id)
    else:
        # Предустанавливаем животное и текущую дату
        form = VetRecordForm(initial={
            'animal': animal.id,
            'date': timezone.now().date(),
            'vet_email': getattr(request.user, 'email', '') or '',
        })
    
    return render(request, 'animals/vetrecord_form.html', {
        'form': form,
        'animal': animal,
        'next': next_url,
        'hide_animal_field': True,   # флаг для шаблона
    })

@role_required('admin', 'vet')
def vet_record_edit(request, pk):
    record = get_object_or_404(VetRecord, pk=pk)
    animal = record.animal
    next_url = get_next_url(request)
    # Определяем URL для отмены: если next передан (из карточки) – используем его, иначе – ветеринарный журнал
    cancel_url = next_url if next_url else reverse('animals:vet_journal')
    if request.method == 'POST':
        form = VetRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            log_action(request.user, 'vet_record_edit', f'Изменена запись ID {record.pk}')
            return redirect(next_url) if next_url else redirect('animals:vet_journal')
    else:
        form = VetRecordForm(instance=record)
    return render(request, 'animals/vetrecord_form.html', {
        'form': form,
        'record': record,
        'animal': animal,
        'next': next_url,
        'cancel_url': cancel_url,   # добавлено
        'hide_animal_field': True,
    })

@role_required('admin', 'vet')
def movement_create(request, animal_pk):
    animal = get_object_or_404(Animal, pk=animal_pk)
    next_url = get_next_url(request)
    if request.method == 'POST':
        form = MovementForm(request.POST)
        if form.is_valid():
            movement = form.save(commit=False)
            movement.animal = animal
            movement.save()

            # FR-13: авто-изменение статуса при выбытии
            if movement.reason == 'adoption':
                animal.status = 'adopted'
                animal.save(update_fields=['status'])
            elif movement.reason == 'death':
                animal.status = 'deceased'
                animal.save(update_fields=['status'])
            elif movement.reason == 'handover':
                animal.status = 'transferred'
                animal.save(update_fields=['status'])

            log_action(request.user, 'movement_create', f'Зафиксировано движение {movement.get_reason_display()} для {movement.animal.unique_id}')
            return redirect(next_url) if next_url else redirect('animals:animal_detail', pk=animal.id)
    else:
        form = MovementForm(initial={'animal': animal.id, 'date': timezone.now().date()})
    return render(request, 'animals/movement_form.html', {
        'form': form,
        'animal': animal,
        'next': next_url,
        'hide_animal_field': True,
    })

@role_required('admin', 'vet', 'volunteer')
def add_photo(request, animal_pk):
    animal = get_object_or_404(Animal, pk=animal_pk)

    # FR-01/FR-05: до 5 фото на животное
    if animal.photos.count() >= 5:
        messages.error(request, 'Нельзя загрузить больше 5 фотографий для одного животного')
        return redirect(f"{reverse('animals:animal_detail', args=[animal.pk])}?tab=photos")

    if request.method == 'POST':
        form = PhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.animal = animal
            photo.uploaded_by = request.user
            photo.save()
            log_action(request.user, 'photo_upload', f'Добавлено фото для {animal.unique_id}')
            return redirect('animals:animal_detail', pk=animal.id)
    else:
        form = PhotoForm()
    return render(request, 'animals/photo_form.html', {'form': form, 'animal': animal})

@role_required('admin', 'vet')
def vet_journal(request):
    # ========== 1. Фильтры (из GET) ==========
    species = request.GET.get('species')
    proc_type = request.GET.get('type')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    records = VetRecord.objects.select_related('animal').all()
    if species:
        records = records.filter(animal__species=species)
    if proc_type:
        records = records.filter(type=proc_type)
    if date_from and date_to:
        records = records.filter(
            Q(date__range=[date_from, date_to]) | Q(next_due_date__range=[date_from, date_to])
        )
    elif date_from:
        records = records.filter(Q(date__gte=date_from) | Q(next_due_date__gte=date_from))
    elif date_to:
        records = records.filter(Q(date__lte=date_to) | Q(next_due_date__lte=date_to))

    records = records.order_by('-date')

    # ========== 2. Календарь ==========
    today = timezone.now().date()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    cal = calendar.monthcalendar(year, month)
    month_days = []
    for week in cal:
        week_days = []
        for d in week:   # используем другое имя, например d
            if d != 0:
                date_obj = datetime(year, month, d).date()
                day_records = VetRecord.objects.filter(
                    Q(date=date_obj) | Q(next_due_date=date_obj)
                ).select_related('animal')
                week_days.append({
                    'day': d,
                    'date': date_obj.isoformat(),
                    'records': day_records,
                    'has_records': day_records.exists(),
                    'record_count': day_records.count(),
                })
            else:
                # Пустая ячейка
                week_days.append({
                    'day': 0,
                    'date': None,
                    'records': [],
                    'has_records': False,
                    'record_count': 0,
                })
        month_days.append(week_days)

    # Навигация по месяцам
    prev_month_date = datetime(year, month, 1) - timedelta(days=1)
    next_month_date = datetime(year, month, 28) + timedelta(days=4)

    # ========== 3. Активная вкладка ==========
    active_tab = request.GET.get('tab', 'table')  # 'table' или 'calendar'

    # ========== 4. Сохраняем GET-параметры (кроме year, month, tab) для ссылок ==========
    get_params = request.GET.copy()
    get_params.pop('year', None)
    get_params.pop('month', None)
    get_params.pop('tab', None)
    filter_query = get_params.urlencode()  # например: species=cat&type=vaccination

    # ========== 5. Контекст ==========
    context = {
        'records': records,
        'species_choices': Animal.SPECIES_CHOICES,
        'type_choices': VetRecord.TYPE_CHOICES,
        'selected_species': species,
        'selected_type': proc_type,
        'date_from': date_from,
        'date_to': date_to,
        'animals': Animal.objects.all(),

        # Данные календаря
        'calendar_days': month_days,
        'current_year': year,
        'current_month': month,
        'prev_year': prev_month_date.year,
        'prev_month': prev_month_date.month,
        'next_year': next_month_date.year,
        'next_month': next_month_date.month,

        # Активная вкладка
        'active_tab': active_tab,
        # Строка фильтров (без & в начале)
        'filter_query': filter_query,
    }
    return render(request, 'animals/vet_journal.html', context)


@role_required('admin', 'vet')
def vet_record_add(request):
    date_param = request.GET.get('date')
    next_url = get_next_url(request, default='/vet/journal/?tab=calendar')
    prefilled_date = ''   # по умолчанию пусто

    if date_param:
        try:
            # Проверяем, что дата в правильном формате
            datetime.strptime(date_param, '%Y-%m-%d')
            prefilled_date = date_param   # сохраняем строку
        except ValueError:
            pass

    if request.method == 'POST':
        form = VetRecordForm(request.POST)
        if form.is_valid():
            record = form.save()
            log_action(request.user, 'vet_record_create', f'Добавлена {record.get_type_display()} для {record.animal.unique_id}')
            return redirect(next_url)
    else:
        form = VetRecordForm(initial={'vet_email': getattr(request.user, 'email', '') or ''})

    return render(request, 'animals/vetrecord_form.html', {
        'form': form,
        'next': next_url,
        'cancel_url': next_url,
        'prefilled_date': prefilled_date,   # передаём дату в шаблон
    })

@login_required
def movement_list(request):
    movements = Movement.objects.select_related('animal').all().order_by('-date')
    animals = Animal.objects.all()

    # Получаем параметры из GET-запроса
    animal_id = request.GET.get('animal')
    reason = request.GET.get('reason')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    # Применяем фильтры
    if animal_id:
        movements = movements.filter(animal_id=animal_id)
    if reason:
        movements = movements.filter(reason=reason)
    if date_from:
        movements = movements.filter(date__gte=date_from)
    if date_to:
        movements = movements.filter(date__lte=date_to)

    context = {
        'movements': movements,
        'animals': animals,
        'selected_animal': animal_id,
        'selected_reason': reason,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'animals/movement_list.html', context)

@login_required
def delete_photo(request, pk):
    photo = get_object_or_404(Photo, pk=pk)
    animal_pk = photo.animal.pk

    # UI-06: подтверждение удаления; плюс безопасное удаление только через POST
    if request.user.role != 'admin' and request.user != photo.uploaded_by:
        messages.error(request, 'У вас нет прав на удаление фото')
        return redirect('animals:animal_detail', pk=animal_pk)

    if request.method == 'POST':
        photo.image.delete()  # удаляет файл с диска
        photo.delete()
        log_action(request.user, 'photo_delete', f'Удалено фото для {photo.animal.unique_id}')
        messages.success(request, 'Фото удалено')
        return redirect(f"{reverse('animals:animal_detail', args=[animal_pk])}?tab=photos")

    return render(request, 'animals/photo_confirm_delete.html', {'photo': photo})

def api_animals(request):
    animals = Animal.objects.values('id', 'unique_id', 'name')
    return JsonResponse(list(animals), safe=False)

@role_required('admin', 'vet')
def movement_create_general(request):
    if request.method == 'POST':
        form = MovementForm(request.POST)
        if form.is_valid():
            movement = form.save()
            log_action(request.user, 'movement_create', f'Зафиксировано движение {movement.get_reason_display()} для {movement.animal.unique_id}')
            return redirect('animals:movement_list')
        else:
            messages.error(request, 'Ошибка в форме. Проверьте данные.')
        return redirect('animals:movement_list')
    else:
        form = MovementForm(initial={'date': timezone.now().date()})
    return render(request, 'animals/movement_form.html', {'form': form})

@role_required('admin', 'vet')
def vet_record_delete(request, pk):
    record = get_object_or_404(VetRecord, pk=pk)
    next_url = get_next_url(request)
    if request.method == 'POST':
        log_action(request.user, 'vet_record_delete', f'Удалена запись {record.get_type_display()} для {record.animal.unique_id}')
        record.delete()
        return redirect_next_or(next_url, 'animals:vet_journal')
    return render(request, 'animals/vetrecord_confirm_delete.html', {'record': record, 'next': next_url})

def animal_search(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return redirect('animals:animal_list')
    
    # Точное совпадение по уникальному номеру (без учёта регистра)
    try:
        animal = Animal.objects.get(unique_id__iexact=query)
        return redirect('animals:animal_detail', pk=animal.pk)
    except Animal.DoesNotExist:
        pass
    
    # Если нет точного совпадения – ищем по вхождению в номер или кличку на странице списка
    return redirect(f"{reverse('animals:animal_list')}?search={query}")

@role_required('admin', 'vet')
def movement_edit(request, pk):
    movement = get_object_or_404(Movement, pk=pk)
    next_url = get_next_url(request)
    if request.method == 'POST':
        form = MovementForm(request.POST, instance=movement)
        if form.is_valid():
            movement = form.save()

            # FR-13: авто-изменение статуса при выбытии
            animal = movement.animal
            if movement.reason == 'adoption':
                animal.status = 'adopted'
                animal.save(update_fields=['status'])
            elif movement.reason == 'death':
                animal.status = 'deceased'
                animal.save(update_fields=['status'])
            elif movement.reason == 'handover':
                animal.status = 'transferred'
                animal.save(update_fields=['status'])

            log_action(request.user, 'movement_edit', f'Изменено движение ID {movement.pk} для {movement.animal.unique_id}')
            messages.success(request, 'Движение обновлено')
            return redirect_next_or(next_url, 'animals:movement_list')
    else:
        form = MovementForm(instance=movement)
    return render(request, 'animals/movement_form.html', {
        'form': form,
        'movement': movement,
        'next': next_url,
        'cancel_url': next_url if next_url else reverse('animals:movement_list')
    })

@role_required('admin', 'vet')
def movement_delete(request, pk):
    movement = get_object_or_404(Movement, pk=pk)
    next_url = get_next_url(request)
    if request.method == 'POST':
        animal_id = movement.animal.unique_id
        movement.delete()
        log_action(request.user, 'movement_delete', f'Удалено движение ID {movement.pk} для {animal_id}')
        messages.success(request, 'Движение удалено')
        return redirect_next_or(next_url, 'animals:movement_list')
    return render(request, 'animals/movement_confirm_delete.html', {
        'movement': movement,
        'next': next_url
    })


@role_required('admin', 'vet')
def movement_contract_pdf(request, pk):
    """FR-12: сформировать договор передачи/усыновления в PDF по движению."""

    movement = get_object_or_404(Movement, pk=pk)
    if movement.reason not in {'adoption', 'handover'}:
        messages.error(request, 'Договор доступен только для усыновления или передачи другому приюту')
        return redirect('animals:movement_list')
    return generate_movement_contract_pdf(movement)


@role_required('admin', 'vet')
def adoption_contract_pdf(request, pk):
    """Generate adoption contract after status becomes adopted (or on demand)."""

    animal = get_object_or_404(Animal, pk=pk)
    if animal.status != 'adopted':
        messages.error(request, 'Договор доступен только для усыновлённых животных')
        return redirect('animals:animal_detail', pk=animal.pk)
    return generate_adoption_contract_pdf(animal)