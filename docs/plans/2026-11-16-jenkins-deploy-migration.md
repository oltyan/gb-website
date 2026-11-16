# gb-website Jenkins Deploy Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A merge to gb-website `main` reaches production without anyone logging in to mycelium.

**Architecture:** Jenkins on EC2 lints, tests, builds and pushes `gb-website:<sha>` and `:latest` to ECR. The existing fleet tooling on mycelium (`/opt/<service>/deploy-pull.sh` on a 5-minute launchd timer, plus the `/_deploy-trigger/` webhook) pulls the image, retags it to the local name the compose file uses, and recreates the container.

**Tech Stack:** Jenkins declarative pipeline, Docker Compose, AWS ECR, Terraform (mm-jenkins), launchd on macOS, pytest for guard tests.

**Spec:** `docs/specs/2026-11-16-jenkins-deploy-migration-design.md`

## Global Constraints

- Compose project name is exactly `gb-website-deploy`. The live volume is `gb-website-deploy_gb_data`; no deploy may create `gb-website_gb_data`.
- ECR repository name is exactly `gb-website`; registry `365647376064.dkr.ecr.us-east-1.amazonaws.com`.
- Local image tag stays `gb-website:latest`; container name stays `gb-website-app`.
- Deploy-trigger service name is exactly `gb-website` (the listener runs `/opt/gb-website/deploy-pull.sh`).
- No change to where secrets are stored. The pipeline must not read, render or write `secrets.env`. The Jenkins credentials `gb-website-secret-key`, `gb-website-oidc-client-id`, `gb-website-oidc-client-secret` stay defined in mm-jenkins and are not touched.
- Do not wrap ECR push in `withAWS`; the EC2 instance role already has the push policy.
- Task order is fixed: Task 1 must be merged and pulled onto mycelium before Task 4's installer step.
- No `terraform apply`, job re-seed, or mycelium install is run by an agent. Those are operator steps (Task 4).
- gb-website tests: `/Users/chris/projects/gb-website/.venv/bin/python -m pytest -q` and `/Users/chris/projects/gb-website/.venv/bin/ruff check app tests scripts` (the worktree has no venv of its own). mm-jenkins tests: `make test`.

## Review Focus

1. **A caller runs `docker compose` without `-p`** (the pull script does) → it must land on the existing volume. Pinned by Task 1's test.
2. **`build: .` is still in the compose file when the pull script runs `compose up`** → compose must use the retagged local image, not rebuild from the checkout. Task 4 verification step 3 checks the running image ID equals the ECR image ID.
3. **Jenkins builds a commit whose tests fail** → nothing is pushed to ECR. Task 3's test asserts the push stage comes after Lint + Test in the file.
4. **`FORCE_DEPLOY` left at its default** → no webhook call; the timer deploys. Task 3's test asserts the default is `false` and the stage is `when`-gated.
5. **A future edit re-adds secret rendering to the Jenkinsfile** → would write production secrets into the EC2 workspace again. Task 3's test asserts `secrets.env` and `withCredentials` for the three `gb-website-*` IDs are absent.

---

### Task 1: Pin the compose project name (gb-website PR 1)

**Files:**
- Modify: `docker-compose.yml` (add top-level `name:`)
- Modify: `architecture.md` (section "Volume name has a project prefix")
- Create: `tests/test_deploy_config.py`

**Interfaces:**
- Produces: compose project name `gb-website-deploy` for every `docker compose` call made from the repo root. Task 4 relies on it.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_deploy_config.py
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def _compose() -> dict:
    return yaml.safe_load((ROOT / "docker-compose.yml").read_text())


def test_compose_project_name_is_pinned_to_existing_volume_prefix():
    # The live DB volume is gb-website-deploy_gb_data. Any other project
    # name makes compose create a fresh, empty volume.
    assert _compose()["name"] == "gb-website-deploy"


def test_compose_keeps_local_image_and_container_names():
    app = _compose()["services"]["app"]
    assert app["image"] == "gb-website:latest"
    assert app["container_name"] == "gb-website-app"
    assert "gb_data:/data" in app["volumes"]
