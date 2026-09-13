"""
QUASAR-TDS API Layer: FastAPI Application (Phase 08)

Wraps the full QUASAR-TDS verification pipeline into 5 HTTP endpoints
per MASTER_PROMPT.md §3 Phase 08 requirements and QUASAR-TDS_Final.md §16.

Endpoints:
    POST   /session                    — Create a new QDS signing session
    POST   /session/{sid}/verify       — Submit stored session for verification
    GET    /session/{sid}/explanation  — Fetch stored explanation record
    POST   /attack                     — Run a named §14 attack scenario (self-contained)
    GET    /benchmark                  — Return Phase 07 experiment matrix as JSON

Design decisions:
    - In-process dicts hold sessions/results (sufficient for single-process SIH prototype).
    - The shared _shared_ledger enforces replay detection across all honest sessions.
    - POST /attack uses its OWN fresh ReplayLedger() per call — attack BLOCKED states
      must not pollute the shared ledger used by honest sessions.
    - GET /benchmark reads pre-generated Phase 07 CSVs; does not re-run the matrix.
    - Zero AI/ML anywhere; all decisions are deterministic rule-based hypotheses.

Terminology per QUASAR-TDS_Final.md §6 used throughout.
"""

from __future__ import annotations

import csv
import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from protocol_core.verifier import (
    create_signing_session,
    verify_submitted_signature,
    SubmittedSignature,
    VerificationResult,
)
from protocol_core.replay_ledger import ReplayLedger
from detection_engine.thresholds import calculate_thresholds, ErrorBudget
from attack_engine import (
    RandomStateForgeryInjector,
    ZGuessInterceptResendInjector,
    XGuessInterceptResendInjector,
    YGuessInterceptResendInjector,
    EntangleAndMeasureInjector,
    BellPairReplacementInjector,
    CorrectionBitAlterationInjector,
    ReplayInjector,
    ImpersonationInjector,
    TranscriptInjectionInjector,
    CommitmentSubstitutionInjector,
    RushingAttemptInjector,
    BaseAttackInjector,
)
from api.schemas import (
    CreateSessionRequest,
    AttackScenarioRequest,
    SessionCreatedResponse,
    VerificationResponse,
    ExplanationResponse,
    AttackScenarioResponse,
    BenchmarkDataResponse,
    BenchmarkRowResponse,
    VerificationPayload,
    VALID_ATTACK_NAMES,
)

# ── Injector registry ──────────────────────────────────────────────────────────

_INJECTOR_REGISTRY: Dict[str, type] = {
    "RandomStateForgery": RandomStateForgeryInjector,
    "ZGuessInterceptResend": ZGuessInterceptResendInjector,
    "XGuessInterceptResend": XGuessInterceptResendInjector,
    "YGuessInterceptResend": YGuessInterceptResendInjector,
    "EntangleAndMeasure": EntangleAndMeasureInjector,
    "BellPairReplacement": BellPairReplacementInjector,
    "CorrectionBitAlteration": CorrectionBitAlterationInjector,
    "Replay": ReplayInjector,
    "Impersonation": ImpersonationInjector,
    "TranscriptInjection": TranscriptInjectionInjector,
    "CommitmentSubstitution": CommitmentSubstitutionInjector,
    "RushingAttempt": RushingAttemptInjector,
}

# ── Application state (lifespan-scoped) ───────────────────────────────────────

_sessions: Dict[str, SubmittedSignature] = {}   # sid → sig_obj
_results: Dict[str, VerificationResult] = {}     # sid → result
_shared_ledger: Optional[ReplayLedger] = None    # single ledger for honest sessions


@asynccontextmanager
async def _lifespan(app: FastAPI):
    global _shared_ledger
    _shared_ledger = ReplayLedger()
    _sessions.clear()
    _results.clear()
    yield
    # Teardown: nothing persistent to clean up for prototype.


# ── FastAPI application ────────────────────────────────────────────────────────

app = FastAPI(
    title="QUASAR-TDS API",
    description=(
        "Deterministic, Non-ML Verification and Attack-Hypothesis Attribution Layer "
        "for Teleportation-Based Quantum Digital Signatures. "
        "All verdicts are model-based hypotheses, never forensic certainty. "
        "Smart India Hackathon 2026 | SIH26141."
    ),
    version="0.8.0",
    lifespan=_lifespan,
)

