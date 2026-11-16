# gb-website: make the Jenkins deploy work again

Status: **draft for approval** (2026-11-16). Nothing in this document has been
built.

## Why

`gb-website-deploy` has not deployed anything since Jenkins moved from mycelium
to EC2 on 2026-05-22. Lint, tests and the image build pass; the job then runs
`docker compose up` on the Jenkins host, where the `shared-tunnel` network, the
data volume and cloudflared do not exist. The job also has no trigger, so
merges never start a build. Every change since May has needed a manual deploy
on mycelium, and the 2026-11 sign-in fixes took three of them.

Full build history and the three failure points are in
[architecture.md](../../architecture.md#why-the-jenkins-job-fails).

## Goal

A merge to `main` reaches production without anyone logging in to mycelium.

Non-goals:

- Moving secrets to a different store (decided: stays as is, see Secrets).
- Changing how the site is served (tunnel, mm-homebody labels, volume).
- Uptime monitoring for the deploy (follow-up).
- Tearing down the retired CloudFront redirect in `infra/`.

Anti-goal: a deploy that starts the site on a new, empty data volume. See
*Compose project name*.

## Approaches

**A. Build on Jenkins, push to ECR, pull on mycelium — chosen.**
This is what every other mycelium service does since Jenkins moved
(`mm-jenkins/docs/superpowers/specs/2026-05-23-post-mycelium-service-deploy-design.md`).
The mycelium-side installer, pull script, launchd timer and force-deploy
webhook already exist and are parameterised per service. gb-website needs
wiring, not new machinery. Cost: gb-website's image lives in the Musical
Mycology AWS account's ECR.

**B. Jenkins only tests; mycelium pulls from GitHub and builds locally.**
No ECR and no AWS credentials on the deploy path, which fits gb-website being
outside the MM org. Rejected: there is no existing template that builds from
git (the `--no-build` variant only pulls public images), so this means writing
and maintaining a one-off deploy script. It also lets mycelium deploy a commit
Jenkins hasn't tested unless a gate is added.

**C. Jenkins reaches into mycelium over SSH and runs compose there.**
Closest to the old Jenkinsfile. Rejected: the fleet design rules out
SSH-via-Tailscale from Jenkins, and it would put a mycelium SSH key in Jenkins.

## Design

### Flow

```
merge to main
   │  (Jenkins pollSCM, every 5 min)
   ▼
Jenkins on EC2:  lint + test → docker build → push gb-website:<sha> and :latest to ECR
   │                                              │
   │ (only if FORCE_DEPLOY=true)                  │ (always, within 5 min)
   ▼                                              ▼
POST /_deploy-trigger/gb-website  ──►  mycelium: /opt/gb-website/deploy-pull.sh
                                          pull :latest, retag as gb-website:latest,
                                          tag old image :rollback-prev,
                                          docker compose up -d --force-recreate
```

Database migrations keep running in the container entrypoint
(`flask db upgrade`), as today.

### Changes in gb-website

1. **`Jenkinsfile.deploy`** — rewrite on the sibling template
   (`mm-mycelium-directory/Jenkinsfile.deploy`):
   - `triggers { pollSCM('H/5 * * * *') }`
   - `parameters { booleanParam FORCE_DEPLOY, default false }`
   - Stages: Checkout → Lint + Test (unchanged) → Build + push to ECR
     (`:<short-sha>` and `:latest`; no `withAWS` wrapper, the instance role
     already carries the push policy) → Force deploy (param-gated `curl` with
     the existing `cf-deploy-trigger-token-*` credentials).
   - Remove the `withCredentials` block that renders `secrets.env` and the
     `docker compose up`. Remove the Smoke stage: after this change a green
     build means "image published", not "site updated", and a curl against the
     public URL would only test the old container.
2. **`docker-compose.yml`** — add a top-level `name: gb-website-deploy`.
   `image: gb-website:latest` and `build: .` stay; the pull script retags the
   ECR image to that local name, and `build:` keeps `make dev` working.
3. **Docs** — update the header comment in the Jenkinsfile, `architecture.md`
   and `docs/runbook-deploy.md` to describe the new flow, including rollback
   and secret rotation.

### Changes in mm-jenkins

4. **ECR** — add `"gb-website"` to `module.consumer_ecr.repos` in
   `terraform/envs/prod/main.tf`. The Jenkins push policy and the
   `mm-mycelium-pull` pull policy both derive from that list, so no separate
   IAM edit.
5. **Force-deploy allowlist** — add `'gb-website'` to `ALLOWED_SERVICES` in
   `bin/templates/listener.py`.
6. **Job definition** — correct the description in
   `jobs/gb-website-deploy/config.xml` (it describes the old secret-rendering
   flow). The trigger itself comes from the Jenkinsfile.

### Operator steps (need a human with access)

7. `terraform apply` in mm-jenkins to create the ECR repository.
8. Re-seed the Jenkins job (`bin/seed-jobs.sh` on the Jenkins host) and run it
   once by hand; `pollSCM` only registers after a first run.
9. On mycelium, reinstall the deploy broker so the allowlist change takes
   effect (`bin/mycelium-install-broker.sh`).
10. On mycelium, `git pull` the gb-website checkout (to pick up the compose
    project name), then install the pull script and timer:

    ```bash
    bash ~/projects/mm-jenkins/bin/mycelium-install-service.sh \
      --service gb-website \
      --ecr-repo 365647376064.dkr.ecr.us-east-1.amazonaws.com/gb-website \
      --compose-dir /Users/chris/Projects/gb-website \
      --container-name gb-website-app \
      --local-image gb-website:latest \
      --no-kuma-monitoring
    ```

11. Delete the stale `secrets.env` left in the Jenkins workspace on EC2 by
    the failed builds.

## Decisions that need care

### Compose project name

The live data volume is `gb-website-deploy_gb_data`, named after the old
Jenkins workspace. The pull script runs plain `docker compose up` from the
checkout directory, which would use project name `gb-website` and create a new
empty `gb-website_gb_data`. Pinning `name: gb-website-deploy` in the compose
file makes every caller (pull script, manual deploy, local debugging) land on
the existing volume. It also makes the `-p gb-website-deploy` flag in the
manual procedure unnecessary.

**This must be merged and pulled onto mycelium before step 10.** Verify with
`docker volume ls` that no `gb-website_gb_data` volume appears after the first
automated deploy.

### Secrets

Decided 2026-11-16: no change to where secrets are stored. The three secrets
remain Jenkins credentials (`gb-website-secret-key`,
`gb-website-oidc-client-id`, `gb-website-oidc-client-secret`).

Consequence to accept: Jenkins on EC2 cannot write files on mycelium, so the
pipeline no longer renders `secrets.env`. The file already on mycelium (copied
by hand on 2026-05-25) is what the container reads, and the pull script is
installed without any env-render flags so it never touches it. Rotating a
secret becomes two manual steps: update it in Jenkins, and edit `secrets.env`
on mycelium. The runbook will say so.

If that becomes a burden, the installer supports rendering the file from SSM
at deploy time. That is a change of secret flow and is out of scope here.

### Compose file changes don't deploy themselves

The pull script pulls images, not git. A change to `docker-compose.yml`
(labels, healthcheck, environment) only takes effect after a `git pull` on
mycelium. Image-only changes, which is nearly all of them, need nothing. The
runbook will call this out.

### Monitoring

Installed with `--no-kuma-monitoring` for now, so a failed pull is only
visible in `~/Library/Logs/gb-website-deploy.log` on mycelium. My call, to
keep this change small; adding a Kuma push monitor later is one installer
flag.

## Verification

1. Jenkins build is green and ECR shows `gb-website:<sha>` and `:latest`.
2. The image architecture matches mycelium (`docker image inspect` on
   mycelium after the first pull). The sibling services already run
   EC2-built images there, so this is expected to pass; check it once.
3. Within 5 minutes the deploy log on mycelium shows `deployed`, and
   `docker ps` shows `gb-website-app` healthy on the new image.
4. `docker volume ls` shows only `gb-website-deploy_gb_data`; the Manifest
   page still lists the 11 past shows.
5. `https://www.grogblossoms.com/healthz` returns ok and `/admin/` sign-in
   works.
6. A build with `FORCE_DEPLOY=true` deploys without waiting for the timer.
7. A second timer tick with no new image logs `no-op`.

## Rollback

- **Bad image:** on mycelium, retag `:rollback-prev` as `gb-website:latest`
  and run `docker compose up -d --force-recreate` in the checkout. The next
  timer tick would re-pull `:latest`, so also revert the commit and let
  Jenkins publish the fix.
- **Bad migration:** restore the database from the Restic backup
  (`scripts/restore.sh`), as today.
- **Abandon the new flow:** unload the launchd agent and delete
  `/opt/gb-website/deploy-pull.sh`; manual deploys keep working throughout.

## Order of work

1. gb-website PR: compose project name only. Merge, `git pull` on mycelium,
   one manual deploy to prove the volume is unaffected.
2. mm-jenkins PR: ECR repo, allowlist, job description. Merge; operator steps
   7–9.
3. gb-website PR: new `Jenkinsfile.deploy` and docs. Merge; first build
   publishes the image.
4. Operator step 10, then run the verification list.
5. Operator step 11.

Step 1 is separate and first on purpose: it is the only change that can lose
data if it's wrong, and it can be checked on its own.

## Open questions

- Is it acceptable for gb-website's image to live in the Musical Mycology
  ECR? Approach A depends on it.
- mm-jenkins is a Musical-Mycology org repository; I have not confirmed I can
  open pull requests there from this session.
