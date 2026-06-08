# Проверка соответствия документации реальному проекту — 2026-05-25

Проверяемый документ: [text.txt](text.txt)

Цель: сверить утверждения о проектировании/реализации с тем, что реально есть в текущем коде/шаблонах/настройках проекта.

Статусы:
- ✅ соответствует (есть в проекте и работает по смыслу)
- 🟡 частично (есть, но отличается: неполно, нестрого по ролям, другой формат/файл, упрощено)
- ❌ не соответствует (в проекте отсутствует или реализовано иначе)
- ⚪ не проверяемо по репозиторию (нужны замеры/инфраструктура/внешняя среда)

---

## 1) Функциональные требования (FR)

### Модуль «Учёт животных»

- FR-01 CRUD карточек + загрузка фото до 5:
  - CRUD карточек ✅: формы/страницы есть ([animals/views.py](animals/views.py), [templates/animals/animal_form.html](templates/animals/animal_form.html), [templates/animals/animal_detail.html](templates/animals/animal_detail.html))
  - загрузка фото ✅: отдельная форма/страница загрузки ([animals/views.py](animals/views.py), [templates/animals/photo_form.html](templates/animals/photo_form.html))
  - лимит «до 5 фото» ❌: ограничение количества фото в коде/шаблонах не обнаружено (кнопка «+ Загрузить фото» показывается всегда).

- FR-02 набор полей карточки ✅: поля присутствуют в модели ([animals/models.py](animals/models.py)).

- FR-03 автогенерация AN-XXXX ✅: реализована в `Animal.save()` ([animals/models.py](animals/models.py)).

- FR-04 поиск/фильтрация ✅/🟡:
  - фильтры по виду/статусу/датам ✅: [animals/filters.py](animals/filters.py) + [templates/animals/animal_list.html](templates/animals/animal_list.html)
  - «глобальный поиск» по номеру/кличке ✅: форма в шапке ([templates/base.html](templates/base.html)), обработчик поиска ([animals/views.py](animals/views.py))
  - отличие от текста 🟡: в документе упоминается параметр `q` и имя маршрута `global_search`, а в проекте URL называется `animals:search` и перекидывает на список через параметр `search`.

- FR-05 удаление фото только админ или автор ✅: проверка прав есть ([animals/views.py](animals/views.py), [templates/animals/animal_detail.html](templates/animals/animal_detail.html)).

### Модуль «Ветеринарное сопровождение»

- FR-06 медкарта/история процедур ✅: вкладка «Ветеринария» в карточке животного и таблица записей ([templates/animals/animal_detail.html](templates/animals/animal_detail.html)).

- FR-07 запись мероприятия (дата/тип/описание/ветеринар/след. дата) ✅: модель и форма есть ([animals/models.py](animals/models.py), [animals/forms.py](animals/forms.py), [templates/animals/vetrecord_form.html](templates/animals/vetrecord_form.html)).

- FR-08 email-напоминание за 3 дня 🟡:
  - есть команда отправки напоминаний ✅: [animals/management/commands/send_reminders.py](animals/management/commands/send_reminders.py)
  - но планирование (cron/Task Scheduler) для этой команды не является частью приложения ❌ (в репозитории нет настроенного расписания именно для напоминаний).
  - также email-адрес формируется упрощённо из `vet_name` 🟡 (это скорее демо-логика).

- FR-09 цветовая индикация статусов здоровья 🟡/❌:
  - в шаблонах выводится класс `s-{{ animal.status }}` ✅ ([templates/animals/animal_list.html](templates/animals/animal_list.html), [templates/animals/animal_detail.html](templates/animals/animal_detail.html))
  - но в CSS определены классы `.s-green/.s-yellow/.s-red/.s-blue`, а не `.s-healthy/.s-quarantine/...` ❌: [static/css/style.css](static/css/style.css)
  - итог: в текущем виде цветовая индикация статусов, описанная в документе, не подтверждается стилями.

- FR-10 календарь процедур ✅/🟡:
  - календарная сетка, маркеры количества, клик по дню → форма с датой ✅: [animals/views.py](animals/views.py), [templates/animals/vet_journal.html](templates/animals/vet_journal.html)
  - отличие от документа 🟡: в тексте утверждается оптимизация «один запрос на месяц», но в коде внутри цикла выполняются запросы на каждый день месяца (N запросов).

