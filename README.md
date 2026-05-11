# MedBook — Healthcare Appointment Booking System

MedBook is a full-featured healthcare appointment booking platform built with Django. It enables patients to find doctors, book appointments, and manage their health journey, while giving doctors tools to manage their schedules and administrators a comprehensive dashboard for oversight.

---

## Tech Stack

| Component        | Technology             | Version |
|------------------|------------------------|---------|
| Backend          | Django                 | 4.2.17  |
| Language         | Python                 | 3.12+   |
| Database (prod)  | MySQL                  | 8.0     |
| Database (dev)   | SQLite                 | 3       |
| MySQL driver     | mysqlclient            | 2.2.6   |
| Image processing | Pillow                 | 11.1.0  |
| Config           | python-decouple        | 3.8     |
| WSGI server      | Gunicorn               | 23.0.0  |
| Frontend         | Bootstrap 5 + vanilla JS | 5.3.3 |
| Reverse proxy    | Nginx                  | alpine  |
| Containerisation | Docker + Docker Compose | —      |

---

## Features

- **User Management & Auth**
  - Custom User model with role-based access (Patient / Doctor / Admin)
  - Patient self-registration with email confirmation (console backend in dev)
  - Login, logout, and full password-reset flow
  - Profile page with photo upload

- **Doctor Listings**
  - Public doctor listing with search by name and filter by specialisation
  - Individual doctor detail page with bio, experience, fee, and availability
  - Admin can create, edit, and delete doctor profiles

- **Appointment Booking**
  - Patients book appointments with doctors by choosing date + time slot
  - Dynamic time-slot selector (JS fetch to `/appointments/available-slots/`)
  - 30-minute slots from 09:00–17:00
  - Double-booking prevention: unique constraint at DB level + form validation
  - Patients can view upcoming/past/cancelled appointments and cancel pending ones
  - Doctors can view their schedule, confirm, and mark appointments complete

- **Admin Dashboard** (`/dashboard/`)
  - Summary stats: total patients, doctors, today's appointments, pending count
  - Recent appointments table with colour-coded status badges
  - User management: list, role filter, activate/deactivate
  - Doctor management: full CRUD
  - Appointment management: status updates with filter

- **Notifications**
  - Flash messages (Bootstrap alerts) for all key actions
  - Email notifications on registration and booking (console backend in dev)

---

## Architecture Overview

```
┌─────────────┐     ┌────────────┐     ┌────────────┐
│   Browser   │────▶│   Nginx    │────▶│  Gunicorn  │
│  (BS5 + JS) │     │ (reverse   │     │  (WSGI)    │
└─────────────┘     │  proxy)    │     └─────┬──────┘
                    └────────────┘           │
                                       ┌────▼────┐
                                       │  Django  │
                                       │  4.2.17  │
                                       └────┬────┘
                                            │
                                    ┌───────▼───────┐
                                    │  MySQL 8.0    │
                                    │  (or SQLite)  │
                                    └───────────────┘
```

The project is organised into four Django apps:

- **accounts** — Custom User model, registration, login/logout, profile
- **doctors** — Doctor model and public listing/detail views
- **appointments** — Appointment model, booking, management, available-slots API
- **dashboard** — Admin-only dashboard with stats and CRUD management

A shared **core** app provides the home page, the `@role_required` decorator, and shared utilities.

---

## Local Setup

```bash
# 1. Clone the repository
git clone <repo-url> && cd medbook

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
# For development extras (coverage, flake8):
pip install -r requirements-dev.txt

# 4. Configure environment
cp .env.example .env
# Edit .env — at minimum set a SECRET_KEY

# 5. Run migrations (SQLite by default)
python manage.py migrate

# 6. Create a superuser (admin)
python manage.py createsuperuser

# 7. Start the development server
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` — you're live!

---

## Environment Variables

