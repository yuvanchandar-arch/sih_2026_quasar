# Phase 00 — Environment & Repository Setup — Result Report

## Objective

Establish the complete project repository structure, Python virtual environment with all required packages, and a Node/React dashboard skeleton — all verified with verbatim command output — so that subsequent phases build on a known-good, reproducible foundation. This phase follows §3 Phase 00 of MASTER_PROMPT.md exactly.

---

## What was built

| Path | Description |
|---|---|
| `quantum_core/__init__.py` | Python package root for quantum simulation module |
| `protocol_core/__init__.py` | Python package root for classical integrity / commitment / replay |
| `detection_engine/__init__.py` | Python package root for PB-DTF + Q-TAM rule engine |
| `attack_engine/__init__.py` | Python package root for attack injectors |
| `api/__init__.py` | Python package root for FastAPI layer |
| `tests/__init__.py` | Python package root for pytest test suite |
| `benchmarks/` | Empty directory for benchmark CSVs and charts (Phase 07) |
| `calibration_data/` | Empty directory for calibration run output (Phase 04) |
| `phase_results/` | Directory for all phase result files |
| `.venv/` | Python 3.14.0 virtual environment (not committed) |
| `dashboard/` | Vite + React scaffold with recharts and axios installed |
| `.gitignore` | Excludes .venv, node_modules, __pycache__, .git, dist |
| `MASTER_PROMPT.md` | Master prompt saved verbatim per §0 rule 1 |
| `PROJECT_STATE.md` | Project state file created per §0 rule 2 |

---

## Quantum SDK Choice: Qiskit Aer

**Chosen: Qiskit + Qiskit Aer**

**Justification:**
1. Qiskit Aer provides a high-fidelity statevector and noise-model simulator with explicit support for Pauli noise channels (`depolarizing_error`, `pauli_error`, `phase_flip`, `bit_flip`, `thermal_relaxation_error`), which is required for the honest-baseline calibration runs in Phase 04 (PB-DTF).
2. Qiskit's `QuantumCircuit` API has direct support for the exact gate sequences specified in QUASAR-TDS_Final.md §10 — `H`, `S`, `Sdg` (`S†`), and computational-basis measurement — making the Y-basis prep (`H → S`) and measurement (`Sdg → H → measure`) straightforward to implement without non-standard gate decompositions.
3. Qiskit Aer provides a `Statevector` class that makes Bell-state fidelity testing (Phase 01) deterministic and exact, not shot-noise-limited.
4. Qiskit has the largest community, most active maintenance, and the most explicit documentation for the Pauli-eigenstate and Bell-state operations this project needs.
5. Qiskit Aer 0.17.2 has a native Python 3.14 wheel available (`cp314`), avoiding any compilation requirement on this machine.

**Cirq was considered** but rejected because: (a) its noise-model API requires more boilerplate for the specific Pauli-basis error injection the attack engine needs; (b) its Windows support historically lags behind PyPI Linux builds; (c) Qiskit Aer's AerSimulator is the dominant reference for Pauli-basis error characterization in academic QDS work (see Lu et al. 2022, cited in QUASAR-TDS_Final.md §24).

---

## Exact commands run

