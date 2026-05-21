# gb-website — Deploy Runbook

## Architecture in one paragraph

gb-website runs on mycelium as a single Flask container. It joins the
`shared-tunnel` Docker network so mm-homebody can register it in the
**one** Cloudflare tunnel that fronts all mycelium services. The
`grogblossoms.com` zone lives in Route 53 (not Cloudflare), so DNS
records are created manually pointing at `<tunnel-uuid>.cfargotunnel.com`.
Admin uploads call the mm-sporekles sidecar at
`http://mm-sporekles-api:3000` on the same `shared-tunnel` network.

## Prerequisites (do once, outside this repo)

### 1. FA-OIDC application

Register `gb-website` in FusionAuth (`auth.musicalmycology.org`,
`mm-internal` tenant). Key settings:

- Authorized redirect URL: `https://www.grogblossoms.com/auth/oidc/callback`
- JWT tab: ID Token + Access Token signing key → `mm-internal default RS256 key`
- JWT tab: JWT populate lambda → the same one bound to mm-mycelium-gateway
- Roles tab: add Application Role `gb-developer`
- Group `gb-developer` → bound to this application's `gb-developer` role
- Register chris's FA user against this application

Capture **Client ID** and **Client Secret** and stash them in Jenkins as
the `gb-website-oidc-client-id` and `gb-website-oidc-client-secret`
credentials (provisioned in `mm-jenkins/jenkins.yaml`). The deploy job
renders them into `secrets.env` on every build — never hand-edit the
file on mycelium.

### 2. mm-homebody allowed_zones

`grogblossoms.com` must be in `mm-homebody/rules.yml` `allowed_zones`
before mm-homebody will accept this container's registration. PR
required to add it. (Optional: also add per-zone DNS opt-out so homebody
doesn't try to create a CF CNAME for a Route 53 zone.)

### 3. Route 53 records (manual — `grogblossoms.com` is not in CF)

Two records in the `grogblossoms.com` zone. The tunnel UUID is the
shared mm tunnel (currently `b58b6f1b-c70e-4321-88e7-bd0bf6ae8a62`,
the `workspace-mcp` tunnel — confirm from CF dashboard).

| Name | Type | Value |
|---|---|---|
| `www.grogblossoms.com` | `CNAME` | `<tunnel-uuid>.cfargotunnel.com` |
| `grogblossoms.com` (apex) | `A` ALIAS | S3 redirect bucket → `https://www.grogblossoms.com/` (or omit until v1.1) |

Route 53 doesn't support CNAME at zone apex; the S3 redirect bucket is
the standard workaround for `www`-canonical sites.

### 4. `shared-tunnel` Docker network

```bash
ssh mycelium
docker network ls | grep -q shared-tunnel || docker network create shared-tunnel
```

Should already exist if mm-sporekles is up.

## One-time mycelium bootstrap

```bash
ssh mycelium
sudo mkdir -p /opt/gb-website/{data,backups}
sudo chown -R "$USER:$(id -gn)" /opt/gb-website
```

(`$USER:$USER` won't work on macOS — Mac users don't have a per-user
primary group; default is `staff`. `id -gn` resolves the right group
on whichever OS this is run on.)

That's it for on-host setup. The repo itself is checked out into the
Jenkins workspace each build — there is no permanent `/opt/gb-website/repo`
clone to keep in sync. `secrets.env` is rendered into that workspace
from Jenkins credentials by `Jenkinsfile.deploy` on every deploy (see
the mm-sporekles `api/.env` pattern this mirrors), so do not create one
by hand.

Provision these credentials in `mm-jenkins/jenkins.yaml` before the
first deploy fires:

| Credential ID | Kind | Maps to |
|---|---|---|
| `gb-website-secret-key` | string | `SECRET_KEY` |
| `gb-website-oidc-client-id` | string | `OIDC_CLIENT_ID` |
| `gb-website-oidc-client-secret` | string | `OIDC_CLIENT_SECRET` |
| `gb-website-smtp` | usernamePassword | `SMTP_USER` / `SMTP_PASSWORD` |

Non-secret config (OIDC discovery URL, sporekles API base, CDN base
URL, SMTP host/port/from, contact email, tenant) is inlined in the
Jenkinsfile heredoc — no Jenkins credential needed.

`backup.env` stays out-of-band — restic/B2 keys are restore-time
credentials and don't belong in the per-deploy render path. Bootstrap
once:

```bash
ssh mycelium
cat > /opt/gb-website/backup.env <<EOF
RESTIC_REPOSITORY=b2:bucket-name:gb-website
RESTIC_PASSWORD=$(openssl rand -hex 32)   # SAVE THIS — required to restore
B2_ACCOUNT_ID=...
B2_ACCOUNT_KEY=...
EOF
chmod 600 /opt/gb-website/backup.env
```

Then trigger the first Jenkins build of `gb-website-deploy`. It will
push the image, render `secrets.env` into the workspace, and
`docker compose up -d` directly on the controller (mm-jenkins is itself
on mycelium — no ssh hop). Tail `docker compose logs -f --tail 100` from
the workspace dir to watch the first start.

There is **no** `cloudflared` container in this stack. mm-homebody owns
the single mycelium cloudflared instance and the only Cloudflare API
token. gb-website declares its hostname via `homebody.*` Docker labels
(see `docker-compose.yml`).

## Verifying after first start

1. `docker compose ps` — `gb-website-app` should be `Up (healthy)`.
2. `docker logs mm-homebody --tail 50 | grep gb-website` — homebody should log a registration line. If you see `zone 'grogblossoms.com' not in allowed_zones`, step 2 of Prerequisites isn't done yet.
3. `docker exec mm-homebody cat /output/config.yml | grep grogblossoms` — should show the ingress entry.
4. After Route 53 records propagate: `curl -I https://www.grogblossoms.com/healthz` → `200 OK`.
5. Smoke: log into `/admin/`, upload a file in `/admin/assets/`, verify it lands at `https://design-assets.grogblossoms.com/assets/<name>`.

## Deploy a change

`git push` to `main` → Jenkins `gb-website-deploy` job triggers → `withCredentials` renders `secrets.env` in the workspace → `docker compose build` builds the image locally → `docker compose up -d` runs on the controller (mm-jenkins is on mycelium, same host as the container — no registry round-trip, matches the mm-sporekles pattern) → curl healthcheck against `https://www.grogblossoms.com/healthz`. mm-homebody picks up label changes on container restart with no manual reconcile.

## Restore from backup

There is no permanent on-host clone — restore from a throwaway clone
plus the live Jenkins workspace for compose context.

```bash
ssh mycelium
# Stop the running app via its container name (no working-dir dependency).
docker stop gb-website-app

# Pull the restore script from a temp clone.
git clone --depth 1 https://github.com/oltyan/gb-website.git /tmp/gb-website-restore
mkdir -p /tmp/restore && /tmp/gb-website-restore/scripts/restore.sh /tmp/restore
cp /tmp/restore/opt/gb-website/backups/grogblossoms-YYYY-MM-DD.db /opt/gb-website/data/grogblossoms.db

# Re-trigger the Jenkins deploy job to bring the app back up with the
# restored DB — that's the canonical path (renders secrets.env + runs
# compose). Trigger from the Jenkins UI or `gh workflow run`-equivalent.
```
