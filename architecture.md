# gb-website — Architecture

Companion to [docs/runbook-deploy.md](docs/runbook-deploy.md) — the runbook
covers *how* you operate the system, this covers *what* the system is.

## Where things run

- **gb-website-app, gb_data volume, shared-tunnel network, cloudflared,
  mm-homebody, mm-sporekles-api:** mycelium (macOS, Docker Desktop).
- **mm-jenkins:** AWS EC2 (`jenkins.musicalmycology.org`). It builds and
  publishes the image; it does not run the site. See
  [How deploys work](#how-deploys-work).
- **Container image:** ECR repository `gb-website` in the Musical Mycology
  AWS account (`365647376064.dkr.ecr.us-east-1.amazonaws.com/gb-website`).
- **DNS zone `grogblossoms.com`, apex → `www` redirect:** Cloudflare. The
  domain is registered at Amazon Registrar but delegated to Cloudflare
  nameservers. See [DNS lives in Cloudflare](#dns-lives-in-cloudflare).
- **Restic backups:** Backblaze B2, config at `/opt/gb-website/backup.env`
  on mycelium.
- **Application secrets** (`SECRET_KEY`, OIDC client id/secret, future SMTP
  credentials): stored as Jenkins JCasC string credentials; the copy the
  container reads is `secrets.env` in the mycelium checkout. See
  [Secrets](#secrets).

## Public request path

```
www.grogblossoms.com
        ▼  (Cloudflare DNS — proxied Tunnel record for the shared mm tunnel)
Cloudflare tunnel
        ▼
cloudflared on mycelium
        ▼  (ingress map pushed by mm-homebody, keyed on Docker labels)
gb-website-app:8000 on shared-tunnel network
        ▼
SQLite at /data/grogblossoms.db in gb-website-deploy_gb_data volume
```

Apex `grogblossoms.com` is a proxied CNAME to `www.grogblossoms.com` in
Cloudflare DNS, plus a Cloudflare Redirect Rule ("Apex to www") that 301s
`http*://grogblossoms.com/*` to `https://www.grogblossoms.com/${2}` with the
query string preserved. Both were created by hand in the Cloudflare
dashboard on 2026-11-13 and are not managed by code in this repo.

## mycelium host

- macOS with Docker Desktop — *not* Linux. `systemctl` does not apply.
- Repos are checked out under `/Users/chris/Projects/<name>/`, not `/opt/`.
  The filesystem is case-insensitive, so `Projects/` and `projects/`
  resolve to the same directory.
- `/opt/` is reserved for paths that need a stable system location:
  `/opt/gb-website/backup.env`, `/opt/mm-sporekles-api/`,
  `/opt/mm-deploy-broker/`, etc.

## Gotchas

### Volume name has a project prefix

The named volume on disk is `gb-website-deploy_gb_data`, not `gb_data`.
Compose prefixes volume names with the project name, and the first deploys
ran from a Jenkins workspace called `gb-website-deploy`.

[docker-compose.yml](docker-compose.yml) pins that project name with a
top-level `name: gb-website-deploy`, so every `docker compose` call from the
repo root lands on the existing volume without a `-p` flag:

```bash
cd /Users/chris/Projects/gb-website
docker compose up -d --wait
```

Do not change or remove the `name:` key. With any other project name compose
creates a fresh empty volume and the real database is orphaned.

### mm-homebody owns cloudflared and `shared-tunnel`

`shared-tunnel` is declared `external: true` in
[docker-compose.yml](docker-compose.yml) — it's created and maintained by
mm-homebody's compose project, not by gb-website. If mm-homebody is down:

- Existing cloudflared ingress map keeps working (public site stays up).
- New container restarts don't get re-registered, so a `down && up` of
  gb-website-app while homebody is down orphans the route until homebody
  comes back.

When mm-homebody's compose restarts cloudflared (same project), the tunnel
reloads ingress — expect transient 502s on `www` until homebody re-pushes
the gb-website entry.

### DNS lives in Cloudflare

The `grogblossoms.com` zone is served by Cloudflare nameservers. The
Route 53 hosted zone is no longer authoritative — records written there
have no effect.

Records in the Cloudflare zone as of 2026-11-13:

| Name | Type | Target | Proxy |
|---|---|---|---|
| `grogblossoms.com` | CNAME | `www.grogblossoms.com` | Proxied |
| `www.grogblossoms.com` | Tunnel | shared mm tunnel (`workspace-mcp`) | Proxied |
| `design-assets.grogblossoms.com` | CNAME | CloudFront (mm-sporekles CDN) | DNS only |
| `_….design-assets.grogblossoms.com` | CNAME | ACM validation for the CDN cert | DNS only |

There are no MX/SPF/DKIM/DMARC records — the domain cannot receive mail.

**2026-11-13 outage:** the bare domain stopped resolving because the zone
had been delegated to Cloudflare without an apex record; the previous
apex redirect (Route 53 alias → CloudFront, PR #15) was stranded in the
old zone. `www` was unaffected. Fixed by adding the apex CNAME and
redirect rule above. When moving a zone between providers, export and
diff the full record set first.

Not yet confirmed: whether mm-homebody's CF-DNS step now manages the `www`
record for this zone, or whether it is still a hand-made record.
`mm-homebody/rules.yml` still annotates the zone as "lives in Route 53;
manual DNS".

## Secrets

Application secrets are stored as Jenkins JCasC string credentials (decided
2026-11-16: no change of secret store).

| Credential ID | Maps to |
|---|---|
| `gb-website-secret-key` | `SECRET_KEY` |
| `gb-website-oidc-client-id` | `OIDC_CLIENT_ID` |
| `gb-website-oidc-client-secret` | `OIDC_CLIENT_SECRET` |
| `gb-website-smtp` (deferred — no mail service provisioned) | `SMTP_USER`, `SMTP_PASSWORD` |

The pipeline no longer delivers them. Jenkins on EC2 cannot write to
mycelium, so [Jenkinsfile.deploy](Jenkinsfile.deploy) does not read or render
secrets, and the mycelium pull script is installed without env rendering. The
container reads `secrets.env` in `/Users/chris/Projects/gb-website` on
mycelium. That file was copied by hand from the archived Jenkins workspace on
2026-05-25 and is now the working copy; it also carries the non-secret config
that used to be inlined in the Jenkinsfile (OIDC discovery URL, sporekles
base, CDN base, SMTP from, contact email, tenant).

Rotating a secret is two manual steps: update the Jenkins credential, then
edit `secrets.env` on mycelium and recreate the container. See
[docs/runbook-deploy.md](docs/runbook-deploy.md).

## How deploys work

```
merge to main
   │  (Jenkins pollSCM, every 5 min)
   ▼
Jenkins on EC2: lint + test → docker build → push gb-website:<sha> and :latest to ECR
   │                                             │
   │ (only if FORCE_DEPLOY=true)                 │ (always, within 5 min)
   ▼                                             ▼
POST /_deploy-trigger/gb-website  ─►  mycelium: /opt/gb-website/deploy-pull.sh
                                         pull :latest, retag as gb-website:latest,
                                         tag the old image :rollback-prev,
                                         docker compose up -d --force-recreate
```

- A green Jenkins build means the image was published, not that the site
  was updated. The deploy result is in `~/Library/Logs/gb-website-deploy.log`
  on mycelium. There is no uptime monitor on the deploy yet.
- The pull script pulls images, not git. A change to
  [docker-compose.yml](docker-compose.yml) only takes effect after a
  `git pull` in the mycelium checkout.
- Database migrations run in the container entrypoint (`flask db upgrade`).
- The mycelium side is installed by
  `mm-jenkins/bin/mycelium-install-service.sh`; the ECR repository,
  deploy-trigger allowlist entry and job definition live in mm-jenkins.
- Design: [docs/specs/2026-11-16-jenkins-deploy-migration-design.md](docs/specs/2026-11-16-jenkins-deploy-migration-design.md).

## Jenkins build history (before the ECR migration)

Under the original Jenkinsfile, `gb-website-deploy` succeeded once (build 10,
2026-05-22) and failed on every run after Jenkins moved to EC2: lint, tests
and the image build passed, then `docker compose up` ran on the Jenkins host,
where mycelium's network and volume do not exist. The job also had no
trigger. Kept for reference.

Build history, from `/opt/mm-jenkins/data/jobs/gb-website-deploy/builds/`:

| Build | Date | Result | Cause |
|---|---|---|---|
| 1 | 2026-05-21 | Failed | Clone returned 403 (repo was not yet readable without credentials) |
| 2 | 2026-05-21 | Failed | Jenkinsfile used `ansiColor`, a plugin option Jenkins doesn't have |
| 3 | 2026-05-21 | Failed | Missing `ghcr-push` credential (registry push, since removed) |
| 4 | 2026-05-21 | Failed | `pip install -e` — multiple top-level packages in a flat layout |
| 5 | 2026-05-21 | Failed | `ruff` found 102 lint errors |
| 6 | 2026-05-21 | Failed | Docker `mounts denied` on a host bind mount (led to the named volume) |
| 7 | 2026-05-22 | Failed | Smoke test could not connect to `www` (DNS/tunnel not ready) |
| 8, 9 | 2026-05-22 | Failed | Smoke test got 502 (curl ran before the container was healthy) |
| 10 | 2026-05-22 | **Success** | Last run with Jenkins on mycelium |
| 11, 13 | 2026-06-11 | Failed | `network shared-tunnel declared as external, but could not be found` |
| 12 | 2026-06-11 | Aborted | Jenkins `failed to run ps` (superseded by 13) |
| 14 | 2026-11-13 | Failed | Same `shared-tunnel` error |
| 15 | 2026-11-16 | Failed | Same `shared-tunnel` error |

A manual deploy on mycelium still works at any time and is the fallback if
the pull path is broken:

```bash
cd /Users/chris/Projects/gb-website && git pull --ff-only
docker compose up -d --build --wait
```
