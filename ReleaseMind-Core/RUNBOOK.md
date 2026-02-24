# 🧠 ReleaseMind — AI DevOps Governance Engine
## Complete Runbook (Windows CMD / PowerShell)

---

## 📁 Final Project Structure

```
ReleaseMind/
└── ReleaseMind-Core/
    ├── backend/
    │   ├── api.py                  ← Main Flask API (all routes)
    │   ├── risk_engine.py          ← Dynamic weighted risk scorer
    │   ├── github_analyzer.py      ← GitHub API integration (Phase 1)
    │   ├── dependency_parser.py    ← networkx graph + blast radius (Phase 3)
    │   ├── metrics_collector.py    ← psutil CPU/memory + kubectl (Phase 5)
    │   ├── db.py                   ← SQLite DB + failure learning (Phase 4)
    │   ├── config_loader.py        ← Cached YAML config reader
    │   ├── requirements.txt
    │   ├── database/
    │   │   └── releasemind.db      ← Auto-created on first run
    │   └── config/
    │       ├── risk_config.yaml    ← All weights (tune without code changes)
    │       └── dependency.json     ← Service dependency graph
    ├── frontend/
    │   ├── templates/
    │   │   └── index.html          ← Full UI (tabs: GitHub, Manual, History, Services)
    │   └── static/
    │       ├── style.css
    │       └── app.js
    ├── k8s/
    │   └── deployment.yaml         ← K8s Deployment + Service + PVC + Secret
    ├── Dockerfile                  ← Production multi-stage Dockerfile
    ├── docker-compose.yml          ← Local Docker setup
    └── RUNBOOK.md                  ← This file
```

---

## 🚀 OPTION 1 — Run Locally (Python)

### Step 1: Install Dependencies
```cmd
cd d:\ReleaseMind\ReleaseMind-Core
pip install -r backend\requirements.txt
```

### Step 2: (Optional) Set GitHub Token
```cmd
set GITHUB_TOKEN=ghp_your_token_here
```

### Step 3: Start the Server
```cmd
python backend\api.py
```

### Step 4: Open Browser
```
http://localhost:7000
```

---

## 🐳 OPTION 2 — Run with Docker

### Step 1: Build Image
```cmd
cd d:\ReleaseMind\ReleaseMind-Core
docker build -t releasemind:latest .
```

### Step 2: Run with Docker Compose
```cmd
docker-compose up -d
```

### Step 3: Check Logs
```cmd
docker-compose logs -f releasemind
```

### Step 4: Stop
```cmd
docker-compose down
```

---

## ☸️ OPTION 3 — Deploy to Kubernetes

### Step 1: Push Image to Registry
```cmd
docker tag releasemind:latest your-registry/releasemind:v2
docker push your-registry/releasemind:v2
```

### Step 2: Update image in k8s/deployment.yaml
Change `image: releasemind:latest` to your registry path.

### Step 3: Set GitHub Token Secret
```cmd
kubectl create secret generic releasemind-secrets --from-literal=github-token=ghp_xxx
```

### Step 4: Apply Manifests
```cmd
kubectl apply -f k8s\deployment.yaml
```

### Step 5: Port-Forward to Test
```cmd
kubectl port-forward svc/releasemind-svc 7000:80
```

---

## 🧪 API Test Commands (PowerShell)

### ① Health Check — Live Metrics
```powershell
Invoke-RestMethod -Uri "http://localhost:7000/metrics" -Method GET | ConvertTo-Json -Depth 4
```

### ② Phase 8 — Analyze a Real GitHub Repo
```powershell
Invoke-RestMethod `
  -Uri "http://localhost:7000/analyze-repo" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{
    "repo_owner": "torvalds",
    "repo_name": "linux",
    "branch": "master",
    "config_drift": false,
    "peak_hours": false
  }' | ConvertTo-Json -Depth 8
```

**With a private repo (GitHub token required):**
```powershell
Invoke-RestMethod `
  -Uri "http://localhost:7000/analyze-repo" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{
    "repo_owner": "YOUR_USERNAME",
    "repo_name": "YOUR_REPO",
    "branch": "main",
    "github_token": "ghp_YOUR_TOKEN",
    "config_drift": true,
    "peak_hours": true
  }' | ConvertTo-Json -Depth 8
```

### ③ Phase 2 — Manual Risk Analysis (Legacy)
```powershell
Invoke-RestMethod `
  -Uri "http://localhost:7000/decide" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{
    "change":      { "intent": "hotfix", "services": ["auth", "payment"] },
    "human":       { "experience": "new", "owns_service": false },
    "environment": { "config_drift": true, "resource_drift": true },
    "timing":      { "peak_hours": true, "weekend": false }
  }' | ConvertTo-Json -Depth 8
