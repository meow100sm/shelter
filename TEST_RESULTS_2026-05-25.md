# Результаты тестирования — 2026-05-25

Среда:
- ОС: Windows
- Python: 3.11.9 (venv `.venv`)
- Проект: Django (shelter_project2)

Ниже зафиксированы результаты реально выполненных прогонов тестов.

---

## 1) Django автотесты (SQLite in-memory)

Команда (PowerShell):

```powershell
$env:DJANGO_TEST_USE_POSTGRES=$null
$env:DJANGO_TEST_DB="sqlite"
c:/Users/dasha/OneDrive/Desktop/shelter_project2/.venv/Scripts/python.exe manage.py test -v 2
```

Результат: ✅ OK (11 тестов)

Вывод:

```text
Found 11 test(s).
Creating test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Operations to perform:
  Synchronize unmigrated apps: crispy_bootstrap5, crispy_forms, django_filters, django_otp, messages, reports, staticfiles
  Apply all migrations: accounts, admin, animals, auth, contenttypes, otp_static, otp_totp, sessions
Synchronizing apps without migrations:
  Creating tables...
    Running deferred SQL...
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0001_initial... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying auth.0007_alter_validators_add_error_messages... OK
  Applying auth.0008_alter_user_username_max_length... OK
  Applying auth.0009_alter_user_last_name_max_length... OK
  Applying auth.0010_alter_group_name_max_length... OK
  Applying auth.0011_update_proxy_permissions... OK
  Applying auth.0012_alter_user_first_name_max_length... OK
  Applying accounts.0001_initial... OK
  Applying accounts.0002_alter_user_role_auditlog... OK
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying admin.0003_logentry_add_action_flag_choices... OK
  Applying animals.0001_initial... OK
  Applying animals.0002_animal_name_photo_uploaded_by... OK
  Applying animals.0003_alter_animal_unique_id... OK
  Applying otp_static.0001_initial... OK
  Applying otp_static.0002_throttling... OK
  Applying otp_static.0003_add_timestamps... OK
  Applying otp_totp.0001_initial... OK
  Applying otp_totp.0002_auto_20190420_0723... OK
  Applying otp_totp.0003_add_timestamps... OK
  Applying sessions.0001_initial... OK
System check identified no issues (0 silenced).
test_admin_only_user_list_ok_for_admin (accounts.tests.AccountsSmokeTests.test_admin_only_user_list_ok_for_admin) ... ok
test_admin_only_user_list_redirects_for_volunteer (accounts.tests.AccountsSmokeTests.test_admin_only_user_list_redirects_for_volunteer) ... ok
test_admin_with_2fa_device_redirects_to_2fa (accounts.tests.AccountsSmokeTests.test_admin_with_2fa_device_redirects_to_2fa) ... ok
test_login_success_creates_audit_log (accounts.tests.AccountsSmokeTests.test_login_success_creates_audit_log) ... ok
test_animal_create_requires_login (animals.tests.AnimalsSmokeTests.test_animal_create_requires_login) ... ok
test_animal_list_ok_for_anonymous (animals.tests.AnimalsSmokeTests.test_animal_list_ok_for_anonymous) ... ok
test_dashboard_ok_for_anonymous (animals.tests.AnimalsSmokeTests.test_dashboard_ok_for_anonymous) ... ok
test_movement_list_requires_login (animals.tests.AnimalsSmokeTests.test_movement_list_requires_login) ... ok
test_volunteer_can_create_animal_min_fields (animals.tests.AnimalsSmokeTests.test_volunteer_can_create_animal_min_fields) ... ok
test_report_form_ok_when_logged_in (reports.tests.ReportsSmokeTests.test_report_form_ok_when_logged_in) ... ok
test_report_form_requires_login (reports.tests.ReportsSmokeTests.test_report_form_requires_login) ... ok

----------------------------------------------------------------------
Ran 11 tests in 8.330s

OK
Destroying test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
```

---

## 2) Django автотесты (PostgreSQL)

Команда (PowerShell):

