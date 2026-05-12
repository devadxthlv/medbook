# AGENT.md — Developer Handoff Documentation

This document is written for the next developer (human or AI) who picks up the MedBook project. It captures what was built, why, the database schema, and where to continue.

---

## What Was Built

### Apps

| App            | Purpose                                                              |
|----------------|----------------------------------------------------------------------|
| `accounts`     | Custom User model (AbstractUser + role), registration, login/logout, profile with photo upload, password reset |
| `doctors`      | Doctor model (linked to User via OneToOneField), public listing with search/filter, detail page |
| `appointments` | Appointment model with time-slot system, booking flow, cancellation, doctor schedule management, available-slots JSON API |
| `dashboard`    | Admin-only dashboard with stats cards, user management (activate/deactivate), doctor CRUD, appointment status management |
| `core`         | Home page, `@role_required` decorator, shared utilities              |

### Models Created

- `accounts.User` — extends `AbstractUser`
- `doctors.Doctor` — extends User with professional details
- `appointments.Appointment` — links Patient ↔ Doctor with date/time/status

### Views Created (by app)

**accounts**: `register`, `CustomLoginView`, `CustomLogoutView`, `profile`, password reset views (4 CBVs)

**doctors**: `doctor_list` (with search + filter), `doctor_detail`

**appointments**: `book_appointment`, `my_appointments`, `cancel_appointment`, `doctor_appointments`, `update_appointment_status`, `available_slots` (JSON API)

**dashboard**: `dashboard_home`, `user_list`, `toggle_user_active`, `doctor_management`, `doctor_create`, `doctor_edit`, `doctor_delete`, `appointment_management`, `admin_update_appointment`

### Templates

- `base.html` — master layout with role-aware navbar, Bootstrap 5, flash messages, footer
- 8 accounts templates (register, login, profile, 4× password reset, email template)
- 2 doctors templates (list with card grid, detail)
- 3 appointments templates (booking with dynamic slots, patient list, doctor schedule)
- 5 dashboard templates (home, user list, doctor list, doctor form, appointment list)

---

## Key Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| **Custom User model from day one** | Django strongly recommends this; changing later requires complex migrations. The `role` field on User avoids needing separate Patient/Doctor profile models for auth. |
| **Split settings (base/development/production)** | Clean separation of concerns. Dev uses SQLite and console email; prod uses MySQL and SMTP. Shared settings in `base.py` avoid duplication. |
| **Pre-defined 30-minute time slots** | Simpler than free-form time entry. The `generate_time_slots()` function creates choices from 09:00–17:00. Easy to change the range or interval. |
| **UniqueConstraint on (doctor, date, time_slot)** | Database-level guarantee against double-booking, even under race conditions. The model's `clean()` method provides a friendlier form-level error. |
| **Doctor linked via OneToOneField** | A User with role=DOCTOR gets an additional Doctor profile. This keeps User lean while adding doctor-specific fields. |
| **Available days as BooleanFields** | Five simple boolean columns (Mon–Fri) are easier to query than a JSON/array field and work across all databases. |
| **python-decouple for config** | Lightweight alternative to django-environ. Reads from `.env` files and environment variables, keeping secrets out of source code. |
| **Console email backend in dev** | Prints emails to stdout, making it easy to verify email sending without external services. |
| **Custom dashboard vs Django admin** | The requirement specifies `/dashboard/` with stats cards and role-specific management. Django admin (`/admin/`) is still available for superusers. |
| **Separate `admin_required` decorator in dashboard** | Checks `is_staff`, `is_superuser`, OR `role == ADMIN`, providing flexible admin access. Different from `@role_required('ADMIN')` which only checks role. |

---

## Database Schema

### `accounts.User` (extends `auth_user`)

| Field          | Type          | Constraints                     | Notes |
|----------------|---------------|---------------------------------|-------|
| id             | BigAutoField  | PK                              | Inherited from AbstractUser |
| username       | CharField(150)| Unique, required                | Inherited |
| email          | EmailField    | —                               | Inherited |
| first_name     | CharField(150)| —                               | Inherited |
| last_name      | CharField(150)| —                               | Inherited |
| password       | CharField     | Hashed (PBKDF2)                | Inherited |
| role           | CharField(10) | Choices: PATIENT/DOCTOR/ADMIN   | Default: PATIENT |
| phone          | CharField(20) | Blank                           | — |
| date_of_birth  | DateField     | Null, blank                     | — |
| address        | TextField     | Blank                           | — |
| profile_photo  | ImageField    | Null, blank                     | upload_to="profile_photos/" |
| is_active      | BooleanField  | Default: True                   | Inherited |
| is_staff       | BooleanField  | Default: False                  | Inherited |
| is_superuser   | BooleanField  | Default: False                  | Inherited |
| date_joined    | DateTimeField | Auto                            | Inherited |

