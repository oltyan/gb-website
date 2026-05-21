#!/usr/bin/env bash
# Run nightly on mycelium (outside containers).
# Snapshots SQLite via .backup, then restic to Backblaze B2.

set -euo pipefail

DATA_DIR=${DATA_DIR:-/opt/gb-website/data}
SNAPSHOT_DIR=${SNAPSHOT_DIR:-/opt/gb-website/backups}
TS=$(date +%F)

mkdir -p "$SNAPSHOT_DIR"
sqlite3 "$DATA_DIR/grogblossoms.db" ".backup '$SNAPSHOT_DIR/grogblossoms-$TS.db'"

# Restic config: RESTIC_REPOSITORY, RESTIC_PASSWORD, B2_ACCOUNT_ID, B2_ACCOUNT_KEY
# loaded from /opt/gb-website/backup.env
set -a; . /opt/gb-website/backup.env; set +a

restic backup "$SNAPSHOT_DIR/grogblossoms-$TS.db"
restic forget --prune --keep-daily 14 --keep-weekly 6 --keep-monthly 6

# Local rotation: keep 7 days of snapshots on disk
find "$SNAPSHOT_DIR" -name 'grogblossoms-*.db' -mtime +7 -delete