### Модуль «Движение животных»

- FR-11 фиксация поступления/перемещений/выбытия ✅: модель и формы есть ([animals/models.py](animals/models.py), [animals/views.py](animals/views.py)).

- FR-12 договор передачи PDF ❌: генерации договора передачи/усыновления как отдельного PDF на основе шаблона в проекте не найдено.

- FR-13 автоизменение статуса при выбытии ❌: в обработчиках создания перемещений нет логики изменения `Animal.status`.

### Модуль «Отчёты»

- FR-14 журнал поступления PDF/Excel 🟡:
  - PDF ✅: генератор есть ([reports/generators.py](reports/generators.py))
  - Excel ❌: отдельного Excel-журнала поступлений нет (в [reports/views.py](reports/views.py) отсутствует ветка для Excel по поступлениям).

- FR-15 журнал вет. мероприятий PDF/Excel 🟡:
  - Excel ✅: есть генератор ([reports/generators.py](reports/generators.py))
  - PDF ❌: вет. журнал в PDF не реализован.

- FR-16 журнал выбытия/перемещений PDF/Excel ✅: реализованы оба формата ([reports/generators.py](reports/generators.py)).

- FR-17 годовой статистический отчёт PDF/Excel 🟡:
  - PDF ✅/🟡: в PDF есть KPI, распределения, топ пород, причины перемещений, типы процедур, «текстовая гистограмма» и галерея фото (см. [reports/generators.py](reports/generators.py))
  - Excel 🟡/❌: Excel-версия сильно упрощена (нет перечисленных листов/диаграмм; только сводные таблицы на одном листе).

### Модуль «Пользователи и безопасность»

- FR-18 логин/пароль ✅: [accounts/views.py](accounts/views.py), [templates/accounts/login.html](templates/accounts/login.html)

- FR-19 роли (admin/vet/volunteer/guest) 🟡:
  - роли в модели ✅: [accounts/models.py](accounts/models.py)
  - гость (аноним) действительно может смотреть дашборд/списки/карточки ✅: [animals/views.py](animals/views.py)
  - но ограничения прав в части животных/ветеринарии/отчётов реализованы нестрого 🟡:
    - многие view-функции защищены только `login_required` и не проверяют роль, хотя меню скрывает ссылки.
    - пример: удаление животного не ограничено ролью (есть только `login_required`).

- FR-20 2FA для admin 🟡:
  - 2FA реализована через `django-otp` + QR (qrcode) ✅: [accounts/views.py](accounts/views.py), [templates/accounts/setup_2fa.html](templates/accounts/setup_2fa.html)
  - отличие от документа 🟡: 2FA фактически включается только если у пользователя уже есть подтверждённое устройство; если устройство не настроено, вход проходит без 2FA.
  - кроме того, в коде 2FA применяется и к роли `vet` (admin/vet), что расходится с частью формулировок из README, но совпадает с текстом документа.

- FR-21 журналирование действий ✅/🟡:
  - таблица аудита есть ✅: [accounts/models.py](accounts/models.py)
  - `log_action()` существует ✅: [accounts/utils.py](accounts/utils.py)
  - отличие от документа 🟡: в документе упоминаются IP/JSON/JSONB, но модель аудита хранит только `action` и текстовое `details` (без отдельного поля IP и без JSONB).

- FR-22 управление учётками только админ + открытая регистрация с кодом ✅:
  - CRUD пользователей только для admin ✅: [accounts/views.py](accounts/views.py)
  - регистрация с кодом VOL2026/VET2026 ✅: [accounts/forms.py](accounts/forms.py), [accounts/views.py](accounts/views.py)

---

## 2) Нефункциональные требования (NFR)

- bcrypt cost=12 ❌/⚪:
  - пакет `bcrypt` присутствует в зависимостях ✅: [requirements.txt](requirements.txt)
  - но явной настройки `PASSWORD_HASHERS` на bcrypt в [shelter/settings.py](shelter/settings.py) нет ❌, поэтому по умолчанию Django использует PBKDF2.

- HTTPS, Nginx, Gunicorn ⚪/❌:
  - в документе описана production-схема Nginx+Gunicorn, но конфигов Nginx/Gunicorn в репозитории нет ❌.
  - это может быть частью внешнего окружения, но по текущему коду подтвердить нельзя ⚪.