```

### ④ Phase 6 — Record Deployment Outcome (Feedback Loop)
```powershell
# Mark deployment #1 as failure → increases auth failure rate
Invoke-RestMethod `
  -Uri "http://localhost:7000/deployment-result" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{ "deployment_id": 1, "outcome": "failure" }' | ConvertTo-Json
```

```powershell
# Mark as success
Invoke-RestMethod `
  -Uri "http://localhost:7000/deployment-result" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{ "deployment_id": 2, "outcome": "success" }' | ConvertTo-Json
```

### ⑤ View Decision History
```powershell
Invoke-RestMethod -Uri "http://localhost:7000/decisions?limit=10" | ConvertTo-Json -Depth 6
```

### ⑥ View Service Failure Rates
```powershell
Invoke-RestMethod -Uri "http://localhost:7000/service-stats" | ConvertTo-Json -Depth 4
```

### ⑦ Hot Reload Config (after editing risk_config.yaml)
```powershell
Invoke-RestMethod -Uri "http://localhost:7000/config/reload" -Method POST | ConvertTo-Json
```

---

## ⚙️ Tuning Risk Weights (No Code Changes)

Edit `backend/config/risk_config.yaml`:

```yaml
weights:
  files_changed_per_file: 0.20    # increase → more sensitive to large PRs
  failure_rate_multiplier: 3.0    # increase → past failures raise risk more
  config_drift_penalty: 4.0       # increase → penalize drift more heavily

strategy_thresholds:
  block_above: 20     # BLOCK if risk >= 20
  canary_above: 14    # CANARY if risk >= 14
  blue_green_above: 8 # BLUE_GREEN if risk >= 8
```

Then hot reload:
```powershell
Invoke-RestMethod -Uri "http://localhost:7000/config/reload" -Method POST
```

---

## 🗄️ Database Schema

```sql
-- deployments table
CREATE TABLE deployments (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp     TEXT,
  risk_score    REAL,
  strategy      TEXT,          -- ROLLING | BLUE_GREEN | CANARY | BLOCK
  outcome       TEXT,          -- pending | success | failure
  service       TEXT,
  developer     TEXT,
  repo_owner    TEXT,
  repo_name     TEXT,
  branch        TEXT,
  commit_sha    TEXT,
  files_changed INTEGER,
  lines_added   INTEGER,
  lines_deleted INTEGER,
  commit_type   TEXT,
  blast_radius  INTEGER,
  dep_depth     INTEGER,
  cpu_at_deploy REAL,
  mem_at_deploy REAL
);

-- service_stats table (rolling 10-deployment window)
CREATE TABLE service_stats (
  service        TEXT PRIMARY KEY,
  total_deploys  INTEGER,
  total_failures INTEGER,
  failure_rate   REAL,          -- 0.0 to 1.0
  last_updated   TEXT
);
```

---

## 🔌 API Route Reference

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/` | Dashboard UI |
| POST | `/analyze-repo` | **Phase 8** — Full GitHub → Risk → DB pipeline |
| POST | `/decide` | Legacy manual risk analysis |
| POST | `/deployment-result` | **Phase 6** — Record success/failure outcome |
| GET | `/decisions?limit=N` | Deployment history |
| GET | `/service-stats` | Per-service failure rates |
| GET | `/metrics` | Live CPU/memory (psutil + kubectl) |
| POST | `/config/reload` | Hot reload risk_config.yaml |

---

## 🔑 GitHub Token (for private repos / higher rate limits)

1. Go to: https://github.com/settings/tokens
2. Generate a classic PAT with `repo` and `read:user` scopes
3. Set it:
   - **Local:** `set GITHUB_TOKEN=ghp_xxx`
   - **Docker:** Add to `.env` file: `GITHUB_TOKEN=ghp_xxx`
   - **K8s:** `kubectl edit secret releasemind-secrets`
   - **UI:** Paste into the "GitHub Token" field directly

---

## 📊 How Risk Is Calculated

```
Risk Score =
  (files_changed × 0.20)
+ (lines_added / 100 × 0.50)
+ (lines_deleted / 100 × 0.10)
+ intent_base_score              # hotfix=2, feature=4, refactor=6, breaking=9
+ (1 - dev_experience) × 3.0    # new dev = +3.0, senior = +0.0
+ (not_owner_penalty × 2.0)
+ (dependency_depth × 1.50)
+ (blast_radius × 0.30)
+ (failure_rate × 3.0 × 10)     # rolling window last 10 deploys
+ (config_drift × 4.0)
+ (resource_drift × 3.0)
+ (cpu_above_75% × 0.10/%)
+ (mem_above_80% × 0.08/%)
+ (peak_hours × 2.0)
+ (weekend × 1.0)
```

All weights are in `backend/config/risk_config.yaml`.
