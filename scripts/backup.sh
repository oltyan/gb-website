#!/usr/bin/env bash
# Run nightly on whichever host runs the gb-website-app container.
# Takes a SQLite snapshot via `.backup` inside the container, copies it
# to the host snapshot dir, then ships it off-site via restic to B2.
#
# The DB lives in the `gb_data` Docker named volume (docker-compose.yml),
# not on the host filesystem — that's why we go through docker exec
# rather than reading the file directly. Portable: works identically on
# Mac, Linux, and any EC2 box without configuring Docker Desktop file
# sharing or host bind paths.

set -euo pipefail

CONTAINER=${CONTAINER:-gb-website-app}
SNAPSHOT_DIR=${SNAPSHOT_DIR:-$HOME/gb-website-backups}
BACKUP_ENV=${BACKUP_ENV:-/opt/gb-website/backup.env}
TS=$(date +%F)

mkdir -p "$SNAPSHOT_DIR"

# `.backup` is the right SQLite snapshot mechanism — atomic, consistent
# under concurrent writers, byte-identical to the original file. Write
# to /tmp inside the container (NOT the named volume) so we don't pollute
# the live DB's filesystem with snapshot copies.
docker exec "$CONTAINER" sqlite3 /data/grogblossoms.db ".backup '/tmp/grogblossoms-${TS}.db'"
docker cp "$CONTAINER:/tmp/grogblossoms-${TS}.db" "$SNAPSHOT_DIR/grogblossoms-${TS}.db"
docker exec "$CONTAINER" rm "/tmp/grogblossoms-${TS}.db"

# Restic config: RESTIC_REPOSITORY, RESTIC_PASSWORD, B2_ACCOUNT_ID, B2_ACCOUNT_KEY
set -a; . "$BACKUP_ENV"; set +a

restic backup "$SNAPSHOT_DIR/grogblossoms-${TS}.db"
restic forget --prune --keep-daily 14 --keep-weekly 6 --keep-monthly 6

# Local rotation: keep 7 days of snapshots on disk
find "$SNAPSHOT_DIR" -name 'grogblossoms-*.db' -mtime +7 -delete
