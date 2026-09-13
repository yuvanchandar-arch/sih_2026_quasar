"""
QUASAR-TDS Attack Engine: Quantum Attacks (Injectors 1 to 6)

Implements the 6 quantum channel/state attacks strictly per QUASAR-TDS_Final.md §14:
1. Random-state forgery (Attack 1)
2. Z-guess intercept–resend (Attack 2)
3. X-guess intercept–resend (Attack 3)
4. Y-guess intercept–resend (Attack 4)
5. Entangle-and-measure (Attack 5, with concrete coupling-angle parameter)
6. Bell-pair replacement (Attack 6)
"""

import math
from typing import Dict, Any, Optional
import numpy as np

from attack_engine.base import BaseAttackInjector, TrialResult
from detection_engine.decision import EvidenceVector
from detection_engine.thresholds import ThresholdResult
from detection_engine.qtam import Q_TAM_classify


class RandomStateForgeryInjector(BaseAttackInjector):
    """
    Attack 1: Random-state forgery (§14 row 1).
    Mechanism: Replaces genuine state material on test positions with random states.
    Expected Evidence: Broad Pauli mismatch across X, Y, Z (ê_b ≈ 0.50); Bell normal or model-dependent.
    Expected Q-TAM: Broad Pauli-basis anomaly (RULE_6_BROAD_PAULI).
    """
    def __init__(self, seed: Optional[int] = None):
        super().__init__(
            attack_id="ATTACK_01_RANDOM_STATE_FORGERY",
            name="Random-state forgery",
            mechanism="Replace genuine states with random states",
            expected_pattern="Broad Pauli mismatch; model-dependent Bell effect",
            seed=seed
        )

    def simulate_trial(
        self,
        thresholds: ThresholdResult,
        n_samples_per_basis: int = 500,
        disturb_bell: bool = False,
        **kwargs
    ) -> TrialResult:
        n = n_samples_per_basis
        # Random states project onto any declared basis outcome with prob 0.5
        e_X = self.rng.binomial(n, 0.50) / n
        e_Y = self.rng.binomial(n, 0.50) / n
        e_Z = self.rng.binomial(n, 0.50) / n
        e_Bell = self.rng.binomial(n, 0.50) / n if disturb_bell else self.rng.binomial(n, 0.005) / n

        d = EvidenceVector(
            e_X=float(e_X), e_Y=float(e_Y), e_Z=float(e_Z), e_Bell=float(e_Bell),
            v_transcript=1, v_freshness=1, v_identity=1, v_hardware=1,
            sample_sizes={"X": n, "Y": n, "Z": n, "Bell": n}
        )

        rec = Q_TAM_classify(d, thresholds)
        is_consistent = (rec.rule_id == "RULE_6_BROAD_PAULI") or (
            disturb_bell and rec.rule_id == "RULE_4_BROADBAND_DEGRADATION"
        )

        return TrialResult(
            attack_id=self.attack_id,
            attack_name=self.name,
            evidence_vector=d,
            verdict=rec.verdict,
            rule_id=rec.rule_id,
            primary_hypothesis=rec.primary_hypothesis,
            is_consistent_with_expected=is_consistent,
            details={"e_X": e_X, "e_Y": e_Y, "e_Z": e_Z, "e_Bell": e_Bell}
        )


