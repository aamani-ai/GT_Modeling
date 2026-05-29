# Cloud Run Deploy Runbook — aamani-ai Shared Infra

> **Status**: battle-tested 2026-05-29 deploying [`gt_models`](../../apps/gt-digital-twin/) (Node + Vite + Express).
> **Audience**: anyone deploying a new dashboard to the team's shared GCP project. Supplements the team's higher-level *"Deployment of Dashboards to Cloud Run"* guide with stack-specific paths (Node + Python), the gotchas surfaced through real deploys, and a debugging cookbook.
> **Companion**: the [`deploy-cloud-run-dashboard`](~/.claude/skills/deploy-cloud-run-dashboard.md) Claude skill — invoke that in a session and Claude walks you through the steps below interactively.

---

## §1. Team infra reference (the IDs you'll paste a hundred times)

All of this is **pre-configured and shared** across every aamani-ai repo. You should not need to provision any of it.

| Resource | Value |
|---|---|
| **GCP project** | `modeling-nonprod-svc-db5x` |
| **Region** | `us-central1` |
| **Artifact Registry** | `us-central1-docker.pkg.dev/modeling-nonprod-svc-db5x/infrasuremodelingdocker` |
| **WIF pool** | `infrasure-gh-actions-pool` (org-wide attribute condition for aamani-ai) |
| **WIF provider (full path)** | `projects/952205173464/locations/global/workloadIdentityPools/infrasure-gh-actions-pool/providers/github-repo-provider` |
| **Deploy SA** (used by GH Actions via WIF impersonation) | `gh-actions-deploy@modeling-nonprod-svc-db5x.iam.gserviceaccount.com` |
| **Runtime SA** (assigned to Cloud Run services) | `project-service-account@modeling-nonprod-svc-db5x.iam.gserviceaccount.com` |
| **Secrets management** | Infisical → auto-synced to GitHub Secrets |
| **Domain for IAP-gated access** | `aamani.ai` |

**Permissions of the deploy SA**: Cloud Run admin, Artifact Registry writer, IAP admin, ServiceAccountUser on the runtime SA only. Limited blast radius by design.

---

## §2. Decisions before you start

Lock these five things before writing any code. They drive everything downstream.

### 2.1 Stack
**Node** (TypeScript / Express / Vite / React) or **Python** (Dash / Flask + gunicorn)? These are the two stacks the team has shipped. Other stacks (Go, Bun, etc.) are possible but un-tested — start from the closer template and adapt.

### 2.2 Service name
Kebab-case, must be unique across the AR repo. Used as:
- Cloud Run service name (`gcloud run deploy <name>`)
- Artifact Registry image tag (`.../infrasuremodelingdocker/<name>:<sha>`)
- Deploy branch (`deploy/<name>`)
- IAP binding target

Convention: short, descriptive, stable. `gt-digital-twin`, `lockport-asset-twin`, `eqr-explorer`. Avoid version suffixes (`-v1`, `-prod`) — Cloud Run revisions handle versioning.

### 2.3 Public vs private
Default to **private (IAP)** unless there's a deliberate reason to expose. The trade:

| Mode | Flag pair | When |
|---|---|---|
| **Private (IAP)** | `--iap --no-allow-unauthenticated` + `domain:aamani.ai` IAP binding | Internal-only, sensitive data, work-in-progress, valuation-grade outputs. Default. |
| **Public** | `--no-iap --allow-unauthenticated` | Showcase / demo, no sensitive data, willing to be scraped/indexed. *Defensible* posture when the dashboard is explicitly framed "not a valuation" with no proprietary numbers. |

To flip later, change two flags + add/remove the IAP-binding step. Documented in §7.1.

### 2.4 Branch convention
`deploy/<service-name>`. Triggers on push. Keeps `main` non-deploying (otherwise every commit deploys, which is too aggressive while iterating). Manual re-deploy with `workflow_dispatch: {}`.

