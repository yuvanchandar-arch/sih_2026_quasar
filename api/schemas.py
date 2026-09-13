"""
QUASAR-TDS API Layer: Pydantic Request and Response Schemas (Phase 08)

Defines strict Pydantic v2 models for all FastAPI endpoint request bodies
and response payloads. No loose dicts are used in any endpoint signature.

All terminology strictly matches QUASAR-TDS_Final.md §6:
  - "attack-hypothesis attribution" not "attack detection accuracy"
  - "model-based hypothesis" not "prediction"
  - "rule-based" not "AI/ML"
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator

# Valid attack injector names — used for 422 validation on POST /attack
VALID_ATTACK_NAMES: List[str] = [
    "RandomStateForgery",
    "ZGuessInterceptResend",
    "XGuessInterceptResend",
    "YGuessInterceptResend",
    "EntangleAndMeasure",
    "BellPairReplacement",
    "CorrectionBitAlteration",
    "Replay",
    "Impersonation",
    "TranscriptInjection",
    "CommitmentSubstitution",
    "RushingAttempt",
]

# -- Request models -------------------------------------------------------------

class CreateSessionRequest(BaseModel):
    """Request body for POST /session."""
    message_text: str = Field(
        default="Hello, QUASAR-TDS!",
        description="Plaintext message to be signed and bound via M_c."
    )
    signer_identity: str = Field(
        default="alice@quantum-node-01.org",
        description="Identity token label for the signer."
    )
    n_samples_per_basis: int = Field(
        default=500, ge=10, le=5000,
        description="Number of quantum test positions per basis. Must be in [10, 5000]."
    )


class AttackScenarioRequest(BaseModel):
    """
    Request body for POST /attack.
    Runs a named attack scenario in a fully self-contained, isolated session
    with its own fresh replay ledger (does not mutate any existing session).
    """
    attack_name: str = Field(
        description=f"Name of the §14 attack injector. One of: {', '.join(VALID_ATTACK_NAMES)}"
    )
    n_samples_per_basis: int = Field(
        default=500, ge=10, le=5000,
        description="Number of quantum test positions per basis for the attack session."
    )

    @field_validator("attack_name")
    @classmethod
    def validate_attack_name(cls, v: str) -> str:
        if v not in VALID_ATTACK_NAMES:
            raise ValueError(
                f"Unknown attack name '{v}'. Valid names: {', '.join(VALID_ATTACK_NAMES)}"
            )
        return v


# -- Shared payload -------------------------------------------------------------

class VerificationPayload(BaseModel):
    """
    Complete verification outcome payload per QUASAR-TDS_Final.md §12.2.
    Embedded in VerificationResponse, ExplanationResponse, AttackScenarioResponse.
    """
    verdict: Literal["ACCEPT", "REJECT", "ALERT"]
    rule_id: str
    primary_hypothesis: str
    alternative_explanation: str
    evidence_values: Dict[str, Any]
    thresholds: Dict[str, float]
    sample_sizes: Dict[str, int]
    evidence_mode: str = "Deterministic rule-based hypothesis (Non-ML)"
    is_model_based_hypothesis: bool = True
    disclaimer: str = "Model-based hypothesis under configured statistical model, not forensic certainty."


# -- Response models ------------------------------------------------------------

class SessionCreatedResponse(BaseModel):
    """Response for POST /session."""
    sid: str
    signature_id: str
    nonce: str
    message_hex: str
    status: Literal["CREATED"] = "CREATED"


class VerificationResponse(BaseModel):
    """Response for POST /session/{sid}/verify."""
    sid: str
    payload: VerificationPayload


class ExplanationResponse(BaseModel):
    """Response for GET /session/{sid}/explanation."""
    sid: str
    session_found: bool
    payload: Optional[VerificationPayload] = None


class AttackScenarioResponse(BaseModel):
    """
    Response for POST /attack.
    The sid belongs to the attack session itself, not any prior POST /session call.
    This is a consciously-chosen self-contained demo model (see phase08_api_report.md).
    """
    attack_name: str
    sid: str
    payload: VerificationPayload


class BenchmarkRowResponse(BaseModel):
    """Single row from the Phase 07 §17.1 experiment matrix with full §17.3 disclosures."""
    scenario_id: int
    scenario_name: str
    scenario_category: str
    attack_model: str
    noise_model: str
    calibrated_baseline: str
    sample_count: str
    error_budget: str
    verdict: str
    rule_id: str
    is_accepted: bool
    replay_ledger_state: str
    empirical_e_X: float
    empirical_e_Y: float
    empirical_e_Z: float
    empirical_e_Bell: float
    latency_ms: float
    simulated_qubits: int
    control_overhead_bytes: int
    rule_label_agreed: bool


class BenchmarkDataResponse(BaseModel):
    """Response for GET /benchmark — all Phase 07 experiment matrix rows as JSON."""
    row_count: int
    rows: List[BenchmarkRowResponse]
