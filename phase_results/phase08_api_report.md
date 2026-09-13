# Phase 08 — API Layer — Result Report

## Objective

Wrap the full QUASAR-TDS verification pipeline into a FastAPI HTTP service with strict Pydantic v2
request/response schemas and no loose dicts anywhere in any endpoint. Per MASTER_PROMPT.md §3 Phase 08:
`POST /session` (create session), `POST /session/{sid}/verify` (submit for verification),
`GET /session/{sid}/explanation` (fetch evidence record), `POST /attack` (run named §14 attack scenario),
`GET /benchmark` (return Phase 07 experiment matrix as JSON). At least one full round-trip test and
one attack-scenario round-trip test required.

---

## What was built

| File | Description |
|------|-------------|
| [`api/schemas.py`](file:///c:/Users/USER/OneDrive/Desktop/Quantum_sih/api/schemas.py) | Pydantic v2 request/response models: `CreateSessionRequest`, `AttackScenarioRequest`, `VerificationPayload` (shared inner model), `SessionCreatedResponse`, `VerificationResponse`, `ExplanationResponse`, `AttackScenarioResponse`, `BenchmarkRowResponse`, `BenchmarkDataResponse`. `VALID_ATTACK_NAMES` list with `@field_validator` for 422 enforcement. |
| [`api/main.py`](file:///c:/Users/USER/OneDrive/Desktop/Quantum_sih/api/main.py) | FastAPI application with 5 endpoints, lifespan-scoped in-process state (`_sessions`, `_results`, `_shared_ledger`), CORS middleware for Phase 09 dashboard, injector registry dict, CSV-reading benchmark handler. |
| [`api/__init__.py`](file:///c:/Users/USER/OneDrive/Desktop/Quantum_sih/api/__init__.py) | Re-exports `app` from `api.main` for test import convenience. |
| [`tests/test_api.py`](file:///c:/Users/USER/OneDrive/Desktop/Quantum_sih/tests/test_api.py) | 14 named tests covering all endpoints, error paths, honest round-trip, live-ledger double-submit replay rejection, 5 attack scenarios, and §17.3 disclosure field coverage. |

---

## Endpoint Table

| Method | Path | Request Schema | Response Schema | Description |
|--------|------|---------------|----------------|-------------|
| `POST` | `/session` | `CreateSessionRequest` | `SessionCreatedResponse` | Create a new QDS signing session via `create_signing_session()` (§15) |
| `POST` | `/session/{sid}/verify` | — (path param only) | `VerificationResponse` | Run `verify_submitted_signature()` against shared ledger |
| `GET` | `/session/{sid}/explanation` | — (path param only) | `ExplanationResponse` | Fetch stored `ExplanationRecord` for a completed session |
| `POST` | `/attack` | `AttackScenarioRequest` | `AttackScenarioResponse` | Self-contained §14 attack scenario (fresh session + fresh ledger) |
| `GET` | `/benchmark` | — | `BenchmarkDataResponse` | Phase 07 §17.1 experiment matrix as JSON (reads pre-generated CSV) |

**Auto-docs:** `GET /docs` (Swagger UI), `GET /redoc` (ReDoc) — both live on `uvicorn api.main:app --reload`.

---

## Exact commands run

```powershell
# 1. Full test suite (73 prior + 14 new API tests)
.venv\Scripts\python.exe -m pytest tests/ -v --tb=short

# 2. App import and route verification
.venv\Scripts\python.exe -c "from api.main import app; print('App imported OK'); print('Routes:', [r.path for r in app.routes])"
```

---

## Exact verification output

### pytest (87/87)

```
============================= test session starts =============================
platform win32 -- Python 3.14.0, pytest-9.1.1, pluggy-1.6.0
configfile: pytest.ini
collected 87 items

tests/test_api.py::test_create_session_returns_valid_sid PASSED          [  1%]
tests/test_api.py::test_verify_honest_session_accepts PASSED             [  2%]
tests/test_api.py::test_full_round_trip_explanation_matches_verify PASSED [  3%]
tests/test_api.py::test_verify_unknown_sid_returns_404 PASSED            [  4%]
tests/test_api.py::test_explanation_before_verify_returns_404 PASSED     [  5%]
tests/test_api.py::test_verify_same_session_twice_second_call_is_replay PASSED [  6%]
tests/test_api.py::test_attack_random_state_forgery PASSED               [  8%]
tests/test_api.py::test_attack_replay PASSED                             [  9%]
tests/test_api.py::test_attack_impersonation PASSED                      [ 10%]
tests/test_api.py::test_attack_transcript_injection PASSED               [ 11%]
tests/test_api.py::test_attack_commitment_substitution PASSED            [ 12%]
tests/test_api.py::test_attack_invalid_name_returns_422 PASSED           [ 13%]
tests/test_api.py::test_benchmark_returns_18_rows PASSED                 [ 14%]
tests/test_api.py::test_benchmark_row_has_required_disclosure_fields PASSED [ 16%]
tests/test_attack_engine.py::test_injector_random_state_forgery PASSED   [ 17%]
tests/test_attack_engine.py::test_injector_z_guess_intercept_resend PASSED [ 18%]
tests/test_attack_engine.py::test_injector_x_guess_intercept_resend PASSED [ 19%]
tests/test_attack_engine.py::test_injector_y_guess_intercept_resend PASSED [ 20%]
tests/test_attack_engine.py::test_injector_entangle_and_measure_boundary_and_monotonicity PASSED [ 21%]
tests/test_attack_engine.py::test_injector_bell_pair_replacement PASSED  [ 22%]
tests/test_attack_engine.py::test_injector_correction_bit_alteration_transcript_failure PASSED [ 24%]
tests/test_attack_engine.py::test_injector_correction_bit_alteration_quantum_mismatch PASSED [ 25%]
tests/test_attack_engine.py::test_injector_replay PASSED                 [ 26%]
tests/test_attack_engine.py::test_injector_impersonation PASSED          [ 27%]
tests/test_attack_engine.py::test_injector_transcript_injection PASSED   [ 28%]
tests/test_attack_engine.py::test_injector_commitment_substitution PASSED [ 29%]
tests/test_attack_engine.py::test_injector_rushing_attempt_rejection PASSED [ 31%]
tests/test_attack_engine.py::test_monte_carlo_runner_batch_n200_all_12_attacks PASSED [ 32%]
tests/test_benchmarks.py::test_noise_models_generation PASSED            [ 33%]
tests/test_benchmarks.py::test_honest_baselines_acceptance_and_error_budget PASSED [ 34%]
tests/test_benchmarks.py::test_attack_matrix_detection_and_bound_compliance PASSED [ 35%]
tests/test_benchmarks.py::test_latency_profiling_completeness PASSED     [ 36%]
tests/test_benchmarks.py::test_state_size_scaling PASSED                 [ 37%]
tests/test_benchmarks.py::test_metric_csv_files_and_disclosures PASSED   [ 39%]
tests/test_benchmarks.py::test_primary_charts_exist_and_valid PASSED     [ 40%]
tests/test_classical_integrity.py::test_commitment_hiding_and_binding PASSED [ 41%]
tests/test_classical_integrity.py::test_commitment_domain_separation PASSED [ 42%]
tests/test_classical_integrity.py::test_transcript_tamper_detected PASSED [ 43%]
tests/test_classical_integrity.py::test_message_binding_requires_fixed_challenge PASSED [ 44%]
tests/test_classical_integrity.py::test_replay_reservation_is_atomic_under_concurrency PASSED [ 45%]
tests/test_classical_integrity.py::test_lease_expiry_releases_crashed_reservation PASSED [ 47%]
tests/test_classical_integrity.py::test_blocked_retention_prevents_immediate_resubmission PASSED [ 48%]
tests/test_detection_engine.py::test_threshold_computation_matches_formula PASSED [ 49%]
tests/test_detection_engine.py::test_error_budget_disclosed_and_summed_correctly PASSED [ 50%]
tests/test_detection_engine.py::test_qtam_replay PASSED                  [ 51%]
tests/test_detection_engine.py::test_qtam_impersonation PASSED           [ 52%]
tests/test_detection_engine.py::test_qtam_transcript_tamper PASSED       [ 54%]
tests/test_detection_engine.py::test_qtam_broadband_degradation PASSED   [ 55%]
tests/test_detection_engine.py::test_qtam_channel_integrity_anomaly PASSED [ 56%]
tests/test_detection_engine.py::test_qtam_broad_pauli_anomaly PASSED     [ 57%]
tests/test_detection_engine.py::test_qtam_partial_broad_pauli_anomaly PASSED [ 58%]
tests/test_detection_engine.py::test_qtam_basis_selective_anomaly PASSED [ 59%]
tests/test_detection_engine.py::test_qtam_ambiguous_anomaly PASSED       [ 60%]
tests/test_detection_engine.py::test_qtam_ordering_edge_case PASSED      [ 62%]
tests/test_detection_engine.py::test_v_hardware_is_auxiliary_not_acceptance_gate PASSED [ 63%]
tests/test_detection_engine.py::test_acceptance_rule_honest_passes PASSED [ 64%]
tests/test_detection_engine.py::test_acceptance_rule_failures PASSED     [ 65%]
tests/test_detection_engine.py::test_dbev_basis_dependent_rules PASSED   [ 66%]
tests/test_detection_engine.py::test_dbev_uniform_matching_fails_on_honest_Y PASSED [ 67%]
tests/test_detection_engine.py::test_forgery_bound_calculation PASSED    [ 68%]
tests/test_detection_engine.py::test_explanation_record_metadata PASSED  [ 70%]
tests/test_detection_engine.py::test_calibration_run_measures_rates_and_computes_thresholds PASSED [ 71%]
tests/test_end_to_end.py::test_full_honest_flow_accepts PASSED           [ 72%]
tests/test_end_to_end.py::test_full_replay_flow_rejects_with_correct_state_transition PASSED [ 73%]
tests/test_end_to_end.py::test_e2e_random_state_forgery PASSED           [ 74%]
tests/test_end_to_end.py::test_e2e_z_guess_intercept_resend PASSED       [ 75%]
tests/test_end_to_end.py::test_e2e_x_guess_intercept_resend PASSED       [ 77%]
tests/test_end_to_end.py::test_e2e_y_guess_intercept_resend PASSED       [ 78%]
tests/test_end_to_end.py::test_e2e_entangle_and_measure PASSED           [ 79%]
tests/test_end_to_end.py::test_e2e_bell_pair_replacement PASSED          [ 80%]
tests/test_end_to_end.py::test_e2e_correction_bit_alteration PASSED      [ 81%]
tests/test_end_to_end.py::test_e2e_replay PASSED                         [ 82%]
tests/test_end_to_end.py::test_e2e_impersonation PASSED                  [ 83%]
tests/test_end_to_end.py::test_e2e_transcript_injection PASSED           [ 85%]
tests/test_end_to_end.py::test_e2e_commitment_substitution PASSED        [ 86%]
tests/test_end_to_end.py::test_e2e_rushing_attempt PASSED                [ 87%]
tests/test_quantum_foundation.py::test_bell_pair_generation_fidelity PASSED [ 88%]
tests/test_quantum_foundation.py::test_teleportation_correction_mapping PASSED [ 89%]
tests/test_quantum_foundation.py::test_x_basis_prep_and_measure PASSED   [ 90%]
tests/test_quantum_foundation.py::test_y_basis_prep_and_measure PASSED   [ 91%]
tests/test_quantum_foundation.py::test_z_basis_prep_and_measure PASSED   [ 93%]
tests/test_quantum_foundation.py::test_honest_phi_plus_XX_correlation PASSED [ 94%]
tests/test_quantum_foundation.py::test_honest_phi_plus_ZZ_correlation PASSED [ 95%]
tests/test_quantum_foundation.py::test_honest_phi_plus_YY_anticorrelation PASSED [ 96%]
tests/test_state_lifecycle.py::test_one_time_use_enforced PASSED         [ 97%]
tests/test_state_lifecycle.py::test_storage_window_behavior PASSED       [ 98%]
tests/test_state_lifecycle.py::test_partition_sizes_match_spec PASSED    [100%]

======================= 87 passed, 2 warnings in 5.21s ========================
```

### App import + routes

```
App imported OK
Routes: ['/openapi.json', '/docs', '/docs/oauth2-redirect', '/redoc',
         '/session', '/session/{sid}/verify', '/session/{sid}/explanation',
         '/attack', '/benchmark']
```

---

## Requirement-by-requirement checklist

- [x] `POST /session` creates a new QDS signing session via `create_signing_session()` with strict Pydantic schema — evidence: `test_create_session_returns_valid_sid` PASSED; returns `sid`, `signature_id`, `nonce`, `message_hex`, `status="CREATED"`.
- [x] `POST /session/{sid}/verify` runs `verify_submitted_signature()` through the shared replay ledger — evidence: `test_verify_honest_session_accepts` PASSED; returns `verdict="ACCEPT"`, `rule_id="RULE_0_ACCEPTANCE"`.
- [x] `GET /session/{sid}/explanation` returns stored `ExplanationRecord` for a completed session — evidence: `test_full_round_trip_explanation_matches_verify` PASSED; `rule_id` and `primary_hypothesis` match verify response exactly.
- [x] Full round-trip (create → verify → explanation) tested end-to-end — evidence: `test_full_round_trip_explanation_matches_verify` PASSED.
- [x] `POST /attack` runs a named attack scenario self-contained — evidence: `test_attack_random_state_forgery`, `test_attack_replay`, `test_attack_impersonation`, `test_attack_transcript_injection`, `test_attack_commitment_substitution` all PASSED.
- [x] Attack-scenario round-trip tested — evidence: five named attack tests PASSED.
- [x] `GET /benchmark` returns Phase 07 experiment matrix — evidence: `test_benchmark_returns_18_rows` (18 rows: 6 honest + 12 attack) PASSED.
- [x] Unknown `sid` on verify returns 404 — evidence: `test_verify_unknown_sid_returns_404` PASSED.
- [x] Explanation before verify returns 404 — evidence: `test_explanation_before_verify_returns_404` PASSED.
- [x] Invalid `attack_name` returns 422 — evidence: `test_attack_invalid_name_returns_422` PASSED.
- [x] **Live-ledger double-submit replay rejection** — same `sid` submitted twice to `POST /session/{sid}/verify` returns `REJECT` + `RULE_1_REPLAY` on the second call, no injector used — evidence: `test_verify_same_session_twice_second_call_is_replay` PASSED.
- [x] §17.3 disclosure fields present on every benchmark row — evidence: `test_benchmark_row_has_required_disclosure_fields` PASSED; asserts `attack_model`, `noise_model`, `calibrated_baseline`, `sample_count`, `error_budget` non-empty on all 18 rows.
- [x] Real Pydantic schemas used — no loose dicts in any endpoint signature — evidence: all request/response bodies declared as Pydantic models in `api/schemas.py`.
- [x] Full regression — 0 regressions against Phases 01–07 — evidence: `87/87 passed` includes all prior 73 tests.
- [x] Self-check: No AI/ML anywhere in Phase 08 — evidence: `api/main.py` uses `create_signing_session` + `verify_submitted_signature` (deterministic rule engine), Pydantic schemas, CSV reading. No model weights, no learned parameters.
- [x] Terminology discipline per §6 — evidence: "attack-hypothesis attribution" used in schemas; "model-based hypothesis, never forensic certainty" in `disclaimer` field; "rule-based hypothesis (Non-ML)" in `evidence_mode` field.

---

## Design Decisions (required disclosures per §0 rule 11)

### 1. In-process session store

Sessions and results are held in Python dicts (`_sessions`, `_results`) scoped to the FastAPI lifespan. An SQLite-backed store is unnecessary for the single-process SIH prototype — the replay ledger already provides persistence for freshness enforcement. This is sufficient for the demo context.

### 2. Attack endpoint uses fresh session + fresh ledger (consciously chosen)

`POST /attack` creates its own fresh signing session and its own `ReplayLedger()` per call.

**Rationale for ledger isolation:** an attack that produces `BLOCKED` state would permanently poison the shared ledger's entry for that `sid`, preventing any future honest session that happened to regenerate the same SID. Fresh ledger per attack call eliminates this cross-contamination.

**Phase 09 consequence (documented here explicitly):** a judge clicking "Run Attack" in the dashboard will always see a brand-new session being attacked, not an attack against the session currently visible on their screen. This is a **consciously-chosen self-contained demo model**. Phase 09's attack picker should be built as a "watch this attack get caught" scenario demonstrator — it shows the attack's own `sid`, evidence vector, and verdict as a complete isolated event, not as a mutation of the main honest session.

### 3. `GET /benchmark` reads pre-generated Phase 07 CSVs

The Phase 07 benchmark matrix takes minutes to run. Reading the pre-generated `benchmarks/experiment_matrix_results.csv` on each request is the correct design — benchmark data is a static, historical record, not a live measurement.

---

## Deviations from QUASAR-TDS_Final.md (if any)

NONE. The spec (§16) names FastAPI as the designated API technology. All 5 endpoints wrap modules built strictly per §8, §12, §13, §14, §15.

---

## Blockers encountered (if any)

**Resolved during build:** `api/schemas.py` was initially written by PowerShell's `Set-Content` cmdlet using Windows-1252 encoding, causing a UTF-8 `SyntaxError` on import. Fixed by re-encoding the file to UTF-8 with `[System.IO.File]::WriteAllText(..., [System.Text.Encoding]::UTF8)`. All subsequent files written correctly.

---

STATUS: READY FOR REVIEW
