# QUASAR-TDS
### Teleportation-Based Quantum Digital Signature — Threat Detection System
**Smart India Hackathon 2026 | Problem Statement SIH26141**

---

> **Disclosure (§12.2):** All verdicts produced by this system are deterministic, rule-based hypotheses derived from statistical evidence vectors. They are not forensic certainties. The system contains zero AI/ML components — every decision is a closed-form calculation or a fixed rule table from the QUASAR-TDS specification.

---

## What this is

QUASAR-TDS implements a fully deterministic quantum digital signature verification pipeline with integrated attack-hypothesis attribution. It simulates the teleportation-based state-material distribution phase using Qiskit, applies a statistical Bell-Decoy Error Vector (DBEV) analysis, and runs a Quantum Threat Attribution Model (Q-TAM) that classifies anomalies into one of 9 named threat patterns — all without any machine learning.

The system is delivered in five integrated layers:
1. **Python backend** — quantum core, protocol core, detection engine, attack simulation engine (Phases 01-07)
2. **FastAPI HTTP API** — 6 endpoints wrapping the full pipeline with health probe (Phase 08 & 10)
3. **React dashboard** — professional judge-facing UI with live circuit visualization and presentation mode (Phase 09)
4. **Docker Compose & Packaging** — multi-container deployment with dual IPv4/IPv6 Nginx reverse proxy (Phase 10)
5. **Final Compliance Verification** — full 19-item §25 audit with 88/88 passing tests on host and in-container (Phase 11)

---

## Quick Start (Local — No Docker)

### Prerequisites

| Tool | Minimum Version | Check |
|------|----------------|-------|
| Python | 3.11+ | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |

### 1. Clone and enter the repository

```bash
git clone <repository-url>
cd Quantum_sih
```

### 2. Create and activate Python virtual environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

This installs the core dependencies. Note that quantum foundations are strictly pinned to the verified versions:
- `qiskit==2.5.2`
- `qiskit-aer==0.17.2`

| Package | Tested Version | Role |
|---------|---------------|------|
| `qiskit` | 2.5.2 (pinned) | Quantum circuit generation, Bell states, Pauli gates |
| `qiskit-aer` | 0.17.2 (pinned) | AerSimulator quantum backend execution |
| `numpy` | 2.4.6 / 2.5.3 | Array math, Hoeffding bound computation |
| `scipy` | 1.17.1 / 1.18.1 | Statistical distributions & correlation analysis |
| `pycryptodome` | 3.23.0 | SHA-256 HMAC, CB-BDS commitments, transcript hash chains |
| `fastapi` | 0.141.1 | REST API framework (6 endpoints) |
| `uvicorn` | 0.52.4 | ASGI web server |
| `httpx` | 0.28.1 | FastAPI TestClient HTTP transport |
| `pydantic` | 2.13.5 | Request/response data validation models |
| `pytest` | 9.1.1 | Test runner (88/88 test suite) |
| `matplotlib` | 3.11.2 | Phase 07 benchmark metric chart generation |

### 4. Run the test suite (88 tests, expected: 88 passed)

```bash
python -m pytest tests/ -v
```

Expected output:
```
========================= 88 passed, 2 warnings in ~5s =========================
```

### 5. Start the FastAPI backend

```bash
uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Confirm it is running:
```bash
curl http://127.0.0.1:8000/health
# Expected: {"status":"ok","version":"0.8.0","service":"QUASAR-TDS"}
```

Interactive API documentation is available at: http://127.0.0.1:8000/docs

### 6. Start the React dashboard

In a separate terminal:

```bash
cd dashboard
npm install
npm run dev
```

Dashboard is available at: http://localhost:5173

The dashboard expects the backend at `http://localhost:8000`. If you run the backend on a different port, update `VITE_API_URL` in `dashboard/.env`:
```
VITE_API_URL=http://localhost:<port>
```

---

## Docker Compose Deployment

### Prerequisites

