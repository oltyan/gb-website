# mm-grogblossoms — Design Spec

**Date:** 2026-05-20
**Repo (target):** `~/projects/mm-grogblossoms`
**Public URL:** `https://grogblossoms.com`
**Brand:** The Grog Blossoms (celtic-pirate fusion band, Renaissance Festival circuit)
**Visual system:** Tavern Noir (brutalist + hand-drawn, monochrome with red/amber accents)

## Overview

A self-hosted CMS-backed website for The Grog Blossoms. The CMS is a lightweight Flask application; the public site is server-rendered Jinja2 templates that absorb the existing Tavern Noir mockups. Content lives in SQLite. Images are pushed to the mm-sporekles asset CDN (`design-assets.musicalmycology.org/grogblossoms/*`) — local storage is not used for public assets. CSS and design tokens are synced from mm-sporekles at build time, matching the pattern established in `mm-website`.

The application runs on mycelium (homelab) in a docker-compose pair: the Flask app and `cloudflared`. Cloudflare Tunnel terminates TLS and routes inbound traffic; there is no port forwarding and no exposure of the home IP. Route53 retains the `grogblossoms.com` zone; the apex/`www` records become CNAMEs to the Cloudflare Tunnel hostname.

## Goals

- Author-friendly editing for blog posts, gallery curation, tour dates, music/merch, and crew profiles.
- Pixel-faithful rendering of the Tavern Noir design (Quarterdeck, Rogue's Gallery, Ship's Manifest, Booty mockups).
- Block-based authoring so theme flourishes (skewed images, sketch borders, torn-paper dividers, scuttlebutt callouts) drop in as content blocks rather than hand-written class strings.
- mm-* fleet conformance: Makefile, `mm-meta.yml`, design sync from sporekles, Jenkins deploy job, homebody labels, `MM_ARCHITECTURE.md` cross-reference.
- Inquiry intake (booking, press, general) with admin inbox + email notification.

## Non-goals

- Not an e-commerce platform. Merch and music link out to Bandcamp / Big Cartel / Shopify / etc.
- Not a 24/7 service. When mycelium is offline the site 5xx's gracefully via Cloudflare; no fail-over.
- No multi-language. English only.
- No comment system. Inquiries are the only inbound user data.
- No realtime, no client-side framework. HTMX only where it earns its keep (admin block editor).

## Tech stack

