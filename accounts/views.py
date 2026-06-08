from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django_otp.plugins.otp_totp.models import TOTPDevice
import qrcode
from io import BytesIO
import base64
from .models import User, AuditLog
from .utils import log_action
from django.http import HttpResponse
import csv
from .permissions import role_required
from django.contrib.auth.forms import PasswordChangeForm
from .forms import ProfileEditForm, RegistrationForm
from django_otp import user_has_device


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Проверяем, есть ли у пользователя настроенное OTP-устройство и требует ли его роль 2FA
            if user.role in ['admin', 'vet'] and user_has_device(user):
                # Если да - сохраняем ID и отправляем на проверку кода
                request.session['pre_2fa_user_id'] = user.id
                return redirect('accounts:2fa_verify')
            else:
                # Если нет - просто логиним
                login(request, user)
                log_action(user, 'login', f'Вход с IP {request.META.get("REMOTE_ADDR")}')
                return redirect('animals:dashboard')
        else:
            messages.error(request, 'Неверный логин или пароль')
    return render(request, 'accounts/login.html')

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            log_action(request.user, 'password_change', 'Пароль изменён')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Исправьте ошибки в форме')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})

def verify_2fa(request):
    user_id = request.session.get('pre_2fa_user_id')
    if not user_id:
        return redirect('accounts:login')
    user = User.objects.get(id=user_id)
    # Пытаемся получить устройство пользователя. Предполагаем, что основное устройство — одно.
    device = TOTPDevice.objects.filter(user=user, confirmed=True).first()
    if not device:
        # Если устройства нет, возможно, его нужно создать. Пока просто ошибка.
        messages.error(request, 'Ошибка: 2FA не настроена. Обратитесь к администратору.')
        return redirect('accounts:login')

    if request.method == 'POST':
        code = request.POST.get('code', '')
        if device.verify_token(code):
            login(request, user)
            del request.session['pre_2fa_user_id']
            log_action(user, 'login_2fa', f'2FA вход с IP {request.META.get("REMOTE_ADDR")}')
            return redirect('animals:dashboard')
        else:
            messages.error(request, 'Неверный код 2FA')

    return render(request, 'accounts/2fa.html')

@login_required
def logout_view(request):
    logout(request)
    log_action(request.user, 'logout', 'Выход из системы')
    return redirect('animals:dashboard')

@login_required
def profile(request):
    user = request.user
    return render(request, 'accounts/profile.html', {'user': user})

@login_required
def setup_2fa(request):
    # FR-20: 2FA доступна для admin и vet
    if request.user.role not in ['admin', 'vet']:
        messages.error(request, '2FA доступна только для ролей Администратор и Ветеринар')
        return redirect('accounts:profile')

    user = request.user
    # Создаём устройство для пользователя, если его ещё нет. confirmed=False означает, что оно ещё не активировано.
    device, created = TOTPDevice.objects.get_or_create(user=user, confirmed=False, defaults={'name': 'default'})

    if request.method == 'POST':
        code = request.POST.get('token')
        if device.verify_token(code):
            device.confirmed = True
            device.save()
            user.is_2fa_enabled = True
            user.save()
            log_action(request.user, '2fa_enable', 'Включена двухфакторная аутентификация')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Неверный код подтверждения. Попробуйте снова.')

    # Генерация QR-кода
    totp_url = device.config_url  # <-- Это стандартный URL для настройки TOTP
    img = qrcode.make(totp_url)
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return render(request, 'accounts/setup_2fa.html', {'qr_base64': qr_base64})

@login_required
def disable_2fa(request):
    # FR-20: 2FA доступна для admin и vet
    if request.user.role not in ['admin', 'vet']:
        messages.error(request, '2FA доступна только для ролей Администратор и Ветеринар')
        return redirect('accounts:profile')

    if request.method == 'POST':
        user = request.user
        TOTPDevice.objects.filter(user=user).delete()
        user.is_2fa_enabled = False
        user.save()
        log_action(request.user, '2fa_disable', 'Отключена двухфакторная аутентификация')
        return redirect('accounts:profile')
    return render(request, 'accounts/disable_2fa.html')

@login_required
@role_required('admin')
def user_list(request):
    users = User.objects.all()
    return render(request, 'accounts/user_list.html', {'users': users})

@login_required
@role_required('admin')
def user_create(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        role = request.POST['role']
        full_name = request.POST['full_name']
        User.objects.create_user(username=username, password=password, role=role, full_name=full_name)
        log_action(request.user, 'user_create', f'Создан пользователь {username}')
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_form.html')

@login_required
@role_required('admin')
def user_edit(request, pk):
    user = User.objects.get(pk=pk)
    if request.method == 'POST':
        user.username = request.POST['username']
        user.role = request.POST['role']
        user.full_name = request.POST['full_name']
        if request.POST.get('password'):
            user.set_password(request.POST['password'])
        user.save()
        log_action(request.user, 'user_edit', 'Пользователь изменён')
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_form.html', {'user': user})

@login_required
@role_required('admin')
def user_delete(request, pk):
    user = User.objects.get(pk=pk)
    if request.method == 'POST':
        username = request.POST['username']
        user.delete()
        log_action(request.user, 'user_delete', f'Удалён пользователь {username}')
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_confirm_delete.html', {'user': user})

@login_required
@role_required('admin')
def audit_log(request):
    logs = AuditLog.objects.select_related('user').all()

    # Фильтрация по пользователю
    user_id = request.GET.get('user')
    if user_id:
        logs = logs.filter(user_id=user_id)

    # Фильтрация по дате
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)
    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)

    # Экспорт в CSV
    if 'export' in request.GET:
        log_action(request.user, 'export_audit', 'Экспорт журнала аудита в CSV')
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="audit_log.csv"'
        # Добавляем BOM для корректного отображения в Excel
        response.write('\ufeff')
        writer = csv.writer(response, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['Дата/время', 'Пользователь', 'Действие', 'Детали'])
        for log in logs:
            # Экранируем переносы строк и лишние пробелы в деталях
            details = (log.details or '').replace('\n', ' ').replace('\r', ' ').strip()
            writer.writerow([
                log.timestamp.strftime('%d.%m.%Y %H:%M:%S'),
                log.user.username if log.user else 'Система',
                log.action,
                details,
            ])
        return response

    # Список пользователей для фильтра
    users = User.objects.all()

    context = {
        'logs': logs,
        'users': users,
        'selected_user': user_id,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'accounts/audit_log.html', context)

@login_required
def profile_edit(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            log_action(request.user, 'profile_edit', 'Обновлён профиль (ФИО/email)')
            return redirect('accounts:profile')
    else:
        form = ProfileEditForm(instance=user)
    return render(request, 'accounts/profile_edit.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            log_action(user, 'register', f'Зарегистрирован новый пользователь {user.username} (роль {user.role})')
            return redirect('accounts:login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})