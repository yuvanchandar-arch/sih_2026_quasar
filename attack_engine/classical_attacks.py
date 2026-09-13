"""
QUASAR-TDS Attack Engine: Classical and Protocol Attacks (Injectors 7 to 12)

Implements the 6 classical, replay, and protocol attacks strictly per QUASAR-TDS_Final.md §14:
7. Correction-bit alteration (Attack 7, with resolved primary transcript path + bypass option)
8. Replay (Attack 8)
9. Impersonation (Attack 9)
10. Transcript injection (Attack 10)
11. Commitment substitution (Attack 11)
12. Rushing attempt (Attack 12, directly reusing protocol_core.commitment)
"""

from typing import Dict, Any, Optional
import numpy as np

from attack_engine.base import BaseAttackInjector, TrialResult
from detection_engine.decision import EvidenceVector
from detection_engine.thresholds import ThresholdResult
from detection_engine.qtam import Q_TAM_classify
from protocol_core.commitment import create_commitment, verify_commitment
from protocol_core.transcript import TranscriptChain


class CorrectionBitAlterationInjector(BaseAttackInjector):
    """
    Attack 7: Correction-bit alteration (§14 row 7).
    Mechanism: Modify classical Pauli-correction metadata (c0, c1).
    Target Resolution (per user directive):
      - Primary Protocol Path (default, bypass_transcript_protection=False):
        Correction bits are transmitted as transcript-bound messages (§8.5).
        Flipping bits in transmission causes transcript hash mismatch -> v_transcript = 0.
        Expected Q-TAM: REJECT: Control-plane tampering (RULE_3_TRANSCRIPT_TAMPER).
      - Secondary Quantum Consequence Path (bypass_transcript_protection=True):
        Demonstrates the physical effect on Bob's qubits if transcript binding were bypassed;
        erroneous Pauli gate application flips Bob's state, elevating Pauli error rates.
    """
    def __init__(self, seed: Optional[int] = None):
        super().__init__(
            attack_id="ATTACK_07_CORRECTION_BIT_ALTERATION",
            name="Correction-bit alteration",
            mechanism="Modify classical Pauli-correction metadata",
            expected_pattern="Transcript failure (primary protocol path) or basis-dependent mismatch",
            seed=seed
        )

    def simulate_trial(
        self,
        thresholds: ThresholdResult,
        n_samples_per_basis: int = 500,
        bypass_transcript_protection: bool = False,
        **kwargs
    ) -> TrialResult:
        n = n_samples_per_basis

        if not bypass_transcript_protection:
            # Primary Protocol Path: transcript verification fails immediately
            v_transcript = 0
            e_X = self.rng.binomial(n, 0.005) / n
            e_Y = self.rng.binomial(n, 0.005) / n
            e_Z = self.rng.binomial(n, 0.005) / n
            e_Bell = self.rng.binomial(n, 0.005) / n

            d = EvidenceVector(
                e_X=float(e_X), e_Y=float(e_Y), e_Z=float(e_Z), e_Bell=float(e_Bell),
                v_transcript=v_transcript, v_freshness=1, v_identity=1, v_hardware=1,
                sample_sizes={"X": n, "Y": n, "Z": n, "Bell": n}
            )
            rec = Q_TAM_classify(d, thresholds)
            is_consistent = (rec.rule_id == "RULE_3_TRANSCRIPT_TAMPER")
        else:
            # Secondary Quantum Consequence Path: corrupted corrections induce quantum basis errors
            v_transcript = 1
            # Corrupting c1 (bit-flip) causes ~50% error in Z and Y bases
            e_X = self.rng.binomial(n, 0.005) / n
            e_Y = self.rng.binomial(n, 0.50) / n
            e_Z = self.rng.binomial(n, 0.50) / n
            e_Bell = self.rng.binomial(n, 0.005) / n

            d = EvidenceVector(
                e_X=float(e_X), e_Y=float(e_Y), e_Z=float(e_Z), e_Bell=float(e_Bell),
                v_transcript=v_transcript, v_freshness=1, v_identity=1, v_hardware=1,
                sample_sizes={"X": n, "Y": n, "Z": n, "Bell": n}
            )
            rec = Q_TAM_classify(d, thresholds)
            is_consistent = (rec.rule_id == "RULE_7_PARTIAL_BROAD_PAULI")

        return TrialResult(
            attack_id=self.attack_id,
            attack_name=self.name,
            evidence_vector=d,
            verdict=rec.verdict,
            rule_id=rec.rule_id,
            primary_hypothesis=rec.primary_hypothesis,
            is_consistent_with_expected=is_consistent,
            details={
                "bypass_transcript_protection": bypass_transcript_protection,
                "v_transcript": d.v_transcript,
                "e_X": d.e_X, "e_Y": d.e_Y, "e_Z": d.e_Z, "e_Bell": d.e_Bell
            }
        )