### 2.5 Secrets
Audit env vars the app needs. Add them to **Infisical** first (it auto-syncs to GitHub Secrets), then reference in the workflow via `${{ secrets.YOUR_SECRET }}`. The dashboard we deployed first (`gt-digital-twin`) needs **none** — pure static SPA reading bundled JSONs. Most data-driven dashboards will need at least a GCS bucket name + maybe a DB connection string.

---

## §3. Per-stack quickstart

### §3.1 Node stack (TypeScript / Express / Vite / etc.)

**What the repo needs:**

1. `package.json` with a working `start` script that listens on `process.env.PORT`:
   ```json
   {
     "engines": { "node": ">=20" },
     "scripts": {
       "build": "...",
       "start": "NODE_ENV=production node dist/index.cjs"
     }
   }
   ```

2. **`Procfile`** at the buildable root (alongside `package.json`):
   ```
   web: npm start
   ```
   *This is required.* Paketo's Node engine does NOT auto-pick `npm start` as the launch process; without the Procfile the container starts a default `node` binary with no args and exits immediately.

3. **Server must bind `0.0.0.0` on `process.env.PORT`**:
   ```ts
   const port = parseInt(process.env.PORT || "5000", 10);
   httpServer.listen({ port, host: "0.0.0.0" }, () => { /* … */ });
   ```
   *Do NOT use `reusePort: true`* — works on Linux, fails with `ENOTSUP` on macOS dev workstations.

4. **Audit native-compile deps**. Anything in `dependencies` that uses node-gyp at install time will fail on the Paketo builder (no Python). Common offenders: `better-sqlite3`, `sharp`, `bcrypt`, `canvas`. If unused, **remove**. If needed, switch to a pure-JS alternative or use a builder with Python (heavier).

5. **Use `builder-jammy-full`** in the workflow (not `-base`/`-tiny`). The Node binary is dynamically linked against `libatomic.so.1`, which `-base` and `-tiny` strip. See §5 gotcha #3.

### §3.2 Python stack (Dash / Flask / gunicorn)

**What the repo needs:**

1. `pyproject.toml` or `requirements.txt` with `gunicorn` + your framework (`dash>=2`, `flask`, etc.). Example pattern from the team's `dashboards/` repo:
   ```toml
   [project]
   requires-python = ">=3.11"
   dependencies = ["dash>=2.17", "gunicorn>=23"]
   ```

2. **`Procfile`** with the gunicorn launch command:
   ```
   web: gunicorn your_module.app:server --bind 0.0.0.0:$PORT
   ```
   Replace `your_module.app:server` with the Flask `server` exposed by your Dash app (i.e., `app.server` where `app = dash.Dash(...)`).

3. **Server reads `$PORT`** — gunicorn does this automatically via the `--bind 0.0.0.0:$PORT` argument; no app code change needed.

4. **Builder choice**: `paketobuildpacks/builder-jammy-base` is usually fine for Python (the libatomic issue is Node-specific). Use `-full` if you also need system libraries (e.g., `libgomp` for some numpy paths, or PDF tools).

### §3.3 Other stacks (Go, Bun, Deno, …)