| Variable                 | Description                              | Example                          |
|--------------------------|------------------------------------------|----------------------------------|
| `SECRET_KEY`             | Django secret key                        | `your-super-secret-key`         |
| `DEBUG`                  | Enable debug mode                        | `True`                           |
| `DJANGO_SETTINGS_MODULE` | Settings module path                    | `medbook.settings.development`   |
| `ALLOWED_HOSTS`          | Comma-separated allowed hosts           | `localhost,127.0.0.1`            |
| `DB_NAME`                | MySQL database name                      | `medbook_db`                     |
| `DB_USER`                | MySQL user                               | `medbook_user`                   |
| `DB_PASSWORD`            | MySQL password                           | `secure-password-here`           |
| `DB_HOST`                | MySQL host                               | `127.0.0.1`                      |
| `DB_PORT`                | MySQL port                               | `3306`                           |
| `EMAIL_HOST`             | SMTP server                              | `smtp.gmail.com`                 |
| `EMAIL_PORT`             | SMTP port                                | `587`                            |
| `EMAIL_HOST_USER`        | SMTP username                            | `your-email@gmail.com`           |
| `EMAIL_HOST_PASSWORD`    | SMTP password / app password             | `your-app-password`              |
| `MEDIA_URL`              | URL prefix for uploaded media            | `/media/`                        |
| `MEDIA_ROOT`             | Filesystem path for uploaded media       | `media/`                         |

---

## Running with Docker

```bash
# 1. Copy and configure environment
cp .env.example .env
# Edit .env — set SECRET_KEY, DEBUG=False, DB credentials

# 2. Build and start services
docker-compose up --build -d

# 3. Run initial migrations and create superuser
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

# 4. Visit http://localhost in your browser
```

Services:
- **web** — Django + Gunicorn on port 8000
- **db** — MySQL 8.0 on port 3306
- **nginx** — Reverse proxy on port 80

---

## Project Structure

```
medbook/
├── medbook/                  # Django project configuration
│   ├── settings/
│   │   ├── base.py           # Shared settings (auth, security, static, etc.)
│   │   ├── development.py    # DEBUG=True, SQLite, console email
│   │   └── production.py     # DEBUG=False, MySQL, SMTP, HTTPS hardening
│   ├── urls.py               # Root URL configuration
│   └── wsgi.py               # WSGI entry point
├── accounts/                 # Custom User model, auth views, profile
├── doctors/                  # Doctor model, listings, detail pages
├── appointments/             # Appointment model, booking, management, API
├── dashboard/                # Admin dashboard views
├── core/                     # Shared utilities: decorators, home page
├── templates/                # Django templates (base + per-app)
│   ├── base.html             # Master template: navbar, messages, footer
│   ├── accounts/             # Register, login, profile, password reset
│   ├── doctors/              # Doctor list, doctor detail
│   ├── appointments/         # Booking, patient appointments, doctor schedule
│   └── dashboard/            # Admin dashboard, user/doctor/appointment management
├── static/
│   ├── css/main.css          # Custom styles on top of Bootstrap 5
│   └── js/main.js            # Auto-dismiss alerts, active nav highlighting
├── media/                    # Uploaded files (gitignored)
├── requirements.txt          # Production dependencies
├── requirements-dev.txt      # Development dependencies
├── .env.example              # Environment variable template
├── manage.py                 # Django management script
├── Dockerfile                # Docker image definition
├── docker-compose.yml        # Multi-service orchestration
├── nginx/default.conf        # Nginx reverse proxy configuration
├── README.md                 # This file
└── AGENT.md                  # Developer handoff documentation
```

---

## API / URL Routes