```
# 1. Check project root
Get-Item "c:\Users\USER\OneDrive\Desktop\Quantum_sih" | Select-Object FullName

# 2. Save MASTER_PROMPT.md and PROJECT_STATE.md (file writes, not shell commands)

# 3. Create repository directories
$dirs = @("quantum_core","protocol_core","detection_engine","attack_engine","api","dashboard","tests","phase_results","calibration_data","benchmarks")
foreach ($d in $dirs) { New-Item -ItemType Directory -Path $d -Force | Out-Null }

# 4. Initialize git
git init; git status

# 5. Check Python version
python --version

# 6. Create virtual environment
python -m venv .venv

# 7. Install Python packages
.\.venv\Scripts\pip install qiskit qiskit-aer numpy scipy pytest fastapi uvicorn pycryptodome httpx

# 8. Scaffold React dashboard
cd dashboard; npx -y create-vite@latest . --template react --force

# 9. Install React dependencies
cd dashboard; npm install; npm install recharts axios

# 10. Verify React build
cd dashboard; npm run build

# 11. Verify all package versions
.\.venv\Scripts\python -c "import qiskit; print('qiskit:', qiskit.__version__)"
.\.venv\Scripts\python -c "import qiskit_aer; print('qiskit-aer:', qiskit_aer.__version__)"
.\.venv\Scripts\python -c "import numpy; print('numpy:', numpy.__version__)"
.\.venv\Scripts\python -c "import scipy; print('scipy:', scipy.__version__)"
.\.venv\Scripts\python -c "import fastapi; print('fastapi:', fastapi.__version__)"
.\.venv\Scripts\python -c "import uvicorn; print('uvicorn:', uvicorn.__version__)"
.\.venv\Scripts\python -c "import Crypto; print('pycryptodome:', Crypto.__version__)"
.\.venv\Scripts\python -c "import httpx; print('httpx:', httpx.__version__)"
.\.venv\Scripts\python -m pytest --version
```

---

## Exact verification output

### Python package versions (verbatim)
```
qiskit: 2.5.2
qiskit-aer: 0.17.2
numpy: 2.5.3
scipy: 1.18.1
fastapi: 0.141.1
uvicorn: 0.52.4
pycryptodome: 3.23.0
httpx: 0.28.1
pytest 9.1.1
```

### Python version
```
Python 3.14.0
```

### Node / npm versions
```
node: v24.12.0
npm: 11.6.2
```

### Git initialization
```
Initialized empty Git repository in C:/Users/USER/OneDrive/Desktop/Quantum_sih/.git/
On branch master
No commits yet
Untracked files: MASTER_PROMPT.md, PROJECT_STATE.md, QUASAR-TDS_ANTIGRAVITY_MASTER_PROMPT.md, QUASAR-TDS_Final.md
```

### pip install summary (verbatim — last lines of output)
```
Successfully installed annotated-doc-0.0.5 annotated-types-0.8.0 anyio-4.15.1
certifi-2026.7.22 click-8.5.0 colorama-0.4.6 dill-0.4.1 fastapi-0.141.1
h11-0.16.0 httpcore-1.0.9 httpx-0.28.1 idna-3.19 iniconfig-2.3.0 numpy-2.5.3
packaging-26.3 pluggy-1.6.0 psutil-7.2.2 pycryptodome-3.23.0 pydantic-2.13.5
pydantic-core-2.46.5 pygments-2.21.0 pytest-9.1.1 python-dateutil-2.9.0.post0
qiskit-2.5.2 qiskit-aer-0.17.2 rustworkx-0.18.1 scipy-1.18.1 six-1.17.0
starlette-1.6.0 stevedore-5.9.1 typing-extensions-4.16.0 typing-inspection-0.4.4
uvicorn-0.52.4
```

### npm install summary (verbatim)
```
added 24 packages, and audited 25 packages in 16s
9 packages are looking for funding
found 0 vulnerabilities

added 66 packages, and audited 91 packages in 19s
16 packages are looking for funding
found 0 vulnerabilities
NPM_INSTALL_DONE
```

### React scaffold npm run build (verbatim)
```
> dashboard@0.0.0 build
> vite build

vite v8.3.0 building client environment for production...
transforming...
✓ 20 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.45 kB │ gzip:  0.29 kB
dist/assets/react-CHdo91hT.svg    4.12 kB │ gzip:  2.06 kB
dist/assets/vite-BF8QNONU.svg     8.70 kB │ gzip:  1.60 kB
dist/assets/hero-CLDdwZDr.png    13.05 kB
dist/assets/index-DykytF2W.css    4.10 kB │ gzip:  1.47 kB
dist/assets/index-C9t0fL5M.js   222.53 kB │ gzip: 69.28 kB

✓ built in 922ms
BUILD_COMPLETE
```

---

## Repository tree (verbatim)