# Allow the Phase 09 React dashboard (any localhost origin) to reach this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _build_payload(result: VerificationResult) -> VerificationPayload:
    """Convert a VerificationResult to a VerificationPayload response model."""
    exp = result.explanation
    ev = result.evidence_vector
    return VerificationPayload(
        verdict=result.verdict,
        rule_id=result.rule_id,
        primary_hypothesis=result.primary_hypothesis,
        alternative_explanation=result.alternative_explanation,
        evidence_values=ev.as_dict(),
        thresholds={
            "X": float(exp.thresholds.get("X", 0.0)),
            "Y": float(exp.thresholds.get("Y", 0.0)),
            "Z": float(exp.thresholds.get("Z", 0.0)),
            "Bell": float(exp.thresholds.get("Bell", 0.0)),
        },
        sample_sizes={k: int(v) for k, v in exp.sample_sizes.items()},
        evidence_mode=exp.evidence_mode,
        is_model_based_hypothesis=exp.is_model_based_hypothesis,
        disclaimer=exp.disclaimer,
    )


def _default_thresholds() -> Any:
    """Compute default calibration-aware thresholds for API sessions."""
    budget = ErrorBudget()
    mu_hats = {"X": 0.01, "Y": 0.01, "Z": 0.01, "Bell": 0.01}
    n_cal = {"X": 1000, "Y": 1000, "Z": 1000, "Bell": 1000}
    n_ver = {"X": 500, "Y": 500, "Z": 500, "Bell": 500}
    return calculate_thresholds(mu_hats, n_cal, n_ver, budget=budget)


# ── Endpoint: POST /session ────────────────────────────────────────────────────

@app.post(
    "/session",
    response_model=SessionCreatedResponse,
    summary="Create a new QDS signing session",
    description=(
        "Runs the signer-side create_signing_session() function (§15) to produce "
        "CB-BDS commitments, a transcript hash chain, and message-binding hash M_c. "
        "The session is held in memory and identified by the returned sid."
    ),
    tags=["Session"],
)
def create_session(request: CreateSessionRequest) -> SessionCreatedResponse:
    message_bytes = request.message_text.encode("utf-8")
    sig_obj, _context = create_signing_session(
        message=message_bytes,
        signer_identity=request.signer_identity,
        n_samples_per_basis=request.n_samples_per_basis,
    )
    sid = sig_obj.sid
    _sessions[sid] = sig_obj
    return SessionCreatedResponse(
        sid=sid,
        signature_id=sig_obj.signature_id,
        nonce=sig_obj.nonce,
        message_hex=message_bytes.hex(),
        status="CREATED",
    )


# ── Endpoint: POST /session/{sid}/verify ──────────────────────────────────────

@app.post(
    "/session/{sid}/verify",
    response_model=VerificationResponse,
    summary="Submit a stored session for verification",
    description=(
        "Executes the full verify_submitted_signature() pipeline (§15) against the "
        "session identified by sid. Uses the shared replay ledger — submitting the "
        "same sid twice will return REJECT: Replay on the second call."
    ),
    tags=["Session"],
)
def verify_session(sid: str) -> VerificationResponse:
    sig_obj = _sessions.get(sid)
    if sig_obj is None:
        raise HTTPException(status_code=404, detail=f"Session '{sid}' not found. Create it first via POST /session.")

    result = verify_submitted_signature(
        submitted_signature=sig_obj,
        message=sig_obj.message,
        replay_ledger=_shared_ledger,
        thresholds=_default_thresholds(),
    )
    _results[sid] = result
    return VerificationResponse(sid=sid, payload=_build_payload(result))


# ── Endpoint: GET /session/{sid}/explanation ──────────────────────────────────

@app.get(
    "/session/{sid}/explanation",
    response_model=ExplanationResponse,
    summary="Fetch the stored explanation record for a completed session",
    description=(
        "Returns the full Q-TAM ExplanationRecord (primary hypothesis, alternative "
        "explanation, evidence vector, thresholds, rule ID) for a session that has "
        "already been submitted to POST /session/{sid}/verify."
    ),
    tags=["Session"],
)
def get_explanation(sid: str) -> ExplanationResponse:
    result = _results.get(sid)
    if result is None:
        if sid not in _sessions:
            raise HTTPException(status_code=404, detail=f"Session '{sid}' not found.")
        raise HTTPException(
            status_code=404,
            detail=f"Session '{sid}' exists but has not been verified yet. Call POST /session/{sid}/verify first."
        )
    return ExplanationResponse(sid=sid, session_found=True, payload=_build_payload(result))