| URL Pattern                              | Method | View                        | Access Level |
|------------------------------------------|--------|-----------------------------|-------------|
| `/`                                      | GET    | Home page                   | Public      |
| `/accounts/register/`                    | GET/POST | Patient registration      | Public      |
| `/accounts/login/`                       | GET/POST | Login                     | Public      |
| `/accounts/logout/`                      | POST   | Logout                      | Authenticated |
| `/accounts/profile/`                     | GET/POST | Profile update            | Authenticated |
| `/accounts/password-reset/`              | GET/POST | Password reset request    | Public      |
| `/accounts/password-reset/done/`         | GET    | Password reset sent         | Public      |
| `/accounts/password-reset/<uid>/<token>/`| GET/POST | Set new password          | Public (token) |
| `/accounts/password-reset/complete/`     | GET    | Password reset complete     | Public      |
| `/doctors/`                              | GET    | Doctor listing              | Public      |
| `/doctors/<pk>/`                         | GET    | Doctor detail               | Public      |
| `/appointments/book/<doctor_pk>/`        | GET/POST | Book appointment          | Patient     |
| `/appointments/my/`                      | GET    | Patient's appointments      | Authenticated |
| `/appointments/cancel/<pk>/`             | POST   | Cancel appointment          | Patient     |
| `/appointments/doctor/`                  | GET    | Doctor's schedule           | Doctor      |
| `/appointments/update-status/<pk>/`      | POST   | Update appointment status   | Doctor      |
| `/appointments/available-slots/`         | GET    | Available slots JSON API    | Public      |
| `/dashboard/`                            | GET    | Admin dashboard             | Admin/Staff |
| `/dashboard/users/`                      | GET    | User management             | Admin/Staff |
| `/dashboard/users/<pk>/toggle-active/`   | POST   | Activate/deactivate user    | Admin/Staff |
| `/dashboard/doctors/`                    | GET    | Doctor management           | Admin/Staff |
| `/dashboard/doctors/create/`             | GET/POST | Create doctor             | Admin/Staff |
| `/dashboard/doctors/<pk>/edit/`          | GET/POST | Edit doctor               | Admin/Staff |
| `/dashboard/doctors/<pk>/delete/`        | POST   | Delete doctor               | Admin/Staff |
| `/dashboard/appointments/`              | GET    | Appointment management      | Admin/Staff |
| `/dashboard/appointments/<pk>/update/`   | POST   | Update appointment status   | Admin/Staff |
| `/admin/`                                | GET    | Django admin site           | Superuser   |

---

## Security Measures Implemented

| Security Feature                    | Implementation Location               |
|------------------------------------|----------------------------------------|
| CSRF protection                    | `CsrfViewMiddleware` in `base.py`; `{% csrf_token %}` in all forms |
| Login required                     | `@login_required` decorator on all data-modifying views |
| Role-based access control          | `@role_required` decorator in `core/decorators.py` |
| Parameterised queries              | Django ORM used throughout; zero raw SQL |
| X-Frame-Options: DENY              | `X_FRAME_OPTIONS = "DENY"` in `base.py` |
| X-Content-Type-Options: nosniff    | `SECURE_CONTENT_TYPE_NOSNIFF = True` in `base.py` |
| Password hashing (PBKDF2)          | Django default `AUTH_PASSWORD_VALIDATORS` in `base.py` |
| Secrets via env vars               | `python-decouple` — `SECRET_KEY`, DB creds loaded from `.env` |
| DEBUG=False in production          | `production.py` sets `DEBUG = False` |
| HTTPS hardening (prod)             | SSL redirect, HSTS, secure cookies in `production.py` |
| Input validation                   | Django forms with built-in validators; model `clean()` methods |
| Double-booking prevention          | DB `UniqueConstraint` + model-level `clean()` validation |
| SecurityMiddleware                 | First middleware in `MIDDLEWARE` list in `base.py` |

---

## Known Limitations & Future Improvements

### Limitations
- No real-time notifications (WebSockets/push) — uses flash messages only
- No payment integration — consultation fee is display-only
- No appointment reminders / follow-up emails
- Profile photos are not resized/optimised on upload
- No rate limiting on login or registration

### Future Improvements
- Add WebSocket-based real-time notifications
- Integrate Stripe/PayPal for online payment
- Add SMS/email appointment reminders
- Implement doctor reviews and ratings
- Add calendar view for doctor schedules
- Add API endpoints (DRF) for mobile app support
- Add Celery for async email sending
- Implement two-factor authentication
- Add comprehensive logging and monitoring
