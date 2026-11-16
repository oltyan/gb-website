# gb-website — Deploy Runbook

## Architecture in one paragraph

gb-website runs on mycelium as a single Flask container. It joins the
`shared-tunnel` Docker network so mm-homebody can register it in the
**one** Cloudflare tunnel that fronts all mycelium services. The
`grogblossoms.com` zone is served by Cloudflare DNS: `www` is a proxied
Tunnel record and the apex redirects to `www` (see Prerequisites § 3).
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
credentials (provisioned in `mm-jenkins/jenkins.yaml`), and put the same
values in `secrets.env` on mycelium (see "Rotate a secret").

### 2. mm-homebody allowed_zones

`grogblossoms.com` must be in `mm-homebody/rules.yml` `allowed_zones`
before mm-homebody will accept this container's registration. PR
required to add it.

### 3. Cloudflare DNS records

The `grogblossoms.com` zone is served by Cloudflare (registered at Amazon
Registrar, delegated to Cloudflare nameservers). Route 53 is not
authoritative. The tunnel is the shared mm tunnel (currently
`b58b6f1b-c70e-4321-88e7-bd0bf6ae8a62`, the `workspace-mcp` tunnel —
confirm from CF dashboard).

| Name | Type | Value | Proxy |
|---|---|---|---|
| `www.grogblossoms.com` | Tunnel | shared mm tunnel | Proxied |
| `grogblossoms.com` (apex) | `CNAME` | `www.grogblossoms.com` | Proxied |

Plus one Redirect Rule (Rules → Redirect Rules), "Apex to www":
wildcard `http*://grogblossoms.com/*` → `https://www.grogblossoms.com/${2}`,
301, preserve query string. The apex record must stay proxied or the rule
never runs.

### 4. `shared-tunnel` Docker network

```bash
ssh mycelium
docker network ls | grep -q shared-tunnel || docker network create shared-tunnel
```

Should already exist if mm-sporekles is up.

## One-time mycelium bootstrap

```bash
ssh mycelium
# /opt/gb-website holds backup.env (restic + B2 credentials). It does
# NOT hold the database — that lives in a Docker named volume (gb_data)
# managed by docker-compose, no host-side path required. Snapshot
# landing dir for backup.sh defaults to $HOME/gb-website-backups
# (override with SNAPSHOT_DIR env var).
sudo mkdir -p /opt/gb-website
sudo chown -R "$USER:$(id -gn)" /opt/gb-website
mkdir -p "$HOME/gb-website-backups"
```

(`$USER:$USER` won't work on macOS — Mac users don't have a per-user
primary group; default is `staff`. `id -gn` resolves the right group
on whichever OS this is run on.)

The repo is checked out at `/Users/chris/Projects/gb-website` on mycelium.
The pull script runs `docker compose` from there, and the container reads
`secrets.env` from that directory. On mycelium that path is a symlink to
`/opt/gb-website/secrets.env`, so the real file sits outside the git checkout
next to `backup.env`. Jenkins runs on EC2 and cannot write to mycelium, so the
file is created and maintained by hand:

```
SECRET_KEY=...
OIDC_CLIENT_ID=...
OIDC_CLIENT_SECRET=...
OIDC_DISCOVERY_URL=https://auth.musicalmycology.org/.well-known/openid-configuration
OIDC_GROUP_REQUIRED=gb-developer
CDN_BASE_URL=https://design-assets.grogblossoms.com/
SPOREKLES_API_BASE=http://mm-sporekles-api:3000
SPOREKLES_TENANT=gb
SMTP_FROM=no-reply@grogblossoms.com
CONTACT_EMAIL=...
```

`chmod 600 secrets.env`. The three secrets are also stored as Jenkins
credentials (`gb-website-secret-key`, `gb-website-oidc-client-id`,
`gb-website-oidc-client-secret` in `mm-jenkins/jenkins.yaml`); keep the two
in step.

`backup.env` stays out-of-band — restic/B2 keys are restore-time
credentials, kept separate from the application's env file. Bootstrap
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

Then install the pull script and its 5-minute launchd timer (needs the
`gb-website` ECR repository and `flock`; both come from the mm-jenkins
setup):