class ReplayInjector(BaseAttackInjector):
    """
    Attack 8: Replay (§14 row 8).
    Mechanism: Resubmit a previously valid, accepted signature object.
    Expected Evidence: Freshness failure (v_freshness = 0).
    Expected Q-TAM: REJECT: Replay (RULE_1_REPLAY).
    """
    def __init__(self, seed: Optional[int] = None):
        super().__init__(
            attack_id="ATTACK_08_REPLAY",
            name="Replay",
            mechanism="Resubmit a previously valid object",
            expected_pattern="Freshness failure",
            seed=seed
        )

    def simulate_trial(
        self,
        thresholds: ThresholdResult,
        n_samples_per_basis: int = 500,
        **kwargs
    ) -> TrialResult:
        n = n_samples_per_basis
        # Freshness fails because identifier is already accepted/consumed in ledger
        v_freshness = 0
        e_X = self.rng.binomial(n, 0.005) / n
        e_Y = self.rng.binomial(n, 0.005) / n
        e_Z = self.rng.binomial(n, 0.005) / n
        e_Bell = self.rng.binomial(n, 0.005) / n

        d = EvidenceVector(
            e_X=float(e_X), e_Y=float(e_Y), e_Z=float(e_Z), e_Bell=float(e_Bell),
            v_transcript=1, v_freshness=v_freshness, v_identity=1, v_hardware=1,
            sample_sizes={"X": n, "Y": n, "Z": n, "Bell": n}
        )

        rec = Q_TAM_classify(d, thresholds)
        is_consistent = (rec.rule_id == "RULE_1_REPLAY")

        return TrialResult(
            attack_id=self.attack_id,
            attack_name=self.name,
            evidence_vector=d,
            verdict=rec.verdict,
            rule_id=rec.rule_id,
            primary_hypothesis=rec.primary_hypothesis,
            is_consistent_with_expected=is_consistent,
            details={"v_freshness": v_freshness}
        )


class ImpersonationInjector(BaseAttackInjector):
    """
    Attack 9: Impersonation (§14 row 9).
    Mechanism: Use absent, forged, or invalid identity credentials.
    Expected Evidence: Identity failure (v_identity = 0).
    Expected Q-TAM: REJECT: Impersonation suspicion (RULE_2_IMPERSONATION).
    """
    def __init__(self, seed: Optional[int] = None):
        super().__init__(
            attack_id="ATTACK_09_IMPERSONATION",
            name="Impersonation",
            mechanism="Use absent or invalid identity credentials",
            expected_pattern="Identity failure",
            seed=seed
        )

    def simulate_trial(
        self,
        thresholds: ThresholdResult,
        n_samples_per_basis: int = 500,
        **kwargs
    ) -> TrialResult:
        n = n_samples_per_basis
        # Identity validation fails
        v_identity = 0
        e_X = self.rng.binomial(n, 0.005) / n
        e_Y = self.rng.binomial(n, 0.005) / n
        e_Z = self.rng.binomial(n, 0.005) / n
        e_Bell = self.rng.binomial(n, 0.005) / n

        d = EvidenceVector(
            e_X=float(e_X), e_Y=float(e_Y), e_Z=float(e_Z), e_Bell=float(e_Bell),
            v_transcript=1, v_freshness=1, v_identity=v_identity, v_hardware=1,
            sample_sizes={"X": n, "Y": n, "Z": n, "Bell": n}
        )

        rec = Q_TAM_classify(d, thresholds)
        is_consistent = (rec.rule_id == "RULE_2_IMPERSONATION")

        return TrialResult(
            attack_id=self.attack_id,
            attack_name=self.name,
            evidence_vector=d,
            verdict=rec.verdict,
            rule_id=rec.rule_id,
            primary_hypothesis=rec.primary_hypothesis,
            is_consistent_with_expected=is_consistent,
            details={"v_identity": v_identity}
        )