class ZGuessInterceptResendInjector(BaseAttackInjector):
    """
    Attack 2: Z-guess intercept–resend (§14 row 2).
    Mechanism: Measures test positions in Z and resends.
    Expected Evidence: Near-baseline Z (ê_Z ≈ 0); elevated complementary errors (ê_X ≈ 0.50, ê_Y ≈ 0.50).
    Expected Q-TAM: Partial broad Pauli anomaly (RULE_7_PARTIAL_BROAD_PAULI).
    """
    def __init__(self, seed: Optional[int] = None):
        super().__init__(
            attack_id="ATTACK_02_Z_GUESS_INTERCEPT_RESEND",
            name="Z-guess intercept–resend",
            mechanism="Measure and resend using a Z guess",
            expected_pattern="Near-baseline Z; elevated complementary-basis errors under the selected encoding",
            seed=seed
        )

    def simulate_trial(
        self,
        thresholds: ThresholdResult,
        n_samples_per_basis: int = 500,
        **kwargs
    ) -> TrialResult:
        n = n_samples_per_basis
        # Z basis guess matches Z test states (error ~0)
        e_Z = self.rng.binomial(n, 0.005) / n
        # Mutually unbiased complementary bases X and Y suffer 50% error
        e_X = self.rng.binomial(n, 0.50) / n
        e_Y = self.rng.binomial(n, 0.50) / n
        e_Bell = self.rng.binomial(n, 0.005) / n  # Decoy channel untouched

        d = EvidenceVector(
            e_X=float(e_X), e_Y=float(e_Y), e_Z=float(e_Z), e_Bell=float(e_Bell),
            v_transcript=1, v_freshness=1, v_identity=1, v_hardware=1,
            sample_sizes={"X": n, "Y": n, "Z": n, "Bell": n}
        )

        rec = Q_TAM_classify(d, thresholds)
        # 2 Pauli elevated (X, Y), Z normal, Bell normal -> Partial broad Pauli anomaly
        is_consistent = (rec.rule_id == "RULE_7_PARTIAL_BROAD_PAULI")

        return TrialResult(
            attack_id=self.attack_id,
            attack_name=self.name,
            evidence_vector=d,
            verdict=rec.verdict,
            rule_id=rec.rule_id,
            primary_hypothesis=rec.primary_hypothesis,
            is_consistent_with_expected=is_consistent,
            details={"e_X": e_X, "e_Y": e_Y, "e_Z": e_Z, "e_Bell": e_Bell}
        )


class XGuessInterceptResendInjector(BaseAttackInjector):
    """
    Attack 3: X-guess intercept–resend (§14 row 3).
    Mechanism: Measures test positions in X and resends.
    Expected Evidence: Near-baseline X (ê_X ≈ 0); elevated complementary errors (ê_Y ≈ 0.50, ê_Z ≈ 0.50).
    Expected Q-TAM: Partial broad Pauli anomaly (RULE_7_PARTIAL_BROAD_PAULI).
    """
    def __init__(self, seed: Optional[int] = None):
        super().__init__(
            attack_id="ATTACK_03_X_GUESS_INTERCEPT_RESEND",
            name="X-guess intercept–resend",
            mechanism="Measure and resend using an X guess",
            expected_pattern="Near-baseline X; elevated complementary-basis errors",
            seed=seed
        )

    def simulate_trial(
        self,
        thresholds: ThresholdResult,
        n_samples_per_basis: int = 500,
        **kwargs
    ) -> TrialResult:
        n = n_samples_per_basis
        # X basis guess matches X test states (error ~0)
        e_X = self.rng.binomial(n, 0.005) / n
        # Complementary bases Y and Z suffer 50% error
        e_Y = self.rng.binomial(n, 0.50) / n
        e_Z = self.rng.binomial(n, 0.50) / n
        e_Bell = self.rng.binomial(n, 0.005) / n  # Decoy channel untouched

        d = EvidenceVector(
            e_X=float(e_X), e_Y=float(e_Y), e_Z=float(e_Z), e_Bell=float(e_Bell),
            v_transcript=1, v_freshness=1, v_identity=1, v_hardware=1,
            sample_sizes={"X": n, "Y": n, "Z": n, "Bell": n}
        )

        rec = Q_TAM_classify(d, thresholds)
        # 2 Pauli elevated (Y, Z), X normal, Bell normal -> Partial broad Pauli anomaly
        is_consistent = (rec.rule_id == "RULE_7_PARTIAL_BROAD_PAULI")

        return TrialResult(
            attack_id=self.attack_id,
            attack_name=self.name,
            evidence_vector=d,
            verdict=rec.verdict,
            rule_id=rec.rule_id,
            primary_hypothesis=rec.primary_hypothesis,
            is_consistent_with_expected=is_consistent,
            details={"e_X": e_X, "e_Y": e_Y, "e_Z": e_Z, "e_Bell": e_Bell}
        )


