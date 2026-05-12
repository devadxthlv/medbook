# AGENT.md — DevSecOps Operational Handbook

This document serves as the "complete AI + engineer operational memory" for the MedBook production deployment. It contains the mental model, architectural constraints, and DevSecOps rationale required to manage and scale the platform.

---

## 1. Repository Mental Model

MedBook is a monolithic Django application containerized using Docker Compose. It leverages the following core structure:

*   **Application Core**: 4 Django apps (`accounts`, `doctors`, `appointments`, `dashboard`) + `core` for shared utilities.
*   **Database Layer**: MySQL 8.0 running internally in the Docker network.
*   **Web Server Layer**: Gunicorn WSGI running within the Python container, sitting behind Nginx.
*   **Reverse Proxy / TLS**: Nginx acting as a public-facing entrypoint, handling SSL termination, static file delivery, and request throttling. Let's Encrypt certificates are provisioned using Certbot.

### Service Relationships

*   **Nginx** → **Django (Web)**: HTTP requests forwarded over internal port `8000`. Static/Media files are served directly by Nginx via Docker volume sharing.
*   **Django (Web)** → **MySQL (DB)**: TCP connection over internal port `3306`.
*   **Certbot** → **Nginx**: Certbot operates in a separate container, performing webroot authentication (`/.well-known/acme-challenge/`) through Nginx for TLS certificate renewal.

---

## 2. Infrastructure Assumptions & Constraints

**Target Environment**: AWS EC2 `t3.micro` or `t2.micro` (1 vCPU, 1 GB RAM).
**Public IP**: `3.27.246.227`
**Primary Domain**: `3-27-246-227.nip.io` (Wildcard DNS)
**Subdomains**: `medbook.3-27-246-227.nip.io`

### Domain Migration Rationale (nip.io)

Initially, the deployment used raw IP access and dot-formatted nip.io domains (`3.27.246.227.nip.io`). This caused several issues:
1.  **Browser Inconsistency**: Some browsers treat dots in subdomains as distinct security boundaries, causing issues with HSTS and certificate validation when switching between IP and domain.
2.  **HSTS/IP Conflicts**: Browsers often cache HSTS for a specific "host". Accessing via IP then Domain (or vice versa) can trigger "Privacy Error" warnings if the certificate doesn't match the host EXACTLY.
3.  **Clean Production Path**: Moving to the dash-formatted nip.io domain (`3-27-246-227.nip.io`) provides a more stable, production-like experience that matches how real domains (like `medbook.com`) behave.

### HSTS & Browser Caching

*   **Strict-Transport-Security**: Currently set to `max-age=31536000` (1 year).
*   **Operational Note**: If you need to downgrade to HTTP (not recommended), you MUST clear the browser's HSTS cache (e.g., in Chrome: `chrome://net-internals/#hsts`).
*   **Redirect Logic**: Nginx is configured to force ALL traffic (including raw IP) to `https://3-27-246-227.nip.io`.

---

## 3. DevSecOps Rationale

We evolved the application from a "working deployment" to a "production-grade" platform through the following layers:

### HTTPS & TLS Layer
*   **Certbot Automation**: Let's Encrypt is fully automated via `scripts/init-letsencrypt.sh` and the Certbot container.
*   **HSTS & Headers**: Nginx sets Strict-Transport-Security, X-Frame-Options, Content-Security-Policy, and X-Content-Type-Options to protect against MITM, Clickjacking, and XSS.
*   **Nginx Hardening**: Rate limiting (`limit_req_zone`) restricts excessive traffic, mitigating basic application-layer DDoS attacks.

### Application Layer (Django)
*   **Production Settings**: `DEBUG=False`, `SECURE_SSL_REDIRECT=True`, `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`.
*   **Secrets Management**: Decoupled using `.env` injected directly into Docker containers. No secrets are baked into the image.

### Server & Host Layer (EC2)
*   **Hardening Script**: `scripts/harden_server.sh` automates OS-level security.
*   **SSH**: Password authentication and root login disabled. Max auth tries limited.
*   **Firewall**: UFW restricts traffic to 22 (SSH), 80 (HTTP), and 443 (HTTPS) only.
*   **Fail2Ban**: Monitors `/var/log/auth.log` and automatically bans IPs with repeated failed SSH attempts.

