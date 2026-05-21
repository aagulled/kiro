# Kirokiro Production Deployment Guide

This document provides a complete, production-ready deployment of the Kirokiro Django backend on a Linux VPS using Nginx + Gunicorn + PostgreSQL + Redis + Let's Encrypt.

**Target Architecture (2026 best practices)**
- Ubuntu 22.04/24.04 LTS
- Python 3.11 + venv
- PostgreSQL 16
- Redis 7 (cache + Celery broker)
- Gunicorn (ASGI/WSGI) behind Unix socket
- Nginx (reverse proxy + static/media serving + SSL termination)
- Let's Encrypt (Certbot) with auto-renewal
- Systemd for process management
- GitHub Actions for CI/CD with zero-downtime reload

All secrets via environment variables. No hardcoded values in code.

## 1. Server Preparation (one-time)

```bash
# As root or sudo user
apt update && apt upgrade -y
apt install -y python3.11 python3.11-venv python3-pip postgresql postgresql-contrib redis-server nginx certbot python3-certbot-nginx git curl ufw fail2ban logrotate

# Create deploy user
useradd -m -s /bin/bash kirokiro
usermod -aG sudo kirokiro
mkdir -p /home/kirokiro/kirokiro
chown -R kirokiro:kirokiro /home/kirokiro
```

## 2. Clone & Python Environment

```bash
su - kirokiro
cd ~
git clone https://github.com/YOUR_ORG/kirokiro.git kirokiro/kirokiro
cd kirokiro/kirokiro
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt gunicorn
```

## 3. PostgreSQL Setup

```bash
sudo -u postgres psql
CREATE DATABASE kirokiro;
CREATE USER kirokiro WITH PASSWORD 'strong-db-password-2026!';
GRANT ALL PRIVILEGES ON DATABASE kirokiro TO kirokiro;
\q
```

Update `.env` with `DATABASE_URL=postgres://kirokiro:strong-db-password-2026!@localhost:5432/kirokiro`

> **Important**: Since you are using PostgreSQL, delete any local `db.sqlite3` file before committing or deploying:
> ```bash
> rm -f db.sqlite3
> ```
> The project `.gitignore` already excludes it.

## 4. Redis Setup & Security

```bash
sudo systemctl enable --now redis-server
sudo mkdir -p /etc/redis
# Copy and customize
sudo cp deploy/redis/kirokiro-redis.conf /etc/redis/kirokiro.conf
# Include in main redis.conf: include /etc/redis/kirokiro.conf
sudo systemctl restart redis-server
```

Test: `redis-cli -a yourpassword ping`

## 5. Django Production Configuration

```bash
cp .env.example .env
# Edit .env with real values (DEBUG=False, real domain, DB, REDIS, SECRET_KEY, etc.)
source venv/bin/activate
python manage.py check --deploy
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

**Important**: Update your domain in `.env` for `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `CORS_ALLOWED_ORIGINS`.

## 6. Gunicorn + Systemd

```bash
sudo mkdir -p /run/gunicorn /var/log/gunicorn
sudo chown -R www-data:www-data /run/gunicorn /var/log/gunicorn

# Copy service
sudo cp deploy/systemd/kirokiro.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now kirokiro
sudo systemctl status kirokiro
```

Gunicorn binds to Unix socket `/run/gunicorn/kirokiro.sock`

## 7. Nginx Configuration

```bash
sudo cp deploy/nginx/kirokiro.conf /etc/nginx/sites-available/kirokiro
sudo mkdir -p /etc/nginx/snippets
sudo cp deploy/nginx/snippets/*.conf /etc/nginx/snippets/
# Edit kirokiro.conf: replace all "yourdomain.com" with your real domain
sudo ln -s /etc/nginx/sites-available/kirokiro /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

## 8. Let's Encrypt SSL + HTTPS

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com --non-interactive --agree-tos -m admin@yourdomain.com
# Auto renewal is handled by certbot timer
sudo systemctl status certbot.timer
```

Certbot automatically edits your nginx conf for SSL and adds renewal hooks.

Add the post-renew hook:
```bash
sudo cp deploy/scripts/reload-nginx.sh /etc/letsencrypt/renewal-hooks/post/
sudo chmod +x /etc/letsencrypt/renewal-hooks/post/reload-nginx.sh
```

