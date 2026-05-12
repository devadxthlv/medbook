#!/bin/bash
set -e

LOG="/var/log/medbook_backup.log"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="db_backup_$TIMESTAMP.sql.gz"

echo "[$TIMESTAMP] Starting backup..." >> "$LOG"

cd /home/ubuntu/medbook

set -a
source .env
set +a

docker compose -f /home/ubuntu/medbook/docker-compose.prod.yml exec -T db \
    mysqldump -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" | gzip > "/tmp/$BACKUP_FILE"

aws s3 cp "/tmp/$BACKUP_FILE" "s3://$S3_BUCKET/backups/db/$BACKUP_FILE"
aws s3 sync /home/ubuntu/medbook/media/ "s3://$S3_BUCKET/backups/media/"

rm "/tmp/$BACKUP_FILE"
echo "[$TIMESTAMP] Backup complete: $BACKUP_FILE" >> "$LOG"
