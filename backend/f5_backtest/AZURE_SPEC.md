# Azure Infrastructure Spec — Max EV Sports Edge Engine

## Resource Group: `rg-maxev-sports-prod`
Region: South Central US (closest to DFW)

---

## 1. PostgreSQL Flexible Server — `maxev-sports-db`

**Purpose:** Single source of truth for all game data, odds, signals, bets, P&L.

| Setting | Value | Why |
|---------|-------|-----|
| SKU | Burstable B1ms (1 vCore, 2 GB RAM) | Our DB is 8.6MB — this is massive overkill but cheapest tier |
| Storage | 32 GB | Room to grow to 10+ seasons |
| Backup | 7-day retention | Default, included |
| Version | PostgreSQL 16 | Latest |
| High Availability | Off | Not critical — research/betting tool, not customer-facing |

**Monthly Cost: ~$13-15/mo**

Scale up to B2s (2 vCore, 4 GB) if we add ML model result storage. ~$25/mo.

---

## 2. Azure Container Apps — `maxev-sports-api`

**Purpose:** FastAPI backend serving the signal engine, book monitor, and execution logic.

| Setting | Value | Why |
|---------|-------|-----|
| CPU | 0.25 vCPU | Lightweight API, most work is DB queries |
| Memory | 0.5 GB | Python + FastAPI overhead |
| Min replicas | 0 | Scale to zero when not in use (off-season) |
| Max replicas | 1 | No need for horizontal scale |
| Ingress | External (HTTPS) | API access from frontend |

**Monthly Cost: ~$0-10/mo** (consumption plan, pay per request — near-free for our volume)

---

## 3. Azure Container Apps — `maxev-sports-web`

**Purpose:** React frontend (static SPA).

**Alternative:** Just deploy to Azure Static Web Apps (free tier) instead of Container Apps.

| Setting | Value |
|---------|-------|
| Plan | Free tier |
| Custom domain | Optional (max-ev-sports.com subdomain) |
| CDN | Built into Static Web Apps |

**Monthly Cost: $0** (free tier handles this easily)

---

## 4. Azure Functions — Cron Scanners

**Purpose:** Timer-triggered functions that run the daily workflow.

| Function | Schedule | What It Does |
|----------|----------|-------------|
| `morning-scan` | `0 14 * * *` (9 AM CT) | Pull today's MLB games + FG odds from Odds API |
| `lineup-scan` | `0 19 * * *` (2 PM CT) | Pull starting pitchers from MLB API, score against signals |
| `f5-odds-scan` | `0 20 * * *` (3 PM CT) | Pull F5 odds for signal-qualifying games only |
| `game-grader` | `0 6 * * *` (1 AM CT) | Grade yesterday's bets, update P&L |
| `weekly-backtest` | `0 10 * * 0` (Sun 5 AM CT) | Re-run backtests with latest data |

| Setting | Value |
|---------|-------|
| Plan | Consumption (pay per execution) |
| Runtime | Python 3.11 |
| Timeout | 5 min per function |

**Monthly Cost: ~$0-2/mo** (Functions consumption plan is essentially free at this volume — maybe 150 executions/month × <5 sec each)

---

## 5. Azure Machine Learning Workspace — `maxev-sports-ml`

**Purpose:** Train gradient boosting / neural net models to find non-linear signal combinations. NOT needed day-one — add when we want to go beyond SQL-based signal testing.

| Setting | Value | Why |
|---------|-------|-----|
| Workspace | Basic | Cheapest |
| Compute | NC6s_v3 (1 GPU, 6 vCPU, 112 GB) | Only spin up for training runs |
| Usage Pattern | On-demand, ~2-4 hours/month | Train new models when we add data |

**Monthly Cost: ~$0 base + $3-5/hr when training**

Typical month: 2 training sessions × 2 hours = ~$12-15/mo for ML compute. Rest of the time the workspace costs nothing.

