<div align="center">
  <h1>🏥 MedBook</h1>
  <p><strong>Healthcare Appointment Booking System & DevSecOps Capstone</strong></p>

  [![Production Deployment](https://github.com/devadxthlv/medbook/actions/workflows/deploy.yml/badge.svg)](https://github.com/devadxthlv/medbook/actions)
  [![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
  [![Django](https://img.shields.io/badge/Django-4.2-green.svg)](https://www.djangoproject.com/)
  [![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
  [![Nginx](https://img.shields.io/badge/Nginx-Secured-009639.svg)](https://nginx.org/)
  [![Let's Encrypt](https://img.shields.io/badge/SSL-Let's_Encrypt-yellow.svg)](https://letsencrypt.org/)

  <p>
    <a href="#-executive-overview">Overview</a> •
    <a href="#-production-architecture">Architecture</a> •
    <a href="#-devsecops--security">DevSecOps</a> •
    <a href="#-deployment-guide">Deployment</a> •
    <a href="#-monitoring--observability">Monitoring</a>
  </p>
</div>

---

## 📌 Executive Overview

**MedBook** is a comprehensive, production-grade healthcare appointment booking system. Built with Django and deployed via a robust DevSecOps pipeline on AWS EC2, it demonstrates advanced architectural patterns, strict security hardening, and continuous delivery mechanisms.

The primary goal of this repository is to showcase a **complete transition from a standard application to a hardened production service**, emphasizing Infrastructure as Code (IaC), zero-downtime deployments, and comprehensive monitoring.

**Production Endpoints:**
* **Primary URL:** [https://3-27-246-227.nip.io](https://3-27-246-227.nip.io)
* **Alias Domain:** [https://medbook.3-27-246-227.nip.io](https://medbook.3-27-246-227.nip.io)

---

## ✨ Key Features

### 🏥 Healthcare Workflow
* **Role-Based Access Control (RBAC):** Distinct workflows for Patients, Doctors, and System Administrators.
* **Appointment Engine:** Dynamic time-slot selector, double-booking prevention, and patient-doctor scheduling.
* **Administrative Dashboard:** Comprehensive management of users, doctors, and system statistics.

### 🔒 DevSecOps & Automation
* **Automated CI/CD:** GitHub Actions pipeline for testing, security scanning, and automated deployment.
* **Production HTTPS:** Automated Let's Encrypt TLS provisioning via Certbot with zero-downtime renewals.
* **Server Hardening:** Automated OS-level firewall (UFW), SSH hardening, and Fail2Ban integration.
* **System Observability:** AWS CloudWatch agent streaming metrics (RAM/Disk) and authentication logs for centralized auditing.

---

## 🛠 Technology Stack

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Backend** | Django 4.2 (Python 3.11) | Rapid development, robust ORM, and built-in security features against CSRF/SQLi. |
| **Database** | MySQL 8.0 | Reliable ACID-compliant data storage, tuned for micro-instance memory constraints. |
| **App Server** | Gunicorn (WSGI) | Production-grade Python server handling concurrent requests efficiently. |
| **Reverse Proxy** | Nginx | Terminates SSL, serves static/media assets directly, and protects Gunicorn via rate limiting. |
| **Containerization** | Docker Compose | Ensures parity between local dev, CI pipeline, and production infrastructure. |
| **CI/CD** | GitHub Actions | Integrated testing, Python `safety` scanning, and automated EC2 SSH deployments. |
| **Host Infra** | AWS EC2 (Ubuntu 22.04) | Cost-effective compute environment for monolithic deployments. |

---

## 🏗 Production Architecture

The application is deployed as a tightly integrated, containerized stack. Nginx acts as the gatekeeper, completely isolating the Django/Gunicorn application and the MySQL database from direct internet exposure.

```text
                  Internet (HTTPS: 443)
                          │
                          ▼
            ┌───────────────────────────┐
            │        AWS EC2 Host       │
            │  (UFW / Fail2Ban Secured) │
            │                           │
            │  ┌─────────────────────┐  │
            │  │  Certbot Container  │  │ (Automated TLS Renewals)
            │  └──────────┬──────────┘  │
            │             │             │
            │  ┌──────────▼──────────┐  │ (SSL Termination, Rate Limiting)
            │  │   Nginx Container   │──┼──▶ Serves Static & Media Assets
            │  └──────────┬──────────┘  │
            │             │             │
            │  ┌──────────▼──────────┐  │ (Port 8000 Internal)
            │  │ Django + Gunicorn   │  │
            │  │    Web Container    │  │
            │  └──────────┬──────────┘  │
            │             │             │
            │  ┌──────────▼──────────┐  │ (Port 3306 Internal)
            │  │  MySQL 8 Container  │  │
            │  └─────────────────────┘  │
            └───────────────────────────┘
                          │
                          ▼
                    AWS CloudWatch (Metrics & Auth Logs)
```

### Request Lifecycle
1. **Client** connects via `https://3-27-246-227.nip.io`.
2. **UFW** permits port 443; **Fail2Ban** monitors for abuse.
3. **Nginx** validates the SSL certificate, enforces security headers, and applies rate limiting (`10r/s`).
4. Static/Media requests are intercepted and served directly by Nginx from shared Docker volumes.
5. Dynamic requests are reverse-proxied over the internal Docker network to **Gunicorn**.
6. **Django** processes the request, interacting with the **MySQL** container internally.

---

## 🛡 Security Architecture

Security is built into the architecture across multiple layers:

### 1. Network & Proxy Security
* **HSTS Enforced:** `Strict-Transport-Security` enforces HTTPS for 1 year, preventing downgrade attacks.
* **Nginx Rate Limiting:** Mitigates application-layer DDoS and credential stuffing.
* **Security Headers:** Enforces CSP, X-Frame-Options (DENY), and X-Content-Type-Options to prevent XSS and clickjacking.

### 2. Host Hardening (`scripts/harden_server.sh`)
* **UFW:** Drops all traffic except ports 22, 80, and 443.
* **SSH Hardening:** Disables password authentication, disables root login, and limits auth retries.
* **Fail2Ban:** Automatically bans IPs exhibiting malicious SSH behavior.

### 3. Application Security (Django)
* **Secure Cookies:** `SESSION_COOKIE_SECURE` and `CSRF_COOKIE_SECURE` strictly enforced.
* **Dependency Scanning:** The CI pipeline runs `safety` to block deployments containing known Python CVEs.

---

## 🚀 DevSecOps Pipeline

The deployment process is entirely automated and hardened to ensure zero-downtime and consistent state.

1. **Push to `main`** triggers GitHub Actions.
2. **CI Tests:** Spins up an ephemeral MySQL container, runs the Django test suite, and scans dependencies for CVEs.
3. **CD Deployment (via SSH):**
   * **State Enforcement:** Forces the server to mirror the `main` branch via `git reset --hard`, eliminating merge conflicts caused by manual server tweaks.
   * **Container Synchronization:** The pipeline waits for the Docker healthcheck to pass before proceeding, ensuring the application is ready for traffic.
   * **Zero-Downtime Migration:** Runs database migrations and static collection inside the healthy container.
4. **Smoke Test:** Executes `scripts/smoke_test.sh` with automated retries to verify public HTTPS reachability and HTTP-to-HTTPS redirection.

---

## 💻 Deployment Guide

### Local Development
```bash
git clone https://github.com/devadxthlv/medbook.git
cd medbook
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env  # Configure secrets
python manage.py migrate
python manage.py runserver
```

### Production Provisioning (EC2)
1. Clone the repository to the host server.
2. Run server hardening and monitoring scripts:
   ```bash
   sudo bash scripts/harden_server.sh
   sudo bash scripts/setup_cloudwatch.sh
   ```
3. Initialize Let's Encrypt certificates (generates dummies, boots Nginx, provisions real certs):
   ```bash
   bash scripts/init-letsencrypt.sh
   ```
4. Deploy the stack:
   ```bash
   bash scripts/deploy.sh
   ```

---

## 📊 Monitoring & Observability

MedBook utilizes **AWS CloudWatch** for deep system observability (`scripts/setup_cloudwatch.sh`):

* **Resource Metrics:** EC2 Memory and Disk usage are polled every 60 seconds.
* **Security Auditing:** `/var/log/auth.log` is streamed in real-time to CloudWatch Logs, allowing centralized tracking of SSH attempts and Fail2Ban actions.
* **Docker Logs:** Standard container logs are managed via Docker's JSON-file driver for localized debugging (`docker compose logs -f`).

---

## 💾 Backup & Recovery

A dedicated backup script (`scripts/backup.sh`) ensures data safety:

1. Connects to the isolated MySQL container.
2. Executes an authenticated `mysqldump`.
3. Compresses the output via `gzip`.
4. Streams the database archive and all user-uploaded media files directly to **Amazon S3**.

*Configured to run automatically via nightly Cron jobs.*

---

## ⚡ Performance & Scalability Notes

* **Memory Tuning:** Due to `t3.micro` constraints (1GB RAM), MySQL is strictly tuned (`innodb-buffer-pool-size=64M`, `performance-schema=OFF`) to prevent Out-Of-Memory (OOM) killer terminations.
* **Worker Allocation:** Gunicorn runs with a conservative worker count to ensure stable memory consumption.
* **Asset Offloading:** Nginx serving static assets eliminates the overhead of passing media requests through the Python application layer.

---

## ⚠️ Known Limitations

1. **Single Point of Failure:** The current monolithic EC2 architecture lacks Multi-AZ redundancy.
2. **Local Media Storage:** Currently relies on Docker volumes synced to S3. True distributed scaling requires `django-storages` pointing directly to S3.
3. **Database Coupling:** MySQL shares compute/memory resources with the web application.

---

## 🔮 Future Improvements

To transition to a true enterprise-scale architecture, the following upgrades are planned:

1. **AWS ECS / Fargate:** Migrate from EC2 Docker-Compose to managed container orchestration for auto-scaling capabilities.
2. **Amazon RDS:** Decouple the MySQL database into a managed, Multi-AZ relational database service.
3. **Application Load Balancer (ALB):** Move TLS termination to AWS ACM on an ALB to support horizontal scaling of web workers.
4. **Redis & Celery:** Implement asynchronous task queues for email notifications and background processing.

---

## 📸 Screenshots

| Dashboard | Appointment Booking |
| :---: | :---: |
| ![Dashboard Placeholder](https://via.placeholder.com/400x250.png?text=Admin+Dashboard) | ![Booking Placeholder](https://via.placeholder.com/400x250.png?text=Appointment+Booking) |
| **CI/CD Pipeline** | **Security Validation** |
| ![Actions Placeholder](https://via.placeholder.com/400x250.png?text=GitHub+Actions) | ![HTTPS Placeholder](https://via.placeholder.com/400x250.png?text=HTTPS+TLS+Lock) |

---
*Architected and Deployed by [Devadath] for the DevSecOps Capstone Project.*
