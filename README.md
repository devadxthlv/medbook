# MedBook — Healthcare DevSecOps Capstone

MedBook is a comprehensive, production-grade healthcare appointment booking system. Built with Django and deployed via a robust DevSecOps pipeline on AWS EC2, it demonstrates advanced architectural patterns, strict security hardening, and continuous delivery mechanisms.

![MedBook Dashboard Placeholder](https://via.placeholder.com/800x400.png?text=MedBook+Dashboard)

## 📌 Project Overview

MedBook enables patients to find doctors and book appointments through a dynamic time-slot system, while giving doctors and administrators powerful tools to manage schedules and user accounts.

**Production URL**: [https://3-27-246-227.nip.io](https://3-27-246-227.nip.io)  
**Alternative Domain**: [https://medbook.3-27-246-227.nip.io](https://medbook.3-27-246-227.nip.io)

This repository serves as a **DevSecOps capstone project**, demonstrating the complete lifecycle of a web application from local development to a highly secure, automated, and observable production environment.

## 🏗 Architecture Overview

The system operates as a containerized stack orchestrated by Docker Compose:

*   **Nginx**: Reverse proxy, SSL terminator, and static asset server.
*   **Django + Gunicorn**: The core Python application backend.
*   **MySQL 8.0**: Relational database engine, optimized for low-memory footprint.
*   **Certbot**: Sidecar service for automated Let's Encrypt TLS certificate renewals.

### Stack Explanation
*   **Backend**: Django 4.2.17 (Python 3.12)
*   **Database**: MySQL 8.0 (Production), SQLite (Local Dev)
*   **Frontend**: Vanilla JS, Bootstrap 5
*   **Infrastructure**: AWS EC2 (Ubuntu), Docker
*   **CI/CD**: GitHub Actions

---

## 🚀 DevSecOps & Security Features

This application implements critical DevSecOps principles, transitioning it from a standard application to a hardened production service.

### 1. Server & Host Hardening
*   **UFW Firewall**: Restricts inbound traffic strictly to ports 22 (SSH), 80 (HTTP), and 443 (HTTPS).
*   **SSH Security**: Password authentication and root logins are disabled. `MaxAuthTries` configured to prevent brute force.
*   **Fail2Ban**: Actively monitors authentication logs and automatically bans malicious IPs.
*   **Unattended Upgrades**: Automated daily application of critical OS security patches.

### 2. Network & Application Security
*   **Automated HTTPS**: Let's Encrypt integration via Certbot with automatic renewals (`init-letsencrypt.sh`).
*   **Domain Migration**: Moved from raw IP access to `3-27-246-227.nip.io` for stable browser behavior and valid TLS.
*   **Nginx Hardening**: Implemented rate limiting (`10r/s`), `client_max_body_size` enforcement, and strict timeout directives to mitigate slow-loris attacks.
*   **Security Headers**: Enforced HSTS, X-Content-Type-Options, X-Frame-Options, and Content Security Policy (CSP).
*   **Django Hardening**: `DEBUG=False`, secure session/CSRF cookies, and parameterized queries using Django's ORM.

### 3. Monitoring & Observability
*   **CloudWatch Agent**: Automated setup script (`setup_cloudwatch.sh`) provisions AWS CloudWatch metrics for EC2 Memory, Disk Usage, and streams `/var/log/auth.log` directly to AWS for centralized auditing.
*   **Automated Smoke Testing**: Post-deployment testing verifies service health (`/health/`) and container stability.

### 4. CI/CD Pipeline
*   **Automated Testing**: GitHub Actions provisions a MySQL service and runs the complete Django test suite on every PR/Push.
*   **Security Scanning**: Uses `safety` to scan Python dependencies for known CVEs.
*   **Automated Deployment**: Secure SSH deployment pipeline triggers `deploy.sh` to pull code, run migrations, rebuild Docker images, and perform zero-downtime container restarts.

---

## 💻 Local Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repo-url> && cd medbook
   ```
2. **Setup virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt -r requirements-dev.txt
   ```
3. **Environment Configuration:**
   ```bash
   cp .env.example .env
   # Edit .env to set a development SECRET_KEY
   ```
4. **Database & Start:**
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

---

## 🌍 AWS Deployment Workflow

### Initial Server Provisioning
1. Provision an Ubuntu EC2 instance and assign an Elastic IP.
2. Clone the repository onto the instance.
3. Run the hardening and monitoring scripts:
   ```bash
   sudo bash scripts/harden_server.sh
   sudo bash scripts/setup_cloudwatch.sh
   ```
4. Create the production `.env` file with production MySQL credentials and secrets.

### Provisioning TLS & Starting Application
Execute the Let's Encrypt initialization script. This creates temporary dummy certificates so Nginx can start, then replaces them with real certs via Certbot webroot challenge:
```bash
bash scripts/init-letsencrypt.sh
```

### CI/CD Deployment
Once the initial stack is running, all future deployments are handled by GitHub Actions. Pushing to the `main` branch will automatically update the EC2 instance.

---

## 💾 Backup Strategy

The system includes a daily automated backup script (`scripts/backup.sh`) which:
1. Performs a `mysqldump` of the database.
2. Compresses the SQL dump using `gzip`.
3. Uploads the dump to an AWS S3 bucket.
4. Syncs user-uploaded media files to S3.

**Cron Configuration (`crontab -e`):**
```cron
0 2 * * * /home/ubuntu/medbook/scripts/backup.sh >> /var/log/medbook_backup.log 2>&1
```

---

## 🛠 Troubleshooting & Production Notes

*   **502 Bad Gateway**: This means Nginx is running but Django is not. Check Django logs: `docker compose -f docker-compose.prod.yml logs web`.
*   **Database Connection Errors**: If `web` is continually restarting, it likely can't reach MySQL. Check: `docker compose -f docker-compose.prod.yml logs db`.
*   **High Memory Usage**: Ensure the swap file is active. `t3.micro` instances can run out of memory during `docker build`.
*   **Deployment Fails**: Review the GitHub Actions console. If tests fail, the deployment is correctly halted.

---

## 🔮 Future Improvements

While this is a robust Capstone release, true enterprise scale would require:
1.  **RDS Migration**: Decoupling the database into Amazon RDS for Multi-AZ support.
2.  **S3 Media Storage**: Implementing `django-storages` to offload media serving directly to AWS S3.
3.  **Load Balancing**: Placing the application behind an Application Load Balancer (ALB) and an Auto Scaling Group.
4.  **Container Registry**: Using AWS ECR to build images in GitHub Actions and pull pre-built images to EC2, rather than building on the micro instance.