- Производительность/нагрузка (≤1с, ≤2с на 1000 записей, ≤20 пользователей) ⚪:
  - в репозитории нет сценариев нагрузочного тестирования (Locust) ❌, и нет результатов замеров, которые можно воспроизвести из кода.

---

## 3) Требования к интерфейсу (UI)

- UI-01 русскоязычный адаптивный интерфейс ✅: шаблоны на русском + адаптивные медиа-правила в CSS ([templates/base.html](templates/base.html), [static/css/style.css](static/css/style.css)).
- UI-02 бургер-меню ✅: кнопка в [templates/base.html](templates/base.html) + логика в [static/js/script.js](static/js/script.js).
- UI-03 миниатюры в списке ✅: [templates/animals/animal_list.html](templates/animals/animal_list.html).
- UI-04 цветовая индикация статусов 🟡/❌: см. FR-09 (классы статусов и CSS не совпадают).
- UI-05 подсказки для полей 🟡: help_text у некоторых полей есть (например, кличка), но это не покрывает все поля.
- UI-06 подтверждение удаления ✅/🟡: часть удалений через confirm/страницы подтверждения есть, но в некоторых местах действие выглядит как прямой переход по ссылке на удаление (в итоге всё равно приходит на confirm-страницу животного).

---

## 4) Актуализация главы «Разработка/реализация» (3.x)

Чтобы описание реализации в [text.txt](text.txt) соответствовало текущему коду, корректные формулировки должны отражать следующие факты:

- Представления: в проекте используются function-based views (а не стандартные class-based views вроде ListView/DetailView) — см. [animals/views.py](animals/views.py).
- Глобальный поиск: маршрут с именем `animals:search` принимает параметр `q` и перенаправляет либо на карточку (точное совпадение `unique_id`), либо на список с параметром `search` (поиск по подстроке) — см. [animals/views.py](animals/views.py), [animals/urls.py](animals/urls.py), [templates/base.html](templates/base.html).
- Отчёты: генерация PDF/Excel реализована в [reports/generators.py](reports/generators.py) (отдельного модуля `reports/services/pdf_report.py` нет).
- Аудит: модель [accounts/models.py](accounts/models.py) хранит пользователя, `action`, `timestamp` и текстовое поле `details`; IP фиксируется строкой в `details` для событий входа/2FA-входа, поля JSONB нет — см. [accounts/views.py](accounts/views.py), [accounts/utils.py](accounts/utils.py).
- UI: основной интерфейс использует кастомный CSS ([static/css/style.css](static/css/style.css)); `crispy-bootstrap5` подключён для разметки отдельных форм, но глобального подключения Bootstrap/Font Awesome в шаблонах нет — см. [templates/base.html](templates/base.html).

---

## 5) Резервное копирование

- Описание резервного копирования в целом ✅ соответствует: есть скрипты, которые делают pg_dump + архив media + retention 30 дней + лог.
  - Linux/macOS: [scripts/backup.sh](scripts/backup.sh)
  - Windows: [scripts/backup.ps1](scripts/backup.ps1)

---

## 6) Тестирование (глава 3.10)

- Утверждения про 11 модульных тестов ✅ соответствует: тесты есть и реально проходят.
  - Файлы: [accounts/tests.py](accounts/tests.py), [animals/tests.py](animals/tests.py), [reports/tests.py](reports/tests.py)

- Утверждения про 2 E2E сценария ✅ соответствует: реализовано и реально проходит.
  - Файл: [e2e/test_smoke_playwright.py](e2e/test_smoke_playwright.py)

Фактический отчёт о прогонах тестов сохранён отдельно: [TEST_RESULTS_2026-05-25.md](TEST_RESULTS_2026-05-25.md).

---

## 7) Итог

Документ [text.txt](text.txt) частично соответствует проекту: базовые модули (животные, вет. записи, движение, аудит, 2FA, отчёты, бэкапы, тесты) в целом присутствуют.

Ключевые несоответствия: лимит «до 5 фото», договор передачи PDF, автоизменение статуса при выбытии, неполная поддержка форматов отчётов (vet PDF / animals Excel), нестрогое разграничение ролей на уровне view (часто только `login_required`), а также ряд «технических» утверждений (Bootstrap/Font Awesome, class-based views, JSONB/IP в аудите, оптимизация календаря), которые не подтверждаются текущим кодом.