Paketo supports many — see [paketo.io/docs](https://paketo.io/docs/). Use the stack-specific buildpack family, set the launch command via Procfile, ensure `$PORT` is consumed. Otherwise the rest of this runbook applies unchanged.

---

## §4. End-to-end deploy steps

Sequential. Run in order. Total time on a clean repo: ~30 min including the GitHub Actions runtime.

### Step 1 — Local production sanity check

Test the production bundle locally **before** writing the workflow. Catches startup errors at your laptop, not 3 minutes into a CI run.

**Node:**
```bash
cd path/to/dashboard
npm install        # use --cache=/tmp/npm-cache-foo if your ~/.npm has root-owned files
npm run build      # produces dist/ artifacts
PORT=5174 npm start
# in another shell:
curl -sS -o /dev/null -w "HTTP %{http_code}\n" http://localhost:5174/
# verify any other routes / static assets
```

**Python:**
```bash
cd path/to/dashboard
pip install -e .            # or pip install -r requirements.txt
PORT=5174 gunicorn your_module.app:server --bind 0.0.0.0:$PORT
curl -sS -o /dev/null -w "HTTP %{http_code}\n" http://localhost:5174/
```

If this fails locally, **stop here**. Fix the bundle before touching CI.

### Step 2 — Add deployment artifacts

1. **`Procfile`** (see §3.1 or §3.2).
2. For Node: pin `engines.node` in `package.json`.
3. The GitHub Actions workflow at `.github/workflows/deploy-<service>.yml` — template in §4.4 below.

### Step 3 — Workflow template (Node)

`.github/workflows/deploy-<service>.yml`:

```yaml
name: Build and Deploy <service> to Cloud Run

on:
  push:
    branches: [deploy/<service>]
  workflow_dispatch: {}

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: 'read'
      id-token: 'write'

    env:
      SERVICE: <service>
      REGION: us-central1
      AR_HOST: us-central1-docker.pkg.dev
      AR_PROJECT: modeling-nonprod-svc-db5x
      AR_REPO: infrasuremodelingdocker
      APP_PATH: apps/<service>/web   # OR `.` if the buildable root IS the repo root

    steps:
      - uses: actions/checkout@v4

      - name: Authenticate to Google Cloud
        uses: 'google-github-actions/auth@v3'
        with:
          project_id: 'modeling-nonprod-svc-db5x'
          workload_identity_provider: 'projects/952205173464/locations/global/workloadIdentityPools/infrasure-gh-actions-pool/providers/github-repo-provider'
          service_account: 'gh-actions-deploy@modeling-nonprod-svc-db5x.iam.gserviceaccount.com'

      - name: Set up Cloud SDK
        uses: 'google-github-actions/setup-gcloud@v3'

      - name: Configure Docker for GAR
        run: gcloud auth configure-docker ${{ env.AR_HOST }} --quiet

      - name: Setup pack CLI
        uses: buildpacks/github-actions/setup-pack@v5.0.0

      - name: Build and push image
        # builder-jammy-FULL (not -base/-tiny): Node binary dynamically links libatomic.so.1
        # BP_NODE_RUN_SCRIPTS=build: tells the Node buildpack to run `npm run build`
        # --path: monorepo subdir; use `.` for single-app repos
        run: |
          IMAGE="${{ env.AR_HOST }}/${{ env.AR_PROJECT }}/${{ env.AR_REPO }}/${{ env.SERVICE }}:${{ github.sha }}"
          pack build "$IMAGE" \
            --builder paketobuildpacks/builder-jammy-full \
            --path ${{ env.APP_PATH }} \
            --env BP_NODE_RUN_SCRIPTS=build \
            --publish

      - name: Deploy to Cloud Run
        # For PRIVATE: --iap --no-allow-unauthenticated (and add the IAP-binding step below)
        # For PUBLIC: --no-iap --allow-unauthenticated (and remove the IAP step)
        run: |
          IMAGE="${{ env.AR_HOST }}/${{ env.AR_PROJECT }}/${{ env.AR_REPO }}/${{ env.SERVICE }}:${{ github.sha }}"
          gcloud run deploy ${{ env.SERVICE }} \
            --image "$IMAGE" \
            --platform managed \
            --region ${{ env.REGION }} \
            --no-iap \
            --allow-unauthenticated \
            --service-account project-service-account@modeling-nonprod-svc-db5x.iam.gserviceaccount.com
            # Optional: --set-env-vars="KEY=${{ secrets.SECRET_FROM_INFISICAL }}"

      # ONLY for PRIVATE (IAP-gated) deploys — delete this step for public:
      # - name: Grant IAP access to aamani.ai domain
      #   run: |
      #     gcloud iap web add-iam-policy-binding \
      #       --resource-type=cloud-run \
      #       --service=${{ env.SERVICE }} \
      #       --region=${{ env.REGION }} \
      #       --member='domain:aamani.ai' \
      #       --role='roles/iap.httpsResourceAccessor' \
      #       --condition=None

      - name: Print service URL
        run: |
          URL=$(gcloud run services describe ${{ env.SERVICE }} --region=${{ env.REGION }} --format='value(status.url)')
          echo "=== Cloud Run service URL: $URL ==="
```

### Step 4 — Workflow template (Python / Dash)

Identical to the Node template above, except the `Build and push image` step:
```yaml
      - name: Build and push image
        run: |
          IMAGE="${{ env.AR_HOST }}/${{ env.AR_PROJECT }}/${{ env.AR_REPO }}/${{ env.SERVICE }}:${{ github.sha }}"
          pack build "$IMAGE" \
            --builder paketobuildpacks/builder-jammy-base \
            --path ${{ env.APP_PATH }} \
            --publish
```
No `BP_NODE_RUN_SCRIPTS`. `-base` builder is fine for Python (libatomic gotcha is Node-specific). Python deps install from `requirements.txt` or `pyproject.toml` automatically.

### Step 5 — Push the deploy branch

```bash
git checkout -b deploy/<service>
git add .github/ <path-to-deploy-artifacts>
git commit -m "Add Cloud Run deploy workflow for <service>"
git push -u origin deploy/<service>
```

### Step 6 — Monitor + verify

```bash
# Find the run that just kicked off
gh run list --workflow=deploy-<service>.yml --branch=deploy/<service> --limit=1 -R aamani-ai/<repo>

# Watch it to completion (~3 min)
gh run watch <run-id> -R aamani-ai/<repo> --exit-status

# If it failed:
gh run view <run-id> -R aamani-ai/<repo> --log-failed

# Grab the live URL:
gcloud --project=modeling-nonprod-svc-db5x run services describe <service> \
  --region=us-central1 --format='value(status.url)'

# Probe (public deploys):
curl -sS -o /dev/null -w "HTTP %{http_code}\n" "$URL/"
```

For IAP deploys, the URL redirects to a Google sign-in. Open in a browser to test.

---

## §5. Gotchas / learnings — symptom → cause → fix

Every entry here is a real failure that cost us debug time. Read this table before your first deploy.

| # | Symptom | Cause | Fix |
|---|---|---|---|
| 1 | `npm ci` fails on `node-gyp rebuild`, *"Could not find Python"* | A dependency requires native compilation (`better-sqlite3`, `sharp`, `bcrypt`, `canvas`); Paketo's Node builder doesn't include Python | Audit deps — most often the dep is dead code from a scaffolded template. Remove it. If genuinely needed, swap to a pure-JS alternative. Last resort: use a heavier builder with Python. |
| 2 | Container builds successfully but Cloud Run says *"container failed to start and listen on the port"* | No `Procfile` — Paketo's Node engine doesn't auto-pick `npm start` as the default launch process | Add a `Procfile` next to `package.json`: `web: npm start` |
| 3 | Container exits immediately, logs show *`node: error while loading shared libraries: libatomic.so.1`* | Node binary is dynamically linked against libatomic; the `-base`/`-tiny` Paketo run images strip that library to keep size small | Switch `--builder paketobuildpacks/builder-jammy-base` → `paketobuildpacks/builder-jammy-full`. Adds ~50MB to the image; Node actually starts. |
| 4 | Monorepo build picks up the wrong directory (e.g., builds the repo root with no `package.json`) | Default `pack build --path .` builds from the workflow checkout dir | `--path apps/<service>/web` (or wherever the buildable root is). Set `APP_PATH` as a workflow env var so it's visible. |
| 5 | Local `npm start` fails with `ENOTSUP` on macOS (`listen ENOTSUP: operation not supported on socket 0.0.0.0:5000`) | `httpServer.listen({ port, host: "0.0.0.0", reusePort: true })` — `reusePort: true` isn't supported for IPv4 on 0.0.0.0 on macOS | Drop `reusePort: true` from the listen options. Linux/Cloud Run is unaffected; macOS dev works again. |
| 6 | macOS port 5000 is taken (HTTP 403 from `ControlCe`) | macOS ControlCenter binds 5000 for AirPlay receiver | Use a different local port (`PORT=5174 npm start`), or System Settings → AirDrop & Handoff → toggle off "AirPlay Receiver" |
| 7 | `gcloud logging read` fails with *"There was a problem refreshing your current auth tokens: Reauthentication failed"* | gcloud needs an interactive browser sign-in once per workstation | Run `gcloud auth login` interactively. Then `gcloud config set project modeling-nonprod-svc-db5x` |
| 8 | GH Actions WIF auth fails with *"Unauthorized request to..."* | New repo isn't in the WIF binding (rare — the team's WIF is org-wide for aamani-ai) | Verify the repo is in the `aamani-ai` org and check the WIF pool's `attribute.repository_owner == aamani-ai` condition. If not in the org, the WIF rejects. |
| 9 | `npm install` fails with `EACCES` against `~/.npm/_cacache/tmp/…` | Root-owned files in npm cache from a past `sudo npm` run | Either `sudo chown -R $(id -u):$(id -g) ~/.npm` (one-time), or use a fresh cache: `npm install --cache=/tmp/npm-cache-<project>` |
| 10 | Cloud Run revision says deployed but URL returns 404/503 | App started but routes don't match what you're hitting | Check `serveStatic` / route definitions; for SPAs, ensure a catch-all serves `index.html` |
| 11 | The cwd in Claude's Bash tool "drifts" after a `cd` command | Bash tool persists cwd across calls | Always use absolute paths in workflow-affecting commands, or prepend `cd /absolute/path && ` to commands. Don't trust `git commit` to find files if a prior `cd` moved the shell |
| 12 | Image deploys but logs show secrets leaked as plain text | `--set-env-vars="KEY=$VALUE"` where `$VALUE` came from `secrets.X` — GitHub redacts the value but it lands in env literally | This is actually fine — GitHub redacts on log lines, the runtime env is correctly set. Confirm by checking the deployed service in Cloud Run console (env vars are listed) |

