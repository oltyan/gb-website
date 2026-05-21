# gb-website

The Grog Blossoms — CMS + public site, deployed on mycelium behind Cloudflare Tunnel.

Brand: **Tavern Noir** (brutalist + hand-drawn).

- Public site: https://grogblossoms.com
- Admin (OIDC, `gb-developer` group): https://grogblossoms.com/admin/
- Spec: [`docs/specs/2026-05-20-mm-grogblossoms-design.md`](docs/specs/2026-05-20-mm-grogblossoms-design.md)
- Plan: [`docs/plans/2026-05-20-mm-grogblossoms.md`](docs/plans/2026-05-20-mm-grogblossoms.md)

## Stack

Python 3.12 · Flask 3 · SQLAlchemy 2.0 · SQLite · Jinja2 · HTMX · gunicorn · docker-compose · Cloudflare Tunnel.

Images are hosted on the [mm-sporekles](https://github.com/oltyan/mm-sporekles) asset CDN under `grogblossoms/`.

## Local dev

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
make sync-design           # pulls Tavern Noir tokens from ~/projects/mm-sporekles
flask --app app db upgrade
make dev                   # http://localhost:5000
```

`make test` runs pytest.

## Deploy

See [`docs/runbook-deploy.md`](docs/runbook-deploy.md).

## Convention

- Templates absorb the mockups in [`docs/mockups/`](docs/mockups/) — preserve Tavern Noir class names.
- Public images reference the mm-sporekles CDN — never store user uploads locally.
- Admin is OIDC-gated; the `gb-developer` group claim is required.