### `doctors.Doctor`

| Field               | Type              | Constraints                                | Notes |
|---------------------|-------------------|--------------------------------------------|-------|
| id                  | BigAutoField      | PK                                         | — |
| user                | OneToOneField     | FK → User, CASCADE, related_name="doctor_profile" | — |
| specialisation      | CharField(10)     | Choices: GP/CARDIO/DERM/NEURO/ORTHO/PEDIA/PSYCH/GYNEC/OPHTH/ENT/URO/ONCO | — |
| bio                 | TextField         | Blank                                      | — |
| years_of_experience | PositiveIntegerField | Default: 0                              | — |
| consultation_fee    | DecimalField(8,2) | Default: 0                                 | — |
| available_monday    | BooleanField      | Default: True                              | — |
| available_tuesday   | BooleanField      | Default: True                              | — |
| available_wednesday | BooleanField      | Default: True                              | — |
| available_thursday  | BooleanField      | Default: True                              | — |
| available_friday    | BooleanField      | Default: True                              | — |

### `appointments.Appointment`

| Field      | Type          | Constraints                                         | Notes |
|------------|---------------|-----------------------------------------------------|-------|
| id         | BigAutoField  | PK                                                  | — |
| patient    | ForeignKey    | FK → User, CASCADE, related_name="patient_appointments" | — |
| doctor     | ForeignKey    | FK → Doctor, CASCADE, related_name="doctor_appointments" | — |
| date       | DateField     | Required                                            | — |
| time_slot  | CharField(5)  | Choices: 30-min slots 09:00–16:30                   | Format: "HH:MM" |
| reason     | TextField     | Blank                                               | — |
| status     | CharField(10) | Choices: PENDING/CONFIRMED/CANCELLED/COMPLETED      | Default: PENDING |
| created_at | DateTimeField | auto_now_add                                        | — |

**Constraint**: `UniqueConstraint(fields=["doctor", "date", "time_slot"], name="unique_doctor_date_timeslot")`

---

## Where to Continue

Priority-ordered tasks for the next developer:

1. **Payment Integration** — Add Stripe/PayPal checkout when booking appointments. The `consultation_fee` field on Doctor is already available.

2. **Appointment Reminders** — Add Celery + Redis for async tasks. Send email/SMS reminders 24h and 1h before appointments.

3. **Doctor Reviews & Ratings** — New `Review` model (FK to Appointment, rating 1–5, comment). Display average rating on doctor cards.

4. **Calendar View** — Add a calendar view (e.g., FullCalendar.js) for doctors to see their schedule visually.

5. **API Layer** — Add Django REST Framework for mobile app support. Serialise existing models and expose CRUD endpoints.

6. **Image Optimisation** — Resize and compress uploaded profile photos using Pillow's thumbnail functionality.

7. **Logging & Monitoring** — Add structured logging, Sentry integration, and health check endpoints.

8. **Two-Factor Auth** — Integrate django-otp or django-allauth for 2FA.

---

## Known Issues / TODOs

- **No email verification gate**: Patients are immediately active after registration. The welcome email is sent but there's no "click to verify" flow blocking login.
- **Weekend handling**: The booking JS sets min-date to today but doesn't grey out weekends in the calendar widget. The backend correctly rejects weekend dates if the doctor isn't available.
- **No timezone awareness in slots**: Time slots are defined in server time. Multi-timezone support would require additional logic.
- **Admin doctor creation**: Uses a simple custom form rather than Django's UserCreationForm for the user portion, so password validation rules (length, commonality) aren't enforced on the admin-created doctor accounts.
- **No pagination on doctor listing**: Works fine with <100 doctors but would benefit from pagination for larger datasets.
- **Console email in dev**: Emails are printed to stdout. Switch to `EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'` and configure SMTP for production.

---

## How to Run Tests

```bash
# Run the full test suite
python manage.py test

# Run with verbose output
python manage.py test --verbosity=2

# Run tests for a specific app
python manage.py test accounts
python manage.py test doctors
python manage.py test appointments
python manage.py test dashboard

# Run with coverage
coverage run manage.py test
coverage report
coverage html  # generates htmlcov/index.html
```

The test suite contains **30 tests** across all four apps:
- `accounts` (10): registration, login, logout, profile, access control
- `doctors` (7): listing, search, filter, detail, 404
- `appointments` (7): booking, double-booking, cancellation, available-slots API
- `dashboard` (6): admin access control, forbidden for patients/doctors