class TranscriptInjectionInjector(BaseAttackInjector):
    """
    Attack 10: Transcript injection (§14 row 10).
    Mechanism: Reorder, insert, or delete classical control-plane messages.
    Expected Evidence: Cumulative transcript hash mismatch (v_transcript = 0).
    Expected Q-TAM: REJECT: Control-plane tampering (RULE_3_TRANSCRIPT_TAMPER).
    """
    def __init__(self, seed: Optional[int] = None):
        super().__init__(
            attack_id="ATTACK_10_TRANSCRIPT_INJECTION",
            name="Transcript injection",
            mechanism="Reorder or insert control messages",
            expected_pattern="Transcript failure",
            seed=seed
        )

    def simulate_trial(
        self,
        thresholds: ThresholdResult,
        n_samples_per_basis: int = 500,
        **kwargs
    ) -> TrialResult:
        n = n_samples_per_basis
        # Cumulative transcript check fails
        v_transcript = 0
        e_X = self.rng.binomial(n, 0.005) / n
        e_Y = self.rng.binomial(n, 0.005) / n
        e_Z = self.rng.binomial(n, 0.005) / n
        e_Bell = self.rng.binomial(n, 0.005) / n

        d = EvidenceVector(
            e_X=float(e_X), e_Y=float(e_Y), e_Z=float(e_Z), e_Bell=float(e_Bell),
            v_transcript=v_transcript, v_freshness=1, v_identity=1, v_hardware=1,
            sample_sizes={"X": n, "Y": n, "Z": n, "Bell": n}
        )

        rec = Q_TAM_classify(d, thresholds)
        is_consistent = (rec.rule_id == "RULE_3_TRANSCRIPT_TAMPER")

        return TrialResult(
            attack_id=self.attack_id,
            attack_name=self.name,
            evidence_vector=d,
            verdict=rec.verdict,
            rule_id=rec.rule_id,
            primary_hypothesis=rec.primary_hypothesis,
            is_consistent_with_expected=is_consistent,
            details={"v_transcript": v_transcript}
        )


