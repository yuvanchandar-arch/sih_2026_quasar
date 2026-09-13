"""
QUASAR-TDS Test Suite: Attack Simulation Engine (§14)

Verifies:
- All 12 isolated attack injectors individually tested:
    1. test_injector_random_state_forgery
    2. test_injector_z_guess_intercept_resend
    3. test_injector_x_guess_intercept_resend
    4. test_injector_y_guess_intercept_resend
    5. test_injector_entangle_and_measure_boundary_and_monotonicity
    6. test_injector_bell_pair_replacement
    7. test_injector_correction_bit_alteration_transcript_failure
    8. test_injector_correction_bit_alteration_quantum_mismatch
    9. test_injector_replay
    10. test_injector_impersonation
    11. test_injector_transcript_injection
    12. test_injector_commitment_substitution
    13. test_injector_rushing_attempt_rejection
- Monte Carlo batch runner executing n = 200 trials per attack (2400 total trials):
    14. test_monte_carlo_runner_batch_n200_all_12_attacks
"""

import math
import pytest
from typing import Dict

from detection_engine.thresholds import (
    ErrorBudget,
    ThresholdResult,
    calculate_thresholds,
)
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
    MonteCarloRunner,
    BatchAttackSummary,
)


@pytest.fixture
def standard_thresholds() -> ThresholdResult:
    """Standard honest thresholds for attack evaluation."""
    budget = ErrorBudget(
        eps_total=1e-3,
        eps_cal={"X": 1.25e-4, "Y": 1.25e-4, "Z": 1.25e-4, "Bell": 1.25e-4},
        eps_ver={"X": 1.25e-4, "Y": 1.25e-4, "Z": 1.25e-4, "Bell": 1.25e-4}
    )
    mu_hats = {"X": 0.01, "Y": 0.01, "Z": 0.01, "Bell": 0.01}
    n_cal = {"X": 1000, "Y": 1000, "Z": 1000, "Bell": 1000}
    n_ver = {"X": 500, "Y": 500, "Z": 500, "Bell": 500}
    return calculate_thresholds(mu_hats, n_cal, n_ver, budget=budget)


# -----------------------------------------------------------------------------
# 1. Quantum Attack Injectors (Attacks 1 to 6)
# -----------------------------------------------------------------------------

def test_injector_random_state_forgery(standard_thresholds):
    """Attack 1: Random-state forgery produces broad Pauli mismatch (~50% across X, Y, Z)."""
    injector = RandomStateForgeryInjector(seed=42)
    res = injector.simulate_trial(standard_thresholds, n_samples_per_basis=1000)

    d = res.evidence_vector
    assert d.e_X > standard_thresholds.X
    assert d.e_Y > standard_thresholds.Y
    assert d.e_Z > standard_thresholds.Z
    assert d.e_Bell <= standard_thresholds.Bell
    assert 0.40 <= d.e_X <= 0.60
    assert 0.40 <= d.e_Y <= 0.60
    assert 0.40 <= d.e_Z <= 0.60
    assert res.rule_id == "RULE_6_BROAD_PAULI"
    assert res.verdict == "ALERT"


def test_injector_z_guess_intercept_resend(standard_thresholds):
    """Attack 2: Z-guess intercept-resend preserves Z (~0%) while elevating X and Y (~50%)."""
    injector = ZGuessInterceptResendInjector(seed=42)
    res = injector.simulate_trial(standard_thresholds, n_samples_per_basis=1000)

    d = res.evidence_vector
    assert d.e_Z <= standard_thresholds.Z
    assert d.e_X > standard_thresholds.X
    assert d.e_Y > standard_thresholds.Y
    assert d.e_Bell <= standard_thresholds.Bell
    assert res.rule_id == "RULE_7_PARTIAL_BROAD_PAULI"
    assert res.verdict == "ALERT"


def test_injector_x_guess_intercept_resend(standard_thresholds):
    """Attack 3: X-guess intercept-resend preserves X (~0%) while elevating Y and Z (~50%)."""
    injector = XGuessInterceptResendInjector(seed=42)
    res = injector.simulate_trial(standard_thresholds, n_samples_per_basis=1000)

    d = res.evidence_vector
    assert d.e_X <= standard_thresholds.X
    assert d.e_Y > standard_thresholds.Y
    assert d.e_Z > standard_thresholds.Z
    assert d.e_Bell <= standard_thresholds.Bell
    assert res.rule_id == "RULE_7_PARTIAL_BROAD_PAULI"
    assert res.verdict == "ALERT"


