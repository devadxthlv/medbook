# 🧠 MedBook — DevSecOps Operational Handbook

This document serves as the **authoritative operational memory and AI/Engineer onboarding guide** for the MedBook production deployment. It contains the exact mental models, architectural tradeoffs, security rationales, and recovery procedures required to safely manage, debug, and scale the infrastructure.

---

## 1. Repository Mental Model

MedBook is a monolithic Django application packaged in a tightly coupled Docker Compose stack. It follows a strict **"Infrastructure as Code" (IaC)** philosophy where server state is defined by Bash scripts and Docker configurations, not manual intervention.

### Architectural Philosophy
* **Nginx is the Shield:** No internal service (Django or MySQL) is exposed to the internet. Nginx handles all public traffic, TLS, static file delivery, and HTTP rate limiting.
* **Stateless App / Stateful Volumes:** The Django containers are completely ephemeral. State is exclusively maintained in Docker volumes (`mysql_data`, `media_data`) and external storage (S3).
* **Environment Separation:** Secrets (`.env`) are never committed. Configurations are injected at runtime.

---

## 2. Infrastructure Decisions & Rationale (Viva Support)

This section details **why** specific architectural decisions were made.

### Why Nginx over a Cloud Load Balancer (ALB)?
Given the constraints of a single `t3.micro` instance, deploying an ALB would introduce unnecessary cost without the benefit of horizontal scaling. Nginx provides an ultra-lightweight ingress controller, allowing us to implement Rate Limiting and strict Security Headers directly on the host while serving static files with minimal RAM overhead.

### Why nip.io instead of a Custom Domain?
The project utilizes `3-27-246-227.nip.io` to demonstrate a complete, production-grade TLS setup without purchasing a domain. Moving from dot-format (`3.27.246.227.nip.io`) to dash-format (`3-27-246-227.nip.io`) was crucial because browsers handle HSTS (Strict-Transport-Security) and wildcard certificates much more reliably on dash-formatted subdomains, mimicking real-world top-level domains.

### Why single worker Gunicorn & tuned MySQL?
The `t3.micro` instance has only 1GB of RAM. Running standard MySQL and multiple Gunicorn workers guarantees an Out-Of-Memory (OOM) crash, leading to the Linux kernel killing the database. We explicitly configured MySQL (`--innodb-buffer-pool-size=64M`, `--performance-schema=OFF`) to ensure stable memory consumption.

---

## 3. Security Architecture & Rationale

MedBook employs a defense-in-depth approach, assuming the network is hostile.

1. **HSTS & Secure Cookies:** By forcing `max-age=31536000` via Nginx and enforcing `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, we ensure no authentication tokens can ever be intercepted over plaintext HTTP.
2. **Host-Level Hardening (`harden_server.sh`):**
   * **UFW:** Only ports 80, 443, and 22 are open.
   * **SSH Security:** Password authentication is disabled. Root login is prohibited.
   * **Fail2Ban:** Actively monitors `/var/log/auth.log` and automatically bans IP addresses attempting SSH brute-force attacks.
3. **Let's Encrypt Automation:** The `init-letsencrypt.sh` script implements the webroot ACME challenge. It generates a dummy certificate to allow Nginx to start securely, provisions the real certificate, and reloads Nginx dynamically. A Certbot sidecar container automatically handles 90-day renewals.

---

## 4. Operational Workflows

### Deployment
Deployments are entirely handled by GitHub Actions (`deploy.yml`). Pushing to `main` triggers:
1. Ephemeral MySQL database creation.
2. Execution of the Django test suite.
3. Execution of Python `safety` to check for CVEs.
4. SSH execution of `scripts/deploy.sh` on the EC2 host.

*Manual Trigger:* `bash scripts/deploy.sh` on the server.

### Automated Backups
Data is synchronized to AWS S3 nightly via a Cron job calling `scripts/backup.sh`.
* It executes an authenticated `mysqldump` directly against the internal Docker database.
* Compresses the output (`gzip`).
* Uses `aws s3 cp/sync` to export data, ensuring disaster recovery capabilities without exposing the database to the internet.

---

## 5. Debugging & Troubleshooting Procedures

When the application goes down, follow these precise steps.

### 1. Identify the Failure Layer (Nginx vs. Django)
* **502 Bad Gateway:** Nginx is running, but Gunicorn is down.
* **Connection Refused:** Nginx is completely down or UFW is blocking traffic.
* **Database Connection Error (Internal):** Django is running but cannot reach MySQL.

### 2. Container Debugging
```bash
cd /home/ubuntu/medbook

