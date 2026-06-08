from django.db import models
from django.utils import timezone
from django.conf import settings
from django.urls import reverse

class Animal(models.Model):
    SPECIES_CHOICES = [('cat', 'Кошка'), ('dog', 'Собака'), ('other', 'Другое')]
    SEX_CHOICES = [('M', 'Мужской'), ('F', 'Женский'), ('U', 'Неизвестно')]
    STATUS_CHOICES = [
        ('intake', 'На приёме'), ('quarantine', 'Карантин'),
        ('healthy', 'Здоров'), ('treatment', 'Требует лечения'),
        ('ready', 'Готов к усыновлению'), ('adopted', 'Усыновлён'),
        ('deceased', 'Усыплён'), ('transferred', 'Передан')
    ]

    unique_id = models.CharField('Уникальный номер', max_length=20, unique=True, blank=True)
    name = models.CharField('Кличка', max_length=100, blank=True, help_text='Кличка животного (если есть)')
    species = models.CharField('Вид', max_length=10, choices=SPECIES_CHOICES)
    breed = models.CharField('Порода', max_length=100, blank=True)
    sex = models.CharField('Пол', max_length=1, choices=SEX_CHOICES, default='U')
    birth_date = models.DateField('Дата рождения', null=True, blank=True)
    approx_age = models.CharField('Примерный возраст', max_length=50, blank=True)
    color = models.CharField('Окрас', max_length=50, blank=True)
    features = models.TextField('Особые приметы', blank=True)
    intake_date = models.DateField('Дата поступления', default=timezone.now)
    intake_source = models.CharField('Источник', max_length=100, blank=True)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='intake')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_animals',
        verbose_name='Создал',
    )
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлена', auto_now=True)

    def get_absolute_url(self):
        return reverse('animals:animal_detail', args=[str(self.id)])

    def save(self, *args, **kwargs):
        if not self.unique_id:   # если номер не задан вручную
            # Получаем последний использованный номер
            last_animal = Animal.objects.order_by('id').last()
            if last_animal and last_animal.unique_id and last_animal.unique_id.startswith('AN-'):
                try:
                    last_num = int(last_animal.unique_id.split('-')[1])
                    new_num = last_num + 1
                except (IndexError, ValueError):
                    new_num = 1
            else:
                new_num = 1
            self.unique_id = f"AN-{new_num:04d}"
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-intake_date']
        verbose_name = 'Животное'
        verbose_name_plural = 'Животные'

    def __str__(self):
        if self.name:
            return f"{self.name} ({self.unique_id})"
        return self.unique_id

class Photo(models.Model):
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField('Фото', upload_to='animals/%Y/%m/')
    order = models.PositiveIntegerField('Порядок', default=0)
    uploaded_at = models.DateTimeField('Загружено', auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Загрузил')

    class Meta:
        ordering = ['order', 'uploaded_at']

    def __str__(self):
        return f"Фото {self.animal.unique_id}"

class VetRecord(models.Model):
    TYPE_CHOICES = [
        ('exam', 'Осмотр'), ('vaccination', 'Вакцинация'), ('deworming', 'Дегельминтизация'),
        ('treatment', 'Лечение'), ('surgery', 'Операция'), ('other', 'Другое')
    ]
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='vet_records')
    date = models.DateField('Дата проведения')
    type = models.CharField('Тип', max_length=20, choices=TYPE_CHOICES)
    description = models.TextField('Описание', blank=True)
    vet_name = models.CharField('Ветеринар', max_length=100, blank=True)
    vet_email = models.EmailField('Email сотрудника', blank=True)
    next_due_date = models.DateField('Дата следующей обработки', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.get_type_display()} для {self.animal.unique_id} от {self.date}"

    def is_overdue(self):
        return self.next_due_date and self.next_due_date < timezone.now().date()

class Movement(models.Model):
    REASON_CHOICES = [
        ('intake', 'Поступление'), ('transfer', 'Перемещение внутри приюта'),
        ('adoption', 'Усыновление'), ('death', 'Смерть'), ('handover', 'Передача другому приюту')
    ]
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='movements')
    date = models.DateField('Дата')
    from_location = models.CharField('Откуда', max_length=100, blank=True)
    to_location = models.CharField('Куда', max_length=100, blank=True)
    reason = models.CharField('Причина', max_length=200, choices=REASON_CHOICES)
    notes = models.TextField('Примечания', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.animal.unique_id} - {self.get_reason_display()} ({self.date})"