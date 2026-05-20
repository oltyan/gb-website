# Working in mm-grogblossoms

This is a Flask CMS for The Grog Blossoms. Tavern Noir design system. Part of mm-* fleet.

## Conventions

- Python 3.12. Flask 3 factory pattern (`app/__init__.py::create_app`).
- SQLAlchemy 2.0 typed declarative style — use `Mapped[...]` annotations, not legacy `Column()`.
- Templates absorb the existing HTML mockups in `gb-website/stitch_the_grog_blossoms_website/` — preserve class names and structure when porting.
- Tavern Noir tokens are synced from `~/projects/mm-sporekles/design-system/` — never edit `app/static/design/` directly.
- Admin is OIDC-gated; the `gb-developer` group claim is required. Do not bypass.
- Public images reference the CDN — never store user uploads locally.

## Testing

`make test` runs pytest. Each new model/view gets at least a smoke test. Block validation and OIDC group checks get unit tests.

## Spec

See `docs/specs/2026-05-20-mm-grogblossoms-design.md` (vendored from gb-website during init).