---

## §6. Debugging cookbook

### 6.1 Workflow failed — read GH Actions logs

```bash
# List recent runs for a workflow:
gh run list --workflow=deploy-<service>.yml -R aamani-ai/<repo>

# Failure logs (only failed steps):
gh run view <run-id> -R aamani-ai/<repo> --log-failed

# Full logs (verbose, big):
gh run view <run-id> -R aamani-ai/<repo> --log

# Search the logs for a specific pattern:
gh run view <run-id> -R aamani-ai/<repo> --log | grep -iE "error|fail"
```

### 6.2 GH Actions logs don't show the real error → read Cloud Run container logs

**This was the critical unblock for our first deploy.** When Cloud Run says *"container failed to start and listen on the port"* with no detail in the GH Actions logs, the actual error is in the **container's stdout/stderr inside Cloud Run**.

```bash
# One-time setup:
gcloud auth login                                       # interactive
gcloud config set project modeling-nonprod-svc-db5x

# Read container logs (last 30, newest first):
gcloud --project=modeling-nonprod-svc-db5x logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="<service>"' \
  --limit=30 \
  --format='value(textPayload,jsonPayload.message)'

# Or filter by severity / time:
gcloud --project=modeling-nonprod-svc-db5x logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="<service>" AND severity>=ERROR' \
  --limit=10
```