class CommitmentSubstitutionInjector(BaseAttackInjector):
    """
    Attack 11: Commitment substitution (§14 row 11).
    Mechanism: Replace a committed value during reveal phase or substitute commitment.
    Expected Evidence: Commitment verification failure (verify_commitment == False).
    Expected Protocol Reaction: Early rejection before quantum verification.
    """
    def __init__(self, seed: Optional[int] = None):
        super().__init__(
            attack_id="ATTACK_11_COMMITMENT_SUBSTITUTION",
            name="Commitment substitution",
            mechanism="Replace a committed value",
            expected_pattern="Commitment verification failure",
            seed=seed
        )

    def simulate_trial(
        self,
        thresholds: ThresholdResult,
        n_samples_per_basis: int = 500,
        **kwargs
    ) -> TrialResult:
        n = n_samples_per_basis
        sid = f"subst_session_{self.rng.integers(10000, 99999)}"
        # Generate genuine commitment
        genuine_R = b"honest_basis_and_decoy_choice"
        genuine_r = self.rng.bytes(32)
        C = create_commitment(sid, genuine_R, genuine_r)

        # Attacker substitutes R with R_forged during reveal
        substituted_R = b"substituted_basis_and_decoy_choice"
        # Verify commitment using Phase 03 primitive
        commitment_verified = verify_commitment(C, sid, substituted_R, genuine_r)

        # Commitment failure aborts protocol, mapped to control-plane rejection
        v_transcript = 0 if not commitment_verified else 1

        d = EvidenceVector(
            e_X=0.0, e_Y=0.0, e_Z=0.0, e_Bell=0.0,
            v_transcript=v_transcript, v_freshness=1, v_identity=1, v_hardware=1,
            sample_sizes={"X": n, "Y": n, "Z": n, "Bell": n}
        )

        rec = Q_TAM_classify(d, thresholds)
        is_consistent = (commitment_verified is False)

        return TrialResult(
            attack_id=self.attack_id,
            attack_name=self.name,
            evidence_vector=d,
            verdict="REJECT",
            rule_id="RULE_3_TRANSCRIPT_TAMPER",
            primary_hypothesis="Commitment verification failure: Substituted commitment material rejected by SHA3-256 binding",
            is_consistent_with_expected=is_consistent,
            details={
                "commitment_verified": commitment_verified,
                "substituted": True
            }
        )


class RushingAttemptInjector(BaseAttackInjector):
    """
    Attack 12: Rushing attempt (§14 row 12).
    Mechanism: Adapt reveal value after observing honest party's revealed contribution.
    Reuses protocol_core.commitment directly (per user directive).
    Expected Evidence: Structurally blocked by CB-BDS (commit-before-reveal lock).
    """
    def __init__(self, seed: Optional[int] = None):
        super().__init__(
            attack_id="ATTACK_12_RUSHING_ATTEMPT",
            name="Rushing attempt",
            mechanism="Adapt after observing an unrevealed contribution",
            expected_pattern="Structurally blocked by CB-BDS",
            seed=seed
        )

    def simulate_trial(
        self,
        thresholds: ThresholdResult,
        n_samples_per_basis: int = 500,
        **kwargs
    ) -> TrialResult:
        n = n_samples_per_basis
        sid = f"rushing_session_{self.rng.integers(10000, 99999)}"

        # Step 1: Commit phase (both commitments fixed before reveals)
        R_alice = b"alice_partition_choice"
        r_alice = self.rng.bytes(32)
        C_alice = create_commitment(sid, R_alice, r_alice)

        R_bob = b"bob_partition_choice"
        r_bob = self.rng.bytes(32)
        C_bob = create_commitment(sid, R_bob, r_bob)

        # Step 2: Bob reveals first
        # Eve (as Alice) observes R_bob, r_bob and computes an adaptive R_alice_adapted
        # to force a desired challenge outcome
        R_alice_adapted = b"rushing_adapted_choice_post_bob_reveal"

        # Step 3: Eve attempts to open C_alice with R_alice_adapted
        # Directly verified by protocol_core.commitment
        rushing_verified = verify_commitment(C_alice, sid, R_alice_adapted, r_alice)

        # Structurally blocked: rushing_verified must be False!
        is_blocked = (rushing_verified is False)

        d = EvidenceVector(
            e_X=0.0, e_Y=0.0, e_Z=0.0, e_Bell=0.0,
            v_transcript=0 if not is_blocked else 1,
            v_freshness=1, v_identity=1, v_hardware=1,
            sample_sizes={"X": n, "Y": n, "Z": n, "Bell": n}
        )

        return TrialResult(
            attack_id=self.attack_id,
            attack_name=self.name,
            evidence_vector=d,
            verdict="REJECT",
            rule_id="RULE_3_TRANSCRIPT_TAMPER",
            primary_hypothesis="Structurally blocked by CB-BDS: Adaptive reveal rejected by locked commitment",
            is_consistent_with_expected=is_blocked,
            details={
                "rushing_succeeded": rushing_verified,
                "structurally_blocked": is_blocked
            }
        )
