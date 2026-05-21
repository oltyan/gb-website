# gb-website — Deploy Runbook

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
OIDC_DISCOVERY_URL=https://fa.example/.well-known/openid-configuration
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

# Cloudflare Tunnel token (created in the CF dashboard for grogblossoms.com)
echo "CF_TUNNEL_TOKEN=eyJh…" >> /opt/gb-website/secrets.env

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

## Sporekles sidecar network

The app reaches the mm-sporekles uploader at `http://mm-sporekles-api:3000`
on the `shared-tunnel` Docker network. That network is created by
mm-sporekles' own deploy. If gb-website is brought up first, create the
network manually:

```bash
docker network create shared-tunnel
```

After mm-sporekles deploys, both stacks share the network and gb-website
can resolve `mm-sporekles-api` by service name.

## Cloudflare Tunnel setup (once, in CF dashboard)

1. Zero Trust → Networks → Tunnels → Create a tunnel (named `gb-website`).
2. Copy the tunnel token into `CF_TUNNEL_TOKEN` in `/opt/gb-website/secrets.env`.
3. Add a public hostname:
   - Subdomain: blank (apex) — only works if zone is on Cloudflare; otherwise use `www`.
   - Domain: `grogblossoms.com`.
   - Service: `http://app:8000`.
4. Add the second hostname `www.grogblossoms.com` mirroring the first.

## DNS

Per spec § DNS: zone delegation to Cloudflare is the recommended path. Update NS records at the registrar to Cloudflare's nameservers; CF dashboard handles the rest. Falls back to keeping Route 53 + `www` canonical if you keep the zone there.

## Deploy a change

`git push` to `main` → Jenkins `gb-website-deploy` job triggers → image pushed to GHCR → SSH to mycelium → `docker compose pull && docker compose up -d` → curl healthcheck.

## Restore from backup

```bash
ssh mycelium
sudo systemctl stop docker-compose@gb-website  # if using systemd; or:
cd /opt/gb-website/repo && docker compose stop app

mkdir -p /tmp/restore && /opt/gb-website/repo/scripts/restore.sh /tmp/restore
cp /tmp/restore/opt/gb-website/backups/grogblossoms-YYYY-MM-DD.db /opt/gb-website/data/grogblossoms.db

docker compose start app
```