```bash
bash ~/projects/mm-jenkins/bin/mycelium-install-service.sh \
  --service gb-website \
  --ecr-repo 365647376064.dkr.ecr.us-east-1.amazonaws.com/gb-website \
  --compose-dir /Users/chris/Projects/gb-website \
  --container-name gb-website-app \
  --local-image gb-website:latest \
  --no-kuma-monitoring
```

The first Jenkins build of `gb-website-deploy` publishes the image; the
timer deploys it within 5 minutes. Watch
`~/Library/Logs/gb-website-deploy.log`.

There is **no** `cloudflared` container in this stack. mm-homebody owns
the single mycelium cloudflared instance and the only Cloudflare API
token. gb-website declares its hostname via `homebody.*` Docker labels
(see `docker-compose.yml`).

## Verifying after first start

1. `docker compose ps` — `gb-website-app` should be `Up (healthy)`.
2. `docker logs mm-homebody --tail 50 | grep gb-website` — homebody should log a registration line. If you see `zone 'grogblossoms.com' not in allowed_zones`, step 2 of Prerequisites isn't done yet.
3. `docker exec mm-homebody cat /output/config.yml | grep grogblossoms` — should show the ingress entry.
4. After DNS records propagate: `curl -I https://www.grogblossoms.com/healthz` → `200 OK`, and `curl -I https://grogblossoms.com/` → `301` to `https://www.grogblossoms.com/`.
5. Smoke: log into `/admin/`, upload a file in `/admin/assets/`, verify it lands at `https://design-assets.grogblossoms.com/assets/<name>`.

## Deploy a change

Merge to `main`. Jenkins (`gb-website-deploy`, polls every 5 minutes) runs
lint and tests, builds the image and pushes it to ECR. The launchd timer on
mycelium pulls it within 5 minutes and recreates `gb-website-app`.

- **Deploy immediately:** run the job with `FORCE_DEPLOY` ticked.
- **Did it deploy?** A green build only means the image was published.
  Check `~/Library/Logs/gb-website-deploy.log` on mycelium (`deployed`,
  `no-op`, or `FAILED`), or `docker ps` for the container's age.
- **Compose file changes** (labels, healthcheck, environment) are not picked
  up by the pull script. After merging one, run on mycelium:
  `cd /Users/chris/Projects/gb-website && git pull --ff-only && docker compose up -d --wait`

mm-homebody picks up label changes on container restart with no manual
reconcile.

## Roll back

On mycelium:

```bash
docker tag 365647376064.dkr.ecr.us-east-1.amazonaws.com/gb-website:rollback-prev gb-website:latest
cd /Users/chris/Projects/gb-website && docker compose up -d --force-recreate
```

The next timer tick re-pulls `:latest` from ECR and would undo this, so also
revert the bad commit on `main` and let Jenkins publish the fix. For a bad
migration, restore the database (below).

## Rotate a secret

1. Update the Jenkins credential (mm-jenkins, JCasC seed).
2. On mycelium, edit `/opt/gb-website/secrets.env` (the checkout's `secrets.env` is a symlink to it).
3. `docker compose up -d --force-recreate` in that directory.

## Manual deploy (fallback)

Works at any time, independent of Jenkins and ECR:

```bash
cd /Users/chris/Projects/gb-website && git pull --ff-only
docker compose up -d --build --wait
```

The compose file pins the project name, so no `-p` flag is needed.

Once the pull timer is installed this is a temporary override: the next
tick sees the container is not on the ECR `:latest` image and replaces the
local build with it. To keep a manual build in place, unload the launchd
agent first.

## Restore from backup

DB lives in the `gb_data` Docker named volume. `scripts/restore.sh`
extracts the latest restic snapshot and `docker cp`s it into the volume
via the (stopped) `gb-website-app` container.

```bash
ssh mycelium

# One-shot restore via the script (latest snapshot by default; pass a
# restic snapshot id to pick a specific one).
git clone --depth 1 https://github.com/oltyan/gb-website.git /tmp/gb-website-restore
/tmp/gb-website-restore/scripts/restore.sh                 # latest
# or:
# /tmp/gb-website-restore/scripts/restore.sh <snapshot-id>
```

The script stops the container, copies the restored DB into
`/data/grogblossoms.db` inside the volume, and restarts. No host-side
data path involved.