# ── Endpoint: POST /attack ─────────────────────────────────────────────────────

@app.post(
    "/attack",
    response_model=AttackScenarioResponse,
    summary="Run a named §14 attack scenario (self-contained)",
    description=(
        "Creates a fresh signing session and fresh replay ledger, applies the named "
        "§14 attack injector, and runs the full verify_submitted_signature() pipeline. "
        "DESIGN DECISION: each call is fully self-contained — the returned sid belongs "
        "to the attack's own session, not any session from POST /session. "
        "A fresh ledger is used so attack BLOCKED states cannot pollute the shared ledger "
        "used by honest sessions. See phase08_api_report.md §Design Decisions for details."
    ),
    tags=["Attack Simulation"],
)
def run_attack(request: AttackScenarioRequest) -> AttackScenarioResponse:
    # Instantiate the injector (schema validator already confirmed the name is valid)
    injector_cls = _INJECTOR_REGISTRY[request.attack_name]
    injector: BaseAttackInjector = injector_cls()

    # Fresh session for the attack
    message_bytes = b"Attack scenario test message."
    sig_obj, _ctx = create_signing_session(
        message=message_bytes,
        n_samples_per_basis=request.n_samples_per_basis,
    )

    # Fresh ledger: attack BLOCKED/REJECTED states must not poison the shared honest ledger
    attack_ledger = ReplayLedger()

    result = verify_submitted_signature(
        submitted_signature=sig_obj,
        message=message_bytes,
        attack_model=injector,
        replay_ledger=attack_ledger,
        thresholds=_default_thresholds(),
    )

    return AttackScenarioResponse(
        attack_name=request.attack_name,
        sid=sig_obj.sid,
        payload=_build_payload(result),
    )


# ── Endpoint: GET /benchmark ──────────────────────────────────────────────────

# Resolve path relative to project root regardless of working directory
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BENCHMARK_CSV = os.path.join(_PROJECT_ROOT, "benchmarks", "experiment_matrix_results.csv")


@app.get(
    "/benchmark",
    response_model=BenchmarkDataResponse,
    summary="Return Phase 07 experiment matrix data",
    description=(
        "Reads the pre-generated Phase 07 §17.1 experiment matrix CSV "
        "(benchmarks/experiment_matrix_results.csv) and returns all 18 rows as JSON "
        "with full §17.3 required disclosures per row: attack_model, noise_model, "
        "calibrated_baseline, sample_count, error_budget."
    ),
    tags=["Benchmarks"],
)
def get_benchmark_data() -> BenchmarkDataResponse:
    if not os.path.exists(_BENCHMARK_CSV):
        raise HTTPException(
            status_code=503,
            detail=(
                f"Benchmark CSV not found at {_BENCHMARK_CSV}. "
                "Run benchmarks/run_benchmarks.py to generate Phase 07 experiment matrix data."
            ),
        )

    rows: List[BenchmarkRowResponse] = []
    with open(_BENCHMARK_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            rows.append(BenchmarkRowResponse(
                scenario_id=int(raw["scenario_id"]),
                scenario_name=raw["scenario_name"],
                scenario_category=raw["scenario_category"],
                attack_model=raw["attack_model"],
                noise_model=raw["noise_model"],
                calibrated_baseline=raw["calibrated_baseline"],
                sample_count=raw["sample_count"],
                error_budget=raw["error_budget"],
                verdict=raw["verdict"],
                rule_id=raw["rule_id"],
                is_accepted=raw["is_accepted"].strip().lower() in ("true", "1", "yes"),
                replay_ledger_state=raw["replay_ledger_state"],
                empirical_e_X=float(raw["empirical_e_X"]),
                empirical_e_Y=float(raw["empirical_e_Y"]),
                empirical_e_Z=float(raw["empirical_e_Z"]),
                empirical_e_Bell=float(raw["empirical_e_Bell"]),
                latency_ms=float(raw["latency_ms"]),
                simulated_qubits=int(raw["simulated_qubits"]),
                control_overhead_bytes=int(raw["control_overhead_bytes"]),
                rule_label_agreed=raw["rule_label_agreed"].strip().lower() in ("true", "1", "yes"),
            ))

    return BenchmarkDataResponse(row_count=len(rows), rows=rows)
