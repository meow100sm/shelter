import django_filters
from django import forms 
from .models import Animal
from django.db import models

class AnimalFilter(django_filters.FilterSet):
    species = django_filters.ChoiceFilter(
        choices=Animal.SPECIES_CHOICES,
        empty_label='Все',
        label='Вид'
    )
    status = django_filters.ChoiceFilter(
        choices=Animal.STATUS_CHOICES,
        empty_label='Все',
        label='Статус'
    )
    intake_date_after = django_filters.DateFilter(
        field_name='intake_date',
        lookup_expr='gte',
        widget=forms.DateInput(attrs={'type': 'date'}),  
        label='Дата поступления с'
    )
    intake_date_before = django_filters.DateFilter(
        field_name='intake_date',
        lookup_expr='lte',
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='по'
    )

    search = django_filters.CharFilter(method='filter_by_search', label='Поиск')
    
    def filter_by_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            models.Q(unique_id__icontains=value) |
            models.Q(name__icontains=value)
        )
    
    class Meta:
        model = Animal
        fields = ['species', 'status', 'intake_date_after', 'intake_date_before', 'search']