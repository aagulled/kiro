#!/bin/bash
# Simple production backup script for Kirokiro
# Run daily via cron: 0 2 * * * /home/kirokiro/kirokiro/deploy/backup/backup.sh

set -euo pipefail

BACKUP_DIR="/backups/kirokiro"
DATE=$(date +%F-%H%M)
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"

# PostgreSQL
PGPASSWORD="${DB_PASSWORD}" pg_dump -h "${DB_HOST}" -U "${DB_USER}" "${DB_NAME}" | gzip > "$BACKUP_DIR/db-$DATE.sql.gz"

# Media files (exclude large temp)
tar --exclude='*.tmp' -czf "$BACKUP_DIR/media-$DATE.tar.gz" -C /home/kirokiro/kirokiro media/

# Redis dump (optional)
cp /var/lib/redis/dump.rdb "$BACKUP_DIR/redis-$DATE.rdb" || true

# Cleanup old
find "$BACKUP_DIR" -type f -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $DATE"
# Optionally: rsync to S3 or remote: aws s3 sync ...