| Layer | Choice |
|---|---|
| Language | Python 3.12 |
| Framework | Flask 3 + Jinja2 |
| ORM | SQLAlchemy 2.0 + Alembic |
| DB | SQLite (single file at `/data/grogblossoms.db`) |
| Forms | Flask-WTF + WTForms |
| Auth | OIDC via `authlib`, federated to the same provider as mm-sporekles. Group `gb-developer` grants access. |
| Admin UI | Hand-rolled Jinja + HTMX. Flask-Admin is **not** used (poor design fit). |
| Markdown rendering | `markdown` (with extensions: `attr_list`, `fenced_code`, `tables`, `nl2br`) — used inside `paragraph` blocks for inline emphasis only |
| Server | Gunicorn |
| Image storage | mm-sporekles S3 bucket, `grogblossoms/` prefix, accessed via boto3. **Credentials and IAM user are placeholders until mm-sporekles infra exposes a scoped uploader.** |
| Email | SMTP (provider TBD — likely Fastmail app password); used only for inquiry notifications |
| Container orchestration | docker-compose |
| Reverse proxy | None internally. Cloudflare Tunnel terminates TLS and routes directly to gunicorn:8000. |
| Tunnel | `cloudflared` container; tunnel managed in the Cloudflare dashboard |
| CI/CD | Jenkins (mm-* fleet pattern); job `mm-grogblossoms-deploy` builds image, pushes, and pulls on mycelium |
| Backups | Nightly `sqlite3 .backup` → restic → Backblaze B2 |
| Design sync | `scripts/sync-design.py` (Python analogue of mm-website's `sync-sporekles-css.mjs`) pulls Tavern Noir tokens + Tailwind config from local mm-sporekles clone into `app/static/design/` at build time |

## Architecture

```
                ┌─────────────────────────────────────────────┐
                │            grogblossoms.com (Route 53)      │
                │           CNAME → <tunnel>.cfargotunnel.com │
                └─────────────────────────────────────────────┘
                                       │
                                       ▼
                        ┌──────────────────────────┐
                        │  Cloudflare edge / tunnel │  (TLS, DDoS, hides home IP)
                        └──────────────────────────┘
                                       │
                            (outbound from mycelium)
                                       │
                ┌──────────────────────┴─────────────────────┐
                │  mycelium (docker-compose)                 │
                │  ┌────────────────┐   ┌────────────────┐   │
                │  │ cloudflared    │──▶│ app (gunicorn) │   │
                │  └────────────────┘   │  Flask + Jinja │   │
                │                       │  + SQLite      │   │
                │                       └────────┬───────┘   │
                │                                │ boto3     │
                └────────────────────────────────┼───────────┘
                                                 ▼
                              design-assets.musicalmycology.org
                              (S3 + CloudFront; mm-sporekles infra)
                              prefix: /grogblossoms/*
```

- The Flask app serves both public pages (`/`, `/log`, `/manifest`, …) and the admin (`/admin/*`).
- OIDC callback is mounted at `/auth/oidc/callback`; the entire `/admin` tree is gated by a `require_group("gb-developer")` decorator.
- Public images are referenced by absolute URL into the CDN — the app never serves user-uploaded media directly. The only static files the app serves are CSS, JS, and built-in icons / brand assets synced from mm-sporekles.

## Content model

All models live in `app/models.py`. SQLAlchemy 2.0 typed declarative style.

### `Post` (Ship's Log)
| Field | Type | Notes |
|---|---|---|
| id | int PK | |
| slug | str unique | URL slug; auto-from-title with manual override |
| title | str | |
| published_at | datetime nullable | null = draft |
| author_name | str | display string, not a FK (single-author site) |
| hero_image_url | str nullable | CDN URL |
| excerpt | str | shown in `/log` index cards |
| blocks | JSON | array of block objects, see "Block format" below |
| created_at / updated_at | datetime | |

### `CrewMember` (Rogue's Gallery)
| Field | Type | Notes |
|---|---|---|
| id | int PK | |
| slug | str unique | |
| name | str | e.g. "THE SIREN" |
| role | str | e.g. "Fiddle & Lore" |
| portrait_url | str | CDN URL |
| quote | str | the italic pullquote on each card |
| bio | text | longer body for a future `/crew/<slug>` page (not v1) |
| entry_no | str | display-only string ("002", "003") |
| tilt | enum (`left`, `right`) | drives the `-rotate-1` / `rotate-1` class |
| accent | enum (`white`, `amber`, `red`) | border accent color |
| sort_order | int | |

### `TourDate` (Ship's Manifest)
| Field | Type | Notes |
|---|---|---|
| id | int PK | |
| event_name | str | "Winter Knights of Cheyenne" |
| venue | str | |
| city | str | |
| state | str | 2-letter |
| starts_at | datetime | |
| ends_at | datetime nullable | for multi-day events |
| ticket_url | str nullable | |
| status | enum (`confirmed`, `tentative`, `past`) | "past" hides date but keeps for archive |
| notes | text nullable | shown in the expanded card |

### `Gallery` + `GalleryImage`
**`Gallery`:** id, slug, title, description, cover_image_url, sort_order, created_at
**`GalleryImage`:** id, gallery_id (FK), image_url, caption, alt_text, sort_order

Galleries can also be referenced as a `gallery_inline` block inside a Post.

### `MusicTrack` (Booty)
| Field | Type | Notes |
|---|---|---|
| id | int PK | |
| title | str | |
| release_name | str nullable | album/EP/single name |
| audio_url | str nullable | direct streaming URL on the CDN |
| bandcamp_url | str nullable | |
| spotify_url | str nullable | |
| apple_music_url | str nullable | |
| duration_sec | int nullable | |
| cover_url | str nullable | CDN URL |
| release_date | date nullable | |
| lyrics | text nullable | |
| sort_order | int | |

### `MerchItem` (Booty)
| Field | Type | Notes |
|---|---|---|
| id | int PK | |
| name | str | |
| description | text | |
| image_url | str | CDN URL |
| price_display | str | "$25" — display only; no checkout |
| external_url | str | link to Bandcamp / Big Cartel / etc. |
| in_stock | bool | |
| sort_order | int | |

### `PressAsset` (Crow's Nest)
| Field | Type | Notes |
|---|---|---|
| id | int PK | |
| title | str | |
| file_url | str | CDN URL |
| kind | enum (`bio`, `logo`, `photo`, `rider`, `stage_plot`, `epk`, `other`) | |
| description | text nullable | |
| sort_order | int | |

### `Inquiry` (Crow's Nest)
| Field | Type | Notes |
|---|---|---|
| id | int PK | |
| kind | enum (`booking`, `press`, `general`) | drives which form fields show on the public form |
| from_name | str | |
| email | str | |
| phone | str nullable | |
| event_date | date nullable | (booking) |
| venue | str nullable | (booking) |
| city | str nullable | (booking) |
| message | text | |
| status | enum (`new`, `replied`, `archived`) | |
| created_at | datetime | |

Submission triggers: (1) store row, (2) SMTP notification to `SiteSettings.contact_email`, (3) success page rendered in Tavern Noir style.

### `Scuttlebutt`
| Field | Type | Notes |
|---|---|---|
| id | int PK | |
| text | str | shown in homepage "Latest Scuttlebutt" panel |
| link_url | str nullable | optional CTA link |
| accent | enum (`white`, `amber`, `red`) | mark color (the "X") |
| sort_order | int | |
| expires_at | datetime nullable | auto-hide past this; null = no expiry |

### `SiteSettings` (singleton; row id always 1)
| Field | Type | Notes |
|---|---|---|
| hero_quote | text | the "celtic-pirate fusion band…" line |
| hero_image_url | str | the Quarterdeck hero image |
| logo_url | str | |
| contact_email | str | inquiry notification recipient |
| social_links | JSON | `[{platform, url}, …]` |
| footer_text | str | "© 1724 THE GROG BLOSSOMS. NO QUARTER GIVEN." |
| ports_visited | int | the "12" stat counter |
| grog_pints | str | the "100+" stat counter (string to allow "100+") |

## Block format

Block-based authoring stored as a JSON array on `Post.blocks` (and reusable in any future model that wants blocks). Each block is:

```json
{
  "type": "paragraph",
  "id": "blk_01HVZX...",
  "data": { /* type-specific */ }
}
```

### v1 block types

| Type | Data fields | Renders as |
|---|---|---|
| `paragraph` | `markdown: str` | `<p>` with inline emphasis. `==highlighted text==` renders as a `pencil-highlight` span; implemented as a custom `markdown.Extension` registered in `app/services/blocks.py` |
| `heading` | `level: 2-4, text: str` | `<h2-4>` in `font-hand`, optional `sketch-underline` |
| `image` | `url, caption, alt, tilt (-2|-1|0|1|2), border (white|amber|red), grayscale (bool)` | `noir-frame sketch-border` wrapper with rotation class |
| `pull_quote` | `text, attribution (opt), style (torn|amber-bar)` | The two pull-quote treatments from the Quarterdeck mockup |
| `gallery_inline` | `gallery_id` | Embeds a `Gallery` as a grid |
| `divider` | `style (torn|dashed-amber|sketch-line)` | The "Torn Paper" / "Duct Tape" divider treatments from the design system |
| `callout` | `label, text, accent (red|amber), tilt` | The "URGENT LOG" / scuttlebutt-style box |
| `stat_pair` | `left: {value, label, accent}, right: {value, label, accent}` | The "12 Ports Visited / 100+ Grog Pints" pattern |
| `bento_card` | `title, body, icon (Material Symbol name), link_url, link_text, accent` | The Smuggler's Crate / Articles of War tiles |

Each block type has two artifacts:

- `app/templates/admin/_blocks/<type>_form.html` — admin partial (edit form fields)
- `app/templates/_blocks/<type>.html` — public renderer (Jinja macro `{% macro render_block(block) %}` dispatches by `type`)

The block editor in admin is HTMX-driven:

- "Add block" button opens a type picker (popover).
- Picking a type appends a new block partial to the form (server round-trip; HTMX).
- Each block has up/down/delete handles. Reorder via Sortable.js (small, vendored).
- Save serializes the form into the `blocks` JSON column. No client-side state machine.

Image fields inside blocks open an asset picker modal: list existing CDN assets (a small `Asset` table records every upload), with an "Upload new" button that pushes to S3 and inserts the URL.

### `Asset` (admin-only, supports the picker)

| Field | Type | Notes |
|---|---|---|
| id | int PK | |
| key | str unique | S3 key under `grogblossoms/` |
| url | str | public CDN URL |
| filename | str | original |
| content_type | str | |
| size_bytes | int | |
| width / height | int nullable | populated for images |
| uploaded_at | datetime | |
| caption | str nullable | optional default caption when reused |

## Public routes

| Path | View | Mockup |
|---|---|---|
| `/` | Quarterdeck (hero, scuttlebutt, ship's log latest 3, bento) | `the_quarterdeck_expanded_home` |
| `/log` | Ship's Log index, paginated | (new — extrapolated from card pattern) |
| `/log/<slug>` | Single post (block renderer) | (new) |
| `/manifest` | Ship's Manifest (tour dates, upcoming + past archive) | `the_ship_s_manifest_tavern_noir_edition` |
| `/crew` | Rogue's Gallery | `the_rogue_s_gallery_tavern_noir_edition` |
| `/booty` | Booty (music tracks + merch) | `the_booty_tavern_noir_edition_v2` |
| `/gallery` | Index of photo galleries | (new) |
| `/gallery/<slug>` | Single gallery (lightbox) | (new) |
| `/crows-nest` | Press kit + contact/booking/press forms | (new) |
| `/crows-nest/submit` | Form POST handler | |
| `/feed.xml` | RSS for Ship's Log | |
| `/sitemap.xml` | Sitemap | |
| `/robots.txt` | Static | |

## Admin routes (all under `/admin`, OIDC-gated, `gb-developer` group required)

- `/admin/` — dashboard (recent posts, inbox count, next 3 tour dates)
- `/admin/posts/` — list + new + edit (block editor)
- `/admin/crew/` — list + new + edit
- `/admin/tour-dates/` — list + new + edit
- `/admin/galleries/` — list + new + edit (incl. image reorder)
- `/admin/music/` — list + new + edit
- `/admin/merch/` — list + new + edit
- `/admin/press/` — list + new + edit
- `/admin/inquiries/` — inbox; rows clickable to detail with status updates
- `/admin/scuttlebutt/` — list + new + edit (with expiry pickers)
- `/admin/assets/` — media library (used by the picker; standalone view to manage)
- `/admin/settings/` — singleton form

## Auth

- OIDC via `authlib`, same identity provider as mm-sporekles (FA-OIDC).
- Required group claim: `gb-developer`. The same group grants access to the sporekles viewer.
- Session stored in Flask's secure signed cookie; `SESSION_COOKIE_SECURE=True`, `HTTPONLY=True`, `SameSite=Lax`.
- Decorator: `@require_group("gb-developer")` on all admin blueprints.
- Unauthenticated requests to `/admin/*` redirect to the OIDC login URL; failed group check renders a "Crew Only" page in Tavern Noir style.

## Image flow (placeholders until mm-sporekles infra exposes the uploader)

**Target end state:**

1. mm-sporekles' `infra/` Terraform adds an IAM user `mm-grogblossoms-uploader` with policy:
   - `s3:PutObject`, `s3:DeleteObject` on `arn:aws:s3:::<assets-bucket>/grogblossoms/*`
   - `s3:ListBucket` on the bucket with prefix condition `grogblossoms/*`
2. Credentials surface as Jenkins credentials and as a docker-compose env vars file (`/opt/mm-grogblossoms/secrets.env`, mode 600, not in repo).
3. Flask app reads `S3_BUCKET`, `S3_PREFIX=grogblossoms/`, `S3_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `CDN_BASE_URL=https://design-assets.musicalmycology.org/`.
4. Upload handler: stream → `boto3.client('s3').upload_fileobj(...)` with `ContentType` and `CacheControl: public, max-age=31536000, immutable` → record `Asset` row with the derived public URL.

**Placeholder until then:**

- `S3_BUCKET=__PLACEHOLDER__`, `AWS_ACCESS_KEY_ID=__PLACEHOLDER__`, `AWS_SECRET_ACCESS_KEY=__PLACEHOLDER__`, `CDN_BASE_URL=https://design-assets.musicalmycology.org/`.
- `app/services/storage.py` exposes `upload(file_obj, filename) -> Asset`. With placeholder creds the implementation raises `NotImplementedError("S3 uploader not yet provisioned — see mm-sporekles infra")`.
- The admin asset picker still works for already-CDN-hosted URLs: admin lets you **paste a CDN URL** to create an `Asset` row manually. This is the v1 path that unblocks content authoring while the IAM piece is being built.

## Email

- SMTP via env: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`.
- Provider: TBD (Fastmail app password is the working assumption).
- One outbound path: inquiry submitted → email to `SiteSettings.contact_email` with the form contents and a link to `/admin/inquiries/<id>`.
- Failures are logged but never block the submission — the DB row is the source of truth.

## Repo layout

```
mm-grogblossoms/
  app/
    __init__.py              # Flask factory
    config.py                # env-driven config
    extensions.py            # db, login, oauth
    models.py                # SQLAlchemy models
    blueprints/
      public/                # /, /log, /manifest, /crew, /booty, /gallery, /crows-nest
      admin/                 # /admin/* (one module per content type)
      auth/                  # OIDC routes
    services/
      storage.py             # boto3 wrapper (placeholder impl in v1)
      email.py               # SMTP wrapper
      blocks.py              # block validation + dispatch
    templates/
      base.html              # global layout (header, footer, grain overlay)
      public/                # one file per public page
      admin/                 # admin layout + per-resource views
      _blocks/               # public renderers (one per block type)
        macros.html          # render_block dispatcher
    static/
      design/                # ← synced from mm-sporekles (gitignored)
      js/
        sortable.min.js
        htmx.min.js
  migrations/                # Alembic
  scripts/
    sync-design.py           # pulls Tavern Noir tokens from ~/projects/mm-sporekles
  tests/
    test_blocks.py
    test_models.py
    test_admin_auth.py
    test_inquiry_flow.py
  Dockerfile
  docker-compose.yml
  Makefile
  Jenkinsfile.deploy
  mm-meta.yml
  MM_ARCHITECTURE.md         # cross-ref to mm-documents canonical
  README.md
  CLAUDE.md
  .env.example
  pyproject.toml
```

## docker-compose (mycelium)

```yaml
services:
  app:
    image: ghcr.io/oltyan/mm-grogblossoms:${TAG:-latest}
    env_file: /opt/mm-grogblossoms/secrets.env
    volumes:
      - /opt/mm-grogblossoms/data:/data
    restart: unless-stopped
    labels:
      - homebody.service=mm-grogblossoms
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 5s
      retries: 3

  cloudflared:
    image: cloudflare/cloudflared:latest
    command: tunnel --no-autoupdate run
    environment:
      - TUNNEL_TOKEN=${CF_TUNNEL_TOKEN}
    restart: unless-stopped
    depends_on:
      app:
        condition: service_healthy
```

The Cloudflare Tunnel is configured in the CF dashboard with one public hostname (`grogblossoms.com` and `www.grogblossoms.com`) pointing at `http://app:8000`. The dashboard-managed tunnel keeps tunnel config out of the repo.

## DNS (Route 53)

Route 53 cannot CNAME the apex to a non-AWS hostname — ALIAS records only target AWS resources, and a raw CNAME at the zone apex is non-conformant. Three viable patterns; **pick one before launch**:

1. **(Recommended) Delegate the zone to Cloudflare.** Change the `grogblossoms.com` NS records at the registrar to Cloudflare's nameservers. CF DNS supports CNAME flattening at the apex, points cleanly at `<tunnel-uuid>.cfargotunnel.com`, and unifies tunnel + DNS in one provider. Loses Route 53 zone management; this is the only meaningful cost.
2. **Keep Route 53; use `www` as canonical.** `www.grogblossoms.com` `CNAME` → `<tunnel-uuid>.cfargotunnel.com`. Apex redirect handled by an S3 static-site redirect bucket (or a one-line Lambda@Edge / Cloudfront function pointed at by ALIAS). Costs ~$0/mo but adds an AWS dependency for the redirect.
3. **Keep Route 53; apex on a worker.** Cloudflare Worker on `grogblossoms.com` 301s to `www`; Route 53 ALIAS-A apex pointed at the worker. Possible but awkward.

Pattern 1 is the path of least resistance unless there's a reason to keep DNS on Route 53. Until decided, the spec writes the public hostname as `www.grogblossoms.com`.

TLS is handled at Cloudflare's edge — no certbot, no Caddy.

## Backups

- Nightly cron in the `app` container: `sqlite3 /data/grogblossoms.db ".backup /data/backup/grogblossoms-$(date +%F).db"`
- Restic snapshots `/data/backup/` to Backblaze B2 with a 90-day retention policy.
- Restore drill documented in README.

## Build & deploy

- `make build` — `docker build -t ghcr.io/oltyan/mm-grogblossoms:dev .`
- `make sync-design` — `python scripts/sync-design.py` reads `~/projects/mm-sporekles/design-system/` and writes the subset Grog Blossoms needs into `app/static/design/`. (The Tavern Noir tokens may live in mm-sporekles under a `tavern-noir/` namespace; the sync script supports a namespace argument.)
- `make dev` — `flask run --debug` on `localhost:5000` against a local SQLite file.
- `make test` — pytest.
- `make deploy` — triggers the Jenkins job.

Jenkins pipeline:

1. Build image, tag with git SHA + `latest`.
2. Push to GHCR.
3. SSH to mycelium, run `docker compose pull && docker compose up -d`.
4. Smoke test: `curl -fsS https://grogblossoms.com/healthz`.

## Testing strategy

- Models + block validation: unit tests against an in-memory SQLite.
- Admin auth: stub the OIDC provider, assert group-gated routes redirect / 403 correctly.
- Inquiry flow: assert DB row created, SMTP called, success page renders.
- Public pages: render smoke tests (200 + key selectors present) using `pytest-flask`.
- Block rendering: each block type rendered with representative data, snapshot-tested against a golden HTML file.

## Open items / explicitly deferred

- **mm-sporekles IAM uploader provisioning.** Placeholders ship in v1; the asset picker supports "paste CDN URL" until the IAM user is real. Tracked in `TODO.md` and on the mm-sporekles side.
- **Tavern Noir token home.** Whether the Tavern Noir tokens live in `mm-sporekles/design-system/tavern-noir/` alongside the Musical Mycology tokens, or in a sibling repo, is a sporekles decision. The sync script will accept whichever path.
- **FA-OIDC second relying-party registration.** Needs an entry for `grogblossoms.com/auth/oidc/callback` and group claim emission for `gb-developer`.
- **CF Tunnel creation.** New tunnel in the CF dashboard; token goes into `/opt/mm-grogblossoms/.env`.
- **Crew bio pages.** v1 ships the Rogue's Gallery cards only; per-member detail pages are deferred.
- **Press kit ZIP download.** "Download all press assets as zip" deferred to v1.1.
- **Music player UX.** v1 supports per-track audio_url (HTML5 `<audio>`); a unified site-wide player bar is deferred.
- **RSS feed for tour dates.** Considered useful; deferred to v1.1.

## Risks & mitigations

- **CF Tunnel as single point of failure.** Acceptable per "not 24/7" goal. If CF is degraded, mitigation is to temporarily flip Route 53 to a static maintenance page (manual).
- **SQLite write contention.** Single-writer; admin is single-user (you). Public site is read-only. No risk at expected load.
- **Image hot-linking by third parties.** Cache-Control immutable + CDN bandwidth absorption is the only defense. Mitigation: monitor CDN usage; add a Referer-based CloudFront rule if abuse appears.
- **OIDC provider outage locks out admin.** Document a break-glass: env var `EMERGENCY_LOGIN_TOKEN` that, when set, unlocks `/admin` with a one-time URL. Disabled by default.

## Postscript (2026-05-20) — sporekles architecture shift

The asset-storage section of this spec describes a model that did not survive:
gb-website was meant to hold its own scoped IAM key and write to a shared
mm-sporekles bucket under a `grogblossoms/` prefix using boto3 directly.
That model is **obsolete**. Retained here as historical record.

What actually shipped:

- mm-sporekles is now a multi-tenant **sidecar API** (Fastify, `api/src/routes/assets.ts`)
  registered in `mm-sporekles/tenants.yml`. The `gb` tenant has its own bucket
  (`gb-design-assets`), its own CloudFront distribution
  (`E1KERTUPUSBD9U` → `design-assets.grogblossoms.com`), and its own FA group
  (`gb-developer`).
- Uploads/deletes/replaces are HTTP multipart calls into the sidecar at
  `POST /:tenant/assets`. The sidecar performs S3 write + `manifest.json` regen
  + CloudFront invalidation server-side.
- Auth is **not** Bearer-token based. The sidecar reads
  `X-Auth-Request-Email/User/Groups` headers (oauth2-proxy / mm-mycelium-gateway
  pattern). Gb-website forwards the admin's identity in those headers when
  calling the sidecar over the `shared-tunnel` Docker network. The sidecar is
  not exposed externally — the network is the trust boundary.
- Config keys `S3_BUCKET`, `S3_PREFIX`, `S3_REGION`, `AWS_ACCESS_KEY_ID`,
  `AWS_SECRET_ACCESS_KEY`, the `boto3` dependency, and the `register_url()`
  "paste CDN URL" fallback are all gone. Replaced by `SPOREKLES_API_BASE` +
  `SPOREKLES_TENANT` and a real multipart upload form in `/admin/assets/`.

### Group model

Gb-website admins need **only `gb-developer`** to use the upload form here.

The MM ecosystem has a separate gateway-side `access_tier` gate
(mm-mycelium-gateway PR #25, sporekles commit `faeaa2f`) that enforces
`mm-developer` membership on requests reaching sporekles via
`mycelium.musicalmycology.org/sporekles/*`. That gate does **not** apply to
gb-website's upload path — `mm-sporekles-api` is only reachable on the
`shared-tunnel` Docker network and has no public ingress. The trust boundary
is the network; the per-tenant `gb-developer` check inside
`api/src/routes/assets.ts` is the only authorization gb-website needs to
satisfy. Per mm-mycelium-gateway's group-gating spec, `gb-developer` is
explicitly an app-internal sporekles RBAC role, not an MM-tier group.

(Admins who also want to use sporekles' own SPA at
`mycelium.musicalmycology.org/sporekles/` would need `mm-developer` on top.
Out of scope for this site.)

See `app/services/storage.py::SporeklesClient` and `docs/runbook-deploy.md`.

