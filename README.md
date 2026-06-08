# PawCare (Shelter project)

Django-приложение для учёта животных в приюте: карточки животных, ветеринарный журнал, движения, отчёты, управление пользователями и аудит действий.

Дата актуализации инструкции: 2026-06-01.

---

## 1) Развёртывание и запуск (демо/разработка)

### Требования

- **Python**: рекомендуется 3.10–3.12 (проект использует Django 4.2).
- **PostgreSQL**: проект по умолчанию настроен на PostgreSQL (см. `shelter/settings.py`).
- (Опционально) **Git**, если вы переносите проект через репозиторий.

> Примечание: в проекте используется виртуальное окружение `.venv/`. Оно нужно, чтобы зависимости из `requirements.txt` ставились изолированно и одинаково на любом устройстве.

---

### Самый простой вариант (только Docker)

Если на другом устройстве вы хотите развернуть проект с минимальными требованиями, используйте Docker Compose: тогда **не нужно устанавливать PostgreSQL и Python** (нужен только Docker Desktop). Этот способ одинаково работает на **Windows** и **Linux**.

1) Установите Docker Desktop.
2) В папке проекта (рядом с `docker-compose.yml`) выполните:

```powershell
docker compose up -d --build
```

То же самое одной командой через скрипт:

```powershell
.\scripts\demo.ps1
```

На Linux/macOS:

```bash
chmod +x scripts/demo.sh
./scripts/demo.sh
```

3) Создайте администратора (один раз):

```powershell
docker compose run --rm web python manage.py createsuperuser
```

Или через скрипт (интерактивно):

```powershell
.\scripts\demo.ps1 -CreateSuperuser
```

4) Откройте приложение:

- http://127.0.0.1:8000/

Остановить все контейнеры:

```powershell
docker compose down
```

Или через скрипт:

```powershell
.\scripts\demo.ps1 -Down
```

Где хранятся данные:

- база PostgreSQL — в docker volume `postgres_data` (не пропадает после `down`)
- загруженные файлы — в папке `media/` на хосте (примонтирована в контейнер)
- собранная статика — в папке `staticfiles/` на хосте

---

### Быстрый старт (Windows PowerShell)

Откройте PowerShell в папке проекта (где лежит `manage.py`).

1) Создать и активировать виртуальное окружение

```powershell
py -m venv .venv
# если команды py нет, используйте:
# python -m venv .venv

# активация (PowerShell):
.\.venv\Scripts\Activate.ps1
```

Если PowerShell ругается на запуск скриптов, выполните один раз в ЭТОМ окне PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

2) Установить зависимости

```powershell
pip install -r requirements.txt
```

(Опционально) dev-инструменты (ruff и т.п.):

```powershell
pip install -r requirements-dev.txt
```

3) Настроить базу данных PostgreSQL

Проект ожидает PostgreSQL-подключение из `shelter/settings.py` (ENGINE `django.db.backends.postgresql_psycopg2`).

- Убедитесь, что PostgreSQL установлен и запущен.
- Создайте базу данных и пользователя, затем:
  - либо приведите PostgreSQL к параметрам из `shelter/settings.py`,
  - либо отредактируйте `DATABASES` в `shelter/settings.py` под вашу машину.

Пример (через `psql`, значения подставьте под свои):

```sql
CREATE USER shelter_user WITH PASSWORD '...';
CREATE DATABASE shelter_db OWNER shelter_user;
GRANT ALL PRIVILEGES ON DATABASE shelter_db TO shelter_user;
```

4) Применить миграции

```powershell
python manage.py migrate
```

5) Создать администратора (для входа)

```powershell
python manage.py createsuperuser
```

6) Собрать статику (важно для корректного отображения CSS/иконок)

В `shelter/settings.py` задано `STATIC_ROOT = BASE_DIR / 'staticfiles'`, и при `DEBUG=True` в `shelter/urls.py` статика отдаётся из `staticfiles/`.
Поэтому при развёртывании на новом устройстве выполните:

```powershell
python manage.py collectstatic --noinput
```

7) Запустить сервер

```powershell
python manage.py runserver
```

После запуска откройте в браузере:

- http://127.0.0.1:8000/ — приложение
- http://127.0.0.1:8000/admin/ — админка Django (опционально)

Если вы хотите показать приложение с другого устройства в той же сети (например, открыть с телефона):

```powershell
python manage.py runserver 0.0.0.0:8000
```

Важно: команда `python ...` должна выполняться в активированном виртуальном окружении `.venv`.
Если у вас установлен Python из Microsoft Store и зависимости не находятся, используйте явный путь:

```powershell
./.venv/Scripts/python.exe manage.py runserver 0.0.0.0:8000
```

Тогда открывайте `http://<IP_вашего_ПК>:8000/`.

---

### Локальный HTTPS (без предупреждений браузера)

В проект добавлён локальный HTTPS-режим на Python (без Docker):

- генерирует самоподписанный сертификат (с SAN для `localhost`, имени ПК и локальных IPv4);
- позволяет доверить его в Windows для текущего пользователя;
- запускает сайт по HTTPS на порту `8444`.

#### Вариант A: HTTPS только на этом ПК (localhost)

1) Сгенерировать сертификат:

```powershell
.\scripts\generate_local_certs.ps1
```

2) Доверить сертификат в Windows (текущий пользователь):

```powershell
.\scripts\install_ca.ps1
```

3) Запустить HTTPS-сервер:

```powershell
.\scripts\run_https.ps1
```

Открыть в браузере:

- `https://localhost:8444/`

#### Вариант B: HTTPS по локальной сети (открыть с телефона)

Важно: для LAN нужно (а) слушать на `0.0.0.0`, (б) открыть порт в Firewall, (в) открывать сайт по IP из одной Wi‑Fi сети, и (г) чтобы сертификат включал этот IP в SAN.

1) Узнать IPv4 адрес Wi‑Fi на ПК (пример):

```powershell
Get-NetIPAddress -AddressFamily IPv4 | Select-Object IPAddress, InterfaceAlias
```

Выберите адрес интерфейса `Wi-Fi` (обычно вида `192.168.x.x`). Дальше он будет обозначен как `<LAN_IP>`.

2) Перегенерировать сертификат (если вы меняли сеть/у вас сменился IP):

```powershell
.\scripts\generate_local_certs.ps1
.\scripts\install_ca.ps1
```

3) Запустить HTTPS так, чтобы сервер слушал на всех интерфейсах:

```powershell
$env:HTTPS_HOST='0.0.0.0'
$env:HTTPS_PORT='8444'
.\scripts\run_https.ps1
```

4) Открыть порт в Windows Firewall (нужно окно PowerShell **от имени администратора**):

```powershell
.\scripts\allow_https_port.ps1
```

5) На телефоне:

- Подключитесь к той же Wi‑Fi сети.
- Откройте `https://<LAN_IP>:8444/`.

Чтобы **не было предупреждений** на телефоне, импортируйте сертификат `caddy/ssl/localhost.cer` как доверенный корневой сертификат:

- Android: Settings → Security → Encryption & credentials → Install a certificate → CA certificate (названия пунктов могут отличаться).
- iOS/iPadOS: отправьте `.cer` на телефон, установите профиль, затем включите доверие: Settings → General → About → Certificate Trust Settings → включить Full Trust.

#### Смена порта

```powershell
$env:HTTPS_PORT='8445'
.\scripts\run_https.ps1
```

#### Troubleshooting (LAN)

- Если на ПК открывается `https://localhost:8444/`, а с телефона нет — это почти всегда Firewall или вы открываете не тот IP (VPN/VirtualBox).
- Проверка доступности порта на ПК:

```powershell
Test-NetConnection 127.0.0.1 -Port 8444
Test-NetConnection <LAN_IP> -Port 8444
```

- Если `Test-NetConnection <LAN_IP> -Port 8444` показывает `TcpTestSucceeded: False` — откройте порт в firewall (шаг 4) и убедитесь, что сеть в профиле **Private**, а не Public.
- Если телефон в «гостевой» сети/включена AP isolation — устройства могут не видеть друг друга.
- Если сменили Wi‑Fi/подключились к VPN — IP может измениться, и нужно заново сгенерировать сертификат.


## Проверка email-напоминаний (за 3 дня)

Команда отправки напоминаний:

```powershell
python manage.py send_reminders
```

Важно:

- Напоминания отправляются по полю `VetRecord.next_due_date` ("Дата следующей обработки"), а не по `VetRecord.date` ("Дата проведения").
- Дата "сегодня" берётся как локальная дата проекта (таймзона `Europe/Moscow`).

### Реальная отправка на почту (SMTP)

По умолчанию письма печатаются в консоль. Чтобы письма приходили на настоящую почту, задайте переменные окружения перед запуском команды.

PowerShell (пример):

```powershell
$env:EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
$env:EMAIL_HOST = 'smtp.gmail.com'
$env:EMAIL_PORT = '587'
$env:EMAIL_HOST_USER = 'your@gmail.com'
$env:EMAIL_HOST_PASSWORD = 'APP_PASSWORD'
$env:EMAIL_USE_TLS = '1'
$env:DEFAULT_FROM_EMAIL = 'your@gmail.com'

python manage.py send_reminders
```

Если при запуске падает с `TimeoutError: timed out`, это означает, что с вашей машины нет доступа к `smtp.gmail.com:587` (сеть/фаервол/антивирус/VPN/провайдер). Быстрая проверка в PowerShell:

```powershell
Test-NetConnection smtp.gmail.com -Port 587
```

В некоторых сетях порт 587 блокируется — попробуйте SSL-порт 465:

```powershell
$env:EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
$env:EMAIL_HOST = 'smtp.gmail.com'
$env:EMAIL_PORT = '465'
$env:EMAIL_HOST_USER = 'your@gmail.com'
$env:EMAIL_HOST_PASSWORD = 'APP_PASSWORD'
$env:EMAIL_USE_SSL = '1'
$env:EMAIL_USE_TLS = '0'
$env:DEFAULT_FROM_EMAIL = 'your@gmail.com'

python manage.py send_reminders
```

Если соединение медленное, можно увеличить таймаут:

```powershell
$env:EMAIL_TIMEOUT = '30'
```

Не коммитьте пароли в репозиторий — используйте переменные окружения или секреты CI/CD.

---

## 1.1) Можно ли “установить PostgreSQL при развёртывании приложения”?

Коротко: **PostgreSQL не ставится через `pip` и не является частью Django-проекта** — это отдельный системный сервис/приложение.

На практике есть 3 рабочих пути:

1) Установить PostgreSQL вручную на новом устройстве.
2) Запускать PostgreSQL в Docker (удобно для демо: не нужно ставить PostgreSQL как сервис).
3) Подключаться к удалённому PostgreSQL (например, на вашем ноутбуке/сервере), если сеть позволяет.

Если цель — быстро показать проект на другом устройстве без долгой установки и настройки сервиса, чаще всего лучше вариант **№2 (Docker)**.

---

## 1.2) Как не потерять существующую базу (перенос PostgreSQL)

Если у вас уже есть заполненная база на текущем ПК, правильный способ переноса — сделать **логический дамп** и восстановить его на новом устройстве.

### Шаг A — сделать дамп на старом устройстве

```powershell
# Формат custom (-F c) удобен для восстановления через pg_restore
pg_dump -h localhost -p 5433 -U shelter_user -F c -f shelter_db.dump shelter_db
```

Если `pg_dump` не находится, значит PostgreSQL-клиентские утилиты не в PATH.
Варианты:

- добавить путь к `...\PostgreSQL\<version>\bin` в PATH;
- или запускать `pg_dump` из этой папки.

### Шаг B — перенести файл дампа и медиа

- Скопируйте `shelter_db.dump` на новое устройство.
- Если важно показать **фото животных**, обязательно перенесите папку `media/` целиком.

### Шаг C — восстановить на новом устройстве

1) Поднимите PostgreSQL (установкой или через Docker), создайте базу и пользователя.
2) Восстановите дамп:

```powershell
# создайте пустую базу (пример)
createdb -h localhost -p 5433 -U shelter_user shelter_db

# восстановление
pg_restore -h localhost -p 5433 -U shelter_user -d shelter_db --clean --if-exists shelter_db.dump
```

Если на новом устройстве имя пользователя/владельца отличается, используйте `pg_restore --no-owner`.

---

## 1.3) Вариант: Django локально, PostgreSQL в Docker

Этот вариант полезен, если вы хотите запускать Django на хосте (через `.venv`), но **не хотите устанавливать PostgreSQL как программу**.

`docker-compose.yml` содержит два сервиса: `db` (PostgreSQL) и `web` (Django). Чтобы поднять только базу:

1) Запустить только PostgreSQL

```powershell
docker compose up -d db
```

2) Проверить, что контейнер живой

```powershell
docker compose ps
```

3) Дальше — обычные шаги Django на хосте (миграции/админ/запуск)

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
python manage.py runserver
```

Остановить базу:

```powershell
docker compose stop db
```

Данные базы сохраняются в docker volume `postgres_data`.

---

### Частые проблемы

- Нет стилей/иконок: выполните `python manage.py collectstatic --noinput`.
- Не подключается PostgreSQL: проверьте host/port/логин/пароль в `shelter/settings.py` и что PostgreSQL действительно слушает этот порт.

---

### Опционально: команда напоминаний

В проекте есть management-команда:

```powershell
python manage.py send_reminders
```

Сейчас включён `EMAIL_BACKEND = console`, поэтому письма будут печататься в консоль (для демо это удобно).

---

## 2) Краткое руководство пользователя

### Роли

- Администратор — управление пользователями, аудит, доступ к отчётам/ветразделу.
- Ветеринар — доступ к ветразделу и отчётам.
- Волонтёр — базовая работа с животными и движением (на некоторых формах скрываются поля, например статус).

### Вход

1) Откройте страницу входа: `/accounts/login/`.
2) Введите логин/пароль.
3) Если у пользователя роль `admin` или `vet` и включена 2FA, после логина появится экран ввода кода.

### 2FA (двухфакторная аутентификация)

- В профиле можно включить 2FA: «Профиль» → «Настроить 2FA» → отсканировать QR-код приложением-аутентификатором.
- Для подтверждения ввести одноразовый код.
- Отключение 2FA делается из профиля.

### Основные разделы

- Дашборд: сводные карточки и предстоящие обработки.
- Животные: список, фильтры, создание и карточка животного.
- Фото: добавление фото в карточке животного (сохраняются в `media/`).
- Ветеринария (admin/vet): журнал ветпроцедур и планирование следующей обработки.
- Движение: учёт поступлений/перемещений/усыновлений и т.д.
- Отчёты (admin/vet): формирование отчётов (PDF/Excel) по типу и периоду.
- Пользователи (admin): создание/редактирование/удаление пользователей.
- Аудит (admin): журнал действий, фильтры, экспорт в CSV.
- Профиль: данные пользователя, смена пароля, управление 2FA.

### Типовой сценарий

1) Войти в систему.
2) Создать животное (раздел «Животные» → «Создать»).
3) В карточке животного добавить фото, ветзаписи и движения.
4) При необходимости сформировать отчёт (раздел «Отчёты»).

---

## 3) Что переносить/не переносить

- `.venv/` — можно не переносить; на новом устройстве проще пересоздать и установить зависимости.
- `media/` — загруженные фото/файлы. Для демонстрации лучше переносить.
- `staticfiles/` — можно пересоздать командой `collectstatic`.
- `__pycache__/`, `.ruff_cache/` — кэш, переносить не нужно.

---

## 4) Автоматические резервные копии (cron + backup.sh)

В проект добавлен скрипт `scripts/backup.sh`, который:

- создаёт дамп базы PostgreSQL с помощью `pg_dump` (по умолчанию пытается сделать дамп через `docker compose exec db`, если база запущена в Docker);
- архивирует папку `media/` (фото животных) в `.tar.gz`;
- удаляет старые копии (дампы/архивы/лог-файлы) старше 30 дней;
- пишет результат работы в лог `backups/logs/backup_YYYY-MM-DD.log`.

### Ручной запуск

На Linux/macOS:

```bash
chmod +x scripts/backup.sh
./scripts/backup.sh
```

### Настройка ежедневного запуска в 02:00

Откройте crontab:

```bash
crontab -e
```

Добавьте строку (путь к проекту замените на свой):

```cron
0 2 * * * /path/to/shelter_project2/scripts/backup.sh
```

### Windows: Планировщик заданий (Task Scheduler) + backup.ps1

Для Windows добавлен скрипт `scripts/backup.ps1` (делает то же самое: дамп БД, архив `media/`, чистка старше 30 дней, логирование).

Пример ручного запуска:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\backup.ps1
```

