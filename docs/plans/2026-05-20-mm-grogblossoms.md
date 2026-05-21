# mm-grogblossoms Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a self-hosted Flask CMS + public site for grogblossoms.com, deployed on mycelium behind Cloudflare Tunnel, with content pushed to the mm-sporekles asset CDN.

**Architecture:** Single Flask 3 app serving public pages and `/admin/*` (OIDC-gated) from Jinja2 templates. SQLite via SQLAlchemy 2.0. Images stored in mm-sporekles' S3 bucket (placeholder uploader v1). CSS/tokens synced from local mm-sporekles clone at build time. docker-compose pair (app + cloudflared) on mycelium.

**Tech Stack:** Python 3.12, Flask 3, SQLAlchemy 2.0, Alembic, Flask-WTF, Authlib (OIDC), Jinja2, HTMX, gunicorn, boto3, pytest, docker-compose, Cloudflare Tunnel.

**Spec reference:** [`docs/superpowers/specs/2026-05-20-mm-grogblossoms-design.md`](../specs/2026-05-20-mm-grogblossoms-design.md)

**Repo path during implementation:** `~/projects/mm-grogblossoms`

---

## Phase Map

| Phase | Outcome at end of phase |
|---|---|
| 0. Foundation | Repo exists, `flask run` serves a "hello" page styled with synced sporekles tokens; CI-ready |
| 1. Auth | OIDC login round-trips; `/admin/*` redirects unauth users; `gb-developer` group enforced |
| 2. Data models | All models defined, Alembic migrations apply cleanly, model tests pass |
| 3. Admin CRUD | Logged-in admin can create/edit/delete every content type via plain forms (no block editor yet) |
| 4. Public pages | Every public route in the spec renders real content from the DB |
| 5. Forms + email | Crow's Nest contact/booking/press forms submit, store, email |
| 6. Block editor | Post body is JSON blocks; admin HTMX editor; all block types render |
| 7. Deploy | Dockerfile, docker-compose, Jenkinsfile, healthz endpoint, deployment runbook |

Each phase ends with passing tests. Commit after every task.

---

## File Structure

```
mm-grogblossoms/
├── app/
│   ├── __init__.py                # create_app() factory
│   ├── config.py                  # env-driven Config classes
│   ├── extensions.py              # db, migrate, oauth, csrf singletons
│   ├── models.py                  # SQLAlchemy 2.0 declarative models
│   ├── blueprints/
│   │   ├── public/
│   │   │   ├── __init__.py        # bp registration
│   │   │   ├── views.py           # /, /log, /manifest, etc.
│   │   │   └── feeds.py           # /feed.xml, /sitemap.xml
│   │   ├── admin/
│   │   │   ├── __init__.py        # admin bp + require_admin decorator wiring
│   │   │   ├── _crud.py           # generic CRUD view helpers
│   │   │   ├── posts.py
│   │   │   ├── crew.py
│   │   │   ├── tour_dates.py
│   │   │   ├── galleries.py
│   │   │   ├── music.py
│   │   │   ├── merch.py
│   │   │   ├── press.py
│   │   │   ├── inquiries.py
│   │   │   ├── scuttlebutt.py
│   │   │   ├── assets.py
│   │   │   ├── settings.py
│   │   │   └── blocks.py          # block editor HTMX endpoints (Phase 6)
│   │   └── auth/
│   │       ├── __init__.py
│   │       └── views.py           # /auth/login, /auth/oidc/callback, /auth/logout
│   ├── services/
│   │   ├── storage.py             # boto3 S3 wrapper (placeholder impl in v1)
│   │   ├── email.py               # SMTP wrapper
│   │   └── blocks.py              # block schema + dispatcher (Phase 6)
│   ├── templates/
│   │   ├── base.html              # site layout (header, footer, grain overlay)
│   │   ├── admin/
│   │   │   ├── base.html
│   │   │   ├── _form.html
│   │   │   ├── _list.html
│   │   │   └── <resource>.html    # one per resource
│   │   ├── public/
│   │   │   ├── home.html          # Quarterdeck
│   │   │   ├── log_index.html
│   │   │   ├── log_detail.html
│   │   │   ├── manifest.html
│   │   │   ├── crew.html
│   │   │   ├── booty.html
│   │   │   ├── gallery_index.html
│   │   │   ├── gallery_detail.html
│   │   │   └── crows_nest.html
│   │   └── _blocks/
│   │       ├── macros.html        # render_block dispatcher
│   │       └── <type>.html        # one per block type
│   └── static/
│       ├── design/                # synced from mm-sporekles (gitignored)
│       └── js/
│           ├── htmx.min.js
│           └── sortable.min.js
├── migrations/                    # Alembic
├── scripts/
│   └── sync-design.py
├── tests/
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_auth.py
│   ├── test_admin_crud.py
│   ├── test_public_views.py
│   ├── test_inquiry_flow.py
│   ├── test_blocks.py
│   └── test_storage.py
├── Dockerfile
├── docker-compose.yml
├── Jenkinsfile.deploy
├── Makefile
├── mm-meta.yml
├── MM_ARCHITECTURE.md
├── README.md
├── CLAUDE.md
├── .env.example
├── .gitignore
└── pyproject.toml
```

---

## Phase 0 — Foundation

### Task 0.1: Initialize repo + Python environment

**Files:**
- Create: `~/projects/mm-grogblossoms/.gitignore`
- Create: `~/projects/mm-grogblossoms/README.md`
- Create: `~/projects/mm-grogblossoms/pyproject.toml`

- [ ] **Step 1: Create repo**

```bash
mkdir -p ~/projects/mm-grogblossoms
cd ~/projects/mm-grogblossoms
git init
git checkout -b main
```

- [ ] **Step 2: Write `.gitignore`**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
*.egg-info/
.pytest_cache/
.ruff_cache/
.mypy_cache/

# Flask
instance/
.flask_session/

# App data
data/
*.db
*.db-journal
*.db-shm
*.db-wal

# Synced design assets
app/static/design/

# Secrets
.env
.env.local
secrets.env