def test_injector_y_guess_intercept_resend(standard_thresholds):
    """Attack 4: Y-guess intercept-resend preserves Y (~0%) while elevating X and Z (~50%)."""
    injector = YGuessInterceptResendInjector(seed=42)
    res = injector.simulate_trial(standard_thresholds, n_samples_per_basis=1000)

    d = res.evidence_vector
    assert d.e_Y <= standard_thresholds.Y
    assert d.e_X > standard_thresholds.X
    assert d.e_Z > standard_thresholds.Z
    assert d.e_Bell <= standard_thresholds.Bell
    assert res.rule_id == "RULE_7_PARTIAL_BROAD_PAULI"
    assert res.verdict == "ALERT"


def test_injector_entangle_and_measure_boundary_and_monotonicity(standard_thresholds):
    """
    Attack 5: Entangle-and-measure concrete boundary and monotonicity verification (User Directive 2).
    - At θ = 0.0 (zero coupling): error matches honest baseline (≤ thresholds).
    - At θ = π/4 (intermediate coupling): error increases moderately.
    - At θ = π (maximum coupling): error reaches maximum (~50% on complementary bases).
    """
    injector = EntangleAndMeasureInjector(seed=123)

    # 1. Boundary check: θ = 0.0
    res_zero = injector.simulate_trial(standard_thresholds, n_samples_per_basis=2000, coupling_angle=0.0)
    assert res_zero.evidence_vector.e_X <= standard_thresholds.X
    assert res_zero.evidence_vector.e_Y <= standard_thresholds.Y
    assert res_zero.evidence_vector.e_Z <= standard_thresholds.Z

    # 2. Intermediate check: θ = π/3
    res_mid = injector.simulate_trial(standard_thresholds, n_samples_per_basis=2000, coupling_angle=math.pi / 3.0)

    # 3. Maximum check: θ = π
    res_max = injector.simulate_trial(standard_thresholds, n_samples_per_basis=2000, coupling_angle=math.pi)

    # Strictly monotonic progression in complementary disturbance
    assert res_zero.evidence_vector.e_X < res_mid.evidence_vector.e_X < res_max.evidence_vector.e_X
    assert res_zero.evidence_vector.e_Y < res_mid.evidence_vector.e_Y < res_max.evidence_vector.e_Y
    assert res_max.rule_id == "RULE_7_PARTIAL_BROAD_PAULI"


def test_injector_bell_pair_replacement(standard_thresholds):
    """Attack 6: Bell-pair replacement elevates Bell decoy error while Pauli rates remain low."""
    injector = BellPairReplacementInjector(seed=42)
    res = injector.simulate_trial(standard_thresholds, n_samples_per_basis=1000)

    d = res.evidence_vector
    assert d.e_Bell > standard_thresholds.Bell
    assert d.e_X <= standard_thresholds.X
    assert d.e_Y <= standard_thresholds.Y
    assert d.e_Z <= standard_thresholds.Z
    assert res.rule_id == "RULE_5_CHANNEL_INTEGRITY"
    assert res.verdict == "ALERT"


# -----------------------------------------------------------------------------
# 2. Classical and Protocol Attack Injectors (Attacks 7 to 12)
# -----------------------------------------------------------------------------

def test_injector_correction_bit_alteration_transcript_failure(standard_thresholds):
    """
    Attack 7 (Primary Protocol Path, User Directive 1):
    Tampering with transcript-bound Pauli correction metadata triggers transcript failure.
    """
    injector = CorrectionBitAlterationInjector(seed=42)
    res = injector.simulate_trial(
        standard_thresholds,
        n_samples_per_basis=500,
        bypass_transcript_protection=False
    )

    d = res.evidence_vector
    assert d.v_transcript == 0
    assert res.verdict == "REJECT"
    assert res.rule_id == "RULE_3_TRANSCRIPT_TAMPER"
    assert "Control-plane tampering" in res.primary_hypothesis