| Tool | Version |
|------|---------|
| Docker | 24+ |
| Docker Compose | v2 (bundled with Docker Desktop) |

### Build and start all services

```bash
docker compose up --build
```

This command:
1. Builds the **backend** image (`Dockerfile.backend`) — Python 3.11-slim with all quantum and API dependencies.
2. Builds the **frontend** image (`Dockerfile.frontend`) — multi-stage: Node 20 compiles the Vite bundle, then Nginx Alpine serves the static assets.
3. Starts both containers on `quasar_internal_network`.
4. Waits for the backend healthcheck (`GET /health`) to pass before starting the frontend.

**Service endpoints after `docker compose up`:**

| Service | URL | Description |
|---------|-----|-------------|
| API (backend) | http://localhost:8000 | FastAPI — all 6 endpoints |
| API docs | http://localhost:8000/docs | Swagger UI |
| Dashboard (frontend) | http://localhost:5173 | React dashboard served via Nginx |
| Nginx health | http://localhost:5173/nginx-health | Container health probe |

### Verify services are healthy

```bash
# Backend health
curl http://localhost:8000/health
# Expected: {"status":"ok","version":"0.8.0","service":"QUASAR-TDS"}

# Nginx health probe
curl http://localhost:5173/nginx-health
# Expected: healthy
```

### Run a full verification round-trip via API

```bash
# 1. Create a session
curl -X POST http://localhost:8000/session \
  -H "Content-Type: application/json" \
  -d "{\"message_text\": \"Hello QUASAR-TDS\", \"signer_identity\": \"alice@quantum-node-01.org\"}"

# 2. Verify the session (replace <sid> with the sid from step 1)
curl -X POST http://localhost:8000/session/<sid>/verify

# 3. Fetch the explanation record
curl http://localhost:8000/session/<sid>/explanation
```

### Run an attack scenario

```bash
curl -X POST http://localhost:8000/attack \
  -H "Content-Type: application/json" \
  -d "{\"attack_name\": \"BellPairReplacement\"}"
```

Valid attack_name values:
RandomStateForgery, ZGuessInterceptResend, XGuessInterceptResend, YGuessInterceptResend,
EntangleAndMeasure, BellPairReplacement, CorrectionBitAlteration, Replay,
Impersonation, TranscriptInjection, CommitmentSubstitution, RushingAttempt

### Stop all services

```bash
docker compose down

# To also remove the named volumes (replay ledger storage):
docker compose down -v
```

---

## Project Structure

```
Quantum_sih/
├── quantum_core/           # Bell-pair generation, teleportation circuit, basis measurement (Phase 01)
├── protocol_core/          # State-material lifecycle, signing session, verifier, replay ledger (Phase 02-03, 06)
├── detection_engine/       # PB-DTF threshold engine, DBEV diagnostic, Q-TAM rule engine (Phase 04)
├── attack_engine/          # 12 isolated §14 attack injectors + Monte Carlo batch runner (Phase 05)
├── api/
│   ├── main.py             # FastAPI application — 6 endpoints (Phase 08)
│   └── schemas.py          # Pydantic v2 request/response models
├── dashboard/              # Vite + React 19 judge-facing dashboard (Phase 09)
│   └── src/
│       ├── App.jsx                    # Router and layout shell
│       ├── TeleportationCircuit.jsx   # Animated quantum circuit SVG with Presentation Mode
│       ├── VerdictPanel.jsx           # ACCEPT/REJECT/ALERT verdict + Hoeffding breakdown
│       ├── ErrorRateChart.jsx         # Per-basis error rate charts with threshold lines
│       ├── AttackLabView.jsx          # Live attack scenario picker (12 attacks)
│       ├── BenchmarkView.jsx          # Phase 07 experiment matrix visualization
│       └── ReplayLedgerView.jsx       # Session history and state-machine transitions
├── calibration_data/       # Calibration run outputs for threshold computation
├── benchmarks/             # Phase 07 experiment matrix CSV + charts
├── tests/                  # 88 pytest tests covering all phases (Phases 01-10)
├── phase_results/          # Per-phase result files with verbatim evidence
├── Dockerfile.backend      # Python 3.11-slim — FastAPI + quantum stack
├── Dockerfile.frontend     # Node 20 builder to Nginx Alpine (multi-stage)
├── docker-compose.yml      # Backend + frontend + volumes + health checks
├── nginx.conf              # SPA fallback, API proxy, gzip, security headers
├── requirements.txt        # Python package pins (no AI/ML packages)
├── MASTER_PROMPT.md        # Project operating charter
├── PROJECT_STATE.md        # Phase completion tracker
└── QUASAR-TDS_Final.md     # Complete technical specification (single source of truth)
```

---

## API Endpoints Reference

| Method | Path | Request | Response | Description |
|--------|------|---------|----------|-------------|
| `GET` | `/health` | — | `{status, version, service}` | Docker healthcheck probe |
| `POST` | `/session` | `{message_text, signer_identity?, n_samples_per_basis?}` | `{sid, signature_id, nonce, message_hex, status}` | Create a new QDS signing session |
| `POST` | `/session/{sid}/verify` | — | `{sid, payload: {verdict, rule_id, ...}}` | Run full verification pipeline |
| `GET` | `/session/{sid}/explanation` | — | Full explanation record | Retrieve stored explanation |
| `POST` | `/attack` | `{attack_name, n_samples_per_basis?}` | Full attack result | Run any §14 named attack end-to-end |
| `GET` | `/benchmark` | — | `{row_count, rows: [...]}` | Phase 07 experiment matrix data |

---

## Zero AI/ML Policy

`requirements.txt` contains no machine learning frameworks (no PyTorch, no TensorFlow, no scikit-learn).
Every verdict is a closed-form statistical hypothesis per §12.2 of QUASAR-TDS_Final.md.
Run `grep -i "torch\|tensorflow\|sklearn\|keras\|ml\|ai" requirements.txt` to confirm — zero matches.

---

## Running Tests in Detail

```bash
# All 88 tests
python -m pytest tests/ -v

# By module
python -m pytest tests/test_quantum_foundation.py -v    # Phase 01: Bell pairs, teleportation, Y-anticorrelation
python -m pytest tests/test_state_lifecycle.py -v       # Phase 02: one-time-use, partition sizes
python -m pytest tests/test_classical_integrity.py -v   # Phase 03: commitments, replay state machine
python -m pytest tests/test_detection_engine.py -v      # Phase 04: thresholds, Q-TAM branches, ordering
python -m pytest tests/test_attack_engine.py -v         # Phase 05: all 12 injectors
python -m pytest tests/test_end_to_end.py -v            # Phase 06: full pipeline round-trips
python -m pytest tests/test_benchmarks.py -v            # Phase 07: noise models, baselines, matrix, latency
python -m pytest tests/test_api.py -v                   # Phase 08 & 10: API endpoints + health probe
```

---

## Phase History

| Phase | Name | Status |
|-------|------|--------|
| 00 | Environment & Repo Setup | APPROVED |
| 01 | Quantum Foundation | APPROVED |
| 02 | State-Material Lifecycle | APPROVED |
| 03 | Classical Integrity Layer | APPROVED |
| 04 | Statistical Detection Engine (PB-DTF) + Q-TAM | APPROVED |
| 05 | Attack Simulation Engine | APPROVED |
| 06 | End-to-End Integration | APPROVED |
| 07 | Performance Evaluation & Benchmarking | APPROVED |
| 08 | API Layer | APPROVED |
| 09 | Professional Judge-Facing Dashboard | APPROVED |
| 10 | Dockerization & Final Packaging | APPROVED |
| 11 | Final Compliance Verification | APPROVED |

**System Status:** Complete & Fully Verified (12 / 12 Phases Approved)

