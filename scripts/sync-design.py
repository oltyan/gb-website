"""Pulls Tavern Noir tokens + Tailwind config from a local mm-sporekles clone.

Mirrors the pattern of mm-website's tools/sync-sporekles-css.mjs.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

DEFAULT_SOURCE = Path.home() / "projects" / "mm-sporekles" / "design-system"
DEST = Path(__file__).resolve().parent.parent / "app" / "static" / "design"

# Subpaths (relative to source root) the Grog Blossoms site uses.
# If Tavern Noir tokens live under a namespace (e.g. tavern-noir/), adjust.
WANTED = [
    "tavern-noir/tokens.css",
    "tavern-noir/tailwind.config.js",
    "fonts/",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args()

    if not args.source.exists():
        print(f"ERROR: source not found: {args.source}", file=sys.stderr)
        print("Clone mm-sporekles to ~/projects/mm-sporekles or pass --source.", file=sys.stderr)
        return 1

    DEST.mkdir(parents=True, exist_ok=True)
    for entry in WANTED:
        src = args.source / entry
        dst = DEST / entry
        if not src.exists():
            print(f"  SKIP (not found): {entry}")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        print(f"  SYNC: {entry}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
