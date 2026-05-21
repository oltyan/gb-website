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

Capture **Client ID** and **Client Secret** for `secrets.env`.

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
sudo mkdir -p /opt/gb-website/{data,backups,repo}
sudo chown -R $USER:$USER /opt/gb-website
cd /opt/gb-website
git clone https://github.com/oltyan/gb-website.git repo
cd repo

# Secrets
cat > /opt/gb-website/secrets.env <<EOF
SECRET_KEY=$(openssl rand -hex 32)
OIDC_CLIENT_ID=...
OIDC_CLIENT_SECRET=...
OIDC_DISCOVERY_URL=https://auth.musicalmycology.org/.well-known/openid-configuration
OIDC_GROUP_REQUIRED=gb-developer
CDN_BASE_URL=https://design-assets.grogblossoms.com/
SPOREKLES_API_BASE=http://mm-sporekles-api:3000
SPOREKLES_TENANT=gb
SMTP_HOST=smtp.fastmail.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
SMTP_FROM=no-reply@grogblossoms.com
CONTACT_EMAIL=chris@grogblossoms.com
SESSION_COOKIE_SECURE=true
EOF
chmod 600 /opt/gb-website/secrets.env

# Backup env
cat > /opt/gb-website/backup.env <<EOF
RESTIC_REPOSITORY=b2:bucket-name:gb-website
RESTIC_PASSWORD=$(openssl rand -hex 32)   # SAVE THIS — required to restore
B2_ACCOUNT_ID=...
B2_ACCOUNT_KEY=...
EOF
chmod 600 /opt/gb-website/backup.env

# First start
cd /opt/gb-website/repo
docker compose up -d
docker compose logs -f --tail 100
```

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

`git push` to `main` → Jenkins `gb-website-deploy` job triggers → image pushed to GHCR → SSH to mycelium → `docker compose pull && docker compose up -d` → curl healthcheck. mm-homebody picks up label changes on container restart with no manual reconcile.

## Restore from backup

```bash
ssh mycelium
cd /opt/gb-website/repo && docker compose stop app

mkdir -p /tmp/restore && /opt/gb-website/repo/scripts/restore.sh /tmp/restore
cp /tmp/restore/opt/gb-website/backups/grogblossoms-YYYY-MM-DD.db /opt/gb-website/data/grogblossoms.db

docker compose start app
```