---

## Environment Assumptions

- **Python**: 3.12+ (tested on 3.12.3)
- **OS**: Linux (Ubuntu 24.04), macOS, or Windows with WSL
- **Database**: SQLite for development (zero config), MySQL 8.0 for production
- **External services**: None required for development; SMTP server needed for production email
- **System packages** (for MySQL support): `gcc`, `default-libmysqlclient-dev`, `pkg-config`
- **System packages** (for Pillow): `libjpeg-dev`, `zlib1g-dev`
- **Docker** (optional): Docker 20+ and Docker Compose v2 for containerised deployment

---

## Production Deployment Notes

Current capstone deployment target:

- AWS EC2 Ubuntu micro instance
- Docker Compose stack: `nginx`, `web`, `db`
- Nginx is the only public application entrypoint; Django/Gunicorn and MySQL stay on the internal Docker network.
- Static files are collected into `static_data`; uploaded files persist in `media_data`; MySQL persists in `mysql_data`.
- `/health/` is the application health endpoint used by Docker and Nginx checks.

Infrastructure decisions:

- Gunicorn is intentionally configured for `WEB_CONCURRENCY=1` with two threads because the EC2 instance has less than 1 GB RAM.
- MySQL uses conservative memory flags: small InnoDB buffer pool, limited connections, and disabled Performance Schema.
- HTTPS settings in Django are environment-controlled. Keep redirects and HSTS disabled until a valid domain certificate exists.
- Bare EC2 public IPs cannot receive Let's Encrypt certificates. Point a domain A record to the instance before running Certbot.
- Keep swap enabled on the micro instance to absorb deploy/build spikes.

Operational commands:

```bash
docker-compose build web
docker-compose up -d
docker-compose ps
docker-compose logs --tail=100 web nginx db
curl -I http://localhost/health/
```

Scaling recommendations:

- Move MySQL to Amazon RDS before real users or PHI-like data.
- Put Nginx behind an ALB for managed TLS, access logs, and health checks.
- Store media in S3 instead of local Docker volumes.
- Add CloudWatch Agent for memory/disk metrics and ship Docker/Nginx logs.
- Add scheduled `mysqldump` plus media archive backups to S3 with restore testing.

---

## Phase 4 — Deployment Stabilisation and CI/CD

Live target:

- EC2 public IP: `3.27.246.227`
- Live URL: `http://3.27.246.227`
- Stack: Docker Compose with `nginx`, `web`, and local `db` MySQL containers.

What was fixed:

- Gunicorn now starts with one worker, a 120 second timeout, and max-request recycling to fit the t3.micro memory limit.
- Django startup now runs `python manage.py wait_for_db` before migrations, avoiding the MySQL readiness race.
- Nginx now proxies to the Docker service upstream `web:8000`, serves static/media volumes, and uses the EC2 public IP as `server_name`.
- Production settings default `ALLOWED_HOSTS` to `3.27.246.227,localhost,127.0.0.1` and `CSRF_TRUSTED_ORIGINS` to `http://3.27.246.227`.
- `docker-compose.prod.yml` uses MySQL healthchecks and only starts `web` after MySQL is healthy.

What was added:

- `.github/workflows/deploy.yml` runs Django tests with a MySQL service, then deploys pushes to `main` over SSH.
- `scripts/deploy.sh` pulls `main`, rebuilds `web`, restarts Compose, prunes old images, and runs the smoke test.
- `scripts/smoke_test.sh` checks `http://3.27.246.227/` and prints Docker status/logs on failure.
- `scripts/backup.sh` dumps MySQL, uploads the compressed dump to S3, and syncs media backups.

Operational commands:

```bash
# Manual deploy on EC2
bash scripts/deploy.sh

# Live logs
docker compose -f docker-compose.prod.yml logs -f

# Container status
docker ps

# Smoke test
bash scripts/smoke_test.sh
```

EC2 security group reminder:

- If `docker ps` shows healthy containers but the site is unreachable, check the AWS console security group.
- Inbound HTTP must allow TCP port `80` from `0.0.0.0/0`.
- SSH should allow TCP port `22` from the maintainer's current IP only.

Backup schedule:

```cron
0 2 * * * /home/ubuntu/medbook/scripts/backup.sh
```

Phase 5 tasks:

- Configure CloudWatch metrics and log shipping.
- Add HTTPS after a domain points to the EC2 instance.
- Complete the project report with deployment screenshots and CI/CD evidence.
