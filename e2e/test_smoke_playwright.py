import pytest
import re
from playwright.sync_api import expect, sync_playwright

from django.contrib.auth import get_user_model


@pytest.mark.e2e
def test_login_and_see_dashboard(live_server):
    User = get_user_model()
    User.objects.create_user(username="e2e", password="e2epass", role="admin")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(f"{live_server.url}/accounts/login/")
        page.fill('input[name="username"]', "e2e")
        page.fill('input[name="password"]', "e2epass")
        page.click('button[type="submit"]')

        # After login should land on dashboard
        page.wait_for_url(f"{live_server.url}/")
        expect(page.locator("h1.title")).to_have_text("Дашборд")

        browser.close()


@pytest.mark.e2e
def test_create_animal_add_vet_record_and_verify(live_server):
    User = get_user_model()
    User.objects.create_user(username="e2e_admin", password="e2epass", role="admin")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Login
        page.goto(f"{live_server.url}/accounts/login/")
        page.fill('input[name="username"]', "e2e_admin")
        page.fill('input[name="password"]', "e2epass")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{live_server.url}/")

        # Create animal
        page.goto(f"{live_server.url}/animals/create/")
        expect(page.locator("h1.title")).to_have_text("Добавление нового животного")

        animal_name = "Барсик E2E"
        page.fill('input[name="name"]', animal_name)
        page.select_option('select[name="species"]', "cat")
        page.select_option('select[name="sex"]', "F")
        page.select_option('select[name="status"]', "intake")
        page.fill('input[name="intake_date"]', "2026-05-25")
        page.fill('input[name="intake_source"]', "E2E")

        page.click('button[type="submit"]')
        page.wait_for_url(re.compile(rf"{re.escape(live_server.url)}/animals/\d+/?$"))

        # Verify animal data on basic tab
        expect(page.locator(".meta")).to_contain_text("Вид:")
        expect(page.locator(".meta")).to_contain_text("Кошка")
        expect(page.locator(".meta")).to_contain_text("Пол:")
        expect(page.locator(".meta")).to_contain_text("Женский")
        expect(page.locator(".meta")).to_contain_text("Кличка:")
        expect(page.locator(".meta")).to_contain_text(animal_name)

        # Go to vet tab
        page.click('a.tab:has-text("Ветеринария")')
        page.wait_for_url(re.compile(r".*[?&]tab=vet.*"))

        # Add vet record
        page.click('a.btn:has-text("Добавить запись")')
        expect(page.locator("h1.title")).to_have_text("Добавление ветеринарной записи")

        vet_description = "Осмотр уха"
        vet_name = "Доктор Тест"

        page.fill('input[name="date"]', "2026-05-25")
        page.select_option('select[name="type"]', "exam")
        page.fill('textarea[name="description"]', vet_description)
        page.fill('input[name="vet_name"]', vet_name)
        page.fill('input[name="next_due_date"]', "2026-06-01")

        page.click('button[type="submit"]')
        page.wait_for_url(re.compile(r".*[?&]tab=vet.*"))

        # Verify vet record data is visible in the table
        table = page.locator("table.table")
        expect(table).to_contain_text("Осмотр")
        expect(table).to_contain_text(vet_description)
        expect(table).to_contain_text(vet_name)
        expect(table).to_contain_text("25.05.2026")
        expect(table).to_contain_text("01.06.2026")

        browser.close()