```

- [ ] **Step 2: Run it and confirm the first test fails**

Run: `/Users/chris/projects/gb-website/.venv/bin/python -m pytest -q tests/test_deploy_config.py`
Expected: `test_compose_project_name_is_pinned...` FAILS with `KeyError: 'name'`; the second test passes.

- [ ] **Step 3: Add `name: gb-website-deploy` as the first top-level key of `docker-compose.yml`**

Put a two-line comment above it saying the name matches the existing `gb-website-deploy_gb_data` volume and must not change.

- [ ] **Step 4: Update `architecture.md`**

In "Volume name has a project prefix", say the project name is now pinned in the compose file, so `-p gb-website-deploy` is no longer needed. Change the manual-deploy command there and in "Why the Jenkins job fails" to `docker compose up -d --build --wait`.

- [ ] **Step 5: Run the full suite and lint**

Run: `/Users/chris/projects/gb-website/.venv/bin/python -m pytest -q && /Users/chris/projects/gb-website/.venv/bin/ruff check app tests scripts`
Expected: 85 passed; `All checks passed!`

- [ ] **Step 6: Commit**

```bash
git add docker-compose.yml architecture.md tests/test_deploy_config.py
git commit -m "fix(deploy): pin compose project name to gb-website-deploy"
```

- [ ] **Step 7: Open the PR and stop**

Title: `fix(deploy): pin compose project name to gb-website-deploy`. The PR body must say: after merge, on mycelium run `git pull --ff-only` then `docker compose up -d --build --wait` (no `-p`), and confirm with `docker volume ls | grep gb` that only `gb-website-deploy_gb_data` exists and the Manifest page still lists 11 shows. Do not start Task 3 until the operator confirms this.

---

### Task 2: ECR repository, allowlist entry, job definition (mm-jenkins PR)

Work in `~/projects/mm-jenkins` on a new branch off `main` (use a worktree; do not edit the main checkout).

**Files:**
- Modify: `terraform/envs/prod/main.tf` (`module "consumer_ecr"` → `repos`)
- Modify: `bin/templates/listener.py` (`ALLOWED_SERVICES`)
- Modify: `tests/test_listener.py`
- Modify: `jobs/gb-website-deploy/config.xml`

**Interfaces:**
- Produces: ECR repo `gb-website` (after operator `terraform apply`); webhook path `/_deploy-trigger/gb-website`; a job with a 5-minute SCM trigger and a `FORCE_DEPLOY` boolean parameter.

- [ ] **Step 1: Write the failing listener test**

Add to `tests/test_listener.py`, next to `test_allowlist_contains_core_and_murias`:

```python
def test_allowlist_contains_gb_website():
    assert 'gb-website' in ALLOWED_SERVICES
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `make test`
Expected: `test_allowlist_contains_gb_website` FAILS.

- [ ] **Step 3: Add `'gb-website'` to `ALLOWED_SERVICES` in `bin/templates/listener.py`**

Comment above it: standalone oltyan repo, not `mm-`-prefixed; built from `gb-website/Jenkinsfile.deploy`; the entry only enables same-build `FORCE_DEPLOY=true` POSTs.

- [ ] **Step 4: Add `"gb-website"` to `module.consumer_ecr.repos` in `terraform/envs/prod/main.tf`**

