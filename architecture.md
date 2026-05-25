# gb-website — Architecture

Companion to [docs/runbook-deploy.md](docs/runbook-deploy.md) — the runbook
covers *how* you operate the system, this covers *what* the system is.

## Where things run

- **gb-website-app, gb_data volume, shared-tunnel network, cloudflared,
  mm-homebody, mm-sporekles-api:** mycelium (macOS, Docker Desktop).
- **mm-jenkins:** AWS as of 2026-05 (was on mycelium). See [Open questions](#open-questions-jenkins-in-aws-migration)
  — the runbook hasn't been updated yet and still assumes Jenkins-on-mycelium.
- **Route 53 zone `grogblossoms.com`, CloudFront apex redirect:** AWS. See
  [infra/main.tf](infra/main.tf).
- **Restic backups:** Backblaze B2, config at `/opt/gb-website/backup.env`
  on mycelium.
- **Application secrets** (`SECRET_KEY`, OIDC client id/secret, future SMTP
  credentials): Jenkins JCasC string credentials, rendered into `secrets.env`
  per build by [Jenkinsfile.deploy](Jenkinsfile.deploy). Jenkins itself is
  in AWS as of 2026-05, but the JCasC pattern is unchanged — the secret
  material remains protected by the AWS pipeline. See [Secrets](#secrets).

## Public request path

```
www.grogblossoms.com
        ▼  (Route 53 CNAME — manual record, not managed by mm-homebody)
<tunnel-uuid>.cfargotunnel.com
        ▼  (Cloudflare tunnel)
cloudflared on mycelium
        ▼  (ingress map pushed by mm-homebody, keyed on Docker labels)
gb-website-app:8000 on shared-tunnel network
        ▼
SQLite at /data/grogblossoms.db in gb-website-deploy_gb_data volume
```

Apex `grogblossoms.com` is a CloudFront distribution that 301s to `www`
(PR #15, see [infra/main.tf](infra/main.tf)).

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
Compose prefixes volume names with the project name; the Jenkins job is
`gb-website-deploy`, so the workspace dir (and therefore the project name)
was `gb-website-deploy`.

**Implication for manual deploys:** always pass `-p gb-website-deploy`:

```bash
cd /Users/chris/Projects/gb-website
docker compose -p gb-website-deploy up -d --wait
```

Without `-p`, compose creates a fresh empty `gb-website_gb_data` and the
surviving DB is orphaned.

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

### DNS not in Cloudflare

`grogblossoms.com` lives in Route 53. mm-homebody's CF-DNS step is a no-op
for this zone (and logs an error until per-zone DNS opt-out lands upstream).
The `www` CNAME → `<tunnel-uuid>.cfargotunnel.com` is a **manual** Route 53
record. If the tunnel is destroyed and recreated with a new UUID, that
CNAME goes stale and has to be hand-updated.

## Secrets

Application secrets are provisioned as Jenkins JCasC string credentials.
The deploy stage of [Jenkinsfile.deploy](Jenkinsfile.deploy) reads them via
`withCredentials` and renders them into `secrets.env` in the workspace
per-build (atomic write + chmod 600). mycelium holds no authoritative copy
of its own — `secrets.env` is replaced on every deploy.

Jenkins itself moved to AWS in 2026-05; the JCasC pattern continues
unchanged. Secret material remains protected by the AWS pipeline.
**Do not migrate this to a different secret store.**

Credentials referenced by [Jenkinsfile.deploy:68-72](Jenkinsfile.deploy:68):

| Credential ID | Maps to |
|---|---|
| `gb-website-secret-key` | `SECRET_KEY` |
| `gb-website-oidc-client-id` | `OIDC_CLIENT_ID` |
| `gb-website-oidc-client-secret` | `OIDC_CLIENT_SECRET` |
| `gb-website-smtp` (deferred — Fastmail not yet provisioned) | `SMTP_USER`, `SMTP_PASSWORD` |

Non-secret config (OIDC discovery URL, sporekles base, CDN base, SMTP from,
contact email, tenant) is inlined in the Jenkinsfile heredoc — not a
Jenkins credential.

**Recovery note (2026-05-25):** the `secrets.env` currently on mycelium was
manually copied from the archived Jenkins workspace at
`/Users/chris/Projects/mm-jenkins/data.archived-20260523/workspace/gb-website-deploy/secrets.env`
after the outage. This is a stop-gap — the next successful AWS-Jenkins
build will overwrite it with a fresh JCasC render.

## Open questions (Jenkins-in-AWS migration)

Following the move of mm-jenkins to AWS in 2026-05, the following are not
yet captured:

- Which AWS service runs Jenkins (EC2 / ECS Fargate / self-hosted /
  AWS-managed)?
- Jenkins UI URL.
- How does AWS Jenkins deploy to mycelium?
  - SSH from the Jenkins agent back to mycelium and run `docker compose up`?
  - Push the image to ECR, mycelium pulls and restarts?
  - Webhook to `mm-deploy-broker` on mycelium (the dir exists at
    `/opt/mm-deploy-broker/` — is this the receiver)?
- The 3 places in the Jenkins setup that need updating for a successful
  build run — enumerate and document.
- [Jenkinsfile.deploy](Jenkinsfile.deploy) (lines 1–9, 53, 95) and
  [docs/runbook-deploy.md](docs/runbook-deploy.md) still assume Jenkins
  runs on mycelium with no SSH hop and no registry round-trip. JCasC-based
  secret rendering is still correct; the host claims aren't. Both files
  need an update pass once the AWS deploy mechanism is nailed down.
