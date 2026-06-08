from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_form, name='report_form'),
]