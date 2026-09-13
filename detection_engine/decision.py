"""
QUASAR-TDS Detection Engine: Decision Vector, Acceptance Rule, and Explanation Records

Implements the 8-component Decision Vector D and acceptance evaluation strictly per
QUASAR-TDS_Final.md §12.1.
Enforces that v_hardware is auxiliary evidence by default unless explicitly configured as a gate.
Implements the ExplanationRecord with mandatory non-ML disclosures per §12.2.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple
from detection_engine.thresholds import ThresholdResult


@dataclass
class EvidenceVector:
    """
    Decision Vector D = ( ê_X, ê_Y, ê_Z, ê_Bell, v_transcript, v_freshness, v_identity, v_hardware )
    along with sample sizes n_b.
    """
    e_X: float
    e_Y: float
    e_Z: float
    e_Bell: float
    v_transcript: int = 1
    v_freshness: int = 1
    v_identity: int = 1
    v_hardware: int = 1
    sample_sizes: Dict[str, int] = field(default_factory=lambda: {
        "X": 500,
        "Y": 500,
        "Z": 500,
        "Bell": 500,
    })

    def as_dict(self) -> Dict[str, Any]:
        return {
            "e_X": self.e_X,
            "e_Y": self.e_Y,
            "e_Z": self.e_Z,
            "e_Bell": self.e_Bell,
            "v_transcript": self.v_transcript,
            "v_freshness": self.v_freshness,
            "v_identity": self.v_identity,
            "v_hardware": self.v_hardware,
            "sample_sizes": dict(self.sample_sizes)
        }


@dataclass(frozen=True)
class ExplanationRecord:
    """
    Explanation record accompanying every acceptance, rejection, or attribution verdict (§12.2).
    Includes primary hypothesis, alternative explanation, evidence values, sample sizes,
    thresholds, rule identifier, and explicit non-ML rule-based hypothesis declaration.
    """
    verdict: str  # ACCEPT, REJECT, or ALERT
    rule_id: str
    primary_hypothesis: str
    alternative_explanation: str
    evidence_values: Dict[str, Any]
    thresholds: Dict[str, float]
    sample_sizes: Dict[str, int]
    evidence_mode: str = "Deterministic rule-based hypothesis (Non-ML)"
    is_model_based_hypothesis: bool = True
    disclaimer: str = "Model-based hypothesis under configured statistical model, not forensic certainty."

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict,
            "rule_id": self.rule_id,
            "primary_hypothesis": self.primary_hypothesis,
            "alternative_explanation": self.alternative_explanation,
            "evidence_values": self.evidence_values,
            "thresholds": self.thresholds,
            "sample_sizes": self.sample_sizes,
            "evidence_mode": self.evidence_mode,
            "is_model_based_hypothesis": self.is_model_based_hypothesis,
            "disclaimer": self.disclaimer
        }


def evaluate_acceptance(
    d: EvidenceVector,
    thresholds: ThresholdResult,
    require_hardware_gate: bool = False
) -> Tuple[bool, Optional[ExplanationRecord]]:
    """
    Evaluates the Acceptance Rule (§12.1):
    Accept ⇔ ê_X ≤ τ_X  AND  ê_Y ≤ τ_Y  AND  ê_Z ≤ τ_Z  AND  ê_Bell ≤ τ_Bell
             AND v_transcript = 1  AND v_freshness = 1  AND v_identity = 1
             (AND v_hardware = 1 if require_hardware_gate is True)

    v_hardware is auxiliary evidence unless deployment configuration explicitly requires it as a gate.
    The acceptance rule is evaluated first; Q-TAM runs only when acceptance fails.

    Returns:
        (is_accepted, explanation_record_if_accepted)
    """
    quantum_pass = (
        (d.e_X <= thresholds.X) and
        (d.e_Y <= thresholds.Y) and
        (d.e_Z <= thresholds.Z) and
        (d.e_Bell <= thresholds.Bell)
    )

    classical_pass = (
        (d.v_transcript == 1) and
        (d.v_freshness == 1) and
        (d.v_identity == 1)
    )

    if require_hardware_gate:
        hardware_pass = (d.v_hardware == 1)
    else:
        # Auxiliary evidence: does not gate acceptance
        hardware_pass = True

    is_accepted = quantum_pass and classical_pass and hardware_pass

    if is_accepted:
        explanation = ExplanationRecord(
            verdict="ACCEPT",
            rule_id="RULE_0_ACCEPTANCE",
            primary_hypothesis="Valid quantum digital signature: all quantum test error rates and classical integrity checks within acceptable bounds",
            alternative_explanation="Undetected low-rate tampering below statistical Hoeffding bound ε_total",
            evidence_values=d.as_dict(),
            thresholds={
                "X": thresholds.X,
                "Y": thresholds.Y,
                "Z": thresholds.Z,
                "Bell": thresholds.Bell
            },
            sample_sizes=dict(d.sample_sizes)
        )
        return True, explanation

    return False, None