Идея настройки в Task Scheduler:

1) Create Task…
2) Trigger: Daily, 02:00
3) Action: Start a program
  - Program/script: `powershell.exe`
  - Arguments:

```text
-ExecutionPolicy Bypass -NoProfile -File "C:\\path\\to\\shelter_project2\\scripts\\backup.ps1"
```

4) Start in (optional): `C:\\path\\to\\shelter_project2`

Логи будут писаться в `backups\\logs\\backup_YYYY-MM-DD.log`.

Если PostgreSQL у вас в Docker, убедитесь, что в момент запуска cron:

- Docker daemon запущен
- у пользователя cron есть доступ к docker (обычно пользователь должен быть в группе `docker`)

### Настройки (опционально)

Можно переопределить параметры через переменные окружения:

- `RETENTION_DAYS` (по умолчанию 30)
- `BACKUP_DIR` (по умолчанию `./backups`)
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`

Скрипт автоматически подхватывает `.env`, если файл существует в корне проекта.

---

## 5) Тестирование

### Автотесты Django (минимальный smoke-набор)

Добавлены минимальные автотесты (проверка основных страниц, логина, ограничений по ролям, базового создания животного).

Запуск:

```powershell
python manage.py test
```

Во время тестов по умолчанию используется SQLite (в памяти), чтобы тесты запускались на любой машине без PostgreSQL.
Если вы хотите прогонять тесты именно на PostgreSQL (на вашей dev-машине), убедитесь, что PostgreSQL запущен (например, `docker compose up -d db`), и включите флаг:

```powershell
$env:DJANGO_TEST_USE_POSTGRES = "1"
python manage.py test
```

То же самое для `pytest` (включая E2E):

```powershell
$env:DJANGO_TEST_USE_POSTGRES = "1"
pytest
```

Альтернативный (более читаемый) переключатель:

```powershell
$env:DJANGO_TEST_DB = "postgres"   # или "sqlite"
python manage.py test
```

### End-to-End (E2E) тестирование (Playwright)

Добавлен базовый E2E smoke‑тест: реальный браузер открывает страницу логина, выполняет вход и проверяет, что отображается «Дашборд».

Установка dev-зависимостей:

```powershell
pip install -r requirements-dev.txt
```

Установка браузера для Playwright (один раз):

```powershell
python -m playwright install chromium
```

Запуск E2E тестов:

```powershell
pytest -m e2e
```