```powershell
$env:DJANGO_TEST_USE_POSTGRES="1"
c:/Users/dasha/OneDrive/Desktop/shelter_project2/.venv/Scripts/python.exe manage.py test -v 2
```

Результат: ✅ OK (11 тестов)

Вывод:

```text
Found 11 test(s).
Creating test database for alias 'default' ('test_shelter_db')...
Operations to perform:
  Synchronize unmigrated apps: crispy_bootstrap5, crispy_forms, django_filters, django_otp, messages, reports, staticfiles
  Apply all migrations: accounts, admin, animals, auth, contenttypes, otp_static, otp_totp, sessions
Synchronizing apps without migrations:
  Creating tables...
    Running deferred SQL...
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0001_initial... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying auth.0007_alter_validators_add_error_messages... OK
  Applying auth.0008_alter_user_username_max_length... OK
  Applying auth.0009_alter_user_last_name_max_length... OK
  Applying auth.0010_alter_group_name_max_length... OK
  Applying auth.0011_update_proxy_permissions... OK
  Applying auth.0012_alter_user_first_name_max_length... OK
  Applying accounts.0001_initial... OK
  Applying accounts.0002_alter_user_role_auditlog... OK
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying admin.0003_logentry_add_action_flag_choices... OK
  Applying animals.0001_initial... OK
  Applying animals.0002_animal_name_photo_uploaded_by... OK
  Applying animals.0003_alter_animal_unique_id... OK
  Applying otp_static.0001_initial... OK
  Applying otp_static.0002_throttling... OK
  Applying otp_static.0003_add_timestamps... OK
  Applying otp_totp.0001_initial... OK
  Applying otp_totp.0002_auto_20190420_0723... OK
  Applying otp_totp.0003_add_timestamps... OK
  Applying sessions.0001_initial... OK
System check identified no issues (0 silenced).
test_admin_only_user_list_ok_for_admin (accounts.tests.AccountsSmokeTests.test_admin_only_user_list_ok_for_admin) ... ok
test_admin_only_user_list_redirects_for_volunteer (accounts.tests.AccountsSmokeTests.test_admin_only_user_list_redirects_for_volunteer) ... ok
test_admin_with_2fa_device_redirects_to_2fa (accounts.tests.AccountsSmokeTests.test_admin_with_2fa_device_redirects_to_2fa) ... ok
test_login_success_creates_audit_log (accounts.tests.AccountsSmokeTests.test_login_success_creates_audit_log) ... ok
test_animal_create_requires_login (animals.tests.AnimalsSmokeTests.test_animal_create_requires_login) ... ok
test_animal_list_ok_for_anonymous (animals.tests.AnimalsSmokeTests.test_animal_list_ok_for_anonymous) ... ok
test_dashboard_ok_for_anonymous (animals.tests.AnimalsSmokeTests.test_dashboard_ok_for_anonymous) ... ok
test_movement_list_requires_login (animals.tests.AnimalsSmokeTests.test_movement_list_requires_login) ... ok
test_volunteer_can_create_animal_min_fields (animals.tests.AnimalsSmokeTests.test_volunteer_can_create_animal_min_fields) ... ok
test_report_form_ok_when_logged_in (reports.tests.ReportsSmokeTests.test_report_form_ok_when_logged_in) ... ok
test_report_form_requires_login (reports.tests.ReportsSmokeTests.test_report_form_requires_login) ... ok

----------------------------------------------------------------------
Ran 11 tests in 8.528s

OK
Destroying test database for alias 'default' ('test_shelter_db')...
```

---

## 3) E2E (Playwright через pytest)

Команда:

```powershell
c:/Users/dasha/OneDrive/Desktop/shelter_project2/.venv/Scripts/python.exe -m pytest -m e2e -q
```

Результат: ✅ OK (2 теста)

Вывод:

```text
..                                                                       [100%]
2 passed in 14.21s
```

Покрытые сценарии:
- `test_login_and_see_dashboard`: логин → проверка, что открывается «Дашборд»
- `test_create_animal_add_vet_record_and_verify`: логин → создание животного → добавление вет. записи → проверка отображения данных