class YGuessInterceptResendInjector(BaseAttackInjector):
    """
    Attack 4: Y-guess intercept–resend (§14 row 4).
    Mechanism: Measures test positions in Y and resends.
    Expected Evidence: Near-baseline Y (ê_Y ≈ 0); elevated complementary errors (ê_X ≈ 0.50, ê_Z ≈ 0.50).
    Expected Q-TAM: Partial broad Pauli anomaly (RULE_7_PARTIAL_BROAD_PAULI).
    """
    def __init__(self, seed: Optional[int] = None):
        super().__init__(
            attack_id="ATTACK_04_Y_GUESS_INTERCEPT_RESEND",
            name="Y-guess intercept–resend",
            mechanism="Measure and resend using a Y guess",
            expected_pattern="Near-baseline Y; elevated complementary-basis errors",
            seed=seed
        )

    def simulate_trial(
        self,
        thresholds: ThresholdResult,
        n_samples_per_basis: int = 500,
        **kwargs
    ) -> TrialResult:
        n = n_samples_per_basis
        # Y basis guess matches Y test states (error ~0)
        e_Y = self.rng.binomial(n, 0.005) / n
        # Complementary bases X and Z suffer 50% error
        e_X = self.rng.binomial(n, 0.50) / n
        e_Z = self.rng.binomial(n, 0.50) / n
        e_Bell = self.rng.binomial(n, 0.005) / n  # Decoy channel untouched

        d = EvidenceVector(
            e_X=float(e_X), e_Y=float(e_Y), e_Z=float(e_Z), e_Bell=float(e_Bell),
            v_transcript=1, v_freshness=1, v_identity=1, v_hardware=1,
            sample_sizes={"X": n, "Y": n, "Z": n, "Bell": n}
        )

        rec = Q_TAM_classify(d, thresholds)
        # 2 Pauli elevated (X, Z), Y normal, Bell normal -> Partial broad Pauli anomaly
        is_consistent = (rec.rule_id == "RULE_7_PARTIAL_BROAD_PAULI")

        return TrialResult(
            attack_id=self.attack_id,
            attack_name=self.name,
            evidence_vector=d,
            verdict=rec.verdict,
            rule_id=rec.rule_id,
            primary_hypothesis=rec.primary_hypothesis,
            is_consistent_with_expected=is_consistent,
            details={"e_X": e_X, "e_Y": e_Y, "e_Z": e_Z, "e_Bell": e_Bell}
        )


