# SafeConnect Backend Production Deployment Guide (Phase 13A)

This document details the production deployment, PostgreSQL database configuration, environment variables, WebSocket operational requirements, and security procedures for the **SafeConnect Backend**.

---

## 1. System Requirements & Architecture

- **Operating System**: Linux (Ubuntu 22.04 LTS / Debian 12 / RHEL 9 recommended)
- **Python**: 3.10+ (Tested on Python 3.13)
- **Database**: PostgreSQL 14+
- **WSGI / Async Server**: Gunicorn with `eventlet` worker
- **Reverse Proxy**: Nginx or Cloudflare / AWS ALB (with SSL/TLS termination)

---

## 2. PostgreSQL Setup

1. **Install PostgreSQL**:
   ```bash
   sudo apt update
   sudo apt install -y postgresql postgresql-contrib
   ```

2. **Create Database User & Database**:
   ```sql
   CREATE USER safeconnect_user WITH PASSWORD 'your_secure_password_here';
   CREATE DATABASE safeconnect_prod OWNER safeconnect_user;
   GRANT ALL PRIVILEGES ON DATABASE safeconnect_prod TO safeconnect_user;
   ```

3. **Verify Database Connection URL Format**:
   `postgresql://safeconnect_user:your_secure_password_here@localhost:5432/safeconnect_prod`

---

## 3. Environment Variables (.env)

Create `.env` in the `backend/` directory using standard key-value pairs:

```ini
FLASK_ENV=production
SECRET_KEY=generate_with_openssl_rand_hex_32
JWT_SECRET_KEY=generate_with_openssl_rand_hex_32

# PostgreSQL Database Connection
DATABASE_URL=postgresql://safeconnect_user:your_secure_password_here@localhost:5432/safeconnect_prod
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30

# CORS & Domain Configuration
FRONTEND_URL=https://safeconnect.example.com
CORS_ORIGINS=https://safeconnect.example.com

# Reverse Proxy (Set PROXY_COUNT=1 when behind Nginx / Cloudflare / AWS ALB)
PROXY_COUNT=1

# Web Push Notification Credentials (VAPID)
VAPID_PUBLIC_KEY=your_vapid_public_key
VAPID_PRIVATE_KEY=your_vapid_private_key
VAPID_CLAIM_EMAIL=mailto:security@safeconnect.example.com
```

> **Security Note**: Never commit `.env` or print secret values in logs or reports.

---

## 4. Database Migrations

SafeConnect uses **Flask-Migrate / Alembic** for database schema evolution without data loss.

1. **Apply Production Database Migrations**:
   ```bash
   cd backend
   flask db upgrade
   ```

2. **Do NOT use `db.create_all()` in production**: The application factory automatically skips `db.create_all()` when `FLASK_ENV=production`.

---

## 5. Production Startup Command

For real-time WebSocket support (Flask-SocketIO), run Gunicorn with the `eventlet` worker class:

```bash
cd backend
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 wsgi:app
```

### Multi-Worker Scaling with Redis Message Queue (Optional)
If scaling to multiple Gunicorn workers (`-w 4`), configure a Redis message queue:
`socketio.init_app(app, message_queue='redis://localhost:6379/0')`

---

## 6. Reverse Proxy & HTTPS Configuration (Nginx)

Example Nginx configuration supporting HTTPS (`wss://` and `https://`):

```nginx
server {
    listen 443 ssl http2;
    server_name api.safeconnect.example.com;

    ssl_certificate /etc/letsencrypt/live/api.safeconnect.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.safeconnect.example.com/privkey.pem;

    # REST API Proxy
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket (Flask-SocketIO) Proxy
    location /socket.io/ {
        proxy_pass http://127.0.0.1:5000/socket.io/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
}
```

---

## 7. Health Check Verification

Verify system and database operational status:

- **System Health**:
  ```bash
  curl -i https://api.safeconnect.example.com/api/health
  ```
  *Expected Response*: `HTTP 200 OK`
  `{"data": {"service": "SafeConnect API", "status": "ok", "version": "1.0.0"}, "message": "Service operational", "success": true}`

- **Database Connectivity**:
  ```bash
  curl -i https://api.safeconnect.example.com/api/health/db
  ```
  *Expected Response*: `HTTP 200 OK`
  `{"data": {"database": "healthy", "status": "ok"}, "message": "Database connected", "success": true}`

---

## 8. Backup & Disaster Recovery

### PostgreSQL Backup (`pg_dump`)
Run a daily automated cron backup:
```bash
pg_dump -U safeconnect_user -h localhost -F c -b -v -f "/var/backups/safeconnect_$(date +%Y%m%d_%H%M%S).dump" safeconnect_prod
```

### PostgreSQL Restore (`pg_restore`)
```bash
pg_restore -U safeconnect_user -h localhost -d safeconnect_prod -v "/var/backups/safeconnect_20260816_120000.dump"
```

---

## 9. Rollback Plan

If a deployment fails:
1. **Application Rollback**: Revert Git release tag / Docker container to previous stable version.
2. **Restart Service**: Restart Gunicorn process (`systemctl restart safeconnect`).
3. **Database Migration Safety**: Do **NOT** run destructive `flask db downgrade` unless schema migration was explicitly tested and audited. Revert to the latest `pg_dump` backup if database inconsistencies occurred.

---

## 10. Operational Logging

Logs are formatted to standard output and `errorlog` / `accesslog` in Gunicorn.
- **Excluded Sensitive Data**: Passwords, JWT strings, private VAPID keys, and exact GPS coordinates are excluded from log outputs.
- **Monitored Errors**: Startup failures, database disconnects, authentication errors, and push delivery status.
