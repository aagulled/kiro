#!/bin/bash
# Safe production deploy script - run on server
# Usage: ./deploy/scripts/deploy.sh

set -euo pipefail

PROJECT_DIR="/home/kirokiro/kirokiro"
VENV="$PROJECT_DIR/venv"
LOG="/var/log/deploy/kirokiro-deploy.log"

mkdir -p /var/log/deploy

echo "[$(date)] Starting deploy..." | tee -a "$LOG"

cd "$PROJECT_DIR"
git fetch --all
git checkout "${DEPLOY_BRANCH:-main}"
git pull --ff-only origin "${DEPLOY_BRANCH:-main}"

source "$VENV/bin/activate"
pip install -r requirements.txt --quiet

python manage.py migrate --noinput 2>&1 | tee -a "$LOG"
python manage.py collectstatic --noinput --clear 2>&1 | tee -a "$LOG"
python manage.py check --deploy 2>&1 | tee -a "$LOG"

# Graceful Gunicorn reload (better than restart for zero downtime)
if systemctl is-active --quiet gunicorn; then
    sudo systemctl reload gunicorn || sudo systemctl restart gunicorn
else
    sudo systemctl start gunicorn
fi

sudo systemctl reload nginx || true

echo "[$(date)] Deploy completed successfully." | tee -a "$LOG"
