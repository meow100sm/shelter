from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('2fa/', views.verify_2fa, name='2fa_verify'),
    path('profile/', views.profile, name='profile'),
    path('setup-2fa/', views.setup_2fa, name='setup_2fa'),
    path('disable-2fa/', views.disable_2fa, name='disable_2fa'),
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('audit/', views.audit_log, name='audit_log'),
    path('change-password/', views.change_password, name='change_password'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('register/', views.register, name='register'),
]