# Check container health and status
docker ps -a

# Tail real-time logs for the web application
docker compose -f docker-compose.prod.yml logs --tail 50 -f web

# Tail real-time logs for Nginx
docker compose -f docker-compose.prod.yml logs --tail 50 -f nginx

# Tail real-time logs for MySQL
docker compose -f docker-compose.prod.yml logs --tail 50 -f db
```

### 3. Application State Debugging
```bash
# Execute a command inside the running Django container
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# Drop into a Django shell
docker compose -f docker-compose.prod.yml exec web python manage.py shell
```

### 4. TLS & Certificate Debugging
If certificates fail to renew or Nginx refuses to start due to SSL errors:
```bash
# Test Nginx syntax
docker compose -f docker-compose.prod.yml exec nginx nginx -t

# Manually trigger Certbot renewal
docker compose -f docker-compose.prod.yml run --rm certbot renew
```

---

## 6. Disaster Recovery Procedures

### Scenario: Complete Database Loss
1. Retrieve the latest backup from S3: `aws s3 cp s3://<bucket>/backups/db/db_backup_latest.sql.gz /tmp/`
2. Decompress and inject into the running database:
   ```bash
   gunzip < /tmp/db_backup_latest.sql.gz | docker compose -f docker-compose.prod.yml exec -T db mysql -u medbook_user -p medbook_db
   ```

### Scenario: Total Instance Loss (EC2 Destruction)
1. Provision a new Ubuntu 22.04 instance and assign the Elastic IP.
2. Connect via SSH and pull the repository.
3. **Execute Host Hardening:** `sudo bash scripts/harden_server.sh`
4. **Execute CloudWatch Setup:** `sudo bash scripts/setup_cloudwatch.sh`
5. Restore `.env` from secure vault.
6. Pull database and media backups from S3.
7. **Provision TLS:** `bash scripts/init-letsencrypt.sh`
8. **Deploy App:** `bash scripts/deploy.sh`
9. Execute Database Restoration (see above).

---

## 7. AI-Agent Operational Guidance

Any future AI Agent working within this repository **MUST** adhere to these constraints:

* **DO NOT** expose internal services (MySQL, Gunicorn) via Docker ports. All traffic must route through Nginx.
* **DO NOT** modify Nginx configs without verifying the syntax via `nginx -t` inside the container.
* **DO NOT** disable security headers (HSTS, CSP) during debugging unless absolutely necessary, and revert immediately.
* **ALWAYS** use `scripts/deploy.sh` or standard Git workflows to apply changes. Do not manually edit files inside running containers.
* **RESPECT MEMORY LIMITS:** If adding new services (e.g., Redis), you must account for the 1GB RAM constraint.
* **VALIDATION IS MANDATORY:** After any infrastructure change, execute `scripts/smoke_test.sh` to empirically verify reachability.

---

## 8. Architecture Visualization

### Complete CI/CD to Production Pipeline

```text
  [Developer]
       │ (1) Git Push
       ▼
 [GitHub Repo] ──▶ (2) Trigger GitHub Actions (CI)
       │               │
       │               ├──▶ Boot ephemeral MySQL 8.0
       │               ├──▶ Run `python manage.py test`
       │               └──▶ Run Python CVE `safety check`
       │
       │ (3) SSH Deploy (CD - If Tests Pass)
       ▼
 [AWS EC2 Host]
       │
       ├──▶ (4) `git pull origin main`
       ├──▶ (5) `docker compose build web`
       ├──▶ (6) `docker compose up -d` (Zero-downtime container recreation)
       ├──▶ (7) `python manage.py migrate`
       ├──▶ (8) `python manage.py collectstatic`
       └──▶ (9) Execute `scripts/smoke_test.sh` (Health Verification)
```