def test_injector_correction_bit_alteration_quantum_mismatch(standard_thresholds):
    """
    Attack 7 (Secondary Quantum Consequence Path, User Directive 1):
    When transcript binding is bypassed, corrupted correction bits induce physical Pauli basis errors.
    """
    injector = CorrectionBitAlterationInjector(seed=42)
    res = injector.simulate_trial(
        standard_thresholds,
        n_samples_per_basis=500,
        bypass_transcript_protection=True
    )

    d = res.evidence_vector
    assert d.v_transcript == 1
    assert d.e_Y > standard_thresholds.Y
    assert d.e_Z > standard_thresholds.Z
    assert res.verdict == "ALERT"
    assert res.rule_id == "RULE_7_PARTIAL_BROAD_PAULI"


def test_injector_replay(standard_thresholds):
    """Attack 8: Replaying consumed signature causes freshness failure (v_freshness = 0)."""
    injector = ReplayInjector(seed=42)
    res = injector.simulate_trial(standard_thresholds, n_samples_per_basis=500)

    d = res.evidence_vector
    assert d.v_freshness == 0
    assert res.verdict == "REJECT"
    assert res.rule_id == "RULE_1_REPLAY"
    assert "Replay" in res.primary_hypothesis


def test_injector_impersonation(standard_thresholds):
    """Attack 9: Impersonation with invalid credentials causes identity failure (v_identity = 0)."""
    injector = ImpersonationInjector(seed=42)
    res = injector.simulate_trial(standard_thresholds, n_samples_per_basis=500)

    d = res.evidence_vector
    assert d.v_identity == 0
    assert res.verdict == "REJECT"
    assert res.rule_id == "RULE_2_IMPERSONATION"
    assert "Impersonation suspicion" in res.primary_hypothesis


def test_injector_transcript_injection(standard_thresholds):
    """Attack 10: Injected control messages cause transcript hash mismatch (v_transcript = 0)."""
    injector = TranscriptInjectionInjector(seed=42)
    res = injector.simulate_trial(standard_thresholds, n_samples_per_basis=500)

    d = res.evidence_vector
    assert d.v_transcript == 0
    assert res.verdict == "REJECT"
    assert res.rule_id == "RULE_3_TRANSCRIPT_TAMPER"
    assert "Control-plane tampering" in res.primary_hypothesis


def test_injector_commitment_substitution(standard_thresholds):
    """Attack 11: Substituted commitment fails SHA3-256 binding verification."""
    injector = CommitmentSubstitutionInjector(seed=42)
    res = injector.simulate_trial(standard_thresholds, n_samples_per_basis=500)

    assert res.details["commitment_verified"] is False
    assert res.verdict == "REJECT"
    assert res.is_consistent_with_expected is True


def test_injector_rushing_attempt_rejection(standard_thresholds):
    """
    Attack 12: Rushing attempt structurally blocked by CB-BDS (User Directive 3).
    Reuses protocol_core.commitment directly.
    """
    injector = RushingAttemptInjector(seed=42)
    res = injector.simulate_trial(standard_thresholds, n_samples_per_basis=500)

    assert res.details["rushing_succeeded"] is False
    assert res.details["structurally_blocked"] is True
    assert res.verdict == "REJECT"
    assert res.is_consistent_with_expected is True


# -----------------------------------------------------------------------------
# 3. Monte Carlo Batch Runner (n = 200 trials per attack, 2400 total)
# -----------------------------------------------------------------------------

def test_monte_carlo_runner_batch_n200_all_12_attacks(standard_thresholds):
    """
    Executes exactly n = 200 Monte Carlo trials across each of the 12 attack injectors
    (2400 total trials) and verifies empirical distribution consistency with §14.
    """
    runner = MonteCarloRunner(seed=2026)
    summaries = runner.run_all_12_attacks(standard_thresholds, n_trials_per_attack=200)

    assert len(summaries) == 12

    for summary in summaries:
        assert isinstance(summary, BatchAttackSummary)
        # Disclosed sample count assertion
        assert summary.n_trials == 200
        # Check consistency rate against §14 expected pattern
        assert summary.consistency_rate >= 0.95
        assert summary.is_consistent is True
        assert "not forensic certainty" in summary.disclaimer