Look for: missing shared libraries, port-binding failures, startup exceptions, OOM kills.

### 6.3 The container starts but doesn't serve

```bash
# Check what process the buildpack set as launch:
gcloud --project=modeling-nonprod-svc-db5x run revisions describe <revision-name> \
  --region=us-central1 --format='value(spec.containers[0].command)'

# Check env vars / PORT setup:
gcloud --project=modeling-nonprod-svc-db5x run revisions describe <revision-name> \
  --region=us-central1 --format='yaml(spec.containers[0].env)'

# Pull the image locally and run it to reproduce:
docker pull us-central1-docker.pkg.dev/modeling-nonprod-svc-db5x/infrasuremodelingdocker/<service>:<sha>
docker run -e PORT=8080 -p 8080:8080 <image-id>
```

### 6.4 The deploy succeeded but the app behaves differently than localhost

Most common: **a dev-only path** in code (e.g., Vite middleware, sourcemap-only error handling) that doesn't run when `NODE_ENV=production`. Reproduce locally with the production build:
```bash
npm run build && NODE_ENV=production PORT=5174 npm start
```

---

## §7. Day-2 operations

### 7.1 Flip public ↔ private

**Public → Private** (add IAP, restrict to aamani.ai):
1. In the deploy workflow, change:
   - `--no-iap` → `--iap`
   - `--allow-unauthenticated` → `--no-allow-unauthenticated`