class EntangleAndMeasureInjector(BaseAttackInjector):
    """
    Attack 5: Entangle-and-measure (§14 row 5).
    Mechanism: Couple an ancilla qubit via controlled unitary with parameterized coupling_angle θ ∈ [0, π].
    Boundary & Monotonicity check (per user directive):
      - At θ = 0.0: zero entanglement (identity coupling) -> honest baseline rates (~0.0).
      - At θ = π: maximum entanglement -> complementary basis disturbance reaches 50% (sin²(θ/2)/2).
    """
    def __init__(self, seed: Optional[int] = None):
        super().__init__(
            attack_id="ATTACK_05_ENTANGLE_AND_MEASURE",
            name="Entangle-and-measure",
            mechanism="Couple an ancilla and measure later",
            expected_pattern="Model-dependent Pauli and Bell deviations",
            seed=seed
        )

    def simulate_trial(
        self,
        thresholds: ThresholdResult,
        n_samples_per_basis: int = 500,
        coupling_angle: float = math.pi,  # Full entangling coupling by default
        disturb_bell: bool = False,
        **kwargs
    ) -> TrialResult:
        n = n_samples_per_basis
        # Controlled rotation coupling induces error strictly proportional to sin²(θ/2)
        induced_p = 0.50 * (math.sin(coupling_angle / 2.0) ** 2)

        # Baseline error + induced disturbance
        p_X = min(0.50, 0.005 + induced_p)
        p_Y = min(0.50, 0.005 + induced_p)
        p_Z = 0.005  # Z is the control eigenbasis, remains invariant
        p_Bell = (0.005 + induced_p) if disturb_bell else 0.005

        e_X = self.rng.binomial(n, p_X) / n
        e_Y = self.rng.binomial(n, p_Y) / n
        e_Z = self.rng.binomial(n, p_Z) / n
        e_Bell = self.rng.binomial(n, p_Bell) / n

        d = EvidenceVector(
            e_X=float(e_X), e_Y=float(e_Y), e_Z=float(e_Z), e_Bell=float(e_Bell),
            v_transcript=1, v_freshness=1, v_identity=1, v_hardware=1,
            sample_sizes={"X": n, "Y": n, "Z": n, "Bell": n}
        )

        rec = Q_TAM_classify(d, thresholds)
        # When coupling is strong, X and Y are elevated -> Partial broad Pauli anomaly
        # When coupling is zero, it falls to Ambiguous or Accept
        if coupling_angle > math.pi / 4:
            is_consistent = (rec.rule_id in [
                "RULE_7_PARTIAL_BROAD_PAULI",
                "RULE_6_BROAD_PAULI",
                "RULE_9_AMBIGUOUS"
            ])
        else:
            is_consistent = (e_X <= thresholds.X and e_Y <= thresholds.Y)

        return TrialResult(
            attack_id=self.attack_id,
            attack_name=self.name,
            evidence_vector=d,
            verdict=rec.verdict,
            rule_id=rec.rule_id,
            primary_hypothesis=rec.primary_hypothesis,
            is_consistent_with_expected=is_consistent,
            details={
                "coupling_angle": coupling_angle,
                "induced_p": induced_p,
                "e_X": e_X, "e_Y": e_Y, "e_Z": e_Z, "e_Bell": e_Bell
            }
        )


class BellPairReplacementInjector(BaseAttackInjector):
    """
    Attack 6: Bell-pair replacement (§14 row 6).
    Mechanism: Replace or degrade the entangled channel on Bell decoys.
    Expected Evidence: Elevated Bell-decoy error (ê_Bell > τ_Bell); Pauli test rates normal.
    Expected Q-TAM: Channel-integrity anomaly (RULE_5_CHANNEL_INTEGRITY).
    """
    def __init__(self, seed: Optional[int] = None):
        super().__init__(
            attack_id="ATTACK_06_BELL_PAIR_REPLACEMENT",
            name="Bell-pair replacement",
            mechanism="Replace or degrade the entangled channel",
            expected_pattern="Elevated Bell-decoy error",
            seed=seed
        )

    def simulate_trial(
        self,
        thresholds: ThresholdResult,
        n_samples_per_basis: int = 500,
        replacement_violation_rate: float = 0.50,
        **kwargs
    ) -> TrialResult:
        n = n_samples_per_basis
        # Pauli tests uncorrupted (error ~0)
        e_X = self.rng.binomial(n, 0.005) / n
        e_Y = self.rng.binomial(n, 0.005) / n
        e_Z = self.rng.binomial(n, 0.005) / n
        # Entangled channel replaced -> elevated decoy violation rate
        e_Bell = self.rng.binomial(n, replacement_violation_rate) / n

        d = EvidenceVector(
            e_X=float(e_X), e_Y=float(e_Y), e_Z=float(e_Z), e_Bell=float(e_Bell),
            v_transcript=1, v_freshness=1, v_identity=1, v_hardware=1,
            sample_sizes={"X": n, "Y": n, "Z": n, "Bell": n}
        )

        rec = Q_TAM_classify(d, thresholds)
        # Bell elevated, all 3 Pauli normal -> Channel-integrity anomaly
        is_consistent = (rec.rule_id == "RULE_5_CHANNEL_INTEGRITY")

        return TrialResult(
            attack_id=self.attack_id,
            attack_name=self.name,
            evidence_vector=d,
            verdict=rec.verdict,
            rule_id=rec.rule_id,
            primary_hypothesis=rec.primary_hypothesis,
            is_consistent_with_expected=is_consistent,
            details={"e_X": e_X, "e_Y": e_Y, "e_Z": e_Z, "e_Bell": e_Bell}
        )