Follow the comment style of the neighbouring entries (what it is, where it's built from, that adding it extends both the instance push policy and the `mm-mycelium-pull` pull policy).

- [ ] **Step 5: Update `jobs/gb-website-deploy/config.xml`**

Mirror `jobs/mm-brownie-deploy/config.xml`:
- `<description>`: build and push to ECR on push to main (5-min SCM polling); mycelium's launchd timer deploys; public oltyan repo so no `credentialsId`.
- Replace `<properties/>` with a `ParametersDefinitionProperty` holding one `BooleanParameterDefinition` named `FORCE_DEPLOY`, default `false`, description naming `/_deploy-trigger/gb-website`.
- Replace `<triggers/>` with one `hudson.triggers.SCMTrigger`, spec `H/5 * * * *`, `ignorePostCommitHooks` false. No timer trigger.
- Leave the `<scm>` block and `scriptPath` unchanged.

- [ ] **Step 6: Run the suite and validate Terraform formatting**

Run: `make test && terraform -chdir=terraform/envs/prod fmt -check`
Expected: all tests pass (the suite includes job-XML and trigger checks); `fmt -check` prints nothing.

- [ ] **Step 7: Commit and open the PR**

```bash
git add terraform/envs/prod/main.tf bin/templates/listener.py tests/test_listener.py jobs/gb-website-deploy/config.xml
git commit -m "feat(gb-website): ECR repo, deploy-trigger allowlist, polled job definition"
```

PR body lists the operator steps this unlocks (Task 4 steps 1–3) and links the gb-website spec.

---

### Task 3: New `Jenkinsfile.deploy` and docs (gb-website PR 2)

Start only after Task 1 is merged and confirmed on mycelium.

**Files:**
- Modify: `Jenkinsfile.deploy` (full rewrite)
- Modify: `tests/test_deploy_config.py`
- Modify: `architecture.md`, `docs/runbook-deploy.md`, `docker-compose.yml` (comments only)

**Interfaces:**
- Consumes: ECR repo `gb-website` and webhook path `/_deploy-trigger/gb-website` from Task 2; Jenkins credentials `cf-deploy-trigger-token-id` and `cf-deploy-trigger-token-secret` (already exist).
- Produces: images `365647376064.dkr.ecr.us-east-1.amazonaws.com/gb-website:<short-sha>` and `:latest` on every green build of `main`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_deploy_config.py`:

```python
JENKINSFILE = (ROOT / "Jenkinsfile.deploy").read_text()
ECR = "365647376064.dkr.ecr.us-east-1.amazonaws.com"


def test_jenkinsfile_polls_scm():
    assert "pollSCM('H/5 * * * *')" in JENKINSFILE


def test_jenkinsfile_pushes_sha_and_latest_to_ecr_after_tests():
    assert ECR in JENKINSFILE
    assert 'docker push "${ECR}:${SHA}"' in JENKINSFILE
    assert 'docker push "${ECR}:latest"' in JENKINSFILE
    assert JENKINSFILE.index("pytest") < JENKINSFILE.index("docker push")


def test_jenkinsfile_never_starts_containers_or_touches_secrets():
    # Jenkins runs on EC2; the site runs on mycelium.
    for forbidden in (
        "docker compose up",
        "secrets.env",
        "gb-website-secret-key",
        "gb-website-oidc-client-id",
        "gb-website-oidc-client-secret",
        "withAWS",
    ):
        assert forbidden not in JENKINSFILE, forbidden


def test_jenkinsfile_force_deploy_is_opt_in():
    assert "name: 'FORCE_DEPLOY'" in JENKINSFILE
    assert "defaultValue: false" in JENKINSFILE
    assert "when { expression { params.FORCE_DEPLOY } }" in JENKINSFILE
    assert "https://mycelium.musicalmycology.org/_deploy-trigger/gb-website" in JENKINSFILE
```

- [ ] **Step 2: Run them and confirm all four fail**

Run: `/Users/chris/projects/gb-website/.venv/bin/python -m pytest -q tests/test_deploy_config.py`
Expected: 4 failed, 2 passed.

- [ ] **Step 3: Rewrite `Jenkinsfile.deploy`**

Use `~/projects/mm-mycelium-directory/Jenkinsfile.deploy` as the template for structure, options and the two shell blocks. Decisions specific to gb-website:
- Header comment: build on EC2, deploy on mycelium by pull; secrets are not handled here; link the spec.
- `agent any`; `triggers { pollSCM('H/5 * * * *') }` (no nightly cron); `parameters` with `FORCE_DEPLOY` (default `false`); `options { timeout 15 min; timestamps(); buildDiscarder(numToKeepStr: '20'); disableConcurrentBuilds() }`.
- Stages, in order: `Checkout` (`checkout scm`), `Lint + Test` (unchanged from today, including the `python:3.12-slim` docker agent with `reuseNode true`), `Build + push to ECR`, `Force deploy on Mycelium`.
- Build + push: `SHA=$(git rev-parse --short HEAD)`, `ECR_HOST=<registry>`, `ECR="${ECR_HOST}/gb-website"`; log in to the **bare host** (`docker login ... "$ECR_HOST"`), `docker build -t "gb-website:${SHA}" .`, tag and push `${ECR}:${SHA}` and `${ECR}:latest`.
- Force deploy: `when`-gated, `withCredentials` for the two `cf-deploy-trigger-token-*` strings only, `curl -fsS -X POST` with the `CF-Access-Client-Id` / `CF-Access-Client-Secret` headers to the URL in the test.
- No Smoke stage. `post { failure { echo 'Build failed' } }`.

- [ ] **Step 4: Run the tests and lint**

Run: `/Users/chris/projects/gb-website/.venv/bin/python -m pytest -q && /Users/chris/projects/gb-website/.venv/bin/ruff check app tests scripts`
Expected: 89 passed; `All checks passed!`

- [ ] **Step 5: Update the docs**

- `docker-compose.yml`: fix the comments on `build:`/`image:` and `env_file:` (image is built by Jenkins and retagged by the mycelium pull script; `build:` is for local dev; `secrets.env` is maintained by hand on mycelium).
- `architecture.md`: replace "Why the Jenkins job fails" → keep the build-history table, replace the "what has to change" list with a "How deploys work" section (flow from the spec); update "Where things run", "Secrets" (rotation is two manual steps; delete the 2026-05-25 "next build will overwrite it" claim) and remove the now-answered "Open questions" entries.
- `docs/runbook-deploy.md`: rewrite "Deploy a change" (merge → Jenkins → ECR → timer; `FORCE_DEPLOY` for immediate), add "Roll back" (`:rollback-prev` procedure from the spec) and "Change the compose file" (needs `git pull` on mycelium), and correct the two places that say Jenkins is on mycelium and that `secrets.env` is rendered every build.

- [ ] **Step 6: Commit and open the PR**

```bash
git add Jenkinsfile.deploy tests/test_deploy_config.py architecture.md docs/runbook-deploy.md docker-compose.yml
git commit -m "feat(deploy): build and push to ECR; mycelium pulls"
```

PR body states: merging this starts nothing on mycelium until Task 4's installer step is done; until then manual deploys still work.

---

### Task 4: Operator steps and verification (human, with agent read-only checks)

No code. Each step is run by the operator; the agent verifies with `portal read mm-jenkins` / `portal ssh mycelium` and public `curl` only.

- [ ] **Step 1 (after Task 2 merges): create the ECR repository**

**RUN ON: workstation** — in `~/projects/mm-jenkins/terraform/envs/prod`: `terraform plan`, confirm it adds the `gb-website` repository, its lifecycle policy, and updates the two IAM policies and nothing else; then `terraform apply`.

- [ ] **Step 2: re-seed the Jenkins job**

**RUN ON: mm-jenkins EC2 (via SSM)** — `cd /opt/mm-jenkins && sudo bin/seed-jobs.sh`
Verify (agent): `/opt/mm-jenkins/data/jobs/gb-website-deploy/config.xml` contains `SCMTrigger` and `FORCE_DEPLOY`.

- [ ] **Step 3: reinstall the deploy broker**

**RUN ON: mycelium** — `cd ~/projects/mm-jenkins && git pull --ff-only && bash bin/mycelium-install-broker.sh`

- [ ] **Step 4 (after Task 3 merges): first image**

Wait for the polled build, or start one by hand. Verify (agent): build log ends `Finished: SUCCESS` and contains both `docker push` lines.

- [ ] **Step 5: install the pull script and timer**

**RUN ON: mycelium** — the installer command in the spec, section "Operator steps", item 10. Precondition: Task 1 is already pulled on mycelium (`grep '^name:' /Users/chris/Projects/gb-website/docker-compose.yml` prints `name: gb-website-deploy`).

- [ ] **Step 6: run the spec's verification list (items 1–7)**

Stop and report if `docker volume ls` shows `gb-website_gb_data`, if the Manifest page does not list 11 shows, or if the running container's image ID differs from the pulled ECR image ID.

- [ ] **Step 7: delete the stale workspace secrets on EC2**

**RUN ON: mm-jenkins EC2 (via SSM)** — remove `secrets.env` from the `gb-website-deploy` workspace under `/opt/mm-jenkins/data/workspace/`. Verify (agent) the file is gone.

---

## Spec deviation

The spec says the job trigger "comes from the Jenkinsfile". Sibling jobs also declare the trigger and the `FORCE_DEPLOY` parameter in `config.xml`, so a re-seed keeps them. Task 2 does both; the Jenkinsfile still declares `pollSCM`.