## 9. Final Permissions & Logs

```bash
sudo chown -R www-data:www-data /home/kirokiro/kirokiro/{staticfiles,media,logs}
sudo chmod 750 /home/kirokiro/kirokiro/media
# logrotate
sudo cp deploy/logrotate/kirokiro /etc/logrotate.d/
sudo logrotate -f /etc/logrotate.d/kirokiro
```

## 10. Firewall (UFW)

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
```

## 11. GitHub Actions CI/CD Setup

1. In GitHub repo → Settings → Secrets and variables → Actions:
   - `SERVER_HOST` = your server IP or domain
   - `SERVER_USER` = kirokiro (or root)
   - `SSH_PRIVATE_KEY` = your private key content (generate ssh-keygen, copy ~/.ssh/id_ed25519)

2. Push to `main` triggers tests + deploy via the workflow `.github/workflows/deploy.yml`

The workflow runs:
- lint + typecheck + pytest + `python manage.py check --deploy`
- On success: SSH → git pull → pip install → migrate → collectstatic → reload gunicorn/nginx

For manual server deploy: `bash deploy/scripts/deploy.sh`

## 12. Monitoring & Error Tracking

- **Sentry**: Already integrated via `SENTRY_DSN` in `.env`. Add the DSN from sentry.io.
- **Uptime**: Use UptimeRobot or BetterStack to ping https://yourdomain.com/health/ (add a simple health view if needed).
- **Server metrics**: Install `prometheus-node-exporter` + Grafana or use Netdata.
- **Logs**: `journalctl -u kirokiro -f`, `tail -f /var/log/nginx/access.log`, Gunicorn logs in /var/log/gunicorn/

## 13. Backups (Critical)

```bash
# Edit deploy/backup/backup.sh with your DB credentials
sudo mkdir -p /backups/kirokiro
sudo chown kirokiro:kirokiro /backups/kirokiro
crontab -e
# Add:
0 3 * * * /home/kirokiro/kirokiro/deploy/backup/backup.sh >> /var/log/backup.log 2>&1
```

Store backups offsite (S3, rsync.net, etc.). Test restores monthly.

## 14. Common Pitfalls & Fixes

1. **"DisallowedHost"** → Add your domain to `ALLOWED_HOSTS` in .env (comma-separated, no spaces).
2. **Static 404** → Run `collectstatic`, ensure Nginx location /static/ alias matches `STATIC_ROOT`.
3. **Gunicorn socket permission** → Ensure www-data owns /run/gunicorn and service has correct User/Group.
4. **Redis connection refused** → Check `REDIS_URL` password and that redis is listening on 127.0.0.1 only.
5. **CSRF / CORS errors in prod** → Populate `CSRF_TRUSTED_ORIGINS` and `CORS_ALLOWED_ORIGINS` with https://yourdomain.com (no trailing slash).
6. **check --deploy fails** → Usually missing HSTS or SECURE_* settings; our settings.py handles this when DEBUG=False.
7. **Media uploads not persisting** → Check MEDIA_ROOT permissions (www-data must write).
8. **Zero-downtime deploys** → Use `systemctl reload gunicorn` (not restart) + Gunicorn preload + max_requests.
9. **High memory** → Tune Gunicorn workers = (2*CPU)+1, add max_requests, use Redis for cache.
10. **Let's Encrypt rate limit** → Use `--staging` flag during testing.

## 15. Scaling Recommendations (Future)

- Use Docker + docker-compose for all services (or Kubernetes)
- Move media to S3 + CloudFront (set `USE_S3=True` + AWS keys in .env; code already supports via django-storages)
- Add Celery worker + beat systemd units for background tasks
- Use PgBouncer for DB connection pooling
- Multi-server: separate API servers behind load balancer
- Use managed services: RDS, ElastiCache, S3 in AWS/GCP

## 16. Quick Health Verification After Deploy

```bash
curl -I https://yourdomain.com/
curl -I https://yourdomain.com/static/admin/css/base.css
curl -I https://yourdomain.com/media/   # should 403 or index if allowed
python manage.py check --deploy
sudo systemctl status kirokiro nginx redis-server
```

**You are now running a secure, production-grade Django stack.**

Update this document as your infrastructure evolves.