2. Add the IAP binding step (template in §4.3, commented out for public).
3. Push to the deploy branch → ~3 min, gated again.

**Private → Public**: reverse those two flag pairs, delete the IAP binding step. (We did this on `gt-digital-twin` — see commit history.)

### 7.2 Add a secret / env var after the fact

1. Add the secret to **Infisical** under the project's Infisical workspace. Within minutes it syncs to GitHub Secrets.
2. Reference in the workflow's deploy step:
   ```yaml
   --set-env-vars="MY_KEY=${{ secrets.MY_INFISICAL_KEY }},OTHER=${{ secrets.OTHER }}"
   ```
3. Push the workflow change → next deploy picks up the env var.
4. **Verify**: in the Cloud Run console, the service's env tab should show the new var (value redacted).

### 7.3 Add a custom domain

Cloud Run supports custom domains via [Cloud Run domain mappings](https://cloud.google.com/run/docs/mapping-custom-domains). Requires:
- DNS access for the target domain (CNAME / A records)
- Domain verified in Search Console with the GCP project's service account

For internal dashboards typically not needed — the default `*.run.app` URL works.

### 7.4 Scaling settings (defaults usually fine)

Cloud Run defaults: scales to zero when idle, autoscales up under load. To tune:
```bash
gcloud run services update <service> --region=us-central1 \
  --min-instances=1 \              # keep 1 warm (avoids cold-start; costs more)
  --max-instances=10 \             # cap concurrency under load
  --cpu=1 --memory=512Mi           # right-size resources
```

Cold-start for a Node app with the runbook's setup is ~1–3 seconds. For dashboards used continuously by a small team, `--min-instances=1` is often worth ~$5–10/mo. Pure showcase pages can stay at `--min-instances=0`.

### 7.5 Costs — rough shape

For a static dashboard (no compute beyond serving JSON + SPA shell):
- **Idle**: ~$0/month with `--min-instances=0`
- **Low traffic** (10s of requests/day): ~$0–$1/month
- **Always-warm** (`--min-instances=1`): ~$5–10/month
- **Heavy traffic** (1000s of requests/day): scales linearly, still typically <$50/month for static workloads

Live-compute dashboards (calling external APIs, running models on request) cost more depending on compute time per request. Cloud Run bills per-request CPU/memory-second.

---

## §8. References

- Team's higher-level guide: *Deployment of Dashboards to Cloud Run* (the original write-up shared in Notion/Slack)
- This repo's Node example: [`apps/gt-digital-twin/`](../../apps/gt-digital-twin/) + [`.github/workflows/deploy-gt-digital-twin.yml`](../../.github/workflows/deploy-gt-digital-twin.yml)
- Team's Python/Dash example: [`/Users/divy/code/work/infrasure_git_codes/dashboards/`](https://github.com/aamani-ai/dashboards) — pyproject.toml + `cloudbuild.yaml`
- Paketo buildpacks: [paketo.io/docs](https://paketo.io/docs/)
- Cloud Run docs: [cloud.google.com/run/docs](https://cloud.google.com/run/docs/)
- IAP for Cloud Run: [cloud.google.com/iap/docs/enabling-cloud-run](https://cloud.google.com/iap/docs/enabling-cloud-run)
- Infisical: team's Infisical workspace (URL in the original Notion/Slack guide)

---

## §9. The skill that drives this runbook interactively

For a Claude-assisted deploy (recommended for new dashboards), the [`deploy-cloud-run-dashboard`](~/.claude/skills/deploy-cloud-run-dashboard.md) skill walks the questions of §2 and then the steps of §4 with you in real time. Invoke `/deploy-cloud-run-dashboard` in a Claude session inside the target repo.
