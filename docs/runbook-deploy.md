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