### CI/CD Pipeline
*   **GitHub Actions**: Automates testing against an isolated MySQL container.
*   **SSH Deploy**: Automatically deploys `main` branch to EC2. The `deploy.sh` script executes `docker-compose build`, runs Django migrations, collects static files, and verifies application health via `smoke_test.sh`.

---

## 4. Operational Commands Cheat-Sheet

**Deployment**
```bash
# Manual deployment trigger
bash scripts/deploy.sh

# Certificate provisioning (Run once per new server setup)
bash scripts/init-letsencrypt.sh
```

**Service Management**
```bash
# Start/Restart production stack
docker compose -f docker-compose.prod.yml up -d

# View real-time logs
docker compose -f docker-compose.prod.yml logs -f web nginx db

# Restart a specific service (e.g., Nginx after a config change)
docker compose -f docker-compose.prod.yml restart nginx
```

**Django Operations (Inside Container)**
```bash
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
docker compose -f docker-compose.prod.yml exec web python manage.py shell
```

**Debugging**
```bash
# Check container health status
docker ps

# Check Nginx syntax before restarting
docker compose -f docker-compose.prod.yml exec nginx nginx -t

# Run the automated smoke test
bash scripts/smoke_test.sh
```

---

## 5. Recovery Procedures

### Database Restoration

1. Locate the latest S3 backup (via `scripts/backup.sh`).
2. Download `db_backup_YYYYMMDD_HHMMSS.sql.gz`.
3. Unzip and restore into the running container:
```bash
gunzip < db_backup.sql.gz | docker compose -f docker-compose.prod.yml exec -T db mysql -u medbook_user -p medbook_db
```

### Complete Infrastructure Recreation

If the EC2 instance is lost:
1. Provision a new Ubuntu EC2 instance.
2. Attach the Elastic IP (if applicable) or update DNS records.
3. Configure the server environment:
   ```bash
   git clone <repo> && cd medbook
   bash scripts/harden_server.sh
   bash scripts/setup_cloudwatch.sh
   ```
4. Restore `.env` file from secure vault.
5. Restore database and media files from S3.
6. Run `bash scripts/init-letsencrypt.sh` to provision new certificates.
7. Run `bash scripts/deploy.sh`.

---

## 6. Known Bottlenecks & Future Scaling

*   **Bottleneck 1: Database on EC2**: MySQL running in Docker shares disk I/O and RAM with the application.
    *   *Migration*: Move the database to Amazon RDS (t3.micro or larger) to isolate database load and get automated point-in-time backups.
*   **Bottleneck 2: Single Node Availability**: The application runs on a single EC2 instance. Any EC2 outage causes downtime.
    *   *Migration*: Introduce an Application Load Balancer (ALB). Move SSL termination to the ALB using AWS ACM. Place EC2 instances in an Auto Scaling Group across multiple Availability Zones.
*   **Bottleneck 3: Local Media Storage**: User-uploaded profile photos are stored on local Docker volumes. Rebuilding or losing the instance loses these files unless recently backed up.
    *   *Migration*: Implement `django-storages` with `boto3` to stream media directly to an Amazon S3 bucket.

---

## 7. Architecture Diagrams

### Application Data Flow
```text
Client Request
      │
      ▼  (HTTPS: 443)
┌──────────────┐
│   Nginx      │ ──▶ Serves Static & Media Files
│ Reverse Proxy│
└──────────────┘
      │  (HTTP: 8000 via Docker Network)
      ▼
┌──────────────┐
│  Gunicorn    │
│ WSGI Server  │
└──────────────┘
      │
      ▼
┌──────────────┐
│   Django     │ ──▶ Application Logic
│  (Python)    │
└──────────────┘
      │  (TCP: 3306 via Docker Network)
      ▼
┌──────────────┐
│  MySQL 8.0   │ ──▶ Persistent Data (Volume: mysql_data)
└──────────────┘
```

### CI/CD Deployment Flow
```text
Developer ──▶ Git Push (main)
                  │
                  ▼
         GitHub Actions (Test Job)
         Spin up MySQL Service
         Run Django Tests & Safety Checks
                  │
             (If Passed)
                  │
                  ▼
         GitHub Actions (Deploy Job)
         SSH into EC2 Instance
                  │
                  ▼
         Execute `scripts/deploy.sh`
         - git pull
         - docker compose build
         - docker compose up
         - python manage.py migrate
         - python manage.py collectstatic
         - bash scripts/smoke_test.sh
```
