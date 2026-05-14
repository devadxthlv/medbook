"""
Screenshot script for MedBook — captures all key pages for the README.

Usage:
    python scripts/take_screenshots.py
"""

import os
import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://3.27.246.227"
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "screenshots")
os.makedirs(OUT_DIR, exist_ok=True)

# Credentials
ADMIN_USER = "admin"
ADMIN_PASS = "Admin@1234!"
PATIENT_USER = "testpatient"
PATIENT_PASS = "Patient@1234!"


def screenshot(page, filename, name):
    """Wait for the page to settle and take a full-page screenshot."""
    page.wait_for_load_state("networkidle")
    time.sleep(0.5)  # brief pause for any CSS transitions
    path = os.path.join(OUT_DIR, filename)
    page.screenshot(path=path, full_page=True)
    size_kb = os.path.getsize(path) / 1024
    print(f"  ✅ {filename} ({name}) — {size_kb:.0f} KB")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        # ── Public pages (no login) ──────────────────────────────────
        print("\n📸 Taking public page screenshots...\n")

        # 1. Home page
        page.goto(BASE_URL + "/")
        screenshot(page, "01_home.png", "Home Page")

        # 2. Registration page
        page.goto(BASE_URL + "/accounts/register/")
        screenshot(page, "02_register.png", "Registration Page")

        # 3. Login page
        page.goto(BASE_URL + "/accounts/login/")
        screenshot(page, "03_login.png", "Login Page")

        # 4. Doctor listing
        page.goto(BASE_URL + "/doctors/")
        screenshot(page, "04_doctor_listing.png", "Doctor Listing")

        # 5. Doctor detail — click the first doctor's "View Profile" link
        page.goto(BASE_URL + "/doctors/")
        page.wait_for_load_state("networkidle")
        doctor_links = page.locator("a[href*='/doctors/']").all()
        detail_clicked = False
        for link in doctor_links:
            href = link.get_attribute("href") or ""
            # Look for a link like /doctors/1/ (detail page)
            if href.startswith("/doctors/") and href.rstrip("/").split("/")[-1].isdigit():
                link.click()
                detail_clicked = True
                break
        if not detail_clicked:
            # Fallback: try btn-primary or any card link
            btn = page.locator("a.btn-primary, a.btn-outline-primary").first
            if btn.count() > 0:
                btn.click()
        screenshot(page, "05_doctor_detail.png", "Doctor Detail Page")

        # ── Patient pages (login as patient) ─────────────────────────
        print("\n🔐 Logging in as patient...\n")

        page.goto(BASE_URL + "/accounts/login/")
        page.wait_for_load_state("networkidle")
        page.fill("input[name='username']", PATIENT_USER)
        page.fill("input[name='password']", PATIENT_PASS)
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")
        print(f"  Logged in as patient — URL: {page.url}")

        # 6. My appointments
        page.goto(BASE_URL + "/appointments/my/")
        screenshot(page, "06_my_appointments.png", "My Appointments")

        # ── Admin pages (log out and log in as admin) ────────────────
        print("\n🔐 Logging in as admin...\n")

        page.goto(BASE_URL + "/accounts/logout/")
        page.wait_for_load_state("networkidle")
        page.goto(BASE_URL + "/accounts/login/")
        page.wait_for_load_state("networkidle")
        page.fill("input[name='username']", ADMIN_USER)
        page.fill("input[name='password']", ADMIN_PASS)
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")
        print(f"  Logged in as admin — URL: {page.url}")

        # 7. Admin dashboard
        page.goto(BASE_URL + "/dashboard/")
        screenshot(page, "07_admin_dashboard.png", "Admin Dashboard")

        # 8. Admin user management
        page.goto(BASE_URL + "/dashboard/users/")
        screenshot(page, "08_admin_users.png", "Admin User Management")

        # 9. Admin doctor management
        page.goto(BASE_URL + "/dashboard/doctors/")
        screenshot(page, "09_admin_doctors.png", "Admin Doctor Management")

        # 10. Admin appointment management
        page.goto(BASE_URL + "/dashboard/appointments/")
        screenshot(page, "10_admin_appointments.png", "Admin Appointment Management")

        browser.close()
        print(f"\n✅ All 10 screenshots saved to {OUT_DIR}/\n")


if __name__ == "__main__":
    main()
