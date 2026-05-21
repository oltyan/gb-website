#!/usr/bin/env bash
# Restore the latest restic snapshot to a chosen target.

set -euo pipefail
TARGET=${1:?Usage: restore.sh /path/to/output-dir}
set -a; . /opt/gb-website/backup.env; set +a
restic restore latest --target "$TARGET"
echo "Restored. Stop the app, replace /opt/gb-website/data/grogblossoms.db, then start."
