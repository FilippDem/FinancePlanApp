#!/bin/bash
# Automated backup of financial planner data
# Run via cron: 0 2 * * * /Volume1/docker/financial-planner/backup.sh

BACKUP_DIR="/Volume1/docker/financial-planner/backups"
DATA_DIR="/Volume1/docker/financial-planner/app-data"
KEEP_DAYS=30

mkdir -p "$BACKUP_DIR"

# Create timestamped backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
tar -czf "$BACKUP_DIR/financial_data_$TIMESTAMP.tar.gz" -C "$DATA_DIR" . 2>/dev/null

# Remove backups older than KEEP_DAYS
find "$BACKUP_DIR" -name "financial_data_*.tar.gz" -mtime +$KEEP_DAYS -delete 2>/dev/null

echo "Backup completed: financial_data_$TIMESTAMP.tar.gz"
