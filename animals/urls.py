from django.urls import path
from . import views

app_name = 'animals'

urlpatterns = [
    # Дашборд и животные
    path('', views.dashboard, name='dashboard'),
    path('animals/', views.animal_list, name='animal_list'),
    path('animals/create/', views.animal_create, name='animal_create'),
    path('animals/<int:pk>/', views.animal_detail, name='animal_detail'),
    path('animals/<int:pk>/edit/', views.animal_edit, name='animal_edit'),
    path('animals/<int:pk>/delete/', views.animal_delete, name='animal_delete'),
    path('search/', views.animal_search, name='search'),

    # Ветеринария
    path('vet/journal/', views.vet_journal, name='vet_journal'),
    path('animals/<int:animal_pk>/vet/add/', views.vet_record_create, name='vet_record_create'),
    path('vet/<int:pk>/edit/', views.vet_record_edit, name='vet_record_edit'),
    path('api/animals/', views.api_animals, name='api_animals'),
    path('vet/add/', views.vet_record_add, name='vet_record_add'),
    path('vet/<int:pk>/delete/', views.vet_record_delete, name='vet_record_delete'),

    # Движение
    path('movements/<int:pk>/contract/', views.movement_contract_pdf, name='movement_contract_pdf'),
    path('animals/<int:pk>/adoption/contract/', views.adoption_contract_pdf, name='adoption_contract_pdf'),
    path('movements/<int:pk>/edit/', views.movement_edit, name='movement_edit'),
    path('movements/<int:pk>/delete/', views.movement_delete, name='movement_delete'),
    path('movements/', views.movement_list, name='movement_list'),
    path('animals/<int:animal_pk>/movement/add/', views.movement_create, name='movement_create'),
    path('movements/add/', views.movement_create_general, name='movement_add'),

    # Фото
    path('animals/<int:animal_pk>/photo/add/', views.add_photo, name='add_photo'),
    path('photo/<int:pk>/delete/', views.delete_photo, name='delete_photo'),
]