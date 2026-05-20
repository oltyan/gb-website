# mm-grogblossoms — Architecture

> Cross-ref to canonical doc in [mm-documents](../mm-documents/MM_ARCHITECTURE.md).

## Position in the fleet

- **Public-facing brand:** The Grog Blossoms (sibling to Musical Mycology / RenQuest).
- **Visual system:** Tavern Noir (separate from MM's warm-naturalist tokens).
- **Asset hosting:** mm-sporekles CDN under `grogblossoms/` prefix.
- **Auth:** Federated OIDC (same IdP as mm-sporekles), group `gb-developer`.

## Components

- `app/` — Flask application (public + admin)
- SQLite at `/data/grogblossoms.db`
- `cloudflared` sidecar terminates TLS via Cloudflare Tunnel
- Backups: nightly sqlite `.backup` → restic → Backblaze B2

## Deploy

`make build` → push to GHCR → Jenkins `mm-grogblossoms-deploy` pulls on mycelium.

See [README.md](README.md) for local development.
See [`docs/specs/2026-05-20-mm-grogblossoms-design.md`](docs/specs/2026-05-20-mm-grogblossoms-design.md) for full spec.
