from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Администратор'),
        ('vet', 'Ветеринар'),
        ('volunteer', 'Волонтёр'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='volunteer')
    full_name = models.CharField('Полное имя', max_length=150, blank=True)
    totp_secret = models.CharField(max_length=32, blank=True, null=True)
    is_2fa_enabled = models.BooleanField('2FA включена', default=False)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

class AuditLog(models.Model):
    user = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Пользователь')
    action = models.CharField(max_length=200, verbose_name='Действие')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Время')
    details = models.TextField(blank=True, verbose_name='Детали')

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Запись аудита'
        verbose_name_plural = 'Журнал аудита'

    def __str__(self):
        return f"{self.timestamp} - {self.user} - {self.action}"