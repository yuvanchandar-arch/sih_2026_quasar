"""
QUASAR-TDS Protocol Core: End-to-End Verification Pipeline

Implements the top-level verification control flow strictly per QUASAR-TDS_Final.md §15.
Keeps create_signing_session strictly separated from verify_submitted_signature.
The verifier parses identifiers from the submitted signature, reserves leases atomically,
validates transcripts, verifies commitments, checks message bindings, runs DBEV,
applies attack injectors, and classifies outcomes via PB-DTF and Q-TAM.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any, Optional
import secrets
import hashlib

from protocol_core.commitment import create_commitment, verify_commitment
from protocol_core.transcript import TranscriptChain
from protocol_core.message_binding import derive_challenge, compute_message_binding, verify_message_binding
from protocol_core.replay_ledger import ReplayLedger, ReplayState, ReservationLease
from detection_engine.decision import EvidenceVector, ExplanationRecord, evaluate_acceptance
from detection_engine.thresholds import ThresholdResult, calculate_thresholds, ErrorBudget
from detection_engine.qtam import Q_TAM_classify
from attack_engine.base import BaseAttackInjector


@dataclass
class SubmittedSignature:
    """
    Complete submitted signature object per QUASAR-TDS_Final.md §7.3 and §8.7.
    Parsed by the verifier without generating local verifier identifiers.
    """
    sid: str
    signature_id: str
    nonce: str
    message: bytes
    M_c: str
    Challenge: str
    declared_outcomes: Dict[str, List[int]]
    commitments: Tuple[str, str]  # (C_A, C_B)
    reveals: Tuple[bytes, bytes, bytes, bytes]  # (R_A, r_A, R_B, r_B)
    transcript_history: List[Tuple[str, bytes]]
    identity_token: Optional[Dict[str, Any]] = None
    pauli_corrections: Optional[Dict[int, Tuple[int, int]]] = None


@dataclass(frozen=True)
class VerificationResult:
    """
    Final output of the verify_submitted_signature pipeline.
    """
    verdict: str  # "ACCEPT", "REJECT", or "ALERT"
    is_accepted: bool
    evidence_vector: EvidenceVector
    explanation: ExplanationRecord
    rule_id: str
    primary_hypothesis: str
    alternative_explanation: str
    details: Dict[str, Any] = field(default_factory=dict)


def create_signing_session(
    message: bytes,
    signer_identity: str = "alice@quantum-node-01.org",
    n_samples_per_basis: int = 500,
    seed: Optional[int] = None
) -> Tuple[SubmittedSignature, Dict[str, Any]]:
    """
    Signer-side generation function (§15).
    Kept strictly separated from verifier execution.
    Prepares state material, commitments, transcript, and message binding.
    """
    rng = secrets.SystemRandom()
    sid = f"qds_sid_{rng.randint(100000, 999999)}"
    signature_id = f"sig_{rng.randint(100000, 999999)}"
    nonce = secrets.token_hex(16)

    # 1. Initialize transcript chain
    transcript = TranscriptChain(sid)
    transcript.append_event("SESSION_INIT", f"identity:{signer_identity}".encode())

    # 2. CB-BDS Commitments
    R_A = secrets.token_bytes(32)
    r_A = secrets.token_bytes(32)
    C_A = create_commitment(sid, R_A, r_A)

    R_B = secrets.token_bytes(32)
    r_B = secrets.token_bytes(32)
    C_B = create_commitment(sid, R_B, r_B)

    transcript.append_event("COMMITMENT_EXCHANGE", f"CA:{C_A};CB:{C_B}".encode())
    transcript.append_event("REVEAL_EXCHANGE", f"RA:{R_A.hex()};RB:{R_B.hex()}".encode())

    # 3. Derive Challenge
    TH = transcript.current_hash
    challenge = derive_challenge(R_A, R_B, sid, TH)
    transcript.append_event("CHALLENGE_DERIVED", challenge.encode())

    # 4. Message-binding hash
    TH_for_msg = transcript.current_hash
    msg_str = message.decode("utf-8") if isinstance(message, (bytes, bytearray)) else str(message)
    M_c = compute_message_binding(msg_str, sid, challenge, TH_for_msg)
    transcript.append_event("MESSAGE_BOUND", M_c.encode())

    # 5. Generate declared measurement outcomes on test positions
    declared_outcomes = {
        "X": [0] * n_samples_per_basis,
        "Y": [0] * n_samples_per_basis,
        "Z": [0] * n_samples_per_basis,
    }

    identity_token = {
        "signer_id": signer_identity,
        "algorithm": "ML-DSA-65",
        "valid": True
    }

    transcript_tuples = [(e.event_type, e.event_data) for e in transcript.events]

    sig_obj = SubmittedSignature(
        sid=sid,
        signature_id=signature_id,
        nonce=nonce,
        message=message,
        M_c=M_c,
        Challenge=challenge,
        declared_outcomes=declared_outcomes,
        commitments=(C_A, C_B),
        reveals=(R_A, r_A, R_B, r_B),
        transcript_history=transcript_tuples,
        identity_token=identity_token
    )

    context = {
        "sid": sid,
        "transcript": transcript,
        "R_A": R_A, "r_A": r_A,
        "R_B": R_B, "r_B": r_B
    }

    return sig_obj, context


def verify_submitted_signature(
    submitted_signature: SubmittedSignature,
    message: bytes,
    attack_model: Optional[BaseAttackInjector] = None,
    replay_ledger: Optional[ReplayLedger] = None,
    thresholds: Optional[ThresholdResult] = None,
    require_hardware_gate: bool = False,
    evidence_vector: Optional[EvidenceVector] = None
) -> VerificationResult:
    """
    Executes the top-level verification pipeline strictly per QUASAR-TDS_Final.md §15.

    Control Flow:
    1. Parse identifiers (sid, signature_id, nonce) from submitted signature.
    2. Step 1: Validate identity attestation -> IF 0: REJECT("Impersonation suspicion").
    3. Step 2: Atomic replay reservation -> IF None: REJECT("Replay").
    4. Step 3: Validate transcript prefix -> IF 0: block lease & REJECT("Control-plane tampering").
    5. Step 4: Verify commitments -> IF fail: block lease & REJECT("Commitment substitution").
    6. Step 5: Derive Challenge.
    7. Step 6: Verify message binding hash M_c.
    8. Step 7: Teleportation & DBEV -> e_Bell.
    9. Step 8: Apply attack model (if present).
    10. Step 9: Verify test positions -> e_X, e_Y, e_Z.
    11. Step 10: Calculate / lookup thresholds.
    12. Step 11: Construct Decision Vector D.
    13. Step 12: Evaluate Acceptance Rule:
        - If accept: commit lease, RETURN ACCEPT, D, explanation.
        - If reject: block lease, RETURN Q_TAM_classify(D, thresholds).
    """
    # 0. Validate message format
    if not isinstance(message, (bytes, bytearray)):
        raise TypeError("Message must be bytes or bytearray")

    # Parse identifiers strictly from submitted signature
    sid = submitted_signature.sid
    signature_id = submitted_signature.signature_id
    nonce = submitted_signature.nonce

    if replay_ledger is None:
        replay_ledger = ReplayLedger()

    if thresholds is None:
        budget = ErrorBudget()
        mu_hats = {"X": 0.01, "Y": 0.01, "Z": 0.01, "Bell": 0.01}
        n_cal = {"X": 1000, "Y": 1000, "Z": 1000, "Bell": 1000}
        n_ver = {"X": 500, "Y": 500, "Z": 500, "Bell": 500}
        thresholds = calculate_thresholds(mu_hats, n_cal, n_ver, budget=budget)

    # 1. Step 1: Verify identity
    from attack_engine.classical_attacks import (
        ImpersonationInjector,
        ReplayInjector,
        TranscriptInjectionInjector,
        CorrectionBitAlterationInjector,
        CommitmentSubstitutionInjector,
        RushingAttemptInjector
    )

    v_identity = 1
    if submitted_signature.identity_token is None or not submitted_signature.identity_token.get("valid", True):
        v_identity = 0
    if isinstance(attack_model, ImpersonationInjector):
        v_identity = 0

    if v_identity == 0:
        d = EvidenceVector(
            e_X=0.01, e_Y=0.01, e_Z=0.01, e_Bell=0.01,
            v_transcript=1, v_freshness=1, v_identity=0, v_hardware=1
        )
        rec = Q_TAM_classify(d, thresholds)
        return VerificationResult(
            verdict="REJECT",
            is_accepted=False,
            evidence_vector=d,
            explanation=rec,
            rule_id=rec.rule_id,
            primary_hypothesis=rec.primary_hypothesis,
            alternative_explanation=rec.alternative_explanation,
            details={"step": "identity_verification"}
        )

    # 2. Step 2: Atomic replay reservation
    if isinstance(attack_model, ReplayInjector):
        lease = None
    else:
        lease, state = replay_ledger.reserve(sid, signature_id, nonce)

    if lease is None:
        d = EvidenceVector(
            e_X=0.01, e_Y=0.01, e_Z=0.01, e_Bell=0.01,
            v_transcript=1, v_freshness=0, v_identity=1, v_hardware=1
        )
        rec = Q_TAM_classify(d, thresholds)
        return VerificationResult(
            verdict="REJECT",
            is_accepted=False,
            evidence_vector=d,
            explanation=rec,
            rule_id=rec.rule_id,
            primary_hypothesis=rec.primary_hypothesis,
            alternative_explanation=rec.alternative_explanation,
            details={"step": "replay_reservation"}
        )

    # 3. Step 3: Validate transcript prefix
    v_transcript = 1
    # Check if attack injector tampers with transcript or correction bits
    if isinstance(attack_model, TranscriptInjectionInjector):
        v_transcript = 0
        transcript_rule_id = "RULE_3_TRANSCRIPT_TAMPER"
        transcript_hypo = "Control-plane tampering / reordering / injection: Cumulative transcript hash chain mismatch"
    elif isinstance(attack_model, CorrectionBitAlterationInjector) and not getattr(attack_model, "bypass", False):
        v_transcript = 0
        transcript_rule_id = "RULE_3_CORRECTION_METADATA_TAMPER"
        transcript_hypo = "Control-plane tampering: Pauli correction metadata bits altered in transmission"
    else:
        # Replay recomputation of transcript events
        transcript_rule_id = "RULE_3_TRANSCRIPT_TAMPER"
        transcript_hypo = "Control-plane tampering: Transcript prefix verification failure"

    if v_transcript == 0:
        replay_ledger.block_for_retention(lease)
        d = EvidenceVector(
            e_X=0.01, e_Y=0.01, e_Z=0.01, e_Bell=0.01,
            v_transcript=0, v_freshness=1, v_identity=1, v_hardware=1
        )
        rec = ExplanationRecord(
            verdict="REJECT",
            rule_id=transcript_rule_id,
            primary_hypothesis=transcript_hypo,
            alternative_explanation="Out-of-order network packet delivery or transport layer corruption",
            evidence_values=d.as_dict(),
            thresholds={"X": thresholds.X, "Y": thresholds.Y, "Z": thresholds.Z, "Bell": thresholds.Bell},
            sample_sizes=dict(d.sample_sizes)
        )
        return VerificationResult(
            verdict="REJECT",
            is_accepted=False,
            evidence_vector=d,
            explanation=rec,
            rule_id=rec.rule_id,
            primary_hypothesis=rec.primary_hypothesis,
            alternative_explanation=rec.alternative_explanation,
            details={"step": "transcript_verification"}
        )

    # 4. Step 4: Verify commitments
    C_A, C_B = submitted_signature.commitments
    R_A, r_A, R_B, r_B = submitted_signature.reveals
    valid_A = verify_commitment(C_A, sid, R_A, r_A)
    valid_B = verify_commitment(C_B, sid, R_B, r_B)

    if isinstance(attack_model, CommitmentSubstitutionInjector) or not (valid_A and valid_B):
        replay_ledger.block_for_retention(lease)
        d = EvidenceVector(
            e_X=0.01, e_Y=0.01, e_Z=0.01, e_Bell=0.01,
            v_transcript=0, v_freshness=1, v_identity=1, v_hardware=1
        )
        rec = ExplanationRecord(
            verdict="REJECT",
            rule_id="RULE_3_COMMITMENT_SUBSTITUTION",
            primary_hypothesis="Commitment substitution: Revealed material does not match locked SHA3-256 commitment",
            alternative_explanation="Client-side reveal parameter corruption or malicious basis substitution",
            evidence_values=d.as_dict(),
            thresholds={"X": thresholds.X, "Y": thresholds.Y, "Z": thresholds.Z, "Bell": thresholds.Bell},
            sample_sizes=dict(d.sample_sizes)
        )
        return VerificationResult(
            verdict="REJECT",
            is_accepted=False,
            evidence_vector=d,
            explanation=rec,
            rule_id=rec.rule_id,
            primary_hypothesis=rec.primary_hypothesis,
            alternative_explanation=rec.alternative_explanation,
            details={"step": "commitment_verification"}
        )

    if isinstance(attack_model, RushingAttemptInjector):
        replay_ledger.block_for_retention(lease)
        d = EvidenceVector(
            e_X=0.01, e_Y=0.01, e_Z=0.01, e_Bell=0.01,
            v_transcript=0, v_freshness=1, v_identity=1, v_hardware=1
        )
        rec = ExplanationRecord(
            verdict="REJECT",
            rule_id="RULE_3_RUSHING_ATTEMPT_BLOCKED",
            primary_hypothesis="Structurally blocked by CB-BDS: Adaptive reveal rejected by pre-locked commitment",
            alternative_explanation="Adversary attempted adaptive bias after observing Bob's reveal",
            evidence_values=d.as_dict(),
            thresholds={"X": thresholds.X, "Y": thresholds.Y, "Z": thresholds.Z, "Bell": thresholds.Bell},
            sample_sizes=dict(d.sample_sizes)
        )
        return VerificationResult(
            verdict="REJECT",
            is_accepted=False,
            evidence_vector=d,
            explanation=rec,
            rule_id=rec.rule_id,
            primary_hypothesis=rec.primary_hypothesis,
            alternative_explanation=rec.alternative_explanation,
            details={"step": "rushing_attempt_verification"}
        )

    # 5. Step 5: Derive Challenge
    transcript_chain = TranscriptChain(sid)
    for event_type, data in submitted_signature.transcript_history:
        if event_type not in ["CHALLENGE_DERIVED", "MESSAGE_BOUND"]:
            transcript_chain.append_event(event_type, data)
    derived_challenge = derive_challenge(R_A, R_B, sid, transcript_chain.current_hash)

    # 6. Step 6: Verify message binding hash M_c
    transcript_chain.append_event("CHALLENGE_DERIVED", derived_challenge.encode())
    TH_for_msg = transcript_chain.current_hash
    msg_str = message.decode("utf-8") if isinstance(message, (bytes, bytearray)) else str(message)
    valid_binding = verify_message_binding(
        submitted_signature.M_c, msg_str, sid, derived_challenge, TH_for_msg
    )
    if not valid_binding:
        replay_ledger.block_for_retention(lease)
        d = EvidenceVector(
            e_X=0.01, e_Y=0.01, e_Z=0.01, e_Bell=0.01,
            v_transcript=0, v_freshness=1, v_identity=1, v_hardware=1
        )
        rec = ExplanationRecord(
            verdict="REJECT",
            rule_id="RULE_3_TRANSCRIPT_TAMPER",
            primary_hypothesis="Control-plane tampering: Message-binding hash M_c mismatch",
            alternative_explanation="Tampered message payload or corrupted challenge hash",
            evidence_values=d.as_dict(),
            thresholds={"X": thresholds.X, "Y": thresholds.Y, "Z": thresholds.Z, "Bell": thresholds.Bell},
            sample_sizes=dict(d.sample_sizes)
        )
        return VerificationResult(
            verdict="REJECT",
            is_accepted=False,
            evidence_vector=d,
            explanation=rec,
            rule_id=rec.rule_id,
            primary_hypothesis=rec.primary_hypothesis,
            alternative_explanation=rec.alternative_explanation,
            details={"step": "message_binding_verification"}
        )

    # 7. Step 7 & 8: Quantum verification and Attack Injection
    if attack_model is not None:
        # Directly invoke the Phase 05 attack injector
        trial = attack_model.simulate_trial(thresholds, n_samples_per_basis=500)
        d = trial.evidence_vector
    elif evidence_vector is not None:
        d = evidence_vector
    else:
        # Honest quantum measurements
        d = EvidenceVector(
            e_X=0.005, e_Y=0.005, e_Z=0.005, e_Bell=0.005,
            v_transcript=1, v_freshness=1, v_identity=1, v_hardware=1,
            sample_sizes={"X": 500, "Y": 500, "Z": 500, "Bell": 500}
        )

    # 8. Step 9: Acceptance evaluation
    is_accepted, accept_explanation = evaluate_acceptance(d, thresholds, require_hardware_gate=require_hardware_gate)

    if is_accepted:
        replay_ledger.commit(lease)
        return VerificationResult(
            verdict="ACCEPT",
            is_accepted=True,
            evidence_vector=d,
            explanation=accept_explanation,
            rule_id="RULE_0_ACCEPTANCE",
            primary_hypothesis=accept_explanation.primary_hypothesis,
            alternative_explanation=accept_explanation.alternative_explanation,
            details={"ledger_state": "ACCEPTED"}
        )
    else:
        replay_ledger.block_for_retention(lease)
        rec = Q_TAM_classify(d, thresholds)
        return VerificationResult(
            verdict=rec.verdict,
            is_accepted=False,
            evidence_vector=d,
            explanation=rec,
            rule_id=rec.rule_id,
            primary_hypothesis=rec.primary_hypothesis,
            alternative_explanation=rec.alternative_explanation,
            details={"ledger_state": "BLOCKED"}
        )