# IDE
.vscode/
.idea/
.DS_Store
```

- [ ] **Step 3: Write `pyproject.toml`**

```toml
[project]
name = "mm-grogblossoms"
version = "0.1.0"
description = "The Grog Blossoms — CMS + public site"
requires-python = ">=3.12"
dependencies = [
  "flask>=3.0,<4",
  "flask-sqlalchemy>=3.1",
  "flask-migrate>=4.0",
  "flask-wtf>=1.2",
  "flask-login>=0.6",
  "sqlalchemy>=2.0,<3",
  "alembic>=1.13",
  "authlib>=1.3",
  "requests>=2.31",
  "boto3>=1.34",
  "markdown>=3.6",
  "python-dotenv>=1.0",
  "gunicorn>=22.0",
  "feedgen>=1.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "pytest-flask>=1.3",
  "ruff>=0.5",
  "black>=24.0",
  "freezegun>=1.5",
  "responses>=0.25",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM"]

[tool.black]
line-length = 100
target-version = ["py312"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
addopts = "-ra --strict-markers"
```

> **Note:** `pythonpath = ["."]` is required so bare `pytest` can discover the `app/` package. Without it the command in Task 0.2 Step 7 fails with `ModuleNotFoundError: No module named 'app'` because `pip install -e .` installs the distribution `mm-grogblossoms` but doesn't declare `app` as a package.

- [ ] **Step 4: Bootstrap venv and install**

```bash
cd ~/projects/mm-grogblossoms
python3.12 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
```

- [ ] **Step 5: Write `README.md` (stub — full content in Task 7.6)**

```markdown
# mm-grogblossoms

The Grog Blossoms — CMS + public site. Part of the `mm-*` fleet. Brand: Tavern Noir.

See `docs/specs/2026-05-20-mm-grogblossoms-design.md` for the design spec.

## Local development

```sh
source .venv/bin/activate
make sync-design
flask --app app run --debug
```
```

- [ ] **Step 6: Commit**

```bash
git add .gitignore pyproject.toml README.md
git commit -m "chore: initialize mm-grogblossoms repo"
```

---

### Task 0.2: Flask app factory + config

**Files:**
- Create: `app/__init__.py`
- Create: `app/config.py`
- Create: `app/extensions.py`
- Create: `.env.example`

- [ ] **Step 1: Write the failing test**

Create `tests/conftest.py`:

```python
import os
import pytest

os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret-do-not-use-in-prod")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("OIDC_CLIENT_ID", "test-client")
os.environ.setdefault("OIDC_CLIENT_SECRET", "test-secret")
os.environ.setdefault("OIDC_DISCOVERY_URL", "https://example.test/.well-known/openid-configuration")
os.environ.setdefault("OIDC_GROUP_REQUIRED", "gb-developer")
os.environ.setdefault("CDN_BASE_URL", "https://design-assets.musicalmycology.org/")
os.environ.setdefault("S3_BUCKET", "__PLACEHOLDER__")
os.environ.setdefault("S3_PREFIX", "grogblossoms/")
os.environ.setdefault("CONTACT_EMAIL", "chris@example.test")


@pytest.fixture
def app():
    from app import create_app
    app = create_app(config_name="testing")
    with app.app_context():
        from app.extensions import db
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
```

Create `tests/test_factory.py`:

```python
def test_app_factory_returns_flask_app(app):
    assert app.name == "app"
    assert app.config["TESTING"] is True


def test_healthz_returns_ok(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json == {"status": "ok"}
```

- [ ] **Step 2: Run tests and confirm they fail**

```bash
pytest tests/test_factory.py -v
```

Expected: `ImportError` or collection error — `app` package doesn't exist yet.

- [ ] **Step 3: Write `app/config.py`**

```python
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    SECRET_KEY: str
    SQLALCHEMY_DATABASE_URI: str
    SQLALCHEMY_TRACK_MODIFICATIONS: bool
    OIDC_CLIENT_ID: str
    OIDC_CLIENT_SECRET: str
    OIDC_DISCOVERY_URL: str
    OIDC_GROUP_REQUIRED: str
    CDN_BASE_URL: str
    S3_BUCKET: str
    S3_PREFIX: str
    S3_REGION: str
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_FROM: str
    CONTACT_EMAIL: str
    SESSION_COOKIE_SECURE: bool
    TESTING: bool
    DEBUG: bool


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def _bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.lower() in ("1", "true", "yes", "on")


def load_config(name: str = "production") -> Config:
    return Config(
        SECRET_KEY=_env("SECRET_KEY") or ("dev" if name != "production" else _require("SECRET_KEY")),
        SQLALCHEMY_DATABASE_URI=_env("DATABASE_URL", "sqlite:///grogblossoms.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        OIDC_CLIENT_ID=_env("OIDC_CLIENT_ID"),
        OIDC_CLIENT_SECRET=_env("OIDC_CLIENT_SECRET"),
        OIDC_DISCOVERY_URL=_env("OIDC_DISCOVERY_URL"),
        OIDC_GROUP_REQUIRED=_env("OIDC_GROUP_REQUIRED", "gb-developer"),
        CDN_BASE_URL=_env("CDN_BASE_URL", "https://design-assets.musicalmycology.org/"),
        S3_BUCKET=_env("S3_BUCKET", "__PLACEHOLDER__"),
        S3_PREFIX=_env("S3_PREFIX", "grogblossoms/"),
        S3_REGION=_env("S3_REGION", "us-east-1"),
        AWS_ACCESS_KEY_ID=_env("AWS_ACCESS_KEY_ID"),
        AWS_SECRET_ACCESS_KEY=_env("AWS_SECRET_ACCESS_KEY"),
        SMTP_HOST=_env("SMTP_HOST"),
        SMTP_PORT=int(_env("SMTP_PORT", "587")),
        SMTP_USER=_env("SMTP_USER"),
        SMTP_PASSWORD=_env("SMTP_PASSWORD"),
        SMTP_FROM=_env("SMTP_FROM", "no-reply@grogblossoms.com"),
        CONTACT_EMAIL=_env("CONTACT_EMAIL", "chris@grogblossoms.com"),
        SESSION_COOKIE_SECURE=_bool("SESSION_COOKIE_SECURE", default=(name == "production")),
        TESTING=(name == "testing"),
        DEBUG=(name == "development"),
    )


def _require(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        raise RuntimeError(f"Required env var missing: {name}")
    return val
```

- [ ] **Step 4: Write `app/extensions.py`**

```python
from authlib.integrations.flask_client import OAuth
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
oauth = OAuth()
login_manager = LoginManager()
csrf = CSRFProtect()
```

- [ ] **Step 5: Write `app/__init__.py`**

```python
import os
from flask import Flask, jsonify
from dataclasses import asdict
from .config import load_config
from .extensions import csrf, db, login_manager, migrate, oauth


def create_app(config_name: str | None = None) -> Flask:
    config_name = config_name or os.environ.get("FLASK_ENV", "production")
    app = Flask(__name__)
    cfg = load_config(config_name)
    app.config.update(asdict(cfg))

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    oauth.init_app(app)

    # Placeholder user_loader so Flask-Login's template context processor
    # can resolve `current_user` before the real User model exists.
    # Task 1.1 replaces this with the real DB-backed loader.
    @login_manager.user_loader
    def _placeholder_user_loader(user_id):  # pragma: no cover
        return None

    @app.get("/healthz")
    def healthz():
        return jsonify(status="ok")

    return app
```

- [ ] **Step 6: Write `.env.example`**

```bash
# Flask
FLASK_ENV=development
SECRET_KEY=change-me-in-prod
DATABASE_URL=sqlite:///grogblossoms.db
SESSION_COOKIE_SECURE=false

# OIDC (FA / sporekles federation)
OIDC_CLIENT_ID=
OIDC_CLIENT_SECRET=
OIDC_DISCOVERY_URL=
OIDC_GROUP_REQUIRED=gb-developer

# mm-sporekles asset CDN
CDN_BASE_URL=https://design-assets.musicalmycology.org/
S3_BUCKET=__PLACEHOLDER__
S3_PREFIX=grogblossoms/
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=__PLACEHOLDER__
AWS_SECRET_ACCESS_KEY=__PLACEHOLDER__

# SMTP
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=no-reply@grogblossoms.com
CONTACT_EMAIL=chris@grogblossoms.com
```

- [ ] **Step 7: Run tests**

```bash
pytest tests/test_factory.py -v
```

Expected: 2 passed.

- [ ] **Step 8: Commit**

```bash
git add app/ tests/ .env.example
git commit -m "feat: Flask app factory + config + healthz"
```

---

### Task 0.3: Base template + sporekles design sync

**Files:**
- Create: `app/templates/base.html`
- Create: `scripts/sync-design.py`
- Create: `Makefile`
- Create: `app/static/design/.gitkeep`

- [ ] **Step 1: Write `scripts/sync-design.py`**

```python
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
```

- [ ] **Step 2: Write `Makefile`**

```makefile
.PHONY: dev test build sync-design migrate fresh-db format lint

sync-design:
	python scripts/sync-design.py

dev: sync-design
	FLASK_ENV=development flask --app app run --debug --port 5000

test:
	pytest -v

migrate:
	flask --app app db upgrade

fresh-db:
	rm -f grogblossoms.db
	flask --app app db upgrade

format:
	black app tests scripts
	ruff check --fix app tests scripts

lint:
	ruff check app tests scripts
	black --check app tests scripts

build:
	docker build -t mm-grogblossoms:dev .
```

- [ ] **Step 3: Write `app/templates/base.html`**

```html
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}The Grog Blossoms{% endblock %}</title>

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@400;600;700;800&family=JetBrains+Mono:wght@400;500;700&family=Geist:wght@400;500&family=Coming+Soon&family=Gaegu:wght@400;700&display=swap" rel="stylesheet">
  <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet">

  <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
  <script>
    tailwind.config = {
      darkMode: "class",
      theme: {
        extend: {
          colors: {
            "surface": "#131313",
            "surface-container": "#1f1f1f",
            "surface-container-low": "#1b1b1b",
            "surface-container-lowest": "#0e0e0e",
            "surface-container-high": "#2a2a2a",
            "background": "#131313",
            "on-background": "#e2e2e2",
            "on-surface": "#e2e2e2",
            "on-surface-variant": "#c4c7c8",
            "primary": "#ffffff",
            "outline": "#8e9192",
            "accent-red": "#A62116",
            "accent-amber": "#C49A4D"
          },
          fontFamily: {
            "headline": ["Bricolage Grotesque"],
            "body": ["Geist"],
            "mono": ["JetBrains Mono"],
            "hand": ["Gaegu"],
            "script": ["Coming Soon"]
          }
        }
      }
    }
  </script>

  <style>
    .grain-overlay {
      background-image: radial-gradient(rgba(255,255,255,0.04) 1px, transparent 1px);
      background-size: 3px 3px;
      opacity: 0.6;
      pointer-events: none;
    }
    .noir-frame { border: 4px solid #fff; box-shadow: 8px 8px 0 0 #000; }
    .sketch-border { border: 2px solid currentColor; border-radius: 255px 15px 225px 15px/15px 225px 15px 255px; }
    .sketch-underline {
      background-image: linear-gradient(120deg, #A62116 0%, #A62116 100%);
      background-repeat: no-repeat;
      background-size: 100% 0.2em;
      background-position: 0 88%;
    }
    .skew-1 { transform: rotate(-1deg); }
    .skew-2 { transform: rotate(1.5deg); }
  </style>

  {% block head_extra %}{% endblock %}
</head>
<body class="bg-background text-on-background font-body selection:bg-accent-red selection:text-white overflow-x-hidden">
<div class="fixed inset-0 grain-overlay z-50"></div>

{% block header %}
<header class="flex justify-between items-center w-full px-6 py-4 bg-background border-b-4 border-primary sticky top-0 z-[60]">
  <a href="{{ url_for('public.home') }}" class="flex items-center gap-4">
    <div class="font-hand text-3xl font-bold tracking-tight text-primary uppercase">The Grog Blossoms</div>
  </a>
  <nav class="hidden md:flex gap-6 items-center">
    <a href="{{ url_for('public.log_index') }}" class="text-on-surface-variant hover:text-accent-red font-mono text-xs uppercase">Ship's Log</a>
    <a href="{{ url_for('public.manifest') }}" class="text-on-surface-variant hover:text-accent-amber font-mono text-xs uppercase">Manifest</a>
    <a href="{{ url_for('public.booty') }}" class="text-on-surface-variant hover:text-accent-amber font-mono text-xs uppercase">Booty</a>
    <a href="{{ url_for('public.crew') }}" class="text-on-surface-variant hover:text-accent-amber font-mono text-xs uppercase">Crew</a>
    <a href="{{ url_for('public.crows_nest') }}" class="text-on-surface-variant hover:text-accent-amber font-mono text-xs uppercase">Crow's Nest</a>
  </nav>
</header>
{% endblock %}

<main class="relative pb-24 md:pb-12">
  {% block content %}{% endblock %}
</main>

<footer class="w-full py-8 px-6 flex flex-col md:flex-row justify-between items-center gap-4 bg-surface-container-lowest border-t-2 border-dashed border-accent-amber">
  <div class="font-hand text-lg text-accent-amber">© 2026 THE GROG BLOSSOMS. NO QUARTER GIVEN.</div>
</footer>

</body>
</html>
```

- [ ] **Step 4: Add a placeholder home view to verify rendering**

Append to `app/__init__.py` just before `return app`:

```python
    from .blueprints.public import bp as public_bp
    app.register_blueprint(public_bp)
```

Create `app/blueprints/__init__.py` (empty):

```python
```

Create `app/blueprints/public/__init__.py`:

```python
from .views import bp

__all__ = ["bp"]
```

Create `app/blueprints/public/views.py`:

```python
from flask import Blueprint, render_template

bp = Blueprint("public", __name__)


@bp.get("/")
def home():
    return render_template("public/home.html")


@bp.get("/log")
def log_index():
    return "Ship's Log (placeholder)"


@bp.get("/manifest")
def manifest():
    return "Manifest (placeholder)"


@bp.get("/crew")
def crew():
    return "Crew (placeholder)"


@bp.get("/booty")
def booty():
    return "Booty (placeholder)"


@bp.get("/crows-nest")
def crows_nest():
    return "Crow's Nest (placeholder)"
```

Create `app/templates/public/home.html`:

```html
{% extends "base.html" %}
{% block content %}
  <section class="px-6 py-12">
    <h1 class="font-hand text-6xl text-primary sketch-underline inline-block">Hoist the Mainsail!</h1>
    <p class="mt-6 font-body text-on-surface-variant max-w-xl">The site lives. The grog flows. Real content forthcoming.</p>
  </section>
{% endblock %}
```

- [ ] **Step 5: Add a smoke test**

Create `tests/test_public_smoke.py`:

```python
def test_home_renders(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Hoist the Mainsail" in response.data
```

- [ ] **Step 6: Run tests**

```bash
pytest -v
```

Expected: 3 passed.

- [ ] **Step 7: Commit**

```bash
git add app/templates/ app/blueprints/ scripts/ Makefile tests/test_public_smoke.py
git commit -m "feat: base template + design sync + home placeholder"
```

---

### Task 0.4: mm-* fleet conformance files

**Files:**
- Create: `mm-meta.yml`
- Create: `MM_ARCHITECTURE.md`
- Create: `CLAUDE.md`

- [ ] **Step 1: Write `mm-meta.yml`**

```yaml
name: mm-grogblossoms
kind: web-app
brand: grog-blossoms
visual-system: tavern-noir
public-url: https://grogblossoms.com
runtime: python3.12
deploys-to: mycelium
exposure: cloudflare-tunnel
depends-on:
  - mm-sporekles  # CSS tokens + asset CDN
notes: |
  Self-hosted Flask CMS + public site. SQLite, single-container app +
  cloudflared sidecar. Images push to mm-sporekles' design-assets bucket
  under the grogblossoms/ prefix (uploader IAM TBD).
```

- [ ] **Step 2: Write `MM_ARCHITECTURE.md`**

```markdown
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
```

- [ ] **Step 3: Write `CLAUDE.md`**

```markdown
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
```

- [ ] **Step 4: Commit**

```bash
git add mm-meta.yml MM_ARCHITECTURE.md CLAUDE.md
git commit -m "chore: mm-* fleet conformance files"
```

---

### Task 0.5: Vendor spec doc + plan into repo

**Files:**
- Create: `docs/specs/2026-05-20-mm-grogblossoms-design.md` (copy)
- Create: `docs/plans/2026-05-20-mm-grogblossoms.md` (copy)

- [ ] **Step 1: Copy the spec and plan from gb-website**

```bash
mkdir -p docs/specs docs/plans
cp ~/projects/gb-website/docs/superpowers/specs/2026-05-20-mm-grogblossoms-design.md docs/specs/
cp ~/projects/gb-website/docs/superpowers/plans/2026-05-20-mm-grogblossoms.md docs/plans/
```

- [ ] **Step 2: Commit**

```bash
git add docs/
git commit -m "docs: vendor spec and implementation plan"
```

---

## Phase 1 — Auth (OIDC + admin gate)

### Task 1.1: User model + Flask-Login wiring

**Files:**
- Create: `app/models.py` (User model only this task)
- Modify: `app/__init__.py` (register login_manager user_loader)
- Test: `tests/test_auth.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_auth.py`:

```python
import pytest
from app.extensions import db
from app.models import User


def test_user_creation_persists(app):
    with app.app_context():
        user = User(
            oidc_sub="abc-123",
            email="chris@example.test",
            display_name="Chris",
            groups_json='["gb-developer"]',
        )
        db.session.add(user)
        db.session.commit()
        fetched = db.session.get(User, user.id)
        assert fetched is not None
        assert fetched.email == "chris@example.test"
        assert "gb-developer" in fetched.groups


def test_user_groups_property_parses_json(app):
    with app.app_context():
        user = User(oidc_sub="x", email="x@y", display_name="x", groups_json='["a","b"]')
        assert user.groups == ["a", "b"]


def test_user_in_group(app):
    with app.app_context():
        user = User(oidc_sub="x", email="x@y", display_name="x", groups_json='["gb-developer"]')
        assert user.in_group("gb-developer") is True
        assert user.in_group("admin") is False
```

- [ ] **Step 2: Run test, confirm failure**

```bash
pytest tests/test_auth.py -v
```

Expected: `ImportError: cannot import name 'User'`.

- [ ] **Step 3: Write `app/models.py`**

```python
"""SQLAlchemy 2.0 typed declarative models."""
from __future__ import annotations

import json
from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    oidc_sub: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    groups_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    @property
    def groups(self) -> list[str]:
        try:
            return json.loads(self.groups_json or "[]")
        except json.JSONDecodeError:
            return []

    @groups.setter
    def groups(self, value: list[str]) -> None:
        self.groups_json = json.dumps(value)

    def in_group(self, name: str) -> bool:
        return name in self.groups
```

- [ ] **Step 4: Wire `user_loader` in `app/__init__.py`**

Add to `app/__init__.py` after `login_manager.init_app(app)`:

```python
    from .models import User

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id))

    login_manager.login_view = "auth.login"
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_auth.py -v
```

Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add app/models.py app/__init__.py tests/test_auth.py
git commit -m "feat: User model with OIDC sub + groups"
```

---

### Task 1.2: Alembic init + initial migration

**Files:**
- Create: `migrations/` (via `flask db init`)
- Create: `migrations/versions/<hash>_initial_users.py`

- [ ] **Step 1: Initialize Alembic**

```bash
flask --app app db init
```

Edit `migrations/env.py` to import the app:

```python
# Near the top, after existing imports:
from app import create_app
from app.extensions import db as _db

flask_app = create_app(config_name="development")
flask_app.app_context().push()
target_metadata = _db.metadata
```

Remove or comment any pre-existing `target_metadata = None` line that conflicts.

- [ ] **Step 2: Generate initial migration**

```bash
flask --app app db migrate -m "initial users table"
```

- [ ] **Step 3: Apply locally and verify**

```bash
flask --app app db upgrade
sqlite3 grogblossoms.db ".schema users"
```

Expected output includes `CREATE TABLE users` with `oidc_sub`, `email`, `groups_json`, etc.

- [ ] **Step 4: Commit**

```bash
git add migrations/
git commit -m "chore: alembic init + users migration"
```

---

### Task 1.3: OIDC auth blueprint

**Files:**
- Create: `app/blueprints/auth/__init__.py`
- Create: `app/blueprints/auth/views.py`
- Modify: `app/__init__.py` (register oauth client + auth bp)
- Test: extends `tests/test_auth.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_auth.py`:

```python
from unittest.mock import patch


def test_login_redirects_to_oidc_provider(client):
    response = client.get("/auth/login")
    assert response.status_code == 302
    # Authlib redirects to the discovery-derived authorize endpoint
    assert "redirect_uri" in response.location or response.location.startswith("http")


def test_logout_clears_session(client, app):
    with client.session_transaction() as sess:
        sess["_user_id"] = "1"
    response = client.get("/auth/logout", follow_redirects=False)
    assert response.status_code == 302
    with client.session_transaction() as sess:
        assert "_user_id" not in sess


def test_oidc_callback_creates_user_and_logs_in(client, app):
    fake_userinfo = {
        "sub": "fa-user-001",
        "email": "chris@example.test",
        "name": "Chris O.",
        "groups": ["gb-developer", "other"],
    }
    fake_token = {"userinfo": fake_userinfo}

    with patch("app.blueprints.auth.views._fetch_token", return_value=fake_token):
        response = client.get("/auth/oidc/callback?code=fake&state=fake")
        assert response.status_code in (302, 303)

    from app.models import User
    with app.app_context():
        user = User.query.filter_by(oidc_sub="fa-user-001").one_or_none()
        assert user is not None
        assert user.email == "chris@example.test"
        assert "gb-developer" in user.groups


def test_oidc_callback_rejects_user_without_required_group(client, app):
    fake_userinfo = {
        "sub": "fa-user-002",
        "email": "norights@example.test",
        "name": "No Rights",
        "groups": ["other"],
    }
    fake_token = {"userinfo": fake_userinfo}

    with patch("app.blueprints.auth.views._fetch_token", return_value=fake_token):
        response = client.get("/auth/oidc/callback?code=fake&state=fake")
        assert response.status_code == 403
```

- [ ] **Step 2: Run tests, confirm failure**

```bash
pytest tests/test_auth.py -v
```

Expected: 4 new tests fail (404 or import error).

- [ ] **Step 3: Register OIDC client in `app/__init__.py`**

Add inside `create_app()`, after `oauth.init_app(app)`:

```python
    if app.config.get("OIDC_DISCOVERY_URL"):
        oauth.register(
            name="fa",
            client_id=app.config["OIDC_CLIENT_ID"],
            client_secret=app.config["OIDC_CLIENT_SECRET"],
            server_metadata_url=app.config["OIDC_DISCOVERY_URL"],
            client_kwargs={"scope": "openid email profile groups"},
        )

    from .blueprints.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")
```

- [ ] **Step 4: Write `app/blueprints/auth/__init__.py`**

```python
from .views import bp

__all__ = ["bp"]
```

- [ ] **Step 5: Write `app/blueprints/auth/views.py`**

```python
from datetime import datetime
from urllib.parse import urlparse

from flask import (
    Blueprint, abort, current_app, redirect, render_template, request,
    session, url_for,
)
from flask_login import login_required, login_user, logout_user

from app.extensions import db, oauth
from app.models import User

bp = Blueprint("auth", __name__)


@bp.get("/login")
def login():
    redirect_uri = url_for("auth.oidc_callback", _external=True)
    next_url = request.args.get("next")
    if next_url and _is_safe_next(next_url):
        session["post_login_next"] = next_url
    return oauth.fa.authorize_redirect(redirect_uri)


@bp.get("/oidc/callback")
def oidc_callback():
    token = _fetch_token()
    userinfo = token.get("userinfo") or oauth.fa.userinfo(token=token)
    required_group = current_app.config.get("OIDC_GROUP_REQUIRED", "gb-developer")
    groups = userinfo.get("groups") or []

    if required_group not in groups:
        return render_template("auth/forbidden.html", required=required_group), 403

    sub = userinfo["sub"]
    user = User.query.filter_by(oidc_sub=sub).one_or_none()
    if user is None:
        user = User(oidc_sub=sub, email=userinfo.get("email", ""),
                    display_name=userinfo.get("name", userinfo.get("email", "")))
        db.session.add(user)
    user.email = userinfo.get("email", user.email)
    user.display_name = userinfo.get("name", user.display_name)
    user.groups = list(groups)
    user.last_login_at = datetime.utcnow()
    db.session.commit()

    login_user(user)
    next_url = session.pop("post_login_next", None) or url_for("admin.dashboard")
    return redirect(next_url)


@bp.get("/logout")
def logout():
    # Idempotent: don't require an active login (stale-session users must be
    # able to log out). logout_user() is a no-op when anonymous; the explicit
    # session.pop guarantees the user_id marker is cleared in either case.
    logout_user()
    session.pop("_user_id", None)
    return redirect(url_for("public.home"))


def _fetch_token():
    """Wrapped so tests can monkeypatch this single seam."""
    return oauth.fa.authorize_access_token()


def _is_safe_next(target: str) -> bool:
    parsed = urlparse(target)
    return not parsed.netloc and parsed.path.startswith("/")
```

- [ ] **Step 6: Add the forbidden template**

Create `app/templates/auth/forbidden.html`:

```html
{% extends "base.html" %}
{% block title %}Crew Only — The Grog Blossoms{% endblock %}
{% block content %}
  <section class="px-6 py-24 max-w-2xl mx-auto">
    <h1 class="font-hand text-6xl text-accent-red sketch-underline inline-block">Crew Only</h1>
    <p class="mt-8 font-body-lg text-on-surface-variant">
      Yer not on the manifest, friend. Required group: <code class="font-mono text-accent-amber">{{ required }}</code>.
    </p>
    <a href="{{ url_for('public.home') }}" class="inline-block mt-12 px-6 py-3 bg-accent-red text-white font-hand uppercase">Back to Port</a>
  </section>
{% endblock %}
```

- [ ] **Step 7: Stub admin dashboard so the redirect in callback resolves**

Append to `app/__init__.py` inside `create_app()`:

```python
    from .blueprints.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix="/admin")
```

Create `app/blueprints/admin/__init__.py`:

```python
from .views import bp

__all__ = ["bp"]
```

Create `app/blueprints/admin/views.py`:

```python
from flask import Blueprint, render_template
from flask_login import login_required

bp = Blueprint("admin", __name__)


@bp.get("/")
@login_required
def dashboard():
    return render_template("admin/dashboard.html")
```

Create `app/templates/admin/base.html`:

```html
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="utf-8">
  <title>{% block title %}Admin — Grog Blossoms{% endblock %}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>body { background:#131313; color:#e2e2e2; font-family: ui-sans-serif, system-ui; }</style>
</head>
<body class="min-h-screen">
  <header class="border-b-2 border-white/20 px-6 py-4 flex justify-between items-center">
    <a href="{{ url_for('admin.dashboard') }}" class="text-xl font-bold tracking-tight">⚓ ADMIN — GROG BLOSSOMS</a>
    <a href="{{ url_for('auth.logout') }}" class="text-sm uppercase tracking-widest border border-white/40 px-3 py-1 hover:bg-white hover:text-black">Logout</a>
  </header>
  <main class="px-6 py-8 max-w-6xl mx-auto">
    {% block content %}{% endblock %}
  </main>
</body>
</html>
```

Create `app/templates/admin/dashboard.html`:

```html
{% extends "admin/base.html" %}
{% block content %}
  <h1 class="text-3xl mb-6">Dashboard</h1>
  <p class="text-on-surface-variant">Content modules will appear here as Phase 3 progresses.</p>
{% endblock %}
```

- [ ] **Step 8: Run tests**

```bash
pytest tests/test_auth.py -v
```

Expected: 7 passed (3 from Task 1.1 + 4 new). If login redirect test fails because the OAuth client isn't registered in testing, adjust the test to mock `oauth.fa.authorize_redirect` similarly.

- [ ] **Step 9: Commit**

```bash
git add app/blueprints/auth/ app/blueprints/admin/ app/templates/auth/ app/templates/admin/ app/__init__.py tests/test_auth.py
git commit -m "feat: OIDC auth flow + admin scaffold"
```

---

### Task 1.4: `require_group` decorator + admin gate test

**Files:**
- Modify: `app/blueprints/admin/__init__.py` — add decorator
- Modify: `app/blueprints/admin/views.py` — apply decorator
- Test: `tests/test_admin_gate.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_admin_gate.py`:

```python
from flask_login import login_user
from app.models import User
from app.extensions import db


def _make_user(app, groups: list[str]) -> int:
    with app.app_context():
        user = User(oidc_sub=f"sub-{groups}", email="x@y", display_name="X")
        user.groups = groups
        db.session.add(user)
        db.session.commit()
        return user.id


def test_admin_redirects_anonymous_to_login(client):
    response = client.get("/admin/", follow_redirects=False)
    assert response.status_code == 302
    assert "/auth/login" in response.location


def test_admin_denies_user_without_required_group(client, app):
    uid = _make_user(app, ["other"])
    with client.session_transaction() as sess:
        sess["_user_id"] = str(uid)
        sess["_fresh"] = True
    response = client.get("/admin/")
    assert response.status_code == 403


def test_admin_allows_user_with_required_group(client, app):
    uid = _make_user(app, ["gb-developer"])
    with client.session_transaction() as sess:
        sess["_user_id"] = str(uid)
        sess["_fresh"] = True
    response = client.get("/admin/")
    assert response.status_code == 200
```

- [ ] **Step 2: Run tests, confirm failure**

```bash
pytest tests/test_admin_gate.py -v
```

Expected: middle test fails — no group enforcement yet.

- [ ] **Step 3: Add `require_group` decorator**

Replace `app/blueprints/admin/__init__.py`:

```python
from functools import wraps
from flask import abort, current_app, render_template
from flask_login import current_user

from .views import bp


def require_admin_group(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        required = current_app.config.get("OIDC_GROUP_REQUIRED", "gb-developer")
        if not current_user.is_authenticated:
            from flask import redirect, request, url_for
            return redirect(url_for("auth.login", next=request.path))
        if not current_user.in_group(required):
            return render_template("auth/forbidden.html", required=required), 403
        return view(*args, **kwargs)
    return wrapper


# Apply decorator at blueprint level via before_request hook:
@bp.before_request
def _gate():
    # Defer to the per-view login_required + custom check for clarity.
    pass


__all__ = ["bp", "require_admin_group"]
```

- [ ] **Step 4: Apply decorator on dashboard view**

Replace `app/blueprints/admin/views.py`:

```python
from functools import wraps

from flask import Blueprint, render_template

bp = Blueprint("admin", __name__)


def _require_group(view):
    """Late-binding wrapper: resolves require_admin_group at request time
    so it works despite the import cycle (views imports __init__ which imports views)."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        from . import require_admin_group
        return require_admin_group(view)(*args, **kwargs)
    return wrapper


@bp.get("/")
@_require_group
def dashboard():
    return render_template("admin/dashboard.html")
```

> **Why the wrapper-inside-wrapper:** `_require_group` is invoked at *decoration time* (import time). At that moment `__init__.py` is partly loaded (the `from .views import bp` line is mid-execution) so `require_admin_group` is not yet bound. The inner `wrapper` defers the lookup to *request time*, when `__init__.py` has finished loading. Don't simplify this to a single-layer `from . import require_admin_group` inside `_require_group` — that fires at decoration time and raises `ImportError`.

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_admin_gate.py -v
```

Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add app/blueprints/admin/ tests/test_admin_gate.py
git commit -m "feat: gb-developer group enforced on /admin"
```

---

## Phase 2 — Data Models

### Task 2.1: Define all content models

Add every content model from the spec to `app/models.py`. This is one large task because the models are short and share enums/helpers.

**Files:**
- Modify: `app/models.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_models.py`:

```python
from datetime import datetime, timedelta

import pytest
from app.extensions import db
from app.models import (
    Asset, Post, CrewMember, TourDate, Gallery, GalleryImage,
    MusicTrack, MerchItem, PressAsset, Inquiry, Scuttlebutt, SiteSettings,
)


def test_asset_creates(app):
    with app.app_context():
        a = Asset(
            key="grogblossoms/img/2026/foo.jpg",
            url="https://design-assets.musicalmycology.org/grogblossoms/img/2026/foo.jpg",
            filename="foo.jpg", content_type="image/jpeg", size_bytes=12345,
        )
        db.session.add(a); db.session.commit()
        assert a.id is not None


def test_post_blocks_default_to_empty_list(app):
    with app.app_context():
        p = Post(slug="hello", title="Hello", author_name="Chris", excerpt="")
        db.session.add(p); db.session.commit()
        assert p.blocks == []


def test_post_published_predicate(app):
    with app.app_context():
        published = Post(slug="a", title="A", author_name="x", excerpt="",
                         published_at=datetime.utcnow() - timedelta(days=1))
        draft = Post(slug="b", title="B", author_name="x", excerpt="")
        future = Post(slug="c", title="C", author_name="x", excerpt="",
                      published_at=datetime.utcnow() + timedelta(days=1))
        for p in (published, draft, future):
            db.session.add(p)
        db.session.commit()
        assert published.is_live() is True
        assert draft.is_live() is False
        assert future.is_live() is False


def test_crew_member_tilt_enum(app):
    with app.app_context():
        c = CrewMember(slug="siren", name="The Siren", role="Fiddle",
                       portrait_url="", quote="", entry_no="002",
                       tilt="left", accent="white", sort_order=0)
        db.session.add(c); db.session.commit()
        assert c.tilt == "left"


def test_tour_date_status_filter(app):
    with app.app_context():
        for status in ("confirmed", "tentative", "past"):
            db.session.add(TourDate(
                event_name=f"E-{status}", venue="V", city="C", state="CA",
                starts_at=datetime.utcnow(), status=status,
            ))
        db.session.commit()
        live = TourDate.query.filter(TourDate.status.in_(("confirmed", "tentative"))).all()
        assert len(live) == 2


def test_gallery_with_images(app):
    with app.app_context():
        g = Gallery(slug="gigs-2026", title="Gigs 2026", description="",
                    cover_image_url="", sort_order=0)
        db.session.add(g); db.session.commit()
        for i in range(3):
            db.session.add(GalleryImage(
                gallery_id=g.id, image_url=f"x{i}", caption=f"c{i}",
                alt_text=f"a{i}", sort_order=i,
            ))
        db.session.commit()
        fresh = db.session.get(Gallery, g.id)
        assert len(fresh.images) == 3
        assert [im.sort_order for im in fresh.images] == [0, 1, 2]


def test_music_track_minimal(app):
    with app.app_context():
        t = MusicTrack(title="Heave Ho", sort_order=0)
        db.session.add(t); db.session.commit()
        assert t.id is not None


def test_merch_item_in_stock_defaults_true(app):
    with app.app_context():
        m = MerchItem(name="Tee", description="", image_url="",
                      price_display="$25", external_url="https://x", sort_order=0)
        db.session.add(m); db.session.commit()
        assert m.in_stock is True


def test_press_asset_kind_enum(app):
    with app.app_context():
        p = PressAsset(title="Bio", file_url="https://x", kind="bio",
                       description="", sort_order=0)
        db.session.add(p); db.session.commit()
        assert p.kind == "bio"


def test_inquiry_defaults(app):
    with app.app_context():
        i = Inquiry(kind="booking", from_name="X", email="x@y",
                    message="hello")
        db.session.add(i); db.session.commit()
        assert i.status == "new"
        assert i.created_at is not None


def test_scuttlebutt_expiry(app):
    with app.app_context():
        live = Scuttlebutt(text="now", accent="amber", sort_order=0)
        expired = Scuttlebutt(text="old", accent="red", sort_order=1,
                              expires_at=datetime.utcnow() - timedelta(days=1))
        future = Scuttlebutt(text="future", accent="white", sort_order=2,
                             expires_at=datetime.utcnow() + timedelta(hours=1))
        for s in (live, expired, future):
            db.session.add(s)
        db.session.commit()
        assert live.is_visible() is True
        assert expired.is_visible() is False
        assert future.is_visible() is True


def test_site_settings_singleton_get_or_create(app):
    with app.app_context():
        s = SiteSettings.get_or_create()
        s2 = SiteSettings.get_or_create()
        assert s.id == 1 and s2.id == 1
        assert SiteSettings.query.count() == 1
```

- [ ] **Step 2: Run tests, confirm failure**

```bash
pytest tests/test_models.py -v
```

Expected: import errors for the new model names.

- [ ] **Step 3: Append all models to `app/models.py`**

Append after the existing `User` model:

```python
from datetime import datetime, date
from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Integer, JSON, String, Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Asset(db.Model):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    url: Mapped[str] = mapped_column(String(1024))
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(127), default="application/octet-stream")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    caption: Mapped[str | None] = mapped_column(String(512), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Post(db.Model):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    author_name: Mapped[str] = mapped_column(String(255), default="The Crew")
    hero_image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    excerpt: Mapped[str] = mapped_column(Text, default="")
    body_md: Mapped[str] = mapped_column(Text, default="")  # Phase 3 uses this; Phase 6 migrates to blocks
    blocks: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def is_live(self) -> bool:
        return self.published_at is not None and self.published_at <= datetime.utcnow()


class CrewMember(db.Model):
    __tablename__ = "crew_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(255))
    portrait_url: Mapped[str] = mapped_column(String(1024), default="")
    quote: Mapped[str] = mapped_column(Text, default="")
    bio: Mapped[str] = mapped_column(Text, default="")
    entry_no: Mapped[str] = mapped_column(String(16), default="")
    tilt: Mapped[str] = mapped_column(String(8), default="left")   # 'left' | 'right'
    accent: Mapped[str] = mapped_column(String(8), default="white")  # 'white' | 'amber' | 'red'
    sort_order: Mapped[int] = mapped_column(Integer, default=0, index=True)


class TourDate(db.Model):
    __tablename__ = "tour_dates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_name: Mapped[str] = mapped_column(String(255))
    venue: Mapped[str] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(255))
    state: Mapped[str] = mapped_column(String(8))
    starts_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ticket_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="confirmed", index=True)  # confirmed|tentative|past
    notes: Mapped[str] = mapped_column(Text, default="")


class Gallery(db.Model):
    __tablename__ = "galleries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    cover_image_url: Mapped[str] = mapped_column(String(1024), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    images: Mapped[list["GalleryImage"]] = relationship(
        back_populates="gallery",
        cascade="all, delete-orphan",
        order_by="GalleryImage.sort_order",
    )


class GalleryImage(db.Model):
    __tablename__ = "gallery_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gallery_id: Mapped[int] = mapped_column(ForeignKey("galleries.id", ondelete="CASCADE"))
    image_url: Mapped[str] = mapped_column(String(1024))
    caption: Mapped[str] = mapped_column(String(512), default="")
    alt_text: Mapped[str] = mapped_column(String(512), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    gallery: Mapped["Gallery"] = relationship(back_populates="images")


class MusicTrack(db.Model):
    __tablename__ = "music_tracks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    release_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    audio_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    bandcamp_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    spotify_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    apple_music_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    duration_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    release_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    lyrics: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class MerchItem(db.Model):
    __tablename__ = "merch_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str] = mapped_column(String(1024), default="")
    price_display: Mapped[str] = mapped_column(String(32), default="")
    external_url: Mapped[str] = mapped_column(String(1024), default="")
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class PressAsset(db.Model):
    __tablename__ = "press_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    file_url: Mapped[str] = mapped_column(String(1024))
    kind: Mapped[str] = mapped_column(String(16), default="other")
    description: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Inquiry(db.Model):
    __tablename__ = "inquiries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(16), default="general", index=True)
    from_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    venue: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="new", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class Scuttlebutt(db.Model):
    __tablename__ = "scuttlebutts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    link_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    accent: Mapped[str] = mapped_column(String(8), default="amber")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def is_visible(self) -> bool:
        return self.expires_at is None or self.expires_at > datetime.utcnow()


class SiteSettings(db.Model):
    __tablename__ = "site_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hero_quote: Mapped[str] = mapped_column(Text, default="")
    hero_image_url: Mapped[str] = mapped_column(String(1024), default="")
    logo_url: Mapped[str] = mapped_column(String(1024), default="")
    contact_email: Mapped[str] = mapped_column(String(255), default="")
    social_links: Mapped[list] = mapped_column(JSON, default=list)
    footer_text: Mapped[str] = mapped_column(Text, default="© 2026 THE GROG BLOSSOMS. NO QUARTER GIVEN.")
    ports_visited: Mapped[int] = mapped_column(Integer, default=0)
    grog_pints: Mapped[str] = mapped_column(String(32), default="0")

    @classmethod
    def get_or_create(cls) -> "SiteSettings":
        instance = db.session.get(cls, 1)
        if instance is None:
            instance = cls(id=1)
            db.session.add(instance)
            db.session.commit()
        return instance
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_models.py -v
```

Expected: 12 passed.

- [ ] **Step 5: Commit**

```bash
git add app/models.py tests/test_models.py
git commit -m "feat: content models (Asset, Post, Crew, Tour, Gallery, Music, Merch, Press, Inquiry, Scuttlebutt, Settings)"
```

---

### Task 2.2: Generate + apply Alembic migration for content models

**Files:**
- Create: `migrations/versions/<hash>_content_models.py`

- [ ] **Step 1: Generate migration**

```bash
flask --app app db migrate -m "content models"
```

- [ ] **Step 2: Inspect the migration file**

Open the new file under `migrations/versions/`. Verify it contains `op.create_table('posts', …)`, `op.create_table('crew_members', …)`, etc. for every model in Task 2.1. Verify no spurious `op.drop_table` calls (those would indicate a bad autogenerate run — likely from an extra metadata import).

- [ ] **Step 3: Apply**

```bash
flask --app app db upgrade
sqlite3 grogblossoms.db ".tables"
```

Expected: table list includes `users posts crew_members tour_dates galleries gallery_images music_tracks merch_items press_assets inquiries scuttlebutts site_settings assets alembic_version`.

- [ ] **Step 4: Commit**

```bash
git add migrations/versions/
git commit -m "chore: migration for content models"
```

---

## Phase 3 — Admin CRUD

Phase 3 uses a tiny generic CRUD helper so each resource only needs to define a Form and register routes. Block editor for Posts is deferred to Phase 6 — for now Posts use a `body_md` Markdown field.

### Task 3.1: Generic CRUD helper + admin layout

**Files:**
- Create: `app/blueprints/admin/_crud.py`
- Create: `app/templates/admin/_list.html`
- Create: `app/templates/admin/_form.html`
- Modify: `app/templates/admin/base.html` — add sidebar nav

- [ ] **Step 1: Write `_crud.py`**

```python
"""Tiny generic CRUD factory.

Each resource module calls register_crud() with:
  - bp           : the admin blueprint
  - prefix       : URL prefix and template tag, e.g. 'posts'
  - model        : SQLAlchemy model
  - form_cls     : WTForms class
  - list_cols    : list of (header, getter) for the list table
  - order_by     : ordering for the list query
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from flask import flash, redirect, render_template, request, url_for

from app.blueprints.admin import require_admin_group
from app.extensions import db


def register_crud(
    bp,
    *,
    prefix: str,
    label: str,
    model: type,
    form_cls: type,
    list_cols: Iterable[tuple[str, Callable[[Any], Any]]],
    order_by=None,
    after_save: Callable[[Any], None] | None = None,
) -> None:
    list_cols = list(list_cols)

    @bp.get(f"/{prefix}/", endpoint=f"{prefix}_list")
    @require_admin_group
    def _list():
        q = model.query
        if order_by is not None:
            q = q.order_by(order_by)
        items = q.all()
        return render_template(
            "admin/_list.html",
            label=label, prefix=prefix, items=items, cols=list_cols,
        )

    @bp.route(f"/{prefix}/new", methods=("GET", "POST"), endpoint=f"{prefix}_new")
    @require_admin_group
    def _new():
        form = form_cls()
        if form.validate_on_submit():
            obj = model()
            form.populate_obj(obj)
            db.session.add(obj)
            db.session.commit()
            if after_save:
                after_save(obj)
            flash(f"{label} created.", "success")
            return redirect(url_for(f"admin.{prefix}_list"))
        return render_template("admin/_form.html",
                               label=label, prefix=prefix, form=form, mode="new")

    @bp.route(f"/{prefix}/<int:id>", methods=("GET", "POST"), endpoint=f"{prefix}_edit")
    @require_admin_group
    def _edit(id: int):
        obj = db.session.get(model, id) or _abort_404()
        form = form_cls(obj=obj)
        if form.validate_on_submit():
            form.populate_obj(obj)
            db.session.commit()
            if after_save:
                after_save(obj)
            flash(f"{label} updated.", "success")
            return redirect(url_for(f"admin.{prefix}_list"))
        return render_template("admin/_form.html",
                               label=label, prefix=prefix, form=form, mode="edit",
                               obj=obj)

    @bp.post(f"/{prefix}/<int:id>/delete", endpoint=f"{prefix}_delete")
    @require_admin_group
    def _delete(id: int):
        obj = db.session.get(model, id) or _abort_404()
        db.session.delete(obj)
        db.session.commit()
        flash(f"{label} deleted.", "success")
        return redirect(url_for(f"admin.{prefix}_list"))


def _abort_404():
    from flask import abort
    abort(404)
```

- [ ] **Step 2: Write `app/templates/admin/_list.html`**

```html
{% extends "admin/base.html" %}
{% block title %}{{ label }} — Admin{% endblock %}
{% block content %}
<div class="flex justify-between items-center mb-6">
  <h1 class="text-3xl">{{ label }}</h1>
  <a href="{{ url_for('admin.' ~ prefix ~ '_new') }}" class="px-4 py-2 bg-white text-black uppercase tracking-widest text-sm">+ New</a>
</div>

<table class="w-full text-left">
  <thead class="border-b border-white/20">
    <tr>
      {% for header, _ in cols %}<th class="py-2 px-3 text-xs uppercase tracking-widest text-white/60">{{ header }}</th>{% endfor %}
      <th></th>
    </tr>
  </thead>
  <tbody>
    {% for item in items %}
    <tr class="border-b border-white/10 hover:bg-white/5">
      {% for _, getter in cols %}
      <td class="py-3 px-3"><a href="{{ url_for('admin.' ~ prefix ~ '_edit', id=item.id) }}">{{ getter(item) }}</a></td>
      {% endfor %}
      <td class="py-3 px-3 text-right">
        <form action="{{ url_for('admin.' ~ prefix ~ '_delete', id=item.id) }}" method="post" onsubmit="return confirm('Delete?')" class="inline">
          <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
          <button class="text-red-400 text-xs uppercase">delete</button>
        </form>
      </td>
    </tr>
    {% else %}
    <tr><td colspan="{{ cols|length + 1 }}" class="py-8 text-center text-white/40">No entries yet.</td></tr>
    {% endfor %}
  </tbody>
</table>
{% endblock %}
```

- [ ] **Step 3: Write `app/templates/admin/_form.html`**

```html
{% extends "admin/base.html" %}
{% block title %}{{ mode|title }} {{ label }} — Admin{% endblock %}
{% block content %}
<h1 class="text-3xl mb-6">{{ mode|title }} {{ label }}</h1>

<form method="post" class="space-y-4 max-w-3xl">
  {{ form.hidden_tag() }}
  {% for field in form if field.name not in ('csrf_token',) %}
  <div>
    <label class="block text-xs uppercase tracking-widest text-white/60 mb-1">{{ field.label.text }}</label>
    {{ field(class_="w-full bg-black/40 border border-white/20 px-3 py-2 text-white font-mono") }}
    {% if field.errors %}
      <ul class="text-red-400 text-xs mt-1">
        {% for err in field.errors %}<li>{{ err }}</li>{% endfor %}
      </ul>
    {% endif %}
  </div>
  {% endfor %}

  <div class="flex gap-3">
    <button class="px-6 py-2 bg-white text-black uppercase tracking-widest">Save</button>
    <a href="{{ url_for('admin.' ~ prefix ~ '_list') }}" class="px-6 py-2 border border-white/40 uppercase tracking-widest">Cancel</a>
  </div>
</form>
{% endblock %}
```

- [ ] **Step 4: Update admin `base.html` with sidebar nav**

Replace `app/templates/admin/base.html`:

```html
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="utf-8">
  <title>{% block title %}Admin — Grog Blossoms{% endblock %}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>body { background:#131313; color:#e2e2e2; font-family: ui-sans-serif, system-ui; }</style>
</head>
<body class="min-h-screen flex">
  <aside class="w-56 border-r-2 border-white/20 p-4">
    <a href="{{ url_for('admin.dashboard') }}" class="block mb-6 text-lg font-bold tracking-tight">⚓ ADMIN</a>
    <nav class="space-y-1 text-sm">
      <a class="block py-1 text-white/70 hover:text-white" href="{{ url_for('admin.posts_list') }}">Ship's Log</a>
      <a class="block py-1 text-white/70 hover:text-white" href="{{ url_for('admin.crew_list') }}">Crew</a>
      <a class="block py-1 text-white/70 hover:text-white" href="{{ url_for('admin.tour_dates_list') }}">Tour Dates</a>
      <a class="block py-1 text-white/70 hover:text-white" href="{{ url_for('admin.galleries_list') }}">Galleries</a>
      <a class="block py-1 text-white/70 hover:text-white" href="{{ url_for('admin.music_list') }}">Music</a>
      <a class="block py-1 text-white/70 hover:text-white" href="{{ url_for('admin.merch_list') }}">Merch</a>
      <a class="block py-1 text-white/70 hover:text-white" href="{{ url_for('admin.press_list') }}">Press Assets</a>
      <a class="block py-1 text-white/70 hover:text-white" href="{{ url_for('admin.inquiries_list') }}">Inquiries</a>
      <a class="block py-1 text-white/70 hover:text-white" href="{{ url_for('admin.scuttlebutt_list') }}">Scuttlebutt</a>
      <a class="block py-1 text-white/70 hover:text-white" href="{{ url_for('admin.assets_list') }}">Media</a>
      <a class="block py-1 text-white/70 hover:text-white" href="{{ url_for('admin.settings') }}">Settings</a>
    </nav>
    <div class="mt-12 pt-4 border-t border-white/10">
      <a class="block text-xs uppercase tracking-widest text-white/40 hover:text-white" href="{{ url_for('auth.logout') }}">Logout</a>
    </div>
  </aside>
  <main class="flex-1 px-8 py-8">
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% for category, msg in messages %}
      <div class="mb-4 px-3 py-2 border border-{% if category == 'success' %}green{% else %}red{% endif %}-400 text-{% if category == 'success' %}green{% else %}red{% endif %}-200">{{ msg }}</div>
      {% endfor %}
    {% endwith %}
    {% block content %}{% endblock %}
  </main>
</body>
</html>
```

- [ ] **Step 5: Commit**

```bash
git add app/blueprints/admin/_crud.py app/templates/admin/
git commit -m "feat: generic admin CRUD + sidebar layout"
```

---

### Task 3.2: Posts admin (Markdown body for v1, blocks in Phase 6)

**Files:**
- Create: `app/blueprints/admin/posts.py`
- Modify: `app/blueprints/admin/__init__.py` — import module
- Test: `tests/test_admin_crud.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_admin_crud.py`:

```python
from app.extensions import db
from app.models import Post, User


def _login_as_admin(client, app):
    with app.app_context():
        u = User(oidc_sub="admin-1", email="a@b", display_name="A")
        u.groups = ["gb-developer"]
        db.session.add(u); db.session.commit()
        uid = u.id
    with client.session_transaction() as sess:
        sess["_user_id"] = str(uid)
        sess["_fresh"] = True


def test_post_list_empty(client, app):
    _login_as_admin(client, app)
    response = client.get("/admin/posts/")
    assert response.status_code == 200
    assert b"Ship" in response.data or b"Posts" in response.data


def test_post_create(client, app):
    _login_as_admin(client, app)
    response = client.post(
        "/admin/posts/new",
        data={
            "slug": "hello", "title": "Hello World",
            "author_name": "Chris", "excerpt": "first post",
            "body_md": "# Hi", "hero_image_url": "",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        assert Post.query.filter_by(slug="hello").one() is not None


def test_post_edit(client, app):
    with app.app_context():
        p = Post(slug="x", title="X", author_name="A", excerpt="")
        db.session.add(p); db.session.commit()
        pid = p.id
    _login_as_admin(client, app)
    response = client.post(
        f"/admin/posts/{pid}",
        data={"slug": "x", "title": "Updated",
              "author_name": "A", "excerpt": "", "body_md": "", "hero_image_url": ""},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        assert db.session.get(Post, pid).title == "Updated"


def test_post_delete(client, app):
    with app.app_context():
        p = Post(slug="z", title="Z", author_name="A", excerpt="")
        db.session.add(p); db.session.commit()
        pid = p.id
    _login_as_admin(client, app)
    response = client.post(f"/admin/posts/{pid}/delete", follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert db.session.get(Post, pid) is None
```

- [ ] **Step 2: Run tests, confirm failure**

```bash
pytest tests/test_admin_crud.py -v
```

Expected: 404s — routes not registered.

- [ ] **Step 3: Write `app/blueprints/admin/posts.py`**

```python
from flask_wtf import FlaskForm
from wtforms import DateTimeLocalField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, URL

from app.models import Post
from . import bp
from ._crud import register_crud


class PostForm(FlaskForm):
    slug = StringField("Slug", validators=[DataRequired(), Length(max=255)])
    title = StringField("Title", validators=[DataRequired(), Length(max=255)])
    author_name = StringField("Author", validators=[DataRequired(), Length(max=255)])
    published_at = DateTimeLocalField("Published at", validators=[Optional()], format="%Y-%m-%dT%H:%M")
    hero_image_url = StringField("Hero image URL", validators=[Optional(), URL()])
    excerpt = TextAreaField("Excerpt", validators=[Optional()])
    body_md = TextAreaField("Body (Markdown — block editor coming in Phase 6)", validators=[Optional()])


register_crud(
    bp,
    prefix="posts",
    label="Ship's Log Post",
    model=Post,
    form_cls=PostForm,
    list_cols=[
        ("Title", lambda p: p.title),
        ("Slug", lambda p: p.slug),
        ("Published", lambda p: p.published_at.strftime("%Y-%m-%d %H:%M") if p.published_at else "draft"),
    ],
    order_by=Post.created_at.desc(),
)
```

- [ ] **Step 4: Import the module so routes register**

Replace `app/blueprints/admin/__init__.py`:

```python
from functools import wraps
from flask import current_app, redirect, render_template, request, url_for
from flask_login import current_user

from .views import bp


def require_admin_group(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        required = current_app.config.get("OIDC_GROUP_REQUIRED", "gb-developer")
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login", next=request.path))
        if not current_user.in_group(required):
            return render_template("auth/forbidden.html", required=required), 403
        return view(*args, **kwargs)
    return wrapper


# Importing these registers routes on `bp`:
from . import posts  # noqa: E402,F401

__all__ = ["bp", "require_admin_group"]
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_admin_crud.py -v
```

Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add app/blueprints/admin/posts.py app/blueprints/admin/__init__.py tests/test_admin_crud.py
git commit -m "feat: posts admin CRUD"
```

---

### Task 3.3: Crew, Tour Dates, Music, Merch, Press, Scuttlebutt admin

Six small modules that all follow the Post pattern. Each defines a Form and calls `register_crud()`.

**Files:**
- Create: `app/blueprints/admin/crew.py`
- Create: `app/blueprints/admin/tour_dates.py`
- Create: `app/blueprints/admin/music.py`
- Create: `app/blueprints/admin/merch.py`
- Create: `app/blueprints/admin/press.py`
- Create: `app/blueprints/admin/scuttlebutt.py`
- Modify: `app/blueprints/admin/__init__.py` — import them

- [ ] **Step 1: Write `crew.py`**

```python
from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from app.models import CrewMember
from . import bp
from ._crud import register_crud


class CrewMemberForm(FlaskForm):
    slug = StringField("Slug", validators=[DataRequired(), Length(max=255)])
    name = StringField("Name", validators=[DataRequired()])
    role = StringField("Role", validators=[DataRequired()])
    portrait_url = StringField("Portrait URL", validators=[Optional()])
    quote = TextAreaField("Quote", validators=[Optional()])
    bio = TextAreaField("Bio", validators=[Optional()])
    entry_no = StringField("Entry #", validators=[Optional()])
    tilt = SelectField("Tilt", choices=[("left", "Left (-1°)"), ("right", "Right (+1°)")])
    accent = SelectField("Accent", choices=[("white", "White"), ("amber", "Amber"), ("red", "Red")])
    sort_order = IntegerField("Sort order", default=0)


register_crud(
    bp, prefix="crew", label="Crew Member",
    model=CrewMember, form_cls=CrewMemberForm,
    list_cols=[
        ("Name", lambda c: c.name),
        ("Role", lambda c: c.role),
        ("Entry #", lambda c: c.entry_no),
    ],
    order_by=CrewMember.sort_order,
)
```

- [ ] **Step 2: Write `tour_dates.py`**

```python
from flask_wtf import FlaskForm
from wtforms import DateTimeLocalField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, URL

from app.models import TourDate
from . import bp
from ._crud import register_crud


class TourDateForm(FlaskForm):
    event_name = StringField("Event", validators=[DataRequired()])
    venue = StringField("Venue", validators=[DataRequired()])
    city = StringField("City", validators=[DataRequired()])
    state = StringField("State", validators=[DataRequired(), Length(max=8)])
    starts_at = DateTimeLocalField("Starts at", validators=[DataRequired()], format="%Y-%m-%dT%H:%M")
    ends_at = DateTimeLocalField("Ends at", validators=[Optional()], format="%Y-%m-%dT%H:%M")
    ticket_url = StringField("Ticket URL", validators=[Optional(), URL()])
    status = SelectField("Status", choices=[("confirmed", "Confirmed"), ("tentative", "Tentative"), ("past", "Past")])
    notes = TextAreaField("Notes", validators=[Optional()])


register_crud(
    bp, prefix="tour_dates", label="Tour Date",
    model=TourDate, form_cls=TourDateForm,
    list_cols=[
        ("Event", lambda t: t.event_name),
        ("Where", lambda t: f"{t.venue}, {t.city} {t.state}"),
        ("Starts", lambda t: t.starts_at.strftime("%Y-%m-%d %H:%M")),
        ("Status", lambda t: t.status),
    ],
    order_by=TourDate.starts_at.desc(),
)
```

- [ ] **Step 3: Write `music.py`**

```python
from flask_wtf import FlaskForm
from wtforms import DateField, IntegerField, StringField, TextAreaField
from wtforms.validators import DataRequired, Optional, URL

from app.models import MusicTrack
from . import bp
from ._crud import register_crud


class MusicTrackForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    release_name = StringField("Release", validators=[Optional()])
    audio_url = StringField("Audio URL (CDN)", validators=[Optional(), URL()])
    bandcamp_url = StringField("Bandcamp URL", validators=[Optional(), URL()])
    spotify_url = StringField("Spotify URL", validators=[Optional(), URL()])
    apple_music_url = StringField("Apple Music URL", validators=[Optional(), URL()])
    duration_sec = IntegerField("Duration (sec)", validators=[Optional()])
    cover_url = StringField("Cover image URL", validators=[Optional(), URL()])
    release_date = DateField("Release date", validators=[Optional()])
    lyrics = TextAreaField("Lyrics", validators=[Optional()])
    sort_order = IntegerField("Sort order", default=0)


register_crud(
    bp, prefix="music", label="Music Track",
    model=MusicTrack, form_cls=MusicTrackForm,
    list_cols=[
        ("Title", lambda t: t.title),
        ("Release", lambda t: t.release_name or "—"),
        ("Date", lambda t: t.release_date.isoformat() if t.release_date else "—"),
    ],
    order_by=MusicTrack.sort_order,
)
```

- [ ] **Step 4: Write `merch.py`**

```python
from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, StringField, TextAreaField
from wtforms.validators import DataRequired, Optional, URL

from app.models import MerchItem
from . import bp
from ._crud import register_crud


class MerchItemForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[Optional()])
    image_url = StringField("Image URL (CDN)", validators=[Optional(), URL()])
    price_display = StringField('Price (display, e.g. "$25")', validators=[Optional()])
    external_url = StringField("Buy URL", validators=[DataRequired(), URL()])
    in_stock = BooleanField("In stock", default=True)
    sort_order = IntegerField("Sort order", default=0)


register_crud(
    bp, prefix="merch", label="Merch Item",
    model=MerchItem, form_cls=MerchItemForm,
    list_cols=[
        ("Name", lambda m: m.name),
        ("Price", lambda m: m.price_display),
        ("Stock", lambda m: "✓" if m.in_stock else "—"),
    ],
    order_by=MerchItem.sort_order,
)
```

- [ ] **Step 5: Write `press.py`**

```python
from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Optional, URL

from app.models import PressAsset
from . import bp
from ._crud import register_crud


class PressAssetForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    file_url = StringField("File URL (CDN)", validators=[DataRequired(), URL()])
    kind = SelectField("Kind", choices=[
        ("bio", "Bio"), ("logo", "Logo"), ("photo", "Photo"),
        ("rider", "Rider"), ("stage_plot", "Stage plot"),
        ("epk", "EPK"), ("other", "Other"),
    ])
    description = TextAreaField("Description", validators=[Optional()])
    sort_order = IntegerField("Sort order", default=0)


register_crud(
    bp, prefix="press", label="Press Asset",
    model=PressAsset, form_cls=PressAssetForm,
    list_cols=[
        ("Title", lambda p: p.title),
        ("Kind", lambda p: p.kind),
    ],
    order_by=PressAsset.sort_order,
)
```

- [ ] **Step 6: Write `scuttlebutt.py`**

```python
from flask_wtf import FlaskForm
from wtforms import DateTimeLocalField, IntegerField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Optional, URL

from app.models import Scuttlebutt
from . import bp
from ._crud import register_crud


class ScuttlebuttForm(FlaskForm):
    text = TextAreaField("Text", validators=[DataRequired()])
    link_url = StringField("Link URL", validators=[Optional(), URL()])
    accent = SelectField("Accent (mark)", choices=[
        ("amber", "Amber"), ("red", "Red"), ("white", "White"),
    ])
    sort_order = IntegerField("Sort order", default=0)
    expires_at = DateTimeLocalField("Expires at", validators=[Optional()], format="%Y-%m-%dT%H:%M")


register_crud(
    bp, prefix="scuttlebutt", label="Scuttlebutt",
    model=Scuttlebutt, form_cls=ScuttlebuttForm,
    list_cols=[
        ("Text", lambda s: (s.text[:60] + "…") if len(s.text) > 60 else s.text),
        ("Accent", lambda s: s.accent),
        ("Expires", lambda s: s.expires_at.strftime("%Y-%m-%d") if s.expires_at else "—"),
    ],
    order_by=Scuttlebutt.sort_order,
)
```

- [ ] **Step 7: Wire imports in admin `__init__.py`**

In `app/blueprints/admin/__init__.py`, update the import line:

```python
from . import posts, crew, tour_dates, music, merch, press, scuttlebutt  # noqa: E402,F401
```

- [ ] **Step 8: Smoke test all routes**

Append to `tests/test_admin_crud.py`:

```python
import pytest


@pytest.mark.parametrize("prefix", ["crew", "tour_dates", "music", "merch", "press", "scuttlebutt"])
def test_admin_list_route_renders(client, app, prefix):
    _login_as_admin(client, app)
    response = client.get(f"/admin/{prefix}/")
    assert response.status_code == 200


@pytest.mark.parametrize("prefix", ["crew", "tour_dates", "music", "merch", "press", "scuttlebutt"])
def test_admin_new_route_renders(client, app, prefix):
    _login_as_admin(client, app)
    response = client.get(f"/admin/{prefix}/new")
    assert response.status_code == 200
```

- [ ] **Step 9: Run tests**

```bash
pytest tests/test_admin_crud.py -v
```

Expected: all passed.

- [ ] **Step 10: Commit**

```bash
git add app/blueprints/admin/ tests/test_admin_crud.py
git commit -m "feat: admin CRUD for crew, tour, music, merch, press, scuttlebutt"
```

---

### Task 3.4: Gallery admin (with image management)

Galleries need a richer editor — list of images inline with reorder/remove. Generic CRUD won't fit; this gets a hand-rolled view.

**Files:**
- Create: `app/blueprints/admin/galleries.py`
- Create: `app/templates/admin/galleries_edit.html`
- Modify: `app/blueprints/admin/__init__.py`
- Test: `tests/test_admin_galleries.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_admin_galleries.py`:

```python
from app.extensions import db
from app.models import Gallery, GalleryImage, User


def _login(client, app):
    with app.app_context():
        u = User(oidc_sub="g-admin", email="a@b", display_name="A")
        u.groups = ["gb-developer"]
        db.session.add(u); db.session.commit()
        uid = u.id
    with client.session_transaction() as sess:
        sess["_user_id"] = str(uid); sess["_fresh"] = True


def test_gallery_create(client, app):
    _login(client, app)
    response = client.post("/admin/galleries/new", data={
        "slug": "g1", "title": "Gigs", "description": "",
        "cover_image_url": "", "sort_order": 0,
    }, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert Gallery.query.filter_by(slug="g1").one() is not None


def test_gallery_add_image(client, app):
    with app.app_context():
        g = Gallery(slug="g2", title="t", description="", cover_image_url="", sort_order=0)
        db.session.add(g); db.session.commit()
        gid = g.id
    _login(client, app)
    response = client.post(f"/admin/galleries/{gid}/images/add", data={
        "image_url": "https://cdn.example/x.jpg",
        "caption": "Pier", "alt_text": "Pier at dusk",
    }, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        g2 = db.session.get(Gallery, gid)
        assert len(g2.images) == 1
        assert g2.images[0].caption == "Pier"


def test_gallery_remove_image(client, app):
    with app.app_context():
        g = Gallery(slug="g3", title="t", description="", cover_image_url="", sort_order=0)
        db.session.add(g); db.session.commit()
        img = GalleryImage(gallery_id=g.id, image_url="x", caption="", alt_text="", sort_order=0)
        db.session.add(img); db.session.commit()
        gid, iid = g.id, img.id
    _login(client, app)
    response = client.post(f"/admin/galleries/{gid}/images/{iid}/delete", follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert db.session.get(GalleryImage, iid) is None
```

- [ ] **Step 2: Run tests, confirm failure**

```bash
pytest tests/test_admin_galleries.py -v
```

Expected: 404s.

- [ ] **Step 3: Write `app/blueprints/admin/galleries.py`**

```python
from flask import abort, flash, redirect, render_template, request, url_for
from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, TextAreaField
from wtforms.validators import DataRequired, Optional, URL

from app.extensions import db
from app.models import Gallery, GalleryImage
from . import bp, require_admin_group


class GalleryForm(FlaskForm):
    slug = StringField("Slug", validators=[DataRequired()])
    title = StringField("Title", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[Optional()])
    cover_image_url = StringField("Cover image URL (CDN)", validators=[Optional(), URL()])
    sort_order = IntegerField("Sort order", default=0)


class GalleryImageForm(FlaskForm):
    image_url = StringField("Image URL (CDN)", validators=[DataRequired(), URL()])
    caption = StringField("Caption", validators=[Optional()])
    alt_text = StringField("Alt text", validators=[Optional()])


@bp.get("/galleries/", endpoint="galleries_list")
@require_admin_group
def galleries_list():
    items = Gallery.query.order_by(Gallery.sort_order).all()
    return render_template(
        "admin/_list.html",
        label="Gallery", prefix="galleries", items=items,
        cols=[
            ("Title", lambda g: g.title),
            ("Slug", lambda g: g.slug),
            ("Images", lambda g: len(g.images)),
        ],
    )


@bp.route("/galleries/new", methods=("GET", "POST"), endpoint="galleries_new")
@require_admin_group
def galleries_new():
    form = GalleryForm()
    if form.validate_on_submit():
        g = Gallery()
        form.populate_obj(g)
        db.session.add(g); db.session.commit()
        flash("Gallery created.", "success")
        return redirect(url_for("admin.galleries_edit", id=g.id))
    return render_template("admin/_form.html", label="Gallery",
                           prefix="galleries", form=form, mode="new")


@bp.route("/galleries/<int:id>", methods=("GET", "POST"), endpoint="galleries_edit")
@require_admin_group
def galleries_edit(id: int):
    g = db.session.get(Gallery, id) or abort(404)
    form = GalleryForm(obj=g)
    image_form = GalleryImageForm()
    if request.method == "POST" and form.validate_on_submit():
        form.populate_obj(g)
        db.session.commit()
        flash("Gallery saved.", "success")
        return redirect(url_for("admin.galleries_edit", id=id))
    return render_template("admin/galleries_edit.html",
                           gallery=g, form=form, image_form=image_form)


@bp.post("/galleries/<int:id>/delete", endpoint="galleries_delete")
@require_admin_group
def galleries_delete(id: int):
    g = db.session.get(Gallery, id) or abort(404)
    db.session.delete(g); db.session.commit()
    flash("Gallery deleted.", "success")
    return redirect(url_for("admin.galleries_list"))


@bp.post("/galleries/<int:id>/images/add", endpoint="galleries_add_image")
@require_admin_group
def galleries_add_image(id: int):
    g = db.session.get(Gallery, id) or abort(404)
    form = GalleryImageForm()
    if form.validate_on_submit():
        next_order = max((im.sort_order for im in g.images), default=-1) + 1
        img = GalleryImage(
            gallery_id=g.id,
            image_url=form.image_url.data,
            caption=form.caption.data or "",
            alt_text=form.alt_text.data or "",
            sort_order=next_order,
        )
        db.session.add(img); db.session.commit()
        flash("Image added.", "success")
    else:
        flash("Image add failed: " + "; ".join(
            f"{f}: {','.join(errs)}" for f, errs in form.errors.items()
        ), "error")
    return redirect(url_for("admin.galleries_edit", id=id))


@bp.post("/galleries/<int:gid>/images/<int:iid>/delete", endpoint="galleries_delete_image")
@require_admin_group
def galleries_delete_image(gid: int, iid: int):
    img = db.session.get(GalleryImage, iid) or abort(404)
    if img.gallery_id != gid:
        abort(404)
    db.session.delete(img); db.session.commit()
    flash("Image removed.", "success")
    return redirect(url_for("admin.galleries_edit", id=gid))


@bp.post("/galleries/<int:gid>/images/<int:iid>/move", endpoint="galleries_move_image")
@require_admin_group
def galleries_move_image(gid: int, iid: int):
    direction = request.form.get("direction", "up")
    img = db.session.get(GalleryImage, iid) or abort(404)
    if img.gallery_id != gid:
        abort(404)
    siblings = sorted(img.gallery.images, key=lambda i: i.sort_order)
    idx = next(i for i, x in enumerate(siblings) if x.id == iid)
    swap_idx = idx - 1 if direction == "up" else idx + 1
    if 0 <= swap_idx < len(siblings):
        img.sort_order, siblings[swap_idx].sort_order = siblings[swap_idx].sort_order, img.sort_order
        db.session.commit()
    return redirect(url_for("admin.galleries_edit", id=gid))
```

- [ ] **Step 4: Write `app/templates/admin/galleries_edit.html`**

```html
{% extends "admin/base.html" %}
{% block title %}Edit Gallery — Admin{% endblock %}
{% block content %}
<h1 class="text-3xl mb-6">Edit Gallery</h1>

<form method="post" class="space-y-4 max-w-3xl mb-12">
  {{ form.hidden_tag() }}
  {% for field in form if field.name not in ('csrf_token',) %}
  <div>
    <label class="block text-xs uppercase tracking-widest text-white/60 mb-1">{{ field.label.text }}</label>
    {{ field(class_="w-full bg-black/40 border border-white/20 px-3 py-2 text-white font-mono") }}
  </div>
  {% endfor %}
  <button class="px-6 py-2 bg-white text-black uppercase tracking-widest">Save Gallery</button>
</form>

<h2 class="text-2xl mb-4">Images ({{ gallery.images|length }})</h2>

<form action="{{ url_for('admin.galleries_add_image', id=gallery.id) }}" method="post" class="space-y-3 max-w-3xl mb-8 border border-white/20 p-4">
  {{ image_form.hidden_tag() }}
  <input name="image_url" placeholder="https://design-assets.musicalmycology.org/grogblossoms/…" class="w-full bg-black/40 border border-white/20 px-3 py-2 font-mono">
  <input name="caption" placeholder="Caption" class="w-full bg-black/40 border border-white/20 px-3 py-2">
  <input name="alt_text" placeholder="Alt text" class="w-full bg-black/40 border border-white/20 px-3 py-2">
  <button class="px-4 py-2 bg-white text-black uppercase tracking-widest text-sm">+ Add image</button>
</form>

<ul class="space-y-2 max-w-3xl">
{% for img in gallery.images %}
  <li class="flex items-center gap-4 border border-white/10 p-3">
    <img src="{{ img.image_url }}" alt="{{ img.alt_text }}" class="w-20 h-20 object-cover grayscale">
    <div class="flex-1">
      <div class="text-sm">{{ img.caption or '—' }}</div>
      <div class="text-xs text-white/40 font-mono break-all">{{ img.image_url }}</div>
    </div>
    <form action="{{ url_for('admin.galleries_move_image', gid=gallery.id, iid=img.id) }}" method="post" class="inline">
      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
      <input type="hidden" name="direction" value="up">
      <button class="px-2 py-1 border border-white/20 text-xs">↑</button>
    </form>
    <form action="{{ url_for('admin.galleries_move_image', gid=gallery.id, iid=img.id) }}" method="post" class="inline">
      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
      <input type="hidden" name="direction" value="down">
      <button class="px-2 py-1 border border-white/20 text-xs">↓</button>
    </form>
    <form action="{{ url_for('admin.galleries_delete_image', gid=gallery.id, iid=img.id) }}" method="post" class="inline" onsubmit="return confirm('Remove?')">
      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
      <button class="px-2 py-1 border border-red-500/40 text-red-300 text-xs">remove</button>
    </form>
  </li>
{% else %}
  <li class="text-white/40">No images yet.</li>
{% endfor %}
</ul>
{% endblock %}
```

- [ ] **Step 5: Wire import**

In `app/blueprints/admin/__init__.py`, expand the import:

```python
from . import posts, crew, tour_dates, galleries, music, merch, press, scuttlebutt  # noqa: E402,F401
```

- [ ] **Step 6: Run tests**

```bash
pytest tests/test_admin_galleries.py -v
```

Expected: 3 passed.

- [ ] **Step 7: Commit**

```bash
git add app/blueprints/admin/galleries.py app/templates/admin/galleries_edit.html app/blueprints/admin/__init__.py tests/test_admin_galleries.py
git commit -m "feat: gallery admin with image add/remove/reorder"
```

---

### Task 3.5: Inquiries admin (read-only inbox + status updates)

**Files:**
- Create: `app/blueprints/admin/inquiries.py`
- Create: `app/templates/admin/inquiries_list.html`
- Create: `app/templates/admin/inquiries_detail.html`
- Modify: `app/blueprints/admin/__init__.py`
- Test: extends `tests/test_admin_crud.py`

- [ ] **Step 1: Write failing test**

Append to `tests/test_admin_crud.py`:

```python
def test_inquiries_inbox_renders(client, app):
    with app.app_context():
        from app.models import Inquiry
        from app.extensions import db
        i = Inquiry(kind="booking", from_name="A", email="a@b", message="hello")
        db.session.add(i); db.session.commit()
    _login_as_admin(client, app)
    r = client.get("/admin/inquiries/")
    assert r.status_code == 200
    assert b"booking" in r.data or b"BOOKING" in r.data


def test_inquiry_status_update(client, app):
    with app.app_context():
        from app.models import Inquiry
        from app.extensions import db
        i = Inquiry(kind="general", from_name="A", email="a@b", message="x")
        db.session.add(i); db.session.commit()
        iid = i.id
    _login_as_admin(client, app)
    r = client.post(f"/admin/inquiries/{iid}/status",
                    data={"status": "replied"}, follow_redirects=True)
    assert r.status_code == 200
    with app.app_context():
        from app.models import Inquiry
        from app.extensions import db
        assert db.session.get(Inquiry, iid).status == "replied"
```

- [ ] **Step 2: Write `app/blueprints/admin/inquiries.py`**

```python
from flask import abort, flash, redirect, render_template, request, url_for

from app.extensions import db
from app.models import Inquiry
from . import bp, require_admin_group


@bp.get("/inquiries/", endpoint="inquiries_list")
@require_admin_group
def inquiries_list():
    items = Inquiry.query.order_by(Inquiry.created_at.desc()).all()
    return render_template("admin/inquiries_list.html", items=items)


@bp.get("/inquiries/<int:id>", endpoint="inquiries_detail")
@require_admin_group
def inquiries_detail(id: int):
    inq = db.session.get(Inquiry, id) or abort(404)
    return render_template("admin/inquiries_detail.html", inq=inq)


@bp.post("/inquiries/<int:id>/status", endpoint="inquiries_status")
@require_admin_group
def inquiries_status(id: int):
    inq = db.session.get(Inquiry, id) or abort(404)
    new_status = request.form.get("status")
    if new_status in ("new", "replied", "archived"):
        inq.status = new_status
        db.session.commit()
        flash(f"Marked {new_status}.", "success")
    return redirect(url_for("admin.inquiries_detail", id=id))
```

- [ ] **Step 3: Write `app/templates/admin/inquiries_list.html`**

```html
{% extends "admin/base.html" %}
{% block title %}Inquiries — Admin{% endblock %}
{% block content %}
<h1 class="text-3xl mb-6">Inquiries</h1>
<table class="w-full">
  <thead class="border-b border-white/20">
    <tr><th class="py-2 px-3 text-left text-xs uppercase">When</th>
        <th class="text-left text-xs uppercase">Kind</th>
        <th class="text-left text-xs uppercase">From</th>
        <th class="text-left text-xs uppercase">Status</th></tr>
  </thead>
  <tbody>
  {% for inq in items %}
    <tr class="border-b border-white/10 hover:bg-white/5">
      <td class="py-3 px-3"><a href="{{ url_for('admin.inquiries_detail', id=inq.id) }}">{{ inq.created_at.strftime('%Y-%m-%d %H:%M') }}</a></td>
      <td class="px-3">{{ inq.kind }}</td>
      <td class="px-3">{{ inq.from_name }} <span class="text-white/40">&lt;{{ inq.email }}&gt;</span></td>
      <td class="px-3">{{ inq.status }}</td>
    </tr>
  {% else %}
    <tr><td colspan="4" class="py-8 text-center text-white/40">Empty inbox.</td></tr>
  {% endfor %}
  </tbody>
</table>
{% endblock %}
```

- [ ] **Step 4: Write `app/templates/admin/inquiries_detail.html`**

```html
{% extends "admin/base.html" %}
{% block title %}Inquiry — Admin{% endblock %}
{% block content %}
<a href="{{ url_for('admin.inquiries_list') }}" class="text-xs uppercase text-white/60">← back to inbox</a>
<h1 class="text-3xl mt-2 mb-6">{{ inq.kind|upper }} — {{ inq.from_name }}</h1>

<dl class="grid grid-cols-[10rem_1fr] gap-y-2 max-w-3xl mb-8 text-sm">
  <dt class="text-white/60">Email</dt><dd>{{ inq.email }}</dd>
  {% if inq.phone %}<dt class="text-white/60">Phone</dt><dd>{{ inq.phone }}</dd>{% endif %}
  {% if inq.event_date %}<dt class="text-white/60">Event date</dt><dd>{{ inq.event_date }}</dd>{% endif %}
  {% if inq.venue %}<dt class="text-white/60">Venue</dt><dd>{{ inq.venue }}</dd>{% endif %}
  {% if inq.city %}<dt class="text-white/60">City</dt><dd>{{ inq.city }}</dd>{% endif %}
  <dt class="text-white/60">Status</dt><dd>{{ inq.status }}</dd>
  <dt class="text-white/60">Received</dt><dd>{{ inq.created_at.strftime('%Y-%m-%d %H:%M') }}</dd>
</dl>

<div class="whitespace-pre-wrap border border-white/20 p-4 max-w-3xl mb-6">{{ inq.message }}</div>

<form method="post" action="{{ url_for('admin.inquiries_status', id=inq.id) }}" class="flex gap-2">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
  {% for s in ['new', 'replied', 'archived'] %}
  <button name="status" value="{{ s }}" class="px-3 py-1 border border-white/40 text-xs uppercase {% if inq.status == s %}bg-white text-black{% endif %}">{{ s }}</button>
  {% endfor %}
</form>
{% endblock %}
```

- [ ] **Step 5: Wire import**

`app/blueprints/admin/__init__.py`:

```python
from . import posts, crew, tour_dates, galleries, music, merch, press, inquiries, scuttlebutt  # noqa
```

- [ ] **Step 6: Run tests**

```bash
pytest tests/test_admin_crud.py -v
```

Expected: passes including the two new inquiry tests.

- [ ] **Step 7: Commit**

```bash
git add app/blueprints/admin/inquiries.py app/templates/admin/inquiries_*.html app/blueprints/admin/__init__.py tests/test_admin_crud.py
git commit -m "feat: inquiry inbox + status updates"
```

---

### Task 3.6: Assets admin (paste CDN URL flow + future upload hook)

**Files:**
- Create: `app/blueprints/admin/assets.py`
- Create: `app/services/storage.py` (placeholder; full impl when IAM lands)
- Create: `app/templates/admin/assets_list.html`
- Modify: `app/blueprints/admin/__init__.py`
- Test: `tests/test_storage.py`

- [ ] **Step 1: Write `app/services/storage.py`**

```python
"""S3 uploader to mm-sporekles' design-assets bucket.

v1: PLACEHOLDER implementation. Real boto3 wiring lands once the
mm-grogblossoms-uploader IAM user is provisioned (see spec, "Image flow").

Until then, the admin asset picker uses the `register_url()` path: paste a
CDN URL of a file you've already placed in the bucket via other means.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import BinaryIO

from flask import current_app

from app.extensions import db
from app.models import Asset


class UploaderNotProvisioned(RuntimeError):
    pass


@dataclass
class UploadResult:
    asset: Asset


def upload(file_obj: BinaryIO, filename: str, content_type: str) -> UploadResult:
    """Stream a file to S3, persist an Asset row, return both."""
    bucket = current_app.config.get("S3_BUCKET", "__PLACEHOLDER__")
    if bucket.startswith("__PLACEHOLDER__"):
        raise UploaderNotProvisioned(
            "S3 uploader is not yet provisioned. Use the 'Paste CDN URL' flow "
            "in /admin/assets/ until mm-sporekles infra exposes the uploader."
        )
    # When the real implementation lands:
    #   import boto3
    #   key = f"{current_app.config['S3_PREFIX']}{_safe_name(filename)}"
    #   s3 = boto3.client('s3', region_name=current_app.config['S3_REGION'])
    #   s3.upload_fileobj(file_obj, bucket, key,
    #       ExtraArgs={'ContentType': content_type,
    #                  'CacheControl': 'public, max-age=31536000, immutable'})
    #   url = current_app.config['CDN_BASE_URL'].rstrip('/') + '/' + key
    #   asset = Asset(key=key, url=url, filename=filename, content_type=content_type, size_bytes=…)
    #   db.session.add(asset); db.session.commit()
    #   return UploadResult(asset=asset)
    raise UploaderNotProvisioned("Real uploader implementation pending.")


def register_url(public_url: str, *, caption: str = "") -> Asset:
    """Record an externally-uploaded CDN URL as an Asset row.

    The URL is expected to be under CDN_BASE_URL + S3_PREFIX.
    """
    cdn = current_app.config["CDN_BASE_URL"].rstrip("/") + "/"
    prefix = current_app.config["S3_PREFIX"]
    if not public_url.startswith(cdn + prefix):
        raise ValueError(f"URL must start with {cdn}{prefix}")
    key = public_url[len(cdn):]
    filename = key.rsplit("/", 1)[-1]
    asset = Asset(
        key=key, url=public_url, filename=filename,
        content_type="application/octet-stream", size_bytes=0,
        caption=caption or None,
    )
    db.session.add(asset); db.session.commit()
    return asset
```

- [ ] **Step 2: Write `tests/test_storage.py`**

```python
import io
import pytest

from app.services.storage import (
    UploaderNotProvisioned, register_url, upload,
)


def test_upload_raises_when_not_provisioned(app):
    with app.app_context():
        with pytest.raises(UploaderNotProvisioned):
            upload(io.BytesIO(b"x"), "x.jpg", "image/jpeg")


def test_register_url_creates_asset(app):
    with app.app_context():
        a = register_url(
            "https://design-assets.musicalmycology.org/grogblossoms/img/foo.jpg",
            caption="Foo",
        )
        assert a.id is not None
        assert a.key == "grogblossoms/img/foo.jpg"
        assert a.caption == "Foo"


def test_register_url_rejects_wrong_prefix(app):
    with app.app_context():
        with pytest.raises(ValueError):
            register_url("https://evil.test/grogblossoms/x.jpg")
```

- [ ] **Step 3: Write `app/blueprints/admin/assets.py`**

```python
from flask import flash, redirect, render_template, request, url_for

from app.models import Asset
from app.services.storage import register_url
from . import bp, require_admin_group


@bp.get("/assets/", endpoint="assets_list")
@require_admin_group
def assets_list():
    items = Asset.query.order_by(Asset.uploaded_at.desc()).all()
    return render_template("admin/assets_list.html", items=items)


@bp.post("/assets/register", endpoint="assets_register")
@require_admin_group
def assets_register():
    url = (request.form.get("url") or "").strip()
    caption = (request.form.get("caption") or "").strip()
    try:
        register_url(url, caption=caption)
        flash("Asset registered.", "success")
    except ValueError as exc:
        flash(f"Rejected: {exc}", "error")
    return redirect(url_for("admin.assets_list"))
```

- [ ] **Step 4: Write `app/templates/admin/assets_list.html`**

```html
{% extends "admin/base.html" %}
{% block title %}Media — Admin{% endblock %}
{% block content %}
<h1 class="text-3xl mb-6">Media</h1>

<div class="border border-white/20 p-4 max-w-3xl mb-8">
  <h2 class="text-sm uppercase tracking-widest mb-3 text-white/60">Register CDN URL</h2>
  <p class="text-xs text-white/40 mb-3">Until the IAM uploader is provisioned, drop the file in the bucket via other means, then paste the public URL here.</p>
  <form method="post" action="{{ url_for('admin.assets_register') }}" class="space-y-2">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <input name="url" placeholder="https://design-assets.musicalmycology.org/grogblossoms/…" class="w-full bg-black/40 border border-white/20 px-3 py-2 font-mono text-sm">
    <input name="caption" placeholder="Caption (optional)" class="w-full bg-black/40 border border-white/20 px-3 py-2">
    <button class="px-4 py-2 bg-white text-black uppercase tracking-widest text-sm">Register</button>
  </form>
</div>

<table class="w-full text-sm">
  <thead class="border-b border-white/20">
    <tr><th class="py-2 px-3 text-left text-xs uppercase">Preview</th>
        <th class="text-left text-xs uppercase">Key</th>
        <th class="text-left text-xs uppercase">Uploaded</th></tr>
  </thead>
  <tbody>
  {% for a in items %}
    <tr class="border-b border-white/10">
      <td class="py-2 px-3">
        {% if a.content_type.startswith('image/') or a.url.endswith(('.jpg','.jpeg','.png','.webp','.gif')) %}
          <img src="{{ a.url }}" alt="" class="w-16 h-16 object-cover">
        {% else %}
          <span class="text-white/40 text-xs">file</span>
        {% endif %}
      </td>
      <td class="px-3 font-mono text-xs break-all">{{ a.key }}</td>
      <td class="px-3 text-xs">{{ a.uploaded_at.strftime('%Y-%m-%d') }}</td>
    </tr>
  {% else %}
    <tr><td colspan="3" class="py-8 text-center text-white/40">No assets registered.</td></tr>
  {% endfor %}
  </tbody>
</table>
{% endblock %}
```

- [ ] **Step 5: Wire import**

`app/blueprints/admin/__init__.py`:

```python
from . import posts, crew, tour_dates, galleries, music, merch, press, inquiries, scuttlebutt, assets  # noqa
```

- [ ] **Step 6: Run tests**

```bash
pytest tests/test_storage.py -v
```

Expected: 3 passed.

- [ ] **Step 7: Commit**

```bash
git add app/services/storage.py app/blueprints/admin/assets.py app/templates/admin/assets_list.html app/blueprints/admin/__init__.py tests/test_storage.py
git commit -m "feat: asset registry (paste URL) + placeholder S3 uploader"
```

---

### Task 3.7: Site settings (singleton) + dashboard widgets

**Files:**
- Create: `app/blueprints/admin/settings.py`
- Create: `app/templates/admin/settings.html`
- Modify: `app/blueprints/admin/views.py` — dashboard widgets
- Modify: `app/templates/admin/dashboard.html`
- Modify: `app/blueprints/admin/__init__.py`

- [ ] **Step 1: Write `app/blueprints/admin/settings.py`**

```python
from flask import flash, redirect, render_template, request, url_for
from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, TextAreaField
from wtforms.validators import Optional, URL

from app.extensions import db
from app.models import SiteSettings
from . import bp, require_admin_group


class SiteSettingsForm(FlaskForm):
    hero_quote = TextAreaField("Hero quote", validators=[Optional()])
    hero_image_url = StringField("Hero image URL", validators=[Optional(), URL()])
    logo_url = StringField("Logo URL", validators=[Optional(), URL()])
    contact_email = StringField("Contact email", validators=[Optional()])
    footer_text = StringField("Footer text", validators=[Optional()])
    ports_visited = IntegerField("Ports visited (stat)", default=0)
    grog_pints = StringField("Grog pints (stat, e.g. '100+')", validators=[Optional()])


@bp.route("/settings/", methods=("GET", "POST"), endpoint="settings")
@require_admin_group
def settings():
    s = SiteSettings.get_or_create()
    form = SiteSettingsForm(obj=s)
    if form.validate_on_submit():
        form.populate_obj(s)
        db.session.commit()
        flash("Settings saved.", "success")
        return redirect(url_for("admin.settings"))
    return render_template("admin/settings.html", form=form)
```

- [ ] **Step 2: Write `app/templates/admin/settings.html`**

```html
{% extends "admin/base.html" %}
{% block title %}Settings — Admin{% endblock %}
{% block content %}
<h1 class="text-3xl mb-6">Site Settings</h1>
<form method="post" class="space-y-4 max-w-3xl">
  {{ form.hidden_tag() }}
  {% for field in form if field.name not in ('csrf_token',) %}
  <div>
    <label class="block text-xs uppercase tracking-widest text-white/60 mb-1">{{ field.label.text }}</label>
    {{ field(class_="w-full bg-black/40 border border-white/20 px-3 py-2 text-white font-mono") }}
  </div>
  {% endfor %}
  <button class="px-6 py-2 bg-white text-black uppercase tracking-widest">Save</button>
</form>
{% endblock %}
```

Note: `social_links` is JSON; for v1 we edit it via a separate textarea later — out of scope for this task.

- [ ] **Step 3: Update dashboard**

Replace `app/blueprints/admin/views.py`:

```python
from datetime import datetime, timedelta

from flask import Blueprint, render_template

from app.models import Inquiry, Post, TourDate
from app.extensions import db

bp = Blueprint("admin", __name__)


def _require_group(view):
    from . import require_admin_group
    return require_admin_group(view)


@bp.get("/")
@_require_group
def dashboard():
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    upcoming = (TourDate.query
                .filter(TourDate.status.in_(("confirmed", "tentative")))
                .filter(TourDate.starts_at >= datetime.utcnow() - timedelta(days=1))
                .order_by(TourDate.starts_at).limit(3).all())
    new_inquiries = Inquiry.query.filter_by(status="new").count()
    return render_template(
        "admin/dashboard.html",
        recent_posts=recent_posts, upcoming=upcoming, new_inquiries=new_inquiries,
    )
```

Replace `app/templates/admin/dashboard.html`:

```html
{% extends "admin/base.html" %}
{% block title %}Dashboard — Admin{% endblock %}
{% block content %}
<h1 class="text-3xl mb-8">Dashboard</h1>

<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
  <div class="border border-white/20 p-4">
    <div class="text-xs uppercase tracking-widest text-white/60 mb-2">New inquiries</div>
    <div class="text-5xl font-bold">{{ new_inquiries }}</div>
    <a href="{{ url_for('admin.inquiries_list') }}" class="text-xs uppercase mt-3 inline-block text-white/60 hover:text-white">View inbox →</a>
  </div>
  <div class="border border-white/20 p-4">
    <div class="text-xs uppercase tracking-widest text-white/60 mb-2">Recent posts</div>
    <ul class="text-sm space-y-1">
      {% for p in recent_posts %}<li><a class="hover:underline" href="{{ url_for('admin.posts_edit', id=p.id) }}">{{ p.title }}</a></li>
      {% else %}<li class="text-white/40">none yet</li>{% endfor %}
    </ul>
  </div>
  <div class="border border-white/20 p-4">
    <div class="text-xs uppercase tracking-widest text-white/60 mb-2">Next tour dates</div>
    <ul class="text-sm space-y-1">
      {% for t in upcoming %}<li>{{ t.starts_at.strftime('%b %d') }} — {{ t.event_name }}</li>
      {% else %}<li class="text-white/40">none scheduled</li>{% endfor %}
    </ul>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 4: Wire settings import**

`app/blueprints/admin/__init__.py`:

```python
from . import posts, crew, tour_dates, galleries, music, merch, press, inquiries, scuttlebutt, assets, settings as _settings  # noqa
```

(Aliased to `_settings` to avoid shadowing Python's built-in `settings`.)

- [ ] **Step 5: Run all tests**

```bash
pytest -v
```

Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add app/blueprints/admin/ app/templates/admin/
git commit -m "feat: site settings + dashboard widgets"
```

---

## Phase 4 — Public Pages

Replace the placeholder routes added in Phase 0 with real, data-driven views. Mockups for reference live in `~/projects/gb-website/stitch_the_grog_blossoms_website/`. Each task ports the mockup HTML to Jinja and binds it to DB content.

### Task 4.1: Quarterdeck (home)

**Files:**
- Modify: `app/blueprints/public/views.py` — real home() view
- Modify: `app/templates/public/home.html` — full Quarterdeck mockup

- [ ] **Step 1: Write failing smoke test**

Append to `tests/test_public_smoke.py`:

```python
from app.extensions import db
from app.models import Post, Scuttlebutt, SiteSettings
from datetime import datetime


def _seed_home(app):
    with app.app_context():
        s = SiteSettings.get_or_create()
        s.hero_quote = "A celtic-pirate fusion band."
        s.hero_image_url = "https://example/x.jpg"
        s.ports_visited = 12
        s.grog_pints = "100+"
        db.session.add(Scuttlebutt(text="Test scuttle", accent="amber", sort_order=0))
        db.session.add(Post(slug="p1", title="Raid at Port Royal", author_name="C",
                            excerpt="The fog was thick",
                            published_at=datetime.utcnow()))
        db.session.commit()


def test_home_renders_with_seeded_data(client, app):
    _seed_home(app)
    response = client.get("/")
    assert response.status_code == 200
    body = response.data.decode()
    assert "celtic-pirate fusion" in body
    assert "Test scuttle" in body
    assert "Raid at Port Royal" in body
    assert "12" in body  # ports_visited
```

- [ ] **Step 2: Replace `app/blueprints/public/views.py`**

```python
from datetime import datetime
from flask import Blueprint, abort, render_template

from app.extensions import db
from app.models import (
    CrewMember, Gallery, MerchItem, MusicTrack, Post, PressAsset,
    Scuttlebutt, SiteSettings, TourDate,
)

bp = Blueprint("public", __name__)


def _live_scuttlebutts():
    return [s for s in Scuttlebutt.query.order_by(Scuttlebutt.sort_order).all() if s.is_visible()]


@bp.get("/")
def home():
    settings = SiteSettings.get_or_create()
    scuttle = _live_scuttlebutts()
    recent = (Post.query
              .filter(Post.published_at.isnot(None))
              .filter(Post.published_at <= datetime.utcnow())
              .order_by(Post.published_at.desc())
              .limit(3).all())
    return render_template("public/home.html",
                           settings=settings, scuttlebutts=scuttle, posts=recent)


@bp.get("/log")
def log_index():
    posts = (Post.query
             .filter(Post.published_at.isnot(None))
             .filter(Post.published_at <= datetime.utcnow())
             .order_by(Post.published_at.desc()).all())
    return render_template("public/log_index.html", posts=posts)


@bp.get("/log/<slug>")
def log_detail(slug: str):
    post = Post.query.filter_by(slug=slug).one_or_none()
    if post is None or not post.is_live():
        abort(404)
    return render_template("public/log_detail.html", post=post)


@bp.get("/manifest")
def manifest():
    now = datetime.utcnow()
    upcoming = (TourDate.query
                .filter(TourDate.status.in_(("confirmed", "tentative")))
                .filter(TourDate.starts_at >= now)
                .order_by(TourDate.starts_at).all())
    past = (TourDate.query
            .filter((TourDate.status == "past") | (TourDate.starts_at < now))
            .order_by(TourDate.starts_at.desc()).all())
    return render_template("public/manifest.html", upcoming=upcoming, past=past)


@bp.get("/crew")
def crew():
    members = CrewMember.query.order_by(CrewMember.sort_order).all()
    return render_template("public/crew.html", members=members)


@bp.get("/booty")
def booty():
    tracks = MusicTrack.query.order_by(MusicTrack.sort_order).all()
    merch = MerchItem.query.order_by(MerchItem.sort_order).all()
    return render_template("public/booty.html", tracks=tracks, merch=merch)


@bp.get("/gallery")
def gallery_index():
    galleries = Gallery.query.order_by(Gallery.sort_order).all()
    return render_template("public/gallery_index.html", galleries=galleries)


@bp.get("/gallery/<slug>")
def gallery_detail(slug: str):
    g = Gallery.query.filter_by(slug=slug).one_or_none()
    if g is None:
        abort(404)
    return render_template("public/gallery_detail.html", gallery=g)


@bp.get("/crows-nest")
def crows_nest():
    press = PressAsset.query.order_by(PressAsset.sort_order).all()
    return render_template("public/crows_nest.html", press=press)
```

- [ ] **Step 3: Replace `app/templates/public/home.html`**

```html
{% extends "base.html" %}
{% block title %}The Grog Blossoms — The Quarterdeck{% endblock %}
{% block content %}
<section class="px-6 py-12 md:py-20">
  <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
    <div class="lg:col-span-7 relative z-10">
      {% if settings.hero_image_url %}
      <div class="noir-frame bg-surface p-2 skew-1 mb-8 sketch-border border-white">
        <img alt="" class="w-full grayscale brightness-90" src="{{ settings.hero_image_url }}">
      </div>
      {% endif %}
      <div class="bg-primary text-background p-6 -mt-12 ml-4 md:ml-12 relative z-20 noir-frame max-w-md skew-2 sketch-border border-accent-amber">
        <h1 class="font-hand text-4xl md:text-5xl leading-tight mb-4 text-accent-red">THE QUARTERDECK</h1>
        <p class="italic">"{{ settings.hero_quote }}"</p>
      </div>
    </div>

    <div class="lg:col-span-5 flex flex-col gap-8">
      <div class="bg-surface-container-low p-8 border-2 border-accent-amber border-dashed relative sketch-border">
        <div class="absolute -top-4 -right-2 bg-accent-red text-white px-3 py-1 font-mono uppercase skew-1 text-xs">URGENT LOG</div>
        <h2 class="font-hand text-3xl mb-4 sketch-underline">Latest Scuttlebutt</h2>
        <ul class="space-y-4">
          {% for s in scuttlebutts %}
          <li class="flex items-start gap-3">
            <span class="font-bold text-accent-{{ s.accent }}">X</span>
            {% if s.link_url %}
            <a class="text-on-surface-variant hover:text-on-surface" href="{{ s.link_url }}">{{ s.text }}</a>
            {% else %}
            <p class="text-on-surface-variant">{{ s.text }}</p>
            {% endif %}
          </li>
          {% else %}
          <li class="text-white/40">All quiet on the deck.</li>
          {% endfor %}
        </ul>
      </div>
    </div>
  </div>
</section>

<section class="bg-surface-container-lowest py-12 border-t-4 border-accent-amber">
  <div class="px-6">
    <div class="grid grid-cols-2 gap-4 max-w-md">
      <div class="bg-accent-red text-white p-4 text-center noir-frame rotate-1 sketch-border">
        <div class="text-5xl font-bold leading-none">{{ settings.ports_visited }}</div>
        <div class="font-hand uppercase text-lg">Ports Visited</div>
      </div>
      <div class="bg-surface border-2 border-accent-amber p-4 text-center noir-frame -rotate-1 sketch-border">
        <div class="text-5xl text-accent-amber font-bold leading-none">{{ settings.grog_pints }}</div>
        <div class="font-hand uppercase text-lg">Grog Pints</div>
      </div>
    </div>
  </div>
</section>

<section class="px-6 py-12">
  <div class="flex items-end justify-between mb-8">
    <h2 class="font-hand text-5xl text-primary">Ship's Log</h2>
    <a class="font-mono text-xs text-accent-amber border-b border-accent-amber" href="{{ url_for('public.log_index') }}">Read every entry →</a>
  </div>
  <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
    {% for p in posts %}
    <article class="group">
      {% if p.hero_image_url %}
      <div class="noir-frame bg-surface p-1 mb-4 sketch-border -rotate-1">
        <img alt="" class="w-full h-48 object-cover grayscale" src="{{ p.hero_image_url }}">
      </div>
      {% endif %}
      <span class="font-mono text-xs text-accent-red uppercase">{{ p.published_at.strftime('%b %d, %Y') }}</span>
      <h3 class="font-hand text-2xl mt-2 mb-3 text-on-surface sketch-underline inline-block">{{ p.title }}</h3>
      <p class="text-on-surface-variant text-sm line-clamp-3">{{ p.excerpt }}</p>
      <a href="{{ url_for('public.log_detail', slug=p.slug) }}" class="mt-4 inline-block font-hand text-accent-amber hover:text-accent-red">CONTINUE THE LOG →</a>
    </article>
    {% else %}
    <div class="col-span-3 text-white/40 text-center py-8">No log entries yet.</div>
    {% endfor %}
  </div>
</section>
{% endblock %}
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_public_smoke.py -v
```

Expected: passes.

- [ ] **Step 5: Commit**

```bash
git add app/blueprints/public/views.py app/templates/public/home.html tests/test_public_smoke.py
git commit -m "feat: Quarterdeck home page"
```

---

### Task 4.2: Ship's Log index + detail

**Files:**
- Create: `app/templates/public/log_index.html`
- Create: `app/templates/public/log_detail.html`

- [ ] **Step 1: Write `log_index.html`**

```html
{% extends "base.html" %}
{% block title %}Ship's Log — The Grog Blossoms{% endblock %}
{% block content %}
<section class="px-6 py-12 max-w-6xl mx-auto">
  <div class="inline-block bg-accent-red text-white px-8 py-3 mb-8 -rotate-1 sketch-border">
    <h1 class="font-hand text-5xl uppercase leading-tight">Ship's Log</h1>
  </div>
  <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
    {% for p in posts %}
    <article class="group">
      {% if p.hero_image_url %}
      <div class="noir-frame bg-surface p-1 mb-4 sketch-border -rotate-1">
        <img alt="" class="w-full h-48 object-cover grayscale" src="{{ p.hero_image_url }}">
      </div>
      {% endif %}
      <span class="font-mono text-xs text-accent-red uppercase">{{ p.published_at.strftime('%b %d, %Y') }}</span>
      <h2 class="font-hand text-2xl mt-2 mb-3 sketch-underline inline-block">
        <a href="{{ url_for('public.log_detail', slug=p.slug) }}">{{ p.title }}</a>
      </h2>
      <p class="text-on-surface-variant text-sm line-clamp-3">{{ p.excerpt }}</p>
    </article>
    {% else %}
    <div class="col-span-3 text-white/40 text-center py-12">The log is empty.</div>
    {% endfor %}
  </div>
</section>
{% endblock %}
```

- [ ] **Step 2: Write `log_detail.html`**

For Phase 4 the post body is plain Markdown (rendered server-side); the block renderer arrives in Phase 6. The template handles both: if `blocks` is non-empty, render via macros; otherwise render `body_md`.

```html
{% extends "base.html" %}
{% block title %}{{ post.title }} — Ship's Log{% endblock %}
{% block content %}
<article class="px-6 py-12 max-w-3xl mx-auto">
  <span class="font-mono text-xs text-accent-red uppercase">{{ post.published_at.strftime('%b %d, %Y') }} — {{ post.author_name }}</span>
  <h1 class="font-hand text-5xl my-4 sketch-underline inline-block">{{ post.title }}</h1>

  {% if post.hero_image_url %}
  <div class="noir-frame bg-surface p-2 my-8 -rotate-1 sketch-border border-white">
    <img alt="" class="w-full grayscale" src="{{ post.hero_image_url }}">
  </div>
  {% endif %}

  {% if post.blocks and post.blocks|length > 0 %}
    {% from "_blocks/macros.html" import render_block %}
    {% for block in post.blocks %}{{ render_block(block) }}{% endfor %}
  {% else %}
    <div class="prose prose-invert max-w-none font-body-lg">
      {{ post.body_md | markdown | safe }}
    </div>
  {% endif %}
</article>
{% endblock %}
```

- [ ] **Step 3: Register `markdown` filter**

Add to `app/__init__.py` inside `create_app()` before `return app`:

```python
    import markdown as md
    @app.template_filter("markdown")
    def _markdown_filter(text: str) -> str:
        if not text:
            return ""
        return md.markdown(text, extensions=["fenced_code", "tables", "nl2br"])
```

- [ ] **Step 4: Create a stub `_blocks/macros.html`**

Create `app/templates/_blocks/macros.html`:

```html
{# Phase 6 fills this with the real dispatcher. Stub is harmless if post.blocks is empty. #}
{% macro render_block(block) %}
<div class="text-white/40 italic">[block type: {{ block.type }} — renderer pending]</div>
{% endmacro %}
```

- [ ] **Step 5: Write smoke test**

Append to `tests/test_public_smoke.py`:

```python
def test_log_index_and_detail(client, app):
    with app.app_context():
        db.session.add(Post(slug="entry", title="Entry", author_name="C",
                            excerpt="ex", body_md="# Hi\n\npara",
                            published_at=datetime.utcnow()))
        db.session.commit()
    r1 = client.get("/log")
    assert r1.status_code == 200 and b"Entry" in r1.data
    r2 = client.get("/log/entry")
    assert r2.status_code == 200 and b"Hi" in r2.data


def test_log_detail_404s_for_draft(client, app):
    with app.app_context():
        db.session.add(Post(slug="draft", title="X", author_name="C", excerpt="", body_md=""))
        db.session.commit()
    r = client.get("/log/draft")
    assert r.status_code == 404
```

- [ ] **Step 6: Run tests + commit**

```bash
pytest tests/test_public_smoke.py -v
git add app/templates/public/log_*.html app/templates/_blocks/macros.html app/__init__.py tests/test_public_smoke.py
git commit -m "feat: Ship's Log index + detail"
```

---

### Task 4.3: Ship's Manifest (tour dates)

**Files:**
- Create: `app/templates/public/manifest.html`

- [ ] **Step 1: Write template**

```html
{% extends "base.html" %}
{% block title %}The Ship's Manifest — Tour Dates{% endblock %}
{% block content %}
<section class="px-6 py-12 max-w-5xl mx-auto">
  <div class="inline-block bg-accent-red text-white px-8 py-3 mb-8 -rotate-1 sketch-border">
    <h1 class="font-hand text-5xl uppercase">The Ship's Manifest</h1>
  </div>

  <h2 class="font-hand text-3xl mt-12 mb-6 text-accent-amber">Upcoming Ports</h2>
  <ul class="space-y-4">
    {% for t in upcoming %}
    <li class="border-2 border-white/20 p-6 grid grid-cols-1 md:grid-cols-[10rem_1fr_auto] gap-4 items-center sketch-border">
      <div>
        <div class="font-hand text-3xl text-accent-amber">{{ t.starts_at.strftime('%b %d') }}</div>
        <div class="font-mono text-xs text-white/60 uppercase">{{ t.starts_at.strftime('%Y') }}</div>
      </div>
      <div>
        <div class="font-hand text-2xl">{{ t.event_name }}</div>
        <div class="text-on-surface-variant text-sm">{{ t.venue }} — {{ t.city }}, {{ t.state }}</div>
        {% if t.notes %}<div class="mt-2 text-sm">{{ t.notes }}</div>{% endif %}
      </div>
      <div>
        {% if t.ticket_url %}
        <a class="px-4 py-2 bg-accent-red text-white font-hand uppercase block text-center" href="{{ t.ticket_url }}">Tickets</a>
        {% else %}
        <span class="font-mono text-xs text-white/40 uppercase">{{ t.status }}</span>
        {% endif %}
      </div>
    </li>
    {% else %}
    <li class="text-white/40 py-8 text-center">No ports on the horizon.</li>
    {% endfor %}
  </ul>

  {% if past %}
  <h2 class="font-hand text-3xl mt-16 mb-6 text-white/60">Ports Visited</h2>
  <ul class="space-y-2 text-sm text-on-surface-variant">
    {% for t in past %}
    <li class="flex gap-4 border-b border-white/10 py-2">
      <span class="font-mono text-xs uppercase w-28 text-white/40">{{ t.starts_at.strftime('%Y-%m-%d') }}</span>
      <span>{{ t.event_name }} — {{ t.venue }}, {{ t.city }} {{ t.state }}</span>
    </li>
    {% endfor %}
  </ul>
  {% endif %}
</section>
{% endblock %}
```

- [ ] **Step 2: Smoke test**

Append to `tests/test_public_smoke.py`:

```python
def test_manifest_lists_upcoming(client, app):
    from app.models import TourDate
    with app.app_context():
        db.session.add(TourDate(event_name="Renfest", venue="V", city="C", state="CA",
                                starts_at=datetime.utcnow().replace(year=2099), status="confirmed"))
        db.session.commit()
    r = client.get("/manifest")
    assert r.status_code == 200 and b"Renfest" in r.data
```

- [ ] **Step 3: Run + commit**

```bash
pytest tests/test_public_smoke.py -v
git add app/templates/public/manifest.html tests/test_public_smoke.py
git commit -m "feat: Ship's Manifest tour dates page"
```

---

### Task 4.4: Rogue's Gallery (crew)

**Files:**
- Create: `app/templates/public/crew.html`

- [ ] **Step 1: Write template**

```html
{% extends "base.html" %}
{% block title %}Rogue's Gallery — The Grog Blossoms{% endblock %}
{% block content %}
<section class="px-6 py-12 max-w-7xl mx-auto">
  <div class="inline-block bg-accent-red text-white px-8 py-3 mb-6 -rotate-1 sketch-border">
    <h1 class="font-hand text-5xl uppercase">Rogue's Gallery</h1>
  </div>
  <p class="font-hand text-2xl max-w-2xl text-on-surface-variant italic border-l-4 border-accent-red pl-6 py-2 mb-12">
    "Wanted for piracy, revelry, and the occasional fine harmony. Approach with caution and a full flagon."
  </p>

  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-12">
    {% for c in members %}
    <div class="sketch-border p-8 {% if c.tilt == 'left' %}-rotate-1{% else %}rotate-1{% endif %} border-accent-{{ c.accent }} flex flex-col">
      <div class="mb-6 border-b-2 border-dashed border-accent-red pb-3 flex justify-between items-end">
        <span class="font-mono text-xs text-accent-amber uppercase tracking-widest">Entry No. {{ c.entry_no }}</span>
      </div>
      {% if c.portrait_url %}
      <div class="noir-frame bg-surface-container-high mb-6 overflow-hidden sketch-border border-white aspect-[4/5]">
        <img alt="{{ c.name }}" class="w-full h-full object-cover grayscale" src="{{ c.portrait_url }}">
      </div>
      {% endif %}
      <h3 class="font-hand text-4xl text-primary mb-2 sketch-underline inline-block w-fit">{{ c.name }}</h3>
      <p class="font-mono text-xs uppercase text-accent-amber mb-6">{{ c.role }}</p>
      {% if c.quote %}
      <div class="mt-auto pt-6 border-t border-dashed border-white/20">
        <p class="font-hand text-xl italic text-on-surface-variant">"{{ c.quote }}"</p>
      </div>
      {% endif %}
    </div>
    {% else %}
    <div class="col-span-3 text-white/40 text-center">No crew aboard yet.</div>
    {% endfor %}
  </div>
</section>
{% endblock %}
```

- [ ] **Step 2: Smoke test + commit**

Append to `tests/test_public_smoke.py`:

```python
def test_crew_page_renders(client, app):
    from app.models import CrewMember
    with app.app_context():
        db.session.add(CrewMember(slug="siren", name="THE SIREN", role="Fiddle",
                                  portrait_url="", quote="x", entry_no="002",
                                  tilt="left", accent="white", sort_order=0))
        db.session.commit()
    r = client.get("/crew")
    assert r.status_code == 200 and b"THE SIREN" in r.data
```

```bash
pytest tests/test_public_smoke.py -v
git add app/templates/public/crew.html tests/test_public_smoke.py
git commit -m "feat: Rogue's Gallery crew page"
```

---

### Task 4.5: Booty (music + merch)

**Files:**
- Create: `app/templates/public/booty.html`

- [ ] **Step 1: Write template**

```html
{% extends "base.html" %}
{% block title %}Booty — The Grog Blossoms{% endblock %}
{% block content %}
<section class="px-6 py-12 max-w-6xl mx-auto">
  <div class="inline-block bg-accent-amber text-background px-8 py-3 mb-8 rotate-1 sketch-border">
    <h1 class="font-hand text-5xl uppercase">The Booty</h1>
  </div>

  <h2 class="font-hand text-4xl mt-8 mb-6">Tunes</h2>
  <ul class="space-y-4 mb-16">
    {% for t in tracks %}
    <li class="flex items-center gap-6 border-2 border-white/20 p-4 sketch-border">
      {% if t.cover_url %}
      <img src="{{ t.cover_url }}" alt="" class="w-16 h-16 object-cover grayscale">
      {% endif %}
      <div class="flex-1">
        <div class="font-hand text-2xl">{{ t.title }}</div>
        {% if t.release_name %}<div class="text-xs text-white/40 uppercase">{{ t.release_name }}</div>{% endif %}
      </div>
      {% if t.audio_url %}
      <audio controls src="{{ t.audio_url }}" class="max-w-xs"></audio>
      {% endif %}
      <div class="flex gap-2">
        {% if t.bandcamp_url %}<a class="px-3 py-1 border border-white/40 text-xs uppercase" href="{{ t.bandcamp_url }}">Bandcamp</a>{% endif %}
        {% if t.spotify_url %}<a class="px-3 py-1 border border-white/40 text-xs uppercase" href="{{ t.spotify_url }}">Spotify</a>{% endif %}
      </div>
    </li>
    {% else %}
    <li class="text-white/40 py-8 text-center">No recordings ashore yet.</li>
    {% endfor %}
  </ul>

  <h2 class="font-hand text-4xl mb-6">Goods</h2>
  <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
    {% for m in merch %}
    <div class="sketch-border p-4 {% if loop.index is odd %}-rotate-1{% else %}rotate-1{% endif %}">
      {% if m.image_url %}
      <div class="noir-frame bg-surface mb-4 overflow-hidden">
        <img src="{{ m.image_url }}" alt="{{ m.name }}" class="w-full h-48 object-cover grayscale">
      </div>
      {% endif %}
      <h3 class="font-hand text-2xl">{{ m.name }}</h3>
      <p class="text-on-surface-variant text-sm mt-2">{{ m.description }}</p>
      <div class="mt-4 flex justify-between items-center">
        <span class="font-hand text-2xl text-accent-amber">{{ m.price_display }}</span>
        <a href="{{ m.external_url }}" class="px-4 py-2 bg-accent-red text-white font-hand uppercase">{% if m.in_stock %}Buy{% else %}Sold Out{% endif %}</a>
      </div>
    </div>
    {% else %}
    <div class="col-span-3 text-white/40 text-center">Hold's empty.</div>
    {% endfor %}
  </div>
</section>
{% endblock %}
```

- [ ] **Step 2: Smoke test + commit**

```python
# Append to tests/test_public_smoke.py
def test_booty_renders(client, app):
    from app.models import MerchItem, MusicTrack
    with app.app_context():
        db.session.add(MusicTrack(title="Heave Ho", sort_order=0))
        db.session.add(MerchItem(name="Tee", description="", image_url="",
                                 price_display="$25", external_url="https://x", sort_order=0))
        db.session.commit()
    r = client.get("/booty")
    assert r.status_code == 200 and b"Heave Ho" in r.data and b"Tee" in r.data
```

```bash
pytest tests/test_public_smoke.py -v
git add app/templates/public/booty.html tests/test_public_smoke.py
git commit -m "feat: Booty page (music + merch)"
```

---

### Task 4.6: Gallery index + detail (with lightbox)

**Files:**
- Create: `app/templates/public/gallery_index.html`
- Create: `app/templates/public/gallery_detail.html`

- [ ] **Step 1: Write `gallery_index.html`**

```html
{% extends "base.html" %}
{% block title %}Galleries — The Grog Blossoms{% endblock %}
{% block content %}
<section class="px-6 py-12 max-w-6xl mx-auto">
  <h1 class="font-hand text-5xl mb-8 sketch-underline inline-block">Galleries</h1>
  <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
    {% for g in galleries %}
    <a href="{{ url_for('public.gallery_detail', slug=g.slug) }}" class="block group">
      <div class="noir-frame bg-surface p-1 sketch-border {% if loop.index is odd %}-rotate-1{% else %}rotate-1{% endif %}">
        {% if g.cover_image_url %}
        <img src="{{ g.cover_image_url }}" alt="" class="w-full h-48 object-cover grayscale group-hover:grayscale-0 transition">
        {% else %}
        <div class="w-full h-48 bg-surface-container-high"></div>
        {% endif %}
      </div>
      <h2 class="font-hand text-2xl mt-3 sketch-underline inline-block">{{ g.title }}</h2>
      <p class="text-sm text-white/60">{{ g.images|length }} images</p>
    </a>
    {% else %}
    <div class="col-span-3 text-white/40 text-center">No galleries yet.</div>
    {% endfor %}
  </div>
</section>
{% endblock %}
```

- [ ] **Step 2: Write `gallery_detail.html` (with vanilla-JS lightbox)**

```html
{% extends "base.html" %}
{% block title %}{{ gallery.title }} — Gallery{% endblock %}
{% block content %}
<section class="px-6 py-12 max-w-6xl mx-auto">
  <a href="{{ url_for('public.gallery_index') }}" class="font-mono text-xs uppercase text-white/60">← all galleries</a>
  <h1 class="font-hand text-5xl my-4 sketch-underline inline-block">{{ gallery.title }}</h1>
  {% if gallery.description %}<p class="max-w-2xl text-on-surface-variant mb-8">{{ gallery.description }}</p>{% endif %}

  <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
    {% for img in gallery.images %}
    <button type="button"
            class="block w-full noir-frame bg-surface p-1 sketch-border {% if loop.index is odd %}-rotate-1{% else %}rotate-1{% endif %}"
            data-lightbox
            data-src="{{ img.image_url }}"
            data-caption="{{ img.caption }}">
      <img src="{{ img.image_url }}" alt="{{ img.alt_text }}"
           class="w-full aspect-[4/3] object-cover grayscale hover:grayscale-0 transition">
    </button>
    {% else %}
    <div class="col-span-4 text-white/40 text-center py-12">Gallery is empty.</div>
    {% endfor %}
  </div>
</section>

<div id="lightbox" class="hidden fixed inset-0 bg-black/95 z-[100] flex items-center justify-center p-6" onclick="this.classList.add('hidden')">
  <figure class="max-w-5xl">
    <img id="lightbox-img" class="max-h-[80vh] max-w-full">
    <figcaption id="lightbox-cap" class="text-white/70 font-mono text-sm mt-3 text-center"></figcaption>
  </figure>
</div>

<script>
document.querySelectorAll('[data-lightbox]').forEach(btn => {
  btn.addEventListener('click', () => {
    document.getElementById('lightbox-img').src = btn.dataset.src;
    document.getElementById('lightbox-cap').textContent = btn.dataset.caption || '';
    document.getElementById('lightbox').classList.remove('hidden');
  });
});
</script>
{% endblock %}
```

- [ ] **Step 3: Smoke test + commit**

```python
def test_gallery_index_and_detail(client, app):
    from app.models import Gallery, GalleryImage
    with app.app_context():
        g = Gallery(slug="g1", title="Gigs", description="", cover_image_url="", sort_order=0)
        db.session.add(g); db.session.commit()
        db.session.add(GalleryImage(gallery_id=g.id, image_url="https://x/y.jpg",
                                    caption="c", alt_text="a", sort_order=0))
        db.session.commit()
    r1 = client.get("/gallery")
    assert r1.status_code == 200 and b"Gigs" in r1.data
    r2 = client.get("/gallery/g1")
    assert r2.status_code == 200 and b"y.jpg" in r2.data
```

```bash
pytest tests/test_public_smoke.py -v
git add app/templates/public/gallery_*.html tests/test_public_smoke.py
git commit -m "feat: gallery index + detail with lightbox"
```

---

### Task 4.7: Crow's Nest (press kit; form HTML stubbed, handler in Phase 5)

**Files:**
- Create: `app/templates/public/crows_nest.html`

- [ ] **Step 1: Write template**

```html
{% extends "base.html" %}
{% block title %}Crow's Nest — Press & Contact{% endblock %}
{% block content %}
<section class="px-6 py-12 max-w-5xl mx-auto">
  <div class="inline-block bg-accent-amber text-background px-8 py-3 mb-8 -rotate-1 sketch-border">
    <h1 class="font-hand text-5xl uppercase">The Crow's Nest</h1>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-12">

    <div>
      <h2 class="font-hand text-3xl mb-4 sketch-underline inline-block">Press Kit</h2>
      <ul class="space-y-3">
        {% for p in press %}
        <li class="flex justify-between border-b border-white/10 py-2">
          <div>
            <a href="{{ p.file_url }}" class="font-hand text-xl hover:text-accent-amber">{{ p.title }}</a>
            <div class="font-mono text-xs uppercase text-white/40">{{ p.kind }}</div>
            {% if p.description %}<div class="text-sm text-on-surface-variant mt-1">{{ p.description }}</div>{% endif %}
          </div>
          <a href="{{ p.file_url }}" class="font-mono text-xs uppercase text-accent-amber self-start">download →</a>
        </li>
        {% else %}
        <li class="text-white/40">No press materials yet.</li>
        {% endfor %}
      </ul>
    </div>

    <div>
      <h2 class="font-hand text-3xl mb-4 sketch-underline inline-block">Make Contact</h2>
      <form method="post" action="{{ url_for('public.crows_nest_submit') }}" class="space-y-3">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
        <select name="kind" class="w-full bg-black/40 border border-white/20 px-3 py-2 font-mono">
          <option value="booking">Booking inquiry</option>
          <option value="press">Press inquiry</option>
          <option value="general">General message</option>
        </select>
        <input name="from_name" required placeholder="Your name" class="w-full bg-black/40 border border-white/20 px-3 py-2">
        <input name="email" required type="email" placeholder="Email" class="w-full bg-black/40 border border-white/20 px-3 py-2">
        <input name="phone" placeholder="Phone (optional)" class="w-full bg-black/40 border border-white/20 px-3 py-2">
        <input name="event_date" type="date" placeholder="Event date" class="w-full bg-black/40 border border-white/20 px-3 py-2">
        <input name="venue" placeholder="Venue (booking)" class="w-full bg-black/40 border border-white/20 px-3 py-2">
        <input name="city" placeholder="City (booking)" class="w-full bg-black/40 border border-white/20 px-3 py-2">
        <textarea name="message" required rows="5" placeholder="Your message" class="w-full bg-black/40 border border-white/20 px-3 py-2"></textarea>
        <button class="px-6 py-2 bg-accent-red text-white font-hand uppercase tracking-widest">Send</button>
      </form>
    </div>
  </div>
</section>
{% endblock %}
```

- [ ] **Step 2: Smoke test**

Append to `tests/test_public_smoke.py`:

```python
def test_crows_nest_renders(client, app):
    r = client.get("/crows-nest")
    assert r.status_code == 200
    assert b"Make Contact" in r.data
```

- [ ] **Step 3: Commit**

```bash
pytest tests/test_public_smoke.py -v
git add app/templates/public/crows_nest.html tests/test_public_smoke.py
git commit -m "feat: Crow's Nest press kit + contact form (handler in Phase 5)"
```

---

### Task 4.8: RSS, sitemap, robots

**Files:**
- Create: `app/blueprints/public/feeds.py`
- Modify: `app/blueprints/public/__init__.py` — register feeds
- Create: `app/templates/public/robots.txt`

- [ ] **Step 1: Write `app/blueprints/public/feeds.py`**

```python
from datetime import datetime, timezone
from flask import Response, render_template, request, url_for
from feedgen.feed import FeedGenerator

from app.models import Post, Gallery, TourDate
from . import bp


@bp.get("/feed.xml")
def feed():
    fg = FeedGenerator()
    fg.title("The Grog Blossoms — Ship's Log")
    fg.link(href=url_for("public.home", _external=True), rel="alternate")
    fg.link(href=url_for("public.feed", _external=True), rel="self")
    fg.description("Dispatches from the Quarterdeck.")
    fg.language("en")
    posts = (Post.query
             .filter(Post.published_at.isnot(None))
             .filter(Post.published_at <= datetime.utcnow())
             .order_by(Post.published_at.desc()).limit(50).all())
    for p in posts:
        fe = fg.add_entry()
        fe.id(url_for("public.log_detail", slug=p.slug, _external=True))
        fe.link(href=url_for("public.log_detail", slug=p.slug, _external=True))
        fe.title(p.title)
        fe.description(p.excerpt or "")
        fe.pubDate(p.published_at.replace(tzinfo=timezone.utc))
    return Response(fg.rss_str(pretty=True), mimetype="application/rss+xml")


@bp.get("/sitemap.xml")
def sitemap():
    urls = [
        url_for("public.home", _external=True),
        url_for("public.log_index", _external=True),
        url_for("public.manifest", _external=True),
        url_for("public.crew", _external=True),
        url_for("public.booty", _external=True),
        url_for("public.gallery_index", _external=True),
        url_for("public.crows_nest", _external=True),
    ]
    for p in Post.query.filter(Post.published_at.isnot(None)).all():
        if p.is_live():
            urls.append(url_for("public.log_detail", slug=p.slug, _external=True))
    for g in Gallery.query.all():
        urls.append(url_for("public.gallery_detail", slug=g.slug, _external=True))
    body = render_template("public/sitemap.xml", urls=urls)
    return Response(body, mimetype="application/xml")


@bp.get("/robots.txt")
def robots():
    return Response(render_template("public/robots.txt",
                                    sitemap_url=url_for("public.sitemap", _external=True)),
                    mimetype="text/plain")
```

- [ ] **Step 2: Templates**

Create `app/templates/public/sitemap.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{% for u in urls %}  <url><loc>{{ u }}</loc></url>
{% endfor %}</urlset>
```

Create `app/templates/public/robots.txt`:

```
User-agent: *
Allow: /
Disallow: /admin/
Disallow: /auth/

Sitemap: {{ sitemap_url }}
```

- [ ] **Step 3: Register feeds blueprint module**

In `app/blueprints/public/__init__.py`, import feeds so routes attach:

```python
from .views import bp
from . import feeds  # noqa: F401

__all__ = ["bp"]
```

- [ ] **Step 4: Smoke test**

Append to `tests/test_public_smoke.py`:

```python
def test_feed_renders(client, app):
    r = client.get("/feed.xml")
    assert r.status_code == 200
    assert b"<rss" in r.data


def test_sitemap_renders(client):
    r = client.get("/sitemap.xml")
    assert r.status_code == 200
    assert b"<urlset" in r.data


def test_robots_renders(client):
    r = client.get("/robots.txt")
    assert r.status_code == 200
    assert b"Disallow: /admin/" in r.data
```

- [ ] **Step 5: Run + commit**

```bash
pytest tests/test_public_smoke.py -v
git add app/blueprints/public/feeds.py app/blueprints/public/__init__.py app/templates/public/sitemap.xml app/templates/public/robots.txt tests/test_public_smoke.py
git commit -m "feat: RSS feed + sitemap + robots.txt"
```

---

## Phase 5 — Forms + Email

### Task 5.1: Email service

**Files:**
- Create: `app/services/email.py`
- Test: `tests/test_email.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_email.py`:

```python
from unittest.mock import MagicMock, patch

from app.services.email import send_inquiry_notification
from app.models import Inquiry


def test_send_inquiry_notification_calls_smtp(app):
    with app.app_context():
        app.config["SMTP_HOST"] = "smtp.example.test"
        app.config["SMTP_PORT"] = 587
        app.config["SMTP_USER"] = "user"
        app.config["SMTP_PASSWORD"] = "pw"
        app.config["SMTP_FROM"] = "no-reply@grogblossoms.com"
        app.config["CONTACT_EMAIL"] = "chris@grogblossoms.com"
        inq = Inquiry(kind="booking", from_name="Cap'n", email="cap@y", message="Hi")

        with patch("app.services.email.smtplib.SMTP") as mock_smtp:
            instance = MagicMock()
            mock_smtp.return_value.__enter__.return_value = instance
            send_inquiry_notification(inq)
            instance.starttls.assert_called_once()
            instance.login.assert_called_once_with("user", "pw")
            instance.send_message.assert_called_once()


def test_send_inquiry_notification_noops_without_smtp_host(app, caplog):
    with app.app_context():
        app.config["SMTP_HOST"] = ""
        inq = Inquiry(kind="general", from_name="X", email="x@y", message="hi")
        # Should not raise.
        send_inquiry_notification(inq)
```

- [ ] **Step 2: Write `app/services/email.py`**

```python
"""SMTP email sender. Single outbound path: inquiry notification."""
from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from flask import current_app, url_for

from app.models import Inquiry

logger = logging.getLogger(__name__)


def send_inquiry_notification(inq: Inquiry) -> None:
    cfg = current_app.config
    host = cfg.get("SMTP_HOST")
    if not host:
        logger.info("SMTP_HOST not configured; skipping notification for inquiry %s", inq.id)
        return

    msg = EmailMessage()
    msg["Subject"] = f"[Grog Blossoms] New {inq.kind} inquiry from {inq.from_name}"
    msg["From"] = cfg["SMTP_FROM"]
    msg["To"] = cfg["CONTACT_EMAIL"]
    msg.set_content(_format_body(inq))

    try:
        with smtplib.SMTP(host, cfg.get("SMTP_PORT", 587), timeout=10) as s:
            s.starttls()
            if cfg.get("SMTP_USER"):
                s.login(cfg["SMTP_USER"], cfg["SMTP_PASSWORD"])
            s.send_message(msg)
    except Exception:
        logger.exception("Failed to send inquiry notification for inquiry %s", inq.id)


def _format_body(inq: Inquiry) -> str:
    try:
        link = url_for("admin.inquiries_detail", id=inq.id, _external=True)
    except RuntimeError:
        link = f"/admin/inquiries/{inq.id}"
    lines = [
        f"Kind:     {inq.kind}",
        f"From:     {inq.from_name} <{inq.email}>",
    ]
    if inq.phone: lines.append(f"Phone:    {inq.phone}")
    if inq.event_date: lines.append(f"Event:    {inq.event_date}")
    if inq.venue: lines.append(f"Venue:    {inq.venue}")
    if inq.city: lines.append(f"City:     {inq.city}")
    lines += ["", "Message:", "--------", inq.message, "", f"Admin: {link}"]
    return "\n".join(lines)
```

- [ ] **Step 3: Run + commit**

```bash
pytest tests/test_email.py -v
git add app/services/email.py tests/test_email.py
git commit -m "feat: SMTP inquiry notification"
```

---

### Task 5.2: Inquiry form submission handler

**Files:**
- Modify: `app/blueprints/public/views.py` — add `crows_nest_submit`
- Create: `app/templates/public/crows_nest_thanks.html`
- Test: `tests/test_inquiry_flow.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_inquiry_flow.py`:

```python
from unittest.mock import patch

from app.models import Inquiry


def test_submit_general_inquiry_persists_and_notifies(client, app):
    with patch("app.blueprints.public.views.send_inquiry_notification") as mock_notify:
        r = client.post("/crows-nest/submit", data={
            "kind": "general",
            "from_name": "Cap'n Salt",
            "email": "salt@y.test",
            "message": "Hello",
        }, follow_redirects=True)
        assert r.status_code == 200
        assert b"thank" in r.data.lower() or b"hoist" in r.data.lower()
        mock_notify.assert_called_once()

    with app.app_context():
        inq = Inquiry.query.first()
        assert inq is not None
        assert inq.from_name == "Cap'n Salt"
        assert inq.kind == "general"


def test_submit_booking_inquiry_keeps_booking_fields(client, app):
    with patch("app.blueprints.public.views.send_inquiry_notification"):
        r = client.post("/crows-nest/submit", data={
            "kind": "booking",
            "from_name": "Promoter",
            "email": "p@y",
            "phone": "555-1212",
            "event_date": "2027-10-15",
            "venue": "The Tavern",
            "city": "Boston",
            "message": "Renfest dates?",
        }, follow_redirects=True)
        assert r.status_code == 200

    with app.app_context():
        inq = Inquiry.query.filter_by(kind="booking").one()
        assert inq.venue == "The Tavern"
        assert inq.city == "Boston"
        assert str(inq.event_date) == "2027-10-15"


def test_submit_missing_required_fields_400(client, app):
    r = client.post("/crows-nest/submit", data={"kind": "general"})
    assert r.status_code in (400, 422)
```

- [ ] **Step 2: Run, confirm failure**

```bash
pytest tests/test_inquiry_flow.py -v
```

- [ ] **Step 3: Add submission handler to `app/blueprints/public/views.py`**

Add the import block at the top:

```python
from datetime import date
from app.services.email import send_inquiry_notification
from app.models import Inquiry
```

Append the handler:

```python
@bp.post("/crows-nest/submit")
def crows_nest_submit():
    kind = (request.form.get("kind") or "general").strip()
    if kind not in ("booking", "press", "general"):
        kind = "general"
    from_name = (request.form.get("from_name") or "").strip()
    email = (request.form.get("email") or "").strip()
    message = (request.form.get("message") or "").strip()
    if not from_name or not email or not message:
        return render_template("public/crows_nest.html",
                               press=PressAsset.query.order_by(PressAsset.sort_order).all(),
                               error="Name, email, and message are required."), 400

    event_date_raw = (request.form.get("event_date") or "").strip()
    event_date_val: date | None = None
    if event_date_raw:
        try:
            event_date_val = date.fromisoformat(event_date_raw)
        except ValueError:
            event_date_val = None

    inq = Inquiry(
        kind=kind, from_name=from_name, email=email,
        phone=(request.form.get("phone") or "").strip() or None,
        event_date=event_date_val,
        venue=(request.form.get("venue") or "").strip() or None,
        city=(request.form.get("city") or "").strip() or None,
        message=message,
    )
    db.session.add(inq); db.session.commit()
    send_inquiry_notification(inq)
    return render_template("public/crows_nest_thanks.html", inq=inq)
```

Add `from flask import request` to the existing imports.

- [ ] **Step 4: Add the thanks template**

Create `app/templates/public/crows_nest_thanks.html`:

```html
{% extends "base.html" %}
{% block title %}Message sent — The Grog Blossoms{% endblock %}
{% block content %}
<section class="px-6 py-24 max-w-2xl mx-auto">
  <h1 class="font-hand text-6xl text-accent-amber sketch-underline inline-block">Message Hoisted!</h1>
  <p class="mt-6 font-body text-on-surface-variant">
    Thank ye, {{ inq.from_name }}. We'll be in touch on the next tide.
  </p>
  <a href="{{ url_for('public.home') }}" class="inline-block mt-12 px-6 py-3 bg-accent-red text-white font-hand uppercase">Back to Port</a>
</section>
{% endblock %}
```

- [ ] **Step 5: CSRF exception for the submit endpoint? Already protected by Flask-WTF CSRFProtect via the hidden token in the form. Verify it stays in.

- [ ] **Step 6: Run tests**

```bash
pytest tests/test_inquiry_flow.py -v
```

Expected: 3 passed.

- [ ] **Step 7: Commit**

```bash
git add app/blueprints/public/views.py app/templates/public/crows_nest_thanks.html tests/test_inquiry_flow.py
git commit -m "feat: Crow's Nest form submit handler + email notification"
```

---

## Phase 6 — Block Editor

Phase 6 replaces the plain `body_md` field on `Post` with a block-based editor. Posts created before this phase keep working: the template renders `body_md` when `blocks` is empty.

### Task 6.1: Block schema + validator service

**Files:**
- Create: `app/services/blocks.py`
- Test: `tests/test_blocks.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_blocks.py`:

```python
import pytest
from app.services.blocks import BLOCK_TYPES, normalize_blocks, validate_block


def test_known_block_types():
    assert set(BLOCK_TYPES) == {
        "paragraph", "heading", "image", "pull_quote",
        "gallery_inline", "divider", "callout", "stat_pair", "bento_card",
    }


def test_validate_paragraph_ok():
    block = {"type": "paragraph", "id": "blk1", "data": {"markdown": "hello"}}
    validate_block(block)  # no raise


def test_validate_unknown_type_raises():
    with pytest.raises(ValueError):
        validate_block({"type": "unknown", "id": "x", "data": {}})


def test_validate_image_requires_url():
    with pytest.raises(ValueError):
        validate_block({"type": "image", "id": "x", "data": {"alt": "x"}})


def test_validate_heading_level_range():
    validate_block({"type": "heading", "id": "x", "data": {"level": 2, "text": "h"}})
    with pytest.raises(ValueError):
        validate_block({"type": "heading", "id": "x", "data": {"level": 5, "text": "h"}})


def test_normalize_blocks_assigns_ids():
    raw = [{"type": "paragraph", "data": {"markdown": "x"}}]
    out = normalize_blocks(raw)
    assert out[0]["id"]


def test_normalize_blocks_filters_invalid():
    raw = [
        {"type": "paragraph", "data": {"markdown": "x"}},
        {"type": "bogus", "data": {}},
    ]
    out = normalize_blocks(raw, strict=False)
    assert len(out) == 1


def test_normalize_blocks_strict_raises():
    raw = [{"type": "bogus", "data": {}}]
    with pytest.raises(ValueError):
        normalize_blocks(raw, strict=True)
```

- [ ] **Step 2: Run, confirm failure**

```bash
pytest tests/test_blocks.py -v
```

- [ ] **Step 3: Write `app/services/blocks.py`**

```python
"""Block schema validation + normalization.

Each block: { "id": str, "type": str, "data": dict }
"""
from __future__ import annotations

import secrets
from typing import Any


def _validate_paragraph(d: dict) -> None:
    if "markdown" not in d:
        raise ValueError("paragraph requires 'markdown'")


def _validate_heading(d: dict) -> None:
    level = d.get("level")
    if level not in (2, 3, 4):
        raise ValueError("heading 'level' must be 2, 3, or 4")
    if not d.get("text"):
        raise ValueError("heading requires 'text'")


def _validate_image(d: dict) -> None:
    if not d.get("url"):
        raise ValueError("image requires 'url'")
    if d.get("tilt") not in (None, -2, -1, 0, 1, 2):
        raise ValueError("image 'tilt' must be -2..2")
    if d.get("border") not in (None, "white", "amber", "red"):
        raise ValueError("image 'border' must be white|amber|red")


def _validate_pull_quote(d: dict) -> None:
    if not d.get("text"):
        raise ValueError("pull_quote requires 'text'")
    if d.get("style") not in (None, "torn", "amber-bar"):
        raise ValueError("pull_quote 'style' must be torn|amber-bar")


def _validate_gallery_inline(d: dict) -> None:
    if not isinstance(d.get("gallery_id"), int):
        raise ValueError("gallery_inline requires int 'gallery_id'")


def _validate_divider(d: dict) -> None:
    if d.get("style") not in (None, "torn", "dashed-amber", "sketch-line"):
        raise ValueError("divider 'style' invalid")


def _validate_callout(d: dict) -> None:
    if not d.get("text") or not d.get("label"):
        raise ValueError("callout requires 'label' and 'text'")
    if d.get("accent") not in (None, "red", "amber"):
        raise ValueError("callout 'accent' must be red|amber")


def _validate_stat_pair(d: dict) -> None:
    for side in ("left", "right"):
        s = d.get(side) or {}
        if not s.get("value") or not s.get("label"):
            raise ValueError(f"stat_pair.{side} requires value+label")


def _validate_bento_card(d: dict) -> None:
    if not d.get("title") or not d.get("body"):
        raise ValueError("bento_card requires title+body")


BLOCK_TYPES: dict[str, Any] = {
    "paragraph": _validate_paragraph,
    "heading": _validate_heading,
    "image": _validate_image,
    "pull_quote": _validate_pull_quote,
    "gallery_inline": _validate_gallery_inline,
    "divider": _validate_divider,
    "callout": _validate_callout,
    "stat_pair": _validate_stat_pair,
    "bento_card": _validate_bento_card,
}


def validate_block(block: dict) -> None:
    if not isinstance(block, dict):
        raise ValueError("block must be a dict")
    t = block.get("type")
    if t not in BLOCK_TYPES:
        raise ValueError(f"unknown block type: {t!r}")
    data = block.get("data") or {}
    if not isinstance(data, dict):
        raise ValueError("block 'data' must be a dict")
    BLOCK_TYPES[t](data)


def normalize_blocks(raw: list[dict], *, strict: bool = False) -> list[dict]:
    out: list[dict] = []
    for b in raw or []:
        try:
            validate_block(b)
        except ValueError:
            if strict:
                raise
            continue
        bid = b.get("id") or f"blk_{secrets.token_hex(8)}"
        out.append({"id": bid, "type": b["type"], "data": b.get("data") or {}})
    return out
```

- [ ] **Step 4: Run + commit**

```bash
pytest tests/test_blocks.py -v
git add app/services/blocks.py tests/test_blocks.py
git commit -m "feat: block schema + validator"
```

---

### Task 6.2: Block renderer macros

**Files:**
- Replace: `app/templates/_blocks/macros.html`
- Create: `app/templates/_blocks/paragraph.html`
- Create: `app/templates/_blocks/heading.html`
- Create: `app/templates/_blocks/image.html`
- Create: `app/templates/_blocks/pull_quote.html`
- Create: `app/templates/_blocks/gallery_inline.html`
- Create: `app/templates/_blocks/divider.html`
- Create: `app/templates/_blocks/callout.html`
- Create: `app/templates/_blocks/stat_pair.html`
- Create: `app/templates/_blocks/bento_card.html`

- [ ] **Step 1: Write `macros.html`**

```html
{% macro render_block(block) %}
  {% set t = block.type %}{% set d = block.data %}
  {% if t == "paragraph" %}{% include "_blocks/paragraph.html" %}
  {% elif t == "heading" %}{% include "_blocks/heading.html" %}
  {% elif t == "image" %}{% include "_blocks/image.html" %}
  {% elif t == "pull_quote" %}{% include "_blocks/pull_quote.html" %}
  {% elif t == "gallery_inline" %}{% include "_blocks/gallery_inline.html" %}
  {% elif t == "divider" %}{% include "_blocks/divider.html" %}
  {% elif t == "callout" %}{% include "_blocks/callout.html" %}
  {% elif t == "stat_pair" %}{% include "_blocks/stat_pair.html" %}
  {% elif t == "bento_card" %}{% include "_blocks/bento_card.html" %}
  {% endif %}
{% endmacro %}
```

- [ ] **Step 2: Each block template**

`paragraph.html`:

```html
<div class="prose prose-invert font-body-lg my-4">{{ d.markdown | pencil_highlight | markdown | safe }}</div>
```

`heading.html`:

```html
<h{{ d.level }} class="font-hand my-6 sketch-underline inline-block
  {% if d.level == 2 %}text-4xl{% elif d.level == 3 %}text-3xl{% else %}text-2xl{% endif %}">
  {{ d.text }}
</h{{ d.level }}>
```

`image.html`:

```html
<figure class="my-8 mx-auto max-w-3xl">
  <div class="noir-frame bg-surface p-2 sketch-border border-{{ d.border or 'white' }}
    {% if d.tilt %}{% if d.tilt < 0 %}rotate-[{{ d.tilt }}deg]{% else %}rotate-[{{ d.tilt }}deg]{% endif %}{% endif %}">
    <img src="{{ d.url }}" alt="{{ d.alt or '' }}"
      class="w-full {% if d.grayscale %}grayscale{% endif %}">
  </div>
  {% if d.caption %}<figcaption class="font-mono text-xs text-white/60 mt-2 text-center uppercase">{{ d.caption }}</figcaption>{% endif %}
</figure>
```

`pull_quote.html`:

```html
{% if d.style == "torn" %}
<blockquote class="border-2 border-dashed border-accent-amber p-6 my-8 max-w-2xl">
  <p class="font-hand text-2xl">"{{ d.text }}"</p>
  {% if d.attribution %}<footer class="mt-3 font-mono text-xs uppercase text-accent-amber">— {{ d.attribution }}</footer>{% endif %}
</blockquote>
{% else %}
<blockquote class="border-l-4 border-accent-red pl-6 py-2 my-8 max-w-2xl">
  <p class="font-body-lg text-on-surface">"{{ d.text }}"</p>
  {% if d.attribution %}<footer class="mt-2 font-hand text-accent-amber">— {{ d.attribution }}</footer>{% endif %}
</blockquote>
{% endif %}
```

`gallery_inline.html`:

```html
{% set _gallery = get_gallery(d.gallery_id) %}
{% if _gallery %}
<div class="my-8 grid grid-cols-2 md:grid-cols-3 gap-3">
  {% for img in _gallery.images %}
  <div class="noir-frame bg-surface p-1 sketch-border {% if loop.index is odd %}-rotate-1{% else %}rotate-1{% endif %}">
    <img src="{{ img.image_url }}" alt="{{ img.alt_text }}" class="w-full aspect-square object-cover grayscale">
  </div>
  {% endfor %}
</div>
{% endif %}
```

`divider.html`:

```html
{% if d.style == "torn" %}
<hr class="my-12 border-0 h-1 bg-[repeating-linear-gradient(90deg,#fff_0_8px,transparent_8px_16px)]">
{% elif d.style == "dashed-amber" %}
<hr class="my-12 border-t-2 border-dashed border-accent-amber">
{% else %}
<hr class="my-12 border-t border-white/40">
{% endif %}
```

`callout.html`:

```html
<div class="my-8 bg-surface-container-low p-6 border-2 border-dashed border-accent-{{ d.accent or 'amber' }} relative sketch-border max-w-2xl">
  <div class="absolute -top-3 -right-3 bg-accent-{{ d.accent or 'amber' }} text-background px-3 py-1 font-mono uppercase text-xs">{{ d.label }}</div>
  <p class="font-body text-on-surface">{{ d.text }}</p>
</div>
```

`stat_pair.html`:

```html
<div class="grid grid-cols-2 gap-4 my-8 max-w-md mx-auto">
  {% for side in [d.left, d.right] %}
  <div class="bg-accent-{{ side.accent or 'red' }} text-white p-4 text-center noir-frame {% if loop.index is odd %}rotate-1{% else %}-rotate-1{% endif %} sketch-border">
    <div class="text-5xl font-bold leading-none">{{ side.value }}</div>
    <div class="font-hand uppercase text-lg">{{ side.label }}</div>
  </div>
  {% endfor %}
</div>
```

`bento_card.html`:

```html
<a href="{{ d.link_url or '#' }}" class="block my-6 noir-frame bg-surface p-6 sketch-border border-accent-{{ d.accent or 'amber' }}">
  <h3 class="font-hand text-2xl mb-2 sketch-underline inline-block">{{ d.title }}</h3>
  <p class="text-on-surface-variant">{{ d.body }}</p>
  {% if d.link_text %}<span class="mt-4 inline-block font-hand text-accent-amber uppercase">{{ d.link_text }} →</span>{% endif %}
</a>
```

- [ ] **Step 3: Add `pencil_highlight` filter + `get_gallery` global**

In `app/__init__.py`, near the markdown filter:

```python
    import re

    @app.template_filter("pencil_highlight")
    def _pencil(text: str) -> str:
        if not text:
            return ""
        return re.sub(r"==(.+?)==",
                      r'<span class="bg-accent-amber/20 px-0.5">\1</span>',
                      text)

    from .models import Gallery as _Gallery
    @app.template_global("get_gallery")
    def _get_gallery(gid: int):
        return db.session.get(_Gallery, gid)
```

- [ ] **Step 4: Smoke test rendering**

Append to `tests/test_blocks.py`:

```python
def test_render_post_with_blocks(client, app):
    from app.extensions import db
    from app.models import Post
    from datetime import datetime

    with app.app_context():
        p = Post(slug="blocky", title="Blocky", author_name="C",
                 excerpt="", published_at=datetime.utcnow(),
                 blocks=[
                     {"id": "1", "type": "paragraph", "data": {"markdown": "Hello ==world==."}},
                     {"id": "2", "type": "heading", "data": {"level": 2, "text": "A heading"}},
                     {"id": "3", "type": "pull_quote", "data": {"text": "yo", "style": "amber-bar"}},
                 ])
        db.session.add(p); db.session.commit()
    r = client.get("/log/blocky")
    assert r.status_code == 200
    body = r.data.decode()
    assert "Hello" in body
    assert "A heading" in body
    assert "yo" in body
```

- [ ] **Step 5: Run + commit**

```bash
pytest tests/test_blocks.py -v
git add app/templates/_blocks/ app/__init__.py tests/test_blocks.py
git commit -m "feat: block renderer macros for all v1 block types"
```

---

### Task 6.3: Block editor admin UI (HTMX)

**Files:**
- Create: `app/blueprints/admin/blocks.py` — HTMX endpoints
- Create: `app/templates/admin/_blocks/<type>_form.html` — one per type
- Create: `app/templates/admin/posts_edit.html` — replaces generic form for Posts
- Modify: `app/blueprints/admin/posts.py` — bypass generic CRUD for edit
- Test: `tests/test_admin_blocks.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_admin_blocks.py`:

```python
import json
from app.extensions import db
from app.models import Post, User


def _login(client, app):
    with app.app_context():
        u = User(oidc_sub="b-admin", email="a@b", display_name="A")
        u.groups = ["gb-developer"]
        db.session.add(u); db.session.commit()
        uid = u.id
    with client.session_transaction() as sess:
        sess["_user_id"] = str(uid); sess["_fresh"] = True


def test_blocks_save_persists(client, app):
    with app.app_context():
        p = Post(slug="bp", title="T", author_name="C", excerpt="")
        db.session.add(p); db.session.commit()
        pid = p.id
    _login(client, app)
    payload = [
        {"type": "paragraph", "data": {"markdown": "hi"}},
        {"type": "heading", "data": {"level": 2, "text": "X"}},
    ]
    r = client.post(f"/admin/posts/{pid}/blocks/save",
                    data={"blocks": json.dumps(payload),
                          "csrf_token": "ignored"},
                    headers={"X-CSRFToken": "ignored"})
    # If CSRF blocks, disable for the test app via app.config["WTF_CSRF_ENABLED"] = False
    assert r.status_code in (200, 302)
    with app.app_context():
        fresh = db.session.get(Post, pid)
        assert len(fresh.blocks) == 2
        assert fresh.blocks[0]["type"] == "paragraph"


def test_blocks_add_endpoint_returns_partial(client, app):
    _login(client, app)
    r = client.get("/admin/blocks/new/paragraph")
    assert r.status_code == 200
    assert b"markdown" in r.data.lower() or b"paragraph" in r.data.lower()
```

In `tests/conftest.py`, disable CSRF in tests by adding to the fixture:

```python
@pytest.fixture
def app():
    from app import create_app
    app = create_app(config_name="testing")
    app.config["WTF_CSRF_ENABLED"] = False
    with app.app_context():
        from app.extensions import db
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
```

- [ ] **Step 2: Write `app/blueprints/admin/blocks.py`**

```python
"""HTMX endpoints for the post block editor."""
import json

from flask import abort, flash, redirect, render_template, request, url_for

from app.extensions import db
from app.models import Post
from app.services.blocks import BLOCK_TYPES, normalize_blocks
from . import bp, require_admin_group


@bp.get("/blocks/new/<block_type>", endpoint="blocks_new_partial")
@require_admin_group
def blocks_new_partial(block_type: str):
    if block_type not in BLOCK_TYPES:
        abort(404)
    import secrets
    return render_template(
        f"admin/_blocks/{block_type}_form.html",
        block={"id": f"blk_{secrets.token_hex(6)}", "type": block_type, "data": {}},
    )


@bp.post("/posts/<int:id>/blocks/save", endpoint="posts_blocks_save")
@require_admin_group
def posts_blocks_save(id: int):
    post = db.session.get(Post, id) or abort(404)
    raw = request.form.get("blocks") or "[]"
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        flash("Invalid blocks JSON.", "error")
        return redirect(url_for("admin.posts_edit", id=id))
    post.blocks = normalize_blocks(parsed, strict=False)
    db.session.commit()
    flash("Blocks saved.", "success")
    return redirect(url_for("admin.posts_edit", id=id))
```

- [ ] **Step 3: Write `app/templates/admin/posts_edit.html`**

```html
{% extends "admin/base.html" %}
{% block title %}Edit Post — Admin{% endblock %}
{% block content %}
<h1 class="text-3xl mb-6">Edit Post</h1>

<form method="post" action="{{ url_for('admin.posts_edit', id=post.id) }}" class="space-y-4 max-w-3xl mb-12">
  {{ form.hidden_tag() }}
  {% for field in form if field.name not in ('csrf_token', 'body_md') %}
  <div>
    <label class="block text-xs uppercase tracking-widest text-white/60 mb-1">{{ field.label.text }}</label>
    {{ field(class_="w-full bg-black/40 border border-white/20 px-3 py-2 text-white font-mono") }}
  </div>
  {% endfor %}
  <button class="px-6 py-2 bg-white text-black uppercase tracking-widest">Save Fields</button>
</form>

<h2 class="text-2xl mb-4">Body Blocks</h2>

<div id="block-editor" class="space-y-3 max-w-3xl">
  {% for b in post.blocks %}
    {% include "admin/_blocks/" ~ b.type ~ "_form.html" with context %}
  {% endfor %}
</div>

<div class="mt-4 flex gap-2 flex-wrap">
  {% for t in block_types %}
  <button hx-get="{{ url_for('admin.blocks_new_partial', block_type=t) }}"
          hx-target="#block-editor" hx-swap="beforeend"
          class="px-3 py-1 border border-white/40 text-xs uppercase">+ {{ t }}</button>
  {% endfor %}
</div>

<form method="post" action="{{ url_for('admin.posts_blocks_save', id=post.id) }}" class="mt-6">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
  <input type="hidden" name="blocks" id="blocks-json">
  <button type="submit" onclick="serialize()" class="px-6 py-2 bg-white text-black uppercase tracking-widest">Save Blocks</button>
</form>

<script src="https://unpkg.com/htmx.org@1.9.12"></script>
<script>
function serialize() {
  const blocks = [];
  document.querySelectorAll('#block-editor > .block-row').forEach(row => {
    const type = row.dataset.type;
    const data = {};
    row.querySelectorAll('[data-field]').forEach(el => {
      let v = el.value;
      if (el.dataset.cast === 'int') v = parseInt(v, 10);
      data[el.dataset.field] = v;
    });
    blocks.push({ id: row.dataset.id, type, data });
  });
  document.getElementById('blocks-json').value = JSON.stringify(blocks);
}
function removeBlock(btn) { btn.closest('.block-row').remove(); }
function moveBlock(btn, dir) {
  const row = btn.closest('.block-row');
  const sibling = dir === 'up' ? row.previousElementSibling : row.nextElementSibling;
  if (sibling) { row.parentNode.insertBefore(dir === 'up' ? row : sibling, dir === 'up' ? sibling : row); }
}
</script>
{% endblock %}
```

- [ ] **Step 4: Per-block-type admin form partials**

The same pattern for every type. Example for `paragraph`:

Create `app/templates/admin/_blocks/paragraph.html`:

```html
<div class="block-row border border-white/20 p-3" data-type="paragraph" data-id="{{ block.id }}">
  <div class="flex justify-between items-center mb-2">
    <span class="font-mono text-xs uppercase text-accent-amber">Paragraph</span>
    <div class="flex gap-1">
      <button type="button" onclick="moveBlock(this,'up')" class="px-2 py-1 border border-white/20 text-xs">↑</button>
      <button type="button" onclick="moveBlock(this,'down')" class="px-2 py-1 border border-white/20 text-xs">↓</button>
      <button type="button" onclick="removeBlock(this)" class="px-2 py-1 border border-red-500/40 text-red-300 text-xs">×</button>
    </div>
  </div>
  <textarea data-field="markdown" rows="3" class="w-full bg-black/40 border border-white/20 px-2 py-1 font-mono text-sm" placeholder="Markdown. Use ==text== for pencil highlight.">{{ block.data.markdown or "" }}</textarea>
</div>
```

Create `heading.html`:

```html
<div class="block-row border border-white/20 p-3" data-type="heading" data-id="{{ block.id }}">
  <div class="flex justify-between items-center mb-2">
    <span class="font-mono text-xs uppercase text-accent-amber">Heading</span>
    <div class="flex gap-1">
      <button type="button" onclick="moveBlock(this,'up')" class="px-2 py-1 border border-white/20 text-xs">↑</button>
      <button type="button" onclick="moveBlock(this,'down')" class="px-2 py-1 border border-white/20 text-xs">↓</button>
      <button type="button" onclick="removeBlock(this)" class="px-2 py-1 border border-red-500/40 text-red-300 text-xs">×</button>
    </div>
  </div>
  <select data-field="level" data-cast="int" class="bg-black/40 border border-white/20 px-2 py-1 mr-2">
    {% for n in [2,3,4] %}<option value="{{n}}" {% if block.data.level == n %}selected{% endif %}>H{{ n }}</option>{% endfor %}
  </select>
  <input data-field="text" value="{{ block.data.text or '' }}" class="bg-black/40 border border-white/20 px-2 py-1 w-full mt-2">
</div>
```

Create `image.html`:

```html
<div class="block-row border border-white/20 p-3" data-type="image" data-id="{{ block.id }}">
  <div class="flex justify-between items-center mb-2">
    <span class="font-mono text-xs uppercase text-accent-amber">Image</span>
    <div class="flex gap-1">
      <button type="button" onclick="moveBlock(this,'up')" class="px-2 py-1 border border-white/20 text-xs">↑</button>
      <button type="button" onclick="moveBlock(this,'down')" class="px-2 py-1 border border-white/20 text-xs">↓</button>
      <button type="button" onclick="removeBlock(this)" class="px-2 py-1 border border-red-500/40 text-red-300 text-xs">×</button>
    </div>
  </div>
  <input data-field="url" value="{{ block.data.url or '' }}" placeholder="CDN URL" class="w-full bg-black/40 border border-white/20 px-2 py-1 font-mono text-sm">
  <input data-field="caption" value="{{ block.data.caption or '' }}" placeholder="Caption" class="w-full bg-black/40 border border-white/20 px-2 py-1 mt-1">
  <input data-field="alt" value="{{ block.data.alt or '' }}" placeholder="Alt text" class="w-full bg-black/40 border border-white/20 px-2 py-1 mt-1">
  <div class="mt-1 flex gap-2">
    <select data-field="tilt" data-cast="int" class="bg-black/40 border border-white/20 px-2 py-1">
      {% for t in [-2,-1,0,1,2] %}<option value="{{ t }}" {% if block.data.tilt == t %}selected{% endif %}>tilt {{ t }}°</option>{% endfor %}
    </select>
    <select data-field="border" class="bg-black/40 border border-white/20 px-2 py-1">
      {% for b in ['white','amber','red'] %}<option value="{{ b }}" {% if block.data.border == b %}selected{% endif %}>{{ b }}</option>{% endfor %}
    </select>
  </div>
</div>
```

Create `pull_quote.html`:

```html
<div class="block-row border border-white/20 p-3" data-type="pull_quote" data-id="{{ block.id }}">
  <div class="flex justify-between items-center mb-2">
    <span class="font-mono text-xs uppercase text-accent-amber">Pull Quote</span>
    <div class="flex gap-1">
      <button type="button" onclick="moveBlock(this,'up')" class="px-2 py-1 border border-white/20 text-xs">↑</button>
      <button type="button" onclick="moveBlock(this,'down')" class="px-2 py-1 border border-white/20 text-xs">↓</button>
      <button type="button" onclick="removeBlock(this)" class="px-2 py-1 border border-red-500/40 text-red-300 text-xs">×</button>
    </div>
  </div>
  <textarea data-field="text" rows="2" class="w-full bg-black/40 border border-white/20 px-2 py-1">{{ block.data.text or '' }}</textarea>
  <input data-field="attribution" value="{{ block.data.attribution or '' }}" placeholder="Attribution" class="w-full bg-black/40 border border-white/20 px-2 py-1 mt-1">
  <select data-field="style" class="bg-black/40 border border-white/20 px-2 py-1 mt-1">
    {% for s in ['amber-bar','torn'] %}<option value="{{ s }}" {% if block.data.style == s %}selected{% endif %}>{{ s }}</option>{% endfor %}
  </select>
</div>
```

Create `gallery_inline.html`:

```html
<div class="block-row border border-white/20 p-3" data-type="gallery_inline" data-id="{{ block.id }}">
  <div class="flex justify-between items-center mb-2">
    <span class="font-mono text-xs uppercase text-accent-amber">Inline Gallery</span>
    <div class="flex gap-1">
      <button type="button" onclick="moveBlock(this,'up')" class="px-2 py-1 border border-white/20 text-xs">↑</button>
      <button type="button" onclick="moveBlock(this,'down')" class="px-2 py-1 border border-white/20 text-xs">↓</button>
      <button type="button" onclick="removeBlock(this)" class="px-2 py-1 border border-red-500/40 text-red-300 text-xs">×</button>
    </div>
  </div>
  <input data-field="gallery_id" data-cast="int" value="{{ block.data.gallery_id or '' }}" placeholder="Gallery ID" class="bg-black/40 border border-white/20 px-2 py-1">
</div>
```

Create `divider.html`:

```html
<div class="block-row border border-white/20 p-3" data-type="divider" data-id="{{ block.id }}">
  <div class="flex justify-between items-center mb-2">
    <span class="font-mono text-xs uppercase text-accent-amber">Divider</span>
    <button type="button" onclick="removeBlock(this)" class="px-2 py-1 border border-red-500/40 text-red-300 text-xs">×</button>
  </div>
  <select data-field="style" class="bg-black/40 border border-white/20 px-2 py-1">
    {% for s in ['torn','dashed-amber','sketch-line'] %}<option value="{{ s }}" {% if block.data.style == s %}selected{% endif %}>{{ s }}</option>{% endfor %}
  </select>
</div>
```

Create `callout.html`:

```html
<div class="block-row border border-white/20 p-3" data-type="callout" data-id="{{ block.id }}">
  <div class="flex justify-between items-center mb-2">
    <span class="font-mono text-xs uppercase text-accent-amber">Callout</span>
    <button type="button" onclick="removeBlock(this)" class="px-2 py-1 border border-red-500/40 text-red-300 text-xs">×</button>
  </div>
  <input data-field="label" value="{{ block.data.label or '' }}" placeholder="Label (e.g. URGENT LOG)" class="w-full bg-black/40 border border-white/20 px-2 py-1">
  <textarea data-field="text" rows="2" class="w-full bg-black/40 border border-white/20 px-2 py-1 mt-1">{{ block.data.text or '' }}</textarea>
  <select data-field="accent" class="bg-black/40 border border-white/20 px-2 py-1 mt-1">
    {% for a in ['amber','red'] %}<option value="{{ a }}" {% if block.data.accent == a %}selected{% endif %}>{{ a }}</option>{% endfor %}
  </select>
</div>
```

Create `stat_pair.html`:

```html
<div class="block-row border border-white/20 p-3" data-type="stat_pair" data-id="{{ block.id }}">
  <div class="flex justify-between items-center mb-2">
    <span class="font-mono text-xs uppercase text-accent-amber">Stat Pair</span>
    <button type="button" onclick="removeBlock(this)" class="px-2 py-1 border border-red-500/40 text-red-300 text-xs">×</button>
  </div>
  <p class="text-xs text-white/40 mb-2">Use the JSON textarea (left/right) — UI to be expanded later.</p>
  <textarea data-field="left" data-cast="json" rows="3" class="w-full bg-black/40 border border-white/20 px-2 py-1 font-mono text-xs">{{ block.data.left | tojson }}</textarea>
  <textarea data-field="right" data-cast="json" rows="3" class="w-full bg-black/40 border border-white/20 px-2 py-1 font-mono text-xs mt-1">{{ block.data.right | tojson }}</textarea>
</div>
```

Note: the `serialize()` JS handles `data-cast="int"`. Add a JSON cast variant — update `serialize()` in `posts_edit.html`:

```javascript
function serialize() {
  const blocks = [];
  document.querySelectorAll('#block-editor > .block-row').forEach(row => {
    const type = row.dataset.type;
    const data = {};
    row.querySelectorAll('[data-field]').forEach(el => {
      let v = el.value;
      if (el.dataset.cast === 'int') v = parseInt(v, 10);
      else if (el.dataset.cast === 'json') {
        try { v = JSON.parse(v); } catch { v = null; }
      }
      data[el.dataset.field] = v;
    });
    blocks.push({ id: row.dataset.id, type, data });
  });
  document.getElementById('blocks-json').value = JSON.stringify(blocks);
}
```

Create `bento_card.html`:

```html
<div class="block-row border border-white/20 p-3" data-type="bento_card" data-id="{{ block.id }}">
  <div class="flex justify-between items-center mb-2">
    <span class="font-mono text-xs uppercase text-accent-amber">Bento Card</span>
    <button type="button" onclick="removeBlock(this)" class="px-2 py-1 border border-red-500/40 text-red-300 text-xs">×</button>
  </div>
  <input data-field="title" value="{{ block.data.title or '' }}" placeholder="Title" class="w-full bg-black/40 border border-white/20 px-2 py-1">
  <textarea data-field="body" rows="2" class="w-full bg-black/40 border border-white/20 px-2 py-1 mt-1">{{ block.data.body or '' }}</textarea>
  <input data-field="link_url" value="{{ block.data.link_url or '' }}" placeholder="Link URL" class="w-full bg-black/40 border border-white/20 px-2 py-1 mt-1">
  <input data-field="link_text" value="{{ block.data.link_text or '' }}" placeholder="Link text" class="w-full bg-black/40 border border-white/20 px-2 py-1 mt-1">
  <select data-field="accent" class="bg-black/40 border border-white/20 px-2 py-1 mt-1">
    {% for a in ['amber','red','white'] %}<option value="{{ a }}" {% if block.data.accent == a %}selected{% endif %}>{{ a }}</option>{% endfor %}
  </select>
</div>
```

- [ ] **Step 5: Override Posts edit view to render the custom template**

Replace `app/blueprints/admin/posts.py`:

```python
from flask import abort, flash, redirect, render_template, request, url_for
from flask_wtf import FlaskForm
from wtforms import DateTimeLocalField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, URL

from app.extensions import db
from app.models import Post
from app.services.blocks import BLOCK_TYPES
from . import bp, require_admin_group
from ._crud import register_crud


class PostForm(FlaskForm):
    slug = StringField("Slug", validators=[DataRequired(), Length(max=255)])
    title = StringField("Title", validators=[DataRequired(), Length(max=255)])
    author_name = StringField("Author", validators=[DataRequired(), Length(max=255)])
    published_at = DateTimeLocalField("Published at", validators=[Optional()], format="%Y-%m-%dT%H:%M")
    hero_image_url = StringField("Hero image URL", validators=[Optional(), URL()])
    excerpt = TextAreaField("Excerpt", validators=[Optional()])
    body_md = TextAreaField("Legacy markdown (only used if no blocks)", validators=[Optional()])


# Register generic CRUD for list/new/delete; override edit.
register_crud(
    bp, prefix="posts", label="Ship's Log Post",
    model=Post, form_cls=PostForm,
    list_cols=[
        ("Title", lambda p: p.title),
        ("Slug", lambda p: p.slug),
        ("Published", lambda p: p.published_at.strftime("%Y-%m-%d %H:%M") if p.published_at else "draft"),
    ],
    order_by=Post.created_at.desc(),
)


# Replace the generic edit endpoint with one that uses the block editor template.
@bp.route("/posts/<int:id>", methods=("GET", "POST"), endpoint="posts_edit")
@require_admin_group
def posts_edit(id: int):
    post = db.session.get(Post, id) or abort(404)
    form = PostForm(obj=post)
    if request.method == "POST" and form.validate_on_submit():
        form.populate_obj(post)
        db.session.commit()
        flash("Post fields saved.", "success")
        return redirect(url_for("admin.posts_edit", id=id))
    return render_template("admin/posts_edit.html",
                           post=post, form=form, block_types=list(BLOCK_TYPES))
```

Flask raises `AssertionError` when two views try to claim the same endpoint name. Add an `exclude` parameter to `_crud.register_crud()` so `posts.py` can opt out of the generic `edit` view and provide its own.

Replace `app/blueprints/admin/_crud.py` with:

```python
"""Tiny generic CRUD factory.

Each resource module calls register_crud() with:
  - bp           : the admin blueprint
  - prefix       : URL prefix and template tag, e.g. 'posts'
  - model        : SQLAlchemy model
  - form_cls     : WTForms class
  - list_cols    : list of (header, getter) for the list table
  - order_by     : ordering for the list query
  - exclude      : tuple of operations to skip ('list','new','edit','delete')
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from flask import flash, redirect, render_template, url_for

from app.blueprints.admin import require_admin_group
from app.extensions import db


def register_crud(
    bp,
    *,
    prefix: str,
    label: str,
    model: type,
    form_cls: type,
    list_cols: Iterable[tuple[str, Callable[[Any], Any]]],
    order_by=None,
    after_save: Callable[[Any], None] | None = None,
    exclude: tuple[str, ...] = (),
) -> None:
    list_cols = list(list_cols)

    if "list" not in exclude:
        @bp.get(f"/{prefix}/", endpoint=f"{prefix}_list")
        @require_admin_group
        def _list():
            q = model.query
            if order_by is not None:
                q = q.order_by(order_by)
            items = q.all()
            return render_template(
                "admin/_list.html",
                label=label, prefix=prefix, items=items, cols=list_cols,
            )

    if "new" not in exclude:
        @bp.route(f"/{prefix}/new", methods=("GET", "POST"), endpoint=f"{prefix}_new")
        @require_admin_group
        def _new():
            form = form_cls()
            if form.validate_on_submit():
                obj = model()
                form.populate_obj(obj)
                db.session.add(obj); db.session.commit()
                if after_save: after_save(obj)
                flash(f"{label} created.", "success")
                return redirect(url_for(f"admin.{prefix}_list"))
            return render_template("admin/_form.html",
                                   label=label, prefix=prefix, form=form, mode="new")

    if "edit" not in exclude:
        @bp.route(f"/{prefix}/<int:id>", methods=("GET", "POST"), endpoint=f"{prefix}_edit")
        @require_admin_group
        def _edit(id: int):
            obj = db.session.get(model, id) or _abort_404()
            form = form_cls(obj=obj)
            if form.validate_on_submit():
                form.populate_obj(obj); db.session.commit()
                if after_save: after_save(obj)
                flash(f"{label} updated.", "success")
                return redirect(url_for(f"admin.{prefix}_list"))
            return render_template("admin/_form.html",
                                   label=label, prefix=prefix, form=form, mode="edit",
                                   obj=obj)

    if "delete" not in exclude:
        @bp.post(f"/{prefix}/<int:id>/delete", endpoint=f"{prefix}_delete")
        @require_admin_group
        def _delete(id: int):
            obj = db.session.get(model, id) or _abort_404()
            db.session.delete(obj); db.session.commit()
            flash(f"{label} deleted.", "success")
            return redirect(url_for(f"admin.{prefix}_list"))


def _abort_404():
    from flask import abort
    abort(404)
```

Then `posts.py` calls it as `register_crud(..., exclude=("edit",))` — see the next code block.

- [ ] **Step 6: Wire `blocks.py` import**

`app/blueprints/admin/__init__.py`:

```python
from . import posts, crew, tour_dates, galleries, music, merch, press, inquiries, scuttlebutt, assets, blocks as _blocks, settings as _settings  # noqa
```

- [ ] **Step 7: Run tests**

```bash
pytest tests/test_admin_blocks.py tests/test_blocks.py -v
```

Expected: passes.

- [ ] **Step 8: Commit**

```bash
git add app/blueprints/admin/blocks.py app/blueprints/admin/posts.py app/blueprints/admin/_crud.py app/templates/admin/posts_edit.html app/templates/admin/_blocks/ tests/test_admin_blocks.py tests/conftest.py
git commit -m "feat: block editor admin UI"
```

---

## Phase 7 — Deployment

### Task 7.1: Dockerfile + entrypoint

**Files:**
- Create: `Dockerfile`
- Create: `docker/entrypoint.sh`

- [ ] **Step 1: Write `Dockerfile`**

```dockerfile
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 ca-certificates wget tini \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

COPY app ./app
COPY migrations ./migrations
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN mkdir -p /data && chown -R nobody:nogroup /data
USER nobody

EXPOSE 8000

ENTRYPOINT ["/usr/bin/tini", "--", "/entrypoint.sh"]
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8000", "--access-logfile", "-", "app:create_app()"]
```

- [ ] **Step 2: Write `docker/entrypoint.sh`**

```bash
#!/bin/sh
set -e

echo "→ Running database migrations…"
flask --app app db upgrade

echo "→ Starting: $*"
exec "$@"
```

- [ ] **Step 3: Commit**

```bash
mkdir -p docker
# (write entrypoint.sh and Dockerfile per steps above)
git add Dockerfile docker/
git commit -m "feat: Dockerfile + entrypoint with auto-migrate"
```

---

### Task 7.2: docker-compose for mycelium

**Files:**
- Create: `docker-compose.yml`

- [ ] **Step 1: Write `docker-compose.yml`**

```yaml
services:
  app:
    image: ghcr.io/oltyan/mm-grogblossoms:${TAG:-latest}
    container_name: mm-grogblossoms-app
    env_file: /opt/mm-grogblossoms/secrets.env
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=sqlite:////data/grogblossoms.db
      - SESSION_COOKIE_SECURE=true
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
      start_period: 20s

  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: mm-grogblossoms-tunnel
    command: tunnel --no-autoupdate run
    environment:
      - TUNNEL_TOKEN=${CF_TUNNEL_TOKEN}
    restart: unless-stopped
    depends_on:
      app:
        condition: service_healthy
    labels:
      - homebody.service=mm-grogblossoms-tunnel
```

Also create `docker-compose.override.example.yml` documenting the local-dev overlay:

```yaml
# Copy to docker-compose.override.yml for local-on-mycelium debugging
services:
  app:
    ports:
      - "8000:8000"
```

- [ ] **Step 2: Commit**

```bash
git add docker-compose.yml docker-compose.override.example.yml
git commit -m "feat: docker-compose with cloudflared sidecar"
```

---

### Task 7.3: Backup script + cron unit

**Files:**
- Create: `scripts/backup.sh`
- Create: `scripts/restore.sh`
- Create: `docker/cron.example`

- [ ] **Step 1: Write `scripts/backup.sh`**

```bash
#!/usr/bin/env bash
# Run nightly on mycelium (outside containers).
# Snapshots SQLite via .backup, then restic to Backblaze B2.

set -euo pipefail

DATA_DIR=${DATA_DIR:-/opt/mm-grogblossoms/data}
SNAPSHOT_DIR=${SNAPSHOT_DIR:-/opt/mm-grogblossoms/backups}
TS=$(date +%F)

mkdir -p "$SNAPSHOT_DIR"
sqlite3 "$DATA_DIR/grogblossoms.db" ".backup '$SNAPSHOT_DIR/grogblossoms-$TS.db'"

# Restic config: RESTIC_REPOSITORY, RESTIC_PASSWORD, B2_ACCOUNT_ID, B2_ACCOUNT_KEY
# loaded from /opt/mm-grogblossoms/backup.env
set -a; . /opt/mm-grogblossoms/backup.env; set +a

restic backup "$SNAPSHOT_DIR/grogblossoms-$TS.db"
restic forget --prune --keep-daily 14 --keep-weekly 6 --keep-monthly 6

# Local rotation: keep 7 days of snapshots on disk
find "$SNAPSHOT_DIR" -name 'grogblossoms-*.db' -mtime +7 -delete
```

- [ ] **Step 2: Write `scripts/restore.sh`**

```bash
#!/usr/bin/env bash
# Restore the latest restic snapshot to a chosen target.

set -euo pipefail
TARGET=${1:?Usage: restore.sh /path/to/output-dir}
set -a; . /opt/mm-grogblossoms/backup.env; set +a
restic restore latest --target "$TARGET"
echo "Restored. Stop the app, replace /opt/mm-grogblossoms/data/grogblossoms.db, then start."
```

- [ ] **Step 3: Document cron entry**

Create `docker/cron.example`:

```
# /etc/cron.d/mm-grogblossoms — install on mycelium as root
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin

# Nightly at 03:17
17 3 * * * root /opt/mm-grogblossoms/repo/scripts/backup.sh >> /var/log/mm-grogblossoms-backup.log 2>&1
```

- [ ] **Step 4: Commit**

```bash
chmod +x scripts/backup.sh scripts/restore.sh
git add scripts/backup.sh scripts/restore.sh docker/cron.example
git commit -m "feat: backup + restore scripts (restic → B2)"
```

---

### Task 7.4: Jenkinsfile

**Files:**
- Create: `Jenkinsfile.deploy`

- [ ] **Step 1: Write `Jenkinsfile.deploy`**

```groovy
pipeline {
    agent any

    environment {
        IMAGE = "ghcr.io/oltyan/mm-grogblossoms"
        GHCR  = credentials('ghcr-push')
        MYCELIUM_HOST = credentials('mycelium-ssh-host')
    }

    options { timestamps(); ansiColor('xterm') }

    stages {
        stage('Checkout') { steps { checkout scm } }

        stage('Lint + Test') {
            agent { docker { image 'python:3.12-slim'; reuseNode true } }
            steps {
                sh '''
                    pip install --no-cache-dir -e ".[dev]"
                    ruff check app tests scripts
                    pytest -v
                '''
            }
        }

        stage('Build + push') {
            steps {
                sh '''
                    echo "$GHCR_PSW" | docker login ghcr.io -u "$GHCR_USR" --password-stdin
                    SHA=$(git rev-parse --short HEAD)
                    docker build -t $IMAGE:$SHA -t $IMAGE:latest .
                    docker push $IMAGE:$SHA
                    docker push $IMAGE:latest
                '''
            }
        }

        stage('Deploy to mycelium') {
            steps {
                sshagent(credentials: ['mycelium-ssh-key']) {
                    sh '''
                        ssh -o StrictHostKeyChecking=accept-new $MYCELIUM_HOST '
                            cd /opt/mm-grogblossoms/repo &&
                            git pull --ff-only &&
                            docker compose pull &&
                            docker compose up -d
                        '
                    '''
                }
            }
        }

        stage('Smoke') {
            steps {
                sh 'curl -fsS --max-time 30 https://grogblossoms.com/healthz || (echo "Healthcheck failed" && exit 1)'
            }
        }
    }

    post {
        failure {
            // Slack / email notification hook — placeholder
            echo 'Deploy failed'
        }
    }
}
```

- [ ] **Step 2: Commit**

```bash
git add Jenkinsfile.deploy
git commit -m "ci: Jenkins deploy pipeline"
```

---

### Task 7.5: One-time mycelium bootstrap runbook

**Files:**
- Create: `docs/runbook-deploy.md`

- [ ] **Step 1: Write runbook**

```markdown
# mm-grogblossoms — Deploy Runbook

## One-time mycelium bootstrap

```bash
ssh mycelium
sudo mkdir -p /opt/mm-grogblossoms/{data,backups,repo}
sudo chown -R $USER:$USER /opt/mm-grogblossoms
cd /opt/mm-grogblossoms
git clone https://github.com/oltyan/mm-grogblossoms.git repo
cd repo

# Secrets
cat > /opt/mm-grogblossoms/secrets.env <<EOF
SECRET_KEY=$(openssl rand -hex 32)
OIDC_CLIENT_ID=...
OIDC_CLIENT_SECRET=...
OIDC_DISCOVERY_URL=https://fa.example/.well-known/openid-configuration
OIDC_GROUP_REQUIRED=gb-developer
CDN_BASE_URL=https://design-assets.musicalmycology.org/
S3_BUCKET=__PLACEHOLDER__
S3_PREFIX=grogblossoms/
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=__PLACEHOLDER__
AWS_SECRET_ACCESS_KEY=__PLACEHOLDER__
SMTP_HOST=smtp.fastmail.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
SMTP_FROM=no-reply@grogblossoms.com
CONTACT_EMAIL=chris@grogblossoms.com
SESSION_COOKIE_SECURE=true
EOF
chmod 600 /opt/mm-grogblossoms/secrets.env

# Cloudflare Tunnel token (created in the CF dashboard for grogblossoms.com)
echo "CF_TUNNEL_TOKEN=eyJh…" >> /opt/mm-grogblossoms/secrets.env

# Backup env
cat > /opt/mm-grogblossoms/backup.env <<EOF
RESTIC_REPOSITORY=b2:bucket-name:mm-grogblossoms
RESTIC_PASSWORD=$(openssl rand -hex 32)   # SAVE THIS — required to restore
B2_ACCOUNT_ID=...
B2_ACCOUNT_KEY=...
EOF
chmod 600 /opt/mm-grogblossoms/backup.env

# First start
cd /opt/mm-grogblossoms/repo
docker compose up -d
docker compose logs -f --tail 100
```

## Cloudflare Tunnel setup (once, in CF dashboard)

1. Zero Trust → Networks → Tunnels → Create a tunnel (named `mm-grogblossoms`).
2. Copy the tunnel token into `CF_TUNNEL_TOKEN` in `/opt/mm-grogblossoms/secrets.env`.
3. Add a public hostname:
   - Subdomain: blank (apex) — only works if zone is on Cloudflare; otherwise use `www`.
   - Domain: `grogblossoms.com`.
   - Service: `http://app:8000`.
4. Add the second hostname `www.grogblossoms.com` mirroring the first.

## DNS

Per spec § DNS: zone delegation to Cloudflare is the recommended path. Update NS records at the registrar to Cloudflare's nameservers; CF dashboard handles the rest. Falls back to keeping Route 53 + `www` canonical if you keep the zone there.

## Deploy a change

`git push` to `main` → Jenkins `mm-grogblossoms-deploy` job triggers → image pushed to GHCR → SSH to mycelium → `docker compose pull && docker compose up -d` → curl healthcheck.

## Restore from backup

```bash
ssh mycelium
sudo systemctl stop docker-compose@mm-grogblossoms  # if using systemd; or:
cd /opt/mm-grogblossoms/repo && docker compose stop app

mkdir -p /tmp/restore && /opt/mm-grogblossoms/repo/scripts/restore.sh /tmp/restore
cp /tmp/restore/opt/mm-grogblossoms/backups/grogblossoms-YYYY-MM-DD.db /opt/mm-grogblossoms/data/grogblossoms.db

docker compose start app
```
```

- [ ] **Step 2: Commit**

```bash
git add docs/runbook-deploy.md
git commit -m "docs: deploy runbook"
```

---

### Task 7.6: README polish + final smoke

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace `README.md` with full version**

```markdown
# mm-grogblossoms

The Grog Blossoms — CMS + public site, deployed on mycelium behind Cloudflare Tunnel.

Part of the `mm-*` fleet. Brand: **Tavern Noir** (brutalist + hand-drawn).

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

- Templates absorb the mockups in `../gb-website/stitch_the_grog_blossoms_website/` — preserve Tavern Noir class names.
- Public images reference the mm-sporekles CDN — never store user uploads locally.
- Admin is OIDC-gated; the `gb-developer` group claim is required.
```

- [ ] **Step 2: Final full test run**

```bash
pytest -v
```

Expected: all tests across all phases pass.

- [ ] **Step 3: Commit + tag v1**

```bash
git add README.md
git commit -m "docs: README"
git tag v1.0.0
git push origin main --tags
```

---

## Self-review checklist

After all phases land, verify against the spec:

- [ ] Every content model in spec § "Content model" exists in `app/models.py` and has an admin CRUD module.
- [ ] Every public route in spec § "Public routes" returns 200 for seeded data (or 404 for unpublished slugs).
- [ ] `/admin/*` is gated by `gb-developer` group. Anon → 302 to login; wrong group → 403.
- [ ] All v1 block types in spec § "Block format" have admin form partials AND public renderer templates.
- [ ] Inquiry submission persists + dispatches SMTP (or no-ops if SMTP unset).
- [ ] Image upload service raises `UploaderNotProvisioned` (placeholder path) AND `register_url` works.
- [ ] CDN URLs are validated against `CDN_BASE_URL + S3_PREFIX`.
- [ ] Healthcheck (`/healthz`) returns `{"status":"ok"}`.
- [ ] `feed.xml`, `sitemap.xml`, `robots.txt` render correctly; admin paths blocked in robots.
- [ ] Cloudflare Tunnel container starts after app healthcheck passes.
- [ ] Nightly backup snapshot script writes both locally and to restic/B2.
- [ ] Spec § "Open items / explicitly deferred" — verify which carry forward as TODOs.
- [ ] Docs are committed: spec, plan, runbook, README.
- [ ] All pytest tests pass: `pytest -v`.

## Postscript (2026-05-20) — sporekles architecture shift

The storage-service sections of this plan (the `S3_BUCKET/S3_PREFIX/AWS_*`
config, the `UploaderNotProvisioned` placeholder, the `register_url()` admin
form, the boto3 import) describe v1 as it was authored. Those parts are
**obsolete** as of 2026-05-20 and have been replaced; the surrounding
plan/checklist is retained as historical record.

Replacement:

- `app/services/storage.py` is now `SporeklesClient`, an HTTP multipart client
  for the mm-sporekles sidecar API. POSTs `{api_base}/{tenant}/assets` with
  the file, sends `X-Auth-Request-Email/User/Groups` headers (oauth2-proxy
  model — sporekles does not check Bearer tokens), parses the response
  `entry` into an `Asset` row.
- Config: drop `S3_*`, `AWS_*`, `boto3`. Add `SPOREKLES_API_BASE`
  (default `http://mm-sporekles-api:3000`), `SPOREKLES_TENANT` (`gb`).
  `CDN_BASE_URL` defaults to `https://design-assets.grogblossoms.com/`.
- Admin: the "Paste CDN URL" form is gone. `/admin/assets/upload` is a real
  multipart upload that streams to the sidecar.
- Docker compose joins the `shared-tunnel` network so it can reach
  `mm-sporekles-api` by service name.

Why the shift: sporekles became multi-tenant (each tenant in `tenants.yml`
gets its own bucket + distro + IAM users + FA group). Direct boto3 from
multiple consuming apps would have duplicated content-type sniffing,
manifest regen, and CloudFront invalidation in every consumer. Centralising
those concerns in the sidecar removed that duplication and let each tenant
keep its own CDN hostname.








