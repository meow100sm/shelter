from django import forms
from .models import Animal, VetRecord, Movement, Photo

class AnimalForm(forms.ModelForm):
    class Meta:
        model = Animal
        fields = '__all__'
        widgets = {
            'intake_date': forms.DateInput(attrs={'type': 'date'}),
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # created_by проставляется автоматически в views; не показываем в форме.
        self.fields.pop('created_by', None)

        # UI-05: подсказки под полями (help_text)
        self.fields['unique_id'].help_text = 'Оставьте пустым для авто-генерации AN-XXXX.'
        self.fields['species'].help_text = 'Выберите вид животного.'
        self.fields['breed'].help_text = 'Необязательно. Например: «метис», «овчарка».'
        self.fields['sex'].help_text = 'Если неизвестно — выберите «Неизвестно».'
        self.fields['birth_date'].help_text = 'Если дата неизвестна — оставьте пустым и заполните примерный возраст.'
        self.fields['approx_age'].help_text = 'Например: «2 года», «6 мес.».'
        self.fields['color'].help_text = 'Например: «рыжий», «чёрно-белый».'
        self.fields['features'].help_text = 'Особые приметы, характер, поведение и т.п.'
        self.fields['intake_date'].help_text = 'Дата поступления в приют.'
        self.fields['intake_source'].help_text = 'Откуда поступило животное (контакт/место/организация).' 
        if 'status' in self.fields:
            self.fields['status'].help_text = 'Текущий статус животного.'
        
        # Если пользователь не админ и не ветеринар – скрываем поле статуса
        if user and user.is_authenticated and user.role not in ['admin', 'vet']:
            self.fields.pop('status', None)
        elif not user or not user.is_authenticated:
            self.fields.pop('status', None)

class VetRecordForm(forms.ModelForm):
    class Meta:
        model = VetRecord
        fields = ['animal', 'date', 'type', 'description', 'vet_name', 'vet_email', 'next_due_date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'next_due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # UI-05: подсказки
        self.fields['animal'].help_text = 'Выберите животное.'
        self.fields['date'].help_text = 'Дата проведения процедуры.'
        self.fields['type'].help_text = 'Тип ветеринарного мероприятия.'
        self.fields['description'].help_text = 'Кратко опишите процедуру и результаты.'
        self.fields['vet_name'].help_text = 'ФИО ветеринара (или подпись).' 
        self.fields['vet_email'].help_text = 'Email сотрудника для напоминания (если указана следующая обработка).'
        self.fields['next_due_date'].help_text = 'Если требуется повтор/следующая обработка — укажите дату.'

class MovementForm(forms.ModelForm):
    class Meta:
        model = Movement
        fields = ['animal', 'date', 'from_location', 'to_location', 'reason', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # UI-05: подсказки
        self.fields['animal'].help_text = 'Животное, к которому относится запись.'
        self.fields['date'].help_text = 'Дата события.'
        self.fields['from_location'].help_text = 'Необязательно. Например: «Карантин», «Вольер 3».'
        self.fields['to_location'].help_text = 'Необязательно. Например: «Новый владелец», «Приют N».'
        self.fields['reason'].help_text = 'Причина/тип события.'
        self.fields['notes'].help_text = 'Дополнительные примечания.'

class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['image', 'order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # UI-05: подсказки
        self.fields['image'].help_text = 'Выберите файл изображения (jpg/png).' 
        self.fields['order'].help_text = 'Порядок отображения в галерее (меньше — раньше).'