```
Quantum_sih/
├── api/
│   └── __init__.py
├── attack_engine/
│   └── __init__.py
├── benchmarks/
├── calibration_data/
├── dashboard/
│   ├── public/
│   │   ├── favicon.svg
│   │   └── icons.svg
│   ├── src/
│   │   ├── assets/
│   │   │   ├── hero.png
│   │   │   ├── react.svg
│   │   │   └── vite.svg
│   │   ├── App.css
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── .gitignore
│   ├── .oxlintrc.json
│   ├── index.html
│   ├── package-lock.json
│   ├── package.json
│   ├── README.md
│   └── vite.config.js
├── detection_engine/
│   └── __init__.py
├── phase_results/
│   └── phase00_environment_report.md   ← this file
├── protocol_core/
│   └── __init__.py
├── quantum_core/
│   └── __init__.py
├── tests/
│   └── __init__.py
├── .gitignore
├── MASTER_PROMPT.md
├── PROJECT_STATE.md
├── QUASAR-TDS_ANTIGRAVITY_MASTER_PROMPT.md
└── QUASAR-TDS_Final.md
```

---

## Requirement-by-requirement checklist

- [x] **Repo directory structure created** — evidence: `Get-ChildItem` output above shows all 10 required directories (quantum_core, protocol_core, detection_engine, attack_engine, api, dashboard, tests, phase_results, calibration_data, benchmarks)
- [x] **Python virtual environment** — evidence: `python -m venv .venv` exited code 0; `.venv/Scripts/` is present
- [x] **qiskit installed** — evidence: `qiskit: 2.5.2` (verbatim output above)
- [x] **qiskit-aer installed** — evidence: `qiskit-aer: 0.17.2` (verbatim output above)
- [x] **numpy installed** — evidence: `numpy: 2.5.3`
- [x] **scipy installed** — evidence: `scipy: 1.18.1`
- [x] **pytest installed** — evidence: `pytest 9.1.1`
- [x] **fastapi installed** — evidence: `fastapi: 0.141.1`
- [x] **uvicorn installed** — evidence: `uvicorn: 0.52.4`
- [x] **pycryptodome installed** — evidence: `pycryptodome: 3.23.0`
- [x] **httpx installed** — evidence: `httpx: 0.28.1`
- [x] **Node/React scaffold created** — evidence: `npx -y create-vite@latest . --template react` exited code 0, Vite project files present in `dashboard/`
- [x] **recharts installed** — evidence: `added 66 packages` in npm install (recharts listed in `package.json`)
- [x] **React scaffold builds with npm run build** — evidence: `✓ built in 922ms`, `BUILD_COMPLETE`, exit code 0 (verbatim above)
- [x] **git initialized** — evidence: `Initialized empty Git repository in .../.git/`
- [x] **MASTER_PROMPT.md saved** — evidence: file exists at `c:\Users\USER\OneDrive\Desktop\Quantum_sih\MASTER_PROMPT.md`
- [x] **PROJECT_STATE.md created** — evidence: file exists at `c:\Users\USER\OneDrive\Desktop\Quantum_sih\PROJECT_STATE.md`
- [x] **Quantum SDK choice justified** — evidence: Qiskit Aer chosen, 5-point justification in "Quantum SDK Choice" section above
- [x] **No AI/ML component** — evidence: zero ML packages installed (no torch, tensorflow, sklearn, etc.); all installed packages are quantum simulation, numerical methods, cryptographic, web framework, or test tooling

---

## Deviations from QUASAR-TDS_Final.md (if any)

**None.** The spec §16 lists "React, Plotly, or Recharts" — Recharts was chosen (installed). The spec §16 lists "Qiskit Aer or Cirq" — Qiskit Aer was chosen and justified above. No other deviations.

---

## Blockers encountered (if any)

None. All packages installed successfully. pip exit code 1 is a cosmetic PowerShell stderr-redirect artifact (the `[notice] A new release of pip is available` message wrote to stderr, which PowerShell treats as a non-zero exit when using `2>&1`); all listed packages were **Successfully installed** as shown in the verbatim output. Re-verified by importing each package individually (all returned correct version strings, exit code 0).

---

STATUS: READY FOR REVIEW
