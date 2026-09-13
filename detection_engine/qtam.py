"""
QUASAR-TDS Detection Engine: Quantum Threat Attribution Matrix (Q-TAM)

Implements the deterministic rule engine strictly per QUASAR-TDS_Final.md §12.2 and §15.
Adheres strictly to the required rule ordering:
    Rule 4 (All Pauli + Bell elevated -> Broadband degradation) MUST be evaluated
    BEFORE Rule 6/7/8 (partial Pauli anomalies) to prevent misclassification.
Produces model-based hypotheses with mandatory non-ML disclosures and alternative explanations.
"""

from typing import Dict, Any, Tuple
from detection_engine.decision import EvidenceVector, ExplanationRecord
from detection_engine.thresholds import ThresholdResult


def count_exceeding_pauli_bases(d: EvidenceVector, thresholds: ThresholdResult) -> int:
    """Counts how many Pauli basis error rates exceed their respective thresholds."""
    count = 0
    if d.e_X > thresholds.X:
        count += 1
    if d.e_Y > thresholds.Y:
        count += 1
    if d.e_Z > thresholds.Z:
        count += 1
    return count


def Q_TAM_classify(
    d: EvidenceVector,
    thresholds: ThresholdResult
) -> ExplanationRecord:
    """
    Evaluates Q-TAM deterministic rule table in strict order (§12.2, §15):

    1. Freshness failure                                 → REJECT: Replay
    2. Identity failure                                  → REJECT: Impersonation suspicion
    3. Transcript failure                                → REJECT: Control-plane tampering / reordering / injection
    4. All Pauli tests AND Bell test elevated             → ALERT: Broadband degradation; re-run DBEV
    5. Bell elevated, all Pauli tests within threshold    → ALERT: Channel-integrity anomaly
    6. All three Pauli tests elevated, Bell normal        → ALERT: Broad Pauli-basis anomaly
    7. Two Pauli tests elevated, Bell normal              → ALERT: Partial broad Pauli anomaly
    8. Exactly one Pauli test elevated                    → ALERT: Basis-selective signature anomaly
    9. Otherwise                                          → ALERT: Ambiguous anomaly

    Returns:
        ExplanationRecord containing verdict, rule_id, primary_hypothesis,
        alternative_explanation, evidence values, sample sizes, and non-ML disclosure.
    """
    threshold_dict = {
        "X": thresholds.X,
        "Y": thresholds.Y,
        "Z": thresholds.Z,
        "Bell": thresholds.Bell
    }
    evidence_dict = d.as_dict()
    sample_sizes_dict = dict(d.sample_sizes)

    # 1. Freshness failure
    if d.v_freshness == 0:
        return ExplanationRecord(
            verdict="REJECT",
            rule_id="RULE_1_REPLAY",
            primary_hypothesis="Replay: Resubmission or expired/consumed identifier detected via freshness failure",
            alternative_explanation="Network delay or benign re-transmission of uncommitted signature",
            evidence_values=evidence_dict,
            thresholds=threshold_dict,
            sample_sizes=sample_sizes_dict
        )

    # 2. Identity failure
    if d.v_identity == 0:
        return ExplanationRecord(
            verdict="REJECT",
            rule_id="RULE_2_IMPERSONATION",
            primary_hypothesis="Impersonation suspicion: Classical identity credential or attestation failure; unauthorized signer",
            alternative_explanation="Credential expiration, key rollover mismatch, or client-side configuration error",
            evidence_values=evidence_dict,
            thresholds=threshold_dict,
            sample_sizes=sample_sizes_dict
        )

    # 3. Transcript failure
    if d.v_transcript == 0:
        return ExplanationRecord(
            verdict="REJECT",
            rule_id="RULE_3_TRANSCRIPT_TAMPER",
            primary_hypothesis="Control-plane tampering / reordering / injection: Cumulative transcript hash chain mismatch",
            alternative_explanation="Out-of-order network packet delivery or classical transport layer corruption",
            evidence_values=evidence_dict,
            thresholds=threshold_dict,
            sample_sizes=sample_sizes_dict
        )

    # Quantum evidence evaluations
    all_pauli = (d.e_X > thresholds.X) and (d.e_Y > thresholds.Y) and (d.e_Z > thresholds.Z)
    bell_elevated = d.e_Bell > thresholds.Bell
    pauli_count = count_exceeding_pauli_bases(d, thresholds)

    # 4. All Pauli tests AND Bell test elevated -> Broadband degradation
    # CRITICAL: Must be evaluated before Rule 6/7/8 to prevent ordering bugs
    if all_pauli and bell_elevated:
        return ExplanationRecord(
            verdict="ALERT",
            rule_id="RULE_4_BROADBAND_DEGRADATION",
            primary_hypothesis="Broadband degradation: Simultaneous elevation across all Pauli bases and Bell decoys; re-run DBEV",
            alternative_explanation="Common environmental noise, severe channel attenuation, or simulator instability",
            evidence_values=evidence_dict,
            thresholds=threshold_dict,
            sample_sizes=sample_sizes_dict
        )

    # 5. Bell elevated, all Pauli tests within threshold -> Channel-integrity anomaly
    if bell_elevated and pauli_count == 0:
        return ExplanationRecord(
            verdict="ALERT",
            rule_id="RULE_5_CHANNEL_INTEGRITY",
            primary_hypothesis="Channel-integrity anomaly: Bell-decoy correlation violation rate elevated while all Pauli basis test rates remain normal",
            alternative_explanation="Elevated quantum channel noise, entanglement source degradation, or hardware noise",
            evidence_values=evidence_dict,
            thresholds=threshold_dict,
            sample_sizes=sample_sizes_dict
        )

    # 6. All three Pauli tests elevated, Bell normal -> Broad Pauli-basis anomaly
    if all_pauli and not bell_elevated:
        return ExplanationRecord(
            verdict="ALERT",
            rule_id="RULE_6_BROAD_PAULI",
            primary_hypothesis="Broad Pauli-basis anomaly: All three Pauli basis test error rates elevated while Bell decoys remain normal",
            alternative_explanation="Correlated calibration drift, random-state forgery attempt, or isotropic state distortion",
            evidence_values=evidence_dict,
            thresholds=threshold_dict,
            sample_sizes=sample_sizes_dict
        )

    # 7. Two Pauli tests elevated, Bell normal -> Partial broad Pauli anomaly
    if pauli_count == 2 and not bell_elevated:
        return ExplanationRecord(
            verdict="ALERT",
            rule_id="RULE_7_PARTIAL_BROAD_PAULI",
            primary_hypothesis="Partial broad Pauli anomaly: Two Pauli basis test error rates elevated while Bell decoys remain normal",
            alternative_explanation="Basis-correlated noise, anisotropic decoherence, or entangle-and-measure attack attempt",
            evidence_values=evidence_dict,
            thresholds=threshold_dict,
            sample_sizes=sample_sizes_dict
        )

    # 8. Exactly one Pauli test elevated -> Basis-selective signature anomaly
    if pauli_count == 1:
        return ExplanationRecord(
            verdict="ALERT",
            rule_id="RULE_8_BASIS_SELECTIVE",
            primary_hypothesis="Basis-selective signature anomaly: Exactly one Pauli basis test error rate elevated",
            alternative_explanation="Consistent with, but not proof of, intercept-resend attack with a specific basis guess, or basis-aligned noise",
            evidence_values=evidence_dict,
            thresholds=threshold_dict,
            sample_sizes=sample_sizes_dict
        )

    # 9. Otherwise -> Ambiguous anomaly
    return ExplanationRecord(
        verdict="ALERT",
        rule_id="RULE_9_AMBIGUOUS",
        primary_hypothesis="Ambiguous anomaly: Unclassified error pattern falling outside structured diagnostic rules",
        alternative_explanation="Manual audit required; mixed attack vectors or non-standard channel disturbance",
        evidence_values=evidence_dict,
        thresholds=threshold_dict,
        sample_sizes=sample_sizes_dict
    )
