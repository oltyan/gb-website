#!/usr/bin/env bash
# Restore the latest restic snapshot into the gb_data named volume.
#
# Usage:
#   scripts/restore.sh                   # restores latest snapshot
#   scripts/restore.sh <snapshot-id>     # restores a specific restic snapshot
#
# Requires the gb-website-app container to exist (running or stopped).
# `docker cp` works on stopped containers too — actually safer that way,
# since SQLite can't be replaced while the process holds it open.

set -euo pipefail

CONTAINER=${CONTAINER:-gb-website-app}
BACKUP_ENV=${BACKUP_ENV:-/opt/gb-website/backup.env}
SNAPSHOT_ID=${1:-latest}

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

set -a; . "$BACKUP_ENV"; set +a

echo "Restoring restic snapshot '$SNAPSHOT_ID' into $TMP …"
restic restore "$SNAPSHOT_ID" --target "$TMP"

# Pick the newest grogblossoms-*.db restic dumped into $TMP. Restic
# preserves the original directory structure, so the file may be a few
# levels deep.
SNAPSHOT_FILE=$(find "$TMP" -name 'grogblossoms-*.db' -type f | sort -r | head -n1)
if [[ -z "$SNAPSHOT_FILE" ]]; then
  echo "ERROR: no grogblossoms-*.db file found in restored snapshot" >&2
  exit 1
fi
echo "Will copy: $SNAPSHOT_FILE"

# Stop the app so SQLite isn't holding the file open during replace.
docker stop "$CONTAINER" || true

# Copy the restored DB into the named volume via the container.
docker cp "$SNAPSHOT_FILE" "$CONTAINER:/data/grogblossoms.db"

# Bring it back up.
docker start "$CONTAINER"

echo "Restore complete. App restarted; verify via /healthz + /admin/."