**Alternative:** Skip Azure ML entirely. Use Compute Instance (a VM with Jupyter) instead:
- Standard_DS3_v2 (4 vCPU, 14 GB RAM): $0.29/hr = ~$2-3 per training session
- Good enough for XGBoost/LightGBM on our dataset size
- GPU only needed if we go deep learning (future)

---

## 6. Azure Cache for Redis — `maxev-sports-cache`

**Purpose:** Cache live odds for fast lookups, cache signal scores during game time.

| Setting | Value |
|---------|-------|
| SKU | Basic C0 (250 MB) |
| Usage | Cache today's odds, signal scores, bet slip state |

**Monthly Cost: ~$15/mo**

**Alternative:** Skip Redis entirely. Store live odds in PostgreSQL. At our volume (15 games/day, poll 2x), a DB query is fast enough. Redis is nice-to-have, not required.

---

## 7. Azure Blob Storage — `maxevsportsdata`

**Purpose:** Store historical data exports, backtest result archives, ML model artifacts.

| Setting | Value |
|---------|-------|
| Tier | Cool (infrequent access) |
| Expected size | <1 GB |

**Monthly Cost: ~$0.01/mo** (basically free)

---

## 8. Azure Key Vault — `maxev-sports-kv`

**Purpose:** Store API keys (Odds API, MLB API if needed), database connection strings.

**Monthly Cost: ~$0.03/mo** (pennies per secret access)

---

## Cost Summary

### Minimum Viable (Day 1)

| Resource | Monthly Cost |
|----------|-------------|
| PostgreSQL Flexible (B1ms) | $15 |
| Container App API (consumption) | $5 |
| Static Web App (free tier) | $0 |
| Azure Functions (consumption) | $1 |
| Blob Storage | $0 |
| Key Vault | $0 |
| **TOTAL** | **~$21/mo** |

### Full Platform (with ML + Redis)

| Resource | Monthly Cost |
|----------|-------------|
| PostgreSQL Flexible (B1ms) | $15 |
| Container App API | $5 |
| Static Web App | $0 |
| Azure Functions | $1 |
| Redis Cache (Basic C0) | $15 |
| ML Compute (on-demand) | $12 |
| Blob Storage | $0 |
| Key Vault | $0 |
| **TOTAL** | **~$48/mo** |

### Comparison

| Option | Monthly | What You Get |
|--------|---------|-------------|
| **Azure Minimum** | **$21** | API + DB + Scanner + Frontend. Everything except ML training. |
| **Azure Full** | **$48** | Above + ML training + Redis cache |
| **VPS (current)** | $0 (already paying) | Could run everything here but less reliable + no ML |
| **Odds API** | $59 | Data feed (required regardless of infra) |
| **Total system cost** | **$80-107/mo** | Full edge engine + data feed |

---

## Deployment Path

### Phase 1: Research (NOW — use VPS + local)
- Keep backtesting local on Mac
- SQLite database stays local
- No Azure cost yet

### Phase 2: Live Scanner (when ready to paper trade)
- Deploy API + Functions to Azure
- Migrate DB to PostgreSQL Flexible
- ~$21/mo

### Phase 3: Full Platform (when signals are validated live)
- Add frontend on Static Web Apps
- Add Redis if polling frequency increases
- ~$36/mo

### Phase 4: ML Training (when expanding signals)
- Add ML workspace with on-demand compute
- Train models monthly
- ~$48/mo

---

## CI/CD

Same pattern as DealFlow CRE:
- GitHub Actions on push to `main`
- Build Docker container → push to Azure Container Registry
- Deploy to Container Apps automatically
- Database migrations via Alembic (if using SQLAlchemy) or raw SQL scripts

---

## Key Decision: VPS vs Azure

The VPS already runs and costs nothing extra. For Phase 2 (paper trading),
we could run the scanner on VPS with a cron job and PostgreSQL there.
Azure makes sense when:
1. We want reliability (VPS has had crypto miner issues)
2. We want ML compute on demand
3. We want to scale or productize this for other users
4. We want CI/CD and proper infrastructure

Recommendation: **Start on VPS for paper trading, migrate to Azure when
going live with real money.** The Azure setup takes <1 hour when ready.
