#!/usr/bin/env bash
# Restore the latest restic snapshot to a chosen target.

set -euo pipefail
TARGET=${1:?Usage: restore.sh /path/to/output-dir}
set -a; . /opt/mm-grogblossoms/backup.env; set +a
restic restore latest --target "$TARGET"
echo "Restored. Stop the app, replace /opt/mm-grogblossoms/data/grogblossoms.db, then start."
