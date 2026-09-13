"""
QUASAR-TDS Test Suite: Detection Engine (PB-DTF + Q-TAM)

Verifies:
- Closed-form Hoeffding threshold computation (§11.1)
- Error budget disclosure and summation constraints (§11.1)
- Exactly 10 named Q-TAM tests (§12.2, §15):
    1. test_qtam_replay
    2. test_qtam_impersonation
    3. test_qtam_transcript_tamper
    4. test_qtam_broadband_degradation
    5. test_qtam_channel_integrity_anomaly
    6. test_qtam_broad_pauli_anomaly
    7. test_qtam_partial_broad_pauli_anomaly
    8. test_qtam_basis_selective_anomaly
    9. test_qtam_ambiguous_anomaly
    10. test_qtam_ordering_edge_case
- v_hardware auxiliary-only behavior (§12.1)
- Acceptance rule evaluation (§12.1)
- DBEV basis-dependent correlation rules (§9)
- Forgery bound calculation (§11.2)
- Explanation record non-ML disclaimers (§12.2)
- Calibration engine execution (§11.1)
"""

import math
import pytest
from typing import Dict

from detection_engine.thresholds import (
    ErrorBudget,
    BasisThreshold,
    ThresholdResult,
    compute_hoeffding_slack,
    calculate_basis_threshold,
    calculate_thresholds,
    compute_forgery_bound,
    compute_union_bound_forgery_probability,
)
from detection_engine.dbev import (
    compute_dbev_basis_counts,
    evaluate_dbev_for_basis,
    run_dbev,
)
from detection_engine.decision import (
    EvidenceVector,
    ExplanationRecord,
    evaluate_acceptance,
)
from detection_engine.qtam import (
    Q_TAM_classify,
    count_exceeding_pauli_bases,
)
from detection_engine.calibration import (
    CalibrationEngine,
    CalibrationReport,
)


@pytest.fixture
def mock_thresholds() -> ThresholdResult:
    """Fixed, standard thresholds for synthetic test evaluation."""
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
# 1. Statistical Thresholds & Error Budget Tests (§11.1)
# -----------------------------------------------------------------------------

def test_threshold_computation_matches_formula():
    """
    Verifies that calculate_basis_threshold matches an exact hand-derived
    one-sided Hoeffding calculation per QUASAR-TDS_Final.md §11.1.
    
    Given:
        μ̂ = 0.02
        ε_cal = 1e-4, n_cal = 1000
        ε_ver = 1e-4, n_ver = 500
        
    Calculations:
        ln(1 / 1e-4) = ln(10000) = 9.210340371976184
        δ_cal = √( 9.210340371976184 / (2 * 1000) ) = 0.06786140424415068
        δ_ver = √( 9.210340371976184 / (2 * 500) )  = 0.09597051824376106
        τ = 0.02 + 0.06786140424415068 + 0.09597051824376106 = 0.18383192248791174
    """
    mu_hat = 0.02
    eps_cal = 1e-4
    n_cal = 1000
    eps_ver = 1e-4
    n_ver = 500

    expected_delta_cal = math.sqrt(math.log(1.0 / eps_cal) / (2.0 * n_cal))
    expected_delta_ver = math.sqrt(math.log(1.0 / eps_ver) / (2.0 * n_ver))
    expected_tau = mu_hat + expected_delta_cal + expected_delta_ver

    bt = calculate_basis_threshold("X", mu_hat, n_cal, n_ver, eps_cal, eps_ver)

    assert math.isclose(bt.delta_cal, expected_delta_cal, rel_tol=1e-12)
    assert math.isclose(bt.delta_ver, expected_delta_ver, rel_tol=1e-12)
    assert math.isclose(bt.tau, expected_tau, rel_tol=1e-12)
    assert math.isclose(bt.tau, 0.18383192248791174, rel_tol=1e-9)
    assert bt.bound_type == "one-sided upper tail bound (Hoeffding)"


def test_error_budget_disclosed_and_summed_correctly():
    """
    Verifies that the error budget satisfies:
    Σ_{b∈{X,Y,Z,Bell}} ( ε_b^cal + ε_b^ver ) ≤ ε_total
    and rejects invalid allocations.
    """
    # Valid allocation
    valid_budget = ErrorBudget(
        eps_total=1e-3,
        eps_cal={"X": 1e-4, "Y": 1e-4, "Z": 1e-4, "Bell": 1e-4},
        eps_ver={"X": 1e-4, "Y": 1e-4, "Z": 1e-4, "Bell": 1e-4}
    )
    assert valid_budget.validate() is True
    assert valid_budget.total_allocated == 8e-4
    assert valid_budget.total_allocated <= valid_budget.eps_total

    # Invalid allocation exceeding eps_total
    invalid_budget = ErrorBudget(
        eps_total=1e-3,
        eps_cal={"X": 2e-4, "Y": 2e-4, "Z": 2e-4, "Bell": 2e-4},
        eps_ver={"X": 2e-4, "Y": 2e-4, "Z": 2e-4, "Bell": 2e-4}
    )
    with pytest.raises(ValueError, match="Error budget violated"):
        invalid_budget.validate()


# -----------------------------------------------------------------------------
# 2. Q-TAM 10 Distinct Named Tests (§12.2, §15)
# -----------------------------------------------------------------------------

def test_qtam_replay(mock_thresholds):
    """Q-TAM Rule 1: Freshness failure -> REJECT: Replay."""
    # Synthetic vector: freshness=0, everything else normal
    d = EvidenceVector(
        e_X=0.02, e_Y=0.02, e_Z=0.02, e_Bell=0.02,
        v_transcript=1, v_freshness=0, v_identity=1, v_hardware=1
    )
    record = Q_TAM_classify(d, mock_thresholds)
    assert record.verdict == "REJECT"
    assert record.rule_id == "RULE_1_REPLAY"
    assert "Replay" in record.primary_hypothesis


def test_qtam_impersonation(mock_thresholds):
    """Q-TAM Rule 2: Identity failure -> REJECT: Impersonation suspicion."""
    # Synthetic vector: identity=0, freshness=1, transcript=1, quantum normal
    d = EvidenceVector(
        e_X=0.02, e_Y=0.02, e_Z=0.02, e_Bell=0.02,
        v_transcript=1, v_freshness=1, v_identity=0, v_hardware=1
    )
    record = Q_TAM_classify(d, mock_thresholds)
    assert record.verdict == "REJECT"
    assert record.rule_id == "RULE_2_IMPERSONATION"
    assert "Impersonation suspicion" in record.primary_hypothesis


def test_qtam_transcript_tamper(mock_thresholds):
    """Q-TAM Rule 3: Transcript failure -> REJECT: Control-plane tampering."""
    # Synthetic vector: transcript=0, freshness=1, identity=1, quantum normal
    d = EvidenceVector(
        e_X=0.02, e_Y=0.02, e_Z=0.02, e_Bell=0.02,
        v_transcript=0, v_freshness=1, v_identity=1, v_hardware=1
    )
    record = Q_TAM_classify(d, mock_thresholds)
    assert record.verdict == "REJECT"
    assert record.rule_id == "RULE_3_TRANSCRIPT_TAMPER"
    assert "Control-plane tampering" in record.primary_hypothesis


def test_qtam_broadband_degradation(mock_thresholds):
    """Q-TAM Rule 4: All Pauli tests AND Bell test elevated -> ALERT: Broadband degradation."""
    # Synthetic vector: all 3 Pauli elevated AND Bell elevated, classicals pass
    d = EvidenceVector(
        e_X=mock_thresholds.X + 0.1,
        e_Y=mock_thresholds.Y + 0.1,
        e_Z=mock_thresholds.Z + 0.1,
        e_Bell=mock_thresholds.Bell + 0.1,
        v_transcript=1, v_freshness=1, v_identity=1, v_hardware=1
    )
    record = Q_TAM_classify(d, mock_thresholds)
    assert record.verdict == "ALERT"
    assert record.rule_id == "RULE_4_BROADBAND_DEGRADATION"
    assert "Broadband degradation" in record.primary_hypothesis


def test_qtam_channel_integrity_anomaly(mock_thresholds):
    """Q-TAM Rule 5: Bell elevated, all Pauli tests normal -> ALERT: Channel-integrity anomaly."""
    # Synthetic vector: Bell elevated, all 3 Pauli well below threshold
    d = EvidenceVector(
        e_X=0.01, e_Y=0.01, e_Z=0.01,
        e_Bell=mock_thresholds.Bell + 0.15,
        v_transcript=1, v_freshness=1, v_identity=1, v_hardware=1
    )
    record = Q_TAM_classify(d, mock_thresholds)
    assert record.verdict == "ALERT"
    assert record.rule_id == "RULE_5_CHANNEL_INTEGRITY"
    assert "Channel-integrity anomaly" in record.primary_hypothesis


def test_qtam_broad_pauli_anomaly(mock_thresholds):
    """Q-TAM Rule 6: All three Pauli tests elevated, Bell normal -> ALERT: Broad Pauli-basis anomaly."""
    # Synthetic vector: all 3 Pauli elevated, Bell below threshold
    d = EvidenceVector(
        e_X=mock_thresholds.X + 0.1,
        e_Y=mock_thresholds.Y + 0.1,
        e_Z=mock_thresholds.Z + 0.1,
        e_Bell=0.01,
        v_transcript=1, v_freshness=1, v_identity=1, v_hardware=1
    )
    record = Q_TAM_classify(d, mock_thresholds)
    assert record.verdict == "ALERT"
    assert record.rule_id == "RULE_6_BROAD_PAULI"
    assert "Broad Pauli-basis anomaly" in record.primary_hypothesis


def test_qtam_partial_broad_pauli_anomaly(mock_thresholds):
    """Q-TAM Rule 7: Two Pauli tests elevated, Bell normal -> ALERT: Partial broad Pauli anomaly."""
    # Synthetic vector: X and Y elevated, Z normal, Bell normal
    d = EvidenceVector(
        e_X=mock_thresholds.X + 0.1,
        e_Y=mock_thresholds.Y + 0.1,
        e_Z=0.01,
        e_Bell=0.01,
        v_transcript=1, v_freshness=1, v_identity=1, v_hardware=1
    )
    record = Q_TAM_classify(d, mock_thresholds)
    assert record.verdict == "ALERT"
    assert record.rule_id == "RULE_7_PARTIAL_BROAD_PAULI"
    assert "Partial broad Pauli anomaly" in record.primary_hypothesis


def test_qtam_basis_selective_anomaly(mock_thresholds):
    """Q-TAM Rule 8: Exactly one Pauli test elevated -> ALERT: Basis-selective signature anomaly."""
    # Synthetic vector: X elevated, Y normal, Z normal, Bell normal
    d = EvidenceVector(
        e_X=mock_thresholds.X + 0.12,
        e_Y=0.01,
        e_Z=0.01,
        e_Bell=0.01,
        v_transcript=1, v_freshness=1, v_identity=1, v_hardware=1
    )
    record = Q_TAM_classify(d, mock_thresholds)
    assert record.verdict == "ALERT"
    assert record.rule_id == "RULE_8_BASIS_SELECTIVE"
    assert "Basis-selective signature anomaly" in record.primary_hypothesis


def test_qtam_ambiguous_anomaly(mock_thresholds):
    """
    Q-TAM Rule 9: Otherwise -> ALERT: Ambiguous anomaly.
    Constructed using the exact reachable fall-through state:
    two Pauli elevated AND Bell elevated (pauli_count=2, bell=elevated).
    This doesn't match rule 4 (needs 3 Pauli), rule 5 (needs 0 Pauli),
    rule 6 (needs 3 Pauli), or rule 7 (needs Bell normal).
    """
    d = EvidenceVector(
        e_X=mock_thresholds.X + 0.1,
        e_Y=mock_thresholds.Y + 0.1,
        e_Z=0.01,
        e_Bell=mock_thresholds.Bell + 0.1,
        v_transcript=1, v_freshness=1, v_identity=1, v_hardware=1
    )
    record = Q_TAM_classify(d, mock_thresholds)
    assert record.verdict == "ALERT"
    assert record.rule_id == "RULE_9_AMBIGUOUS"
    assert "Ambiguous anomaly" in record.primary_hypothesis


def test_qtam_ordering_edge_case(mock_thresholds):
    """
    CRITICAL ORDERING EDGE-CASE TEST (§12.2, master prompt requirement):
    Construct a vector where all three Pauli bases AND Bell are elevated simultaneously.
    Assert the result is 'Broadband degradation' (Rule 4), NOT 'Broad Pauli-basis anomaly' (Rule 6).
    This proves that Rule 4 is evaluated strictly BEFORE Rule 6 in the engine.
    """
    d = EvidenceVector(
        e_X=mock_thresholds.X + 0.15,
        e_Y=mock_thresholds.Y + 0.15,
        e_Z=mock_thresholds.Z + 0.15,
        e_Bell=mock_thresholds.Bell + 0.15,
        v_transcript=1, v_freshness=1, v_identity=1, v_hardware=1
    )
    record = Q_TAM_classify(d, mock_thresholds)

    # Must match Rule 4 Broadband degradation
    assert record.rule_id == "RULE_4_BROADBAND_DEGRADATION"
    assert record.verdict == "ALERT"
    assert "Broadband degradation" in record.primary_hypothesis
    # Explicitly prove it did NOT trigger Rule 6 Broad Pauli
    assert record.rule_id != "RULE_6_BROAD_PAULI"
    assert "Broad Pauli-basis anomaly" not in record.primary_hypothesis


# -----------------------------------------------------------------------------
# 3. Auxiliary Evidence & Acceptance Rule Tests (§12.1)
# -----------------------------------------------------------------------------

def test_v_hardware_is_auxiliary_not_acceptance_gate(mock_thresholds):
    """
    Verifies that v_hardware is auxiliary evidence by default per §12.1:
    Even when v_hardware = 0, an honest signature PASSES acceptance by default.
    When require_hardware_gate=True is explicitly enabled, v_hardware=0 causes acceptance to fail.
    """
    # Honest quantum rates and classical flags, but v_hardware = 0
    d_aux_fail = EvidenceVector(
        e_X=0.01, e_Y=0.01, e_Z=0.01, e_Bell=0.01,
        v_transcript=1, v_freshness=1, v_identity=1, v_hardware=0
    )

    # Default configuration: v_hardware is auxiliary only -> MUST ACCEPT
    accepted_default, record_default = evaluate_acceptance(
        d_aux_fail, mock_thresholds, require_hardware_gate=False
    )
    assert accepted_default is True
    assert record_default is not None
    assert record_default.verdict == "ACCEPT"

    # Strict deployment configuration: v_hardware enabled as gate -> MUST REJECT
    accepted_strict, record_strict = evaluate_acceptance(
        d_aux_fail, mock_thresholds, require_hardware_gate=True
    )
    assert accepted_strict is False
    assert record_strict is None


def test_acceptance_rule_honest_passes(mock_thresholds):
    """Acceptance rule accepts when all quantum rates <= thresholds and classical flags == 1."""
    d_honest = EvidenceVector(
        e_X=mock_thresholds.X - 0.05,
        e_Y=mock_thresholds.Y - 0.05,
        e_Z=mock_thresholds.Z - 0.05,
        e_Bell=mock_thresholds.Bell - 0.05,
        v_transcript=1, v_freshness=1, v_identity=1, v_hardware=1
    )
    is_accepted, record = evaluate_acceptance(d_honest, mock_thresholds)
    assert is_accepted is True
    assert record is not None
    assert record.verdict == "ACCEPT"


def test_acceptance_rule_failures(mock_thresholds):
    """Acceptance rule fails whenever any quantum rate exceeds threshold or classical flag fails."""
    # Test each failure condition individually
    cases = [
        # Quantum threshold exceedances
        EvidenceVector(e_X=mock_thresholds.X + 0.01, e_Y=0.01, e_Z=0.01, e_Bell=0.01),
        EvidenceVector(e_X=0.01, e_Y=mock_thresholds.Y + 0.01, e_Z=0.01, e_Bell=0.01),
        EvidenceVector(e_X=0.01, e_Y=0.01, e_Z=mock_thresholds.Z + 0.01, e_Bell=0.01),
        EvidenceVector(e_X=0.01, e_Y=0.01, e_Z=0.01, e_Bell=mock_thresholds.Bell + 0.01),
        # Classical integrity failures
        EvidenceVector(e_X=0.01, e_Y=0.01, e_Z=0.01, e_Bell=0.01, v_transcript=0),
        EvidenceVector(e_X=0.01, e_Y=0.01, e_Z=0.01, e_Bell=0.01, v_freshness=0),
        EvidenceVector(e_X=0.01, e_Y=0.01, e_Z=0.01, e_Bell=0.01, v_identity=0),
    ]

    for d in cases:
        is_accepted, record = evaluate_acceptance(d, mock_thresholds)
        assert is_accepted is False
        assert record is None


# -----------------------------------------------------------------------------
# 4. DBEV Basis-Dependent Correlation Tests (§9)
# -----------------------------------------------------------------------------

def test_dbev_basis_dependent_rules():
    """
    Verifies basis-dependent Bell-decoy correlation rules per §9:
    - X/X: Expected same outcomes (violations: 01, 10)
    - Z/Z: Expected same outcomes (violations: 01, 10)
    - Y/Y: Expected opposite outcomes (violations: 00, 11)
    """
    # Counts dictionary: 500 identical (00, 11), 500 opposite (01, 10)
    counts = {"00": 250, "11": 250, "01": 250, "10": 250}

    res_X = evaluate_dbev_for_basis("X", counts)
    res_Z = evaluate_dbev_for_basis("Z", counts)
    res_Y = evaluate_dbev_for_basis("Y", counts)

    # For X and Z, opposite outcomes (01, 10) are violations
    assert res_X["violations"] == 500
    assert res_X["violation_rate"] == 0.5
    assert res_Z["violations"] == 500
    assert res_Z["violation_rate"] == 0.5

    # For Y, same outcomes (00, 11) are violations (anti-correlation expected!)
    assert res_Y["violations"] == 500
    assert res_Y["violation_rate"] == 0.5

    # Multi-basis aggregate run
    full_counts = {
        "X": {"00": 500, "11": 500},        # 0 violations for X
        "Z": {"00": 500, "11": 500},        # 0 violations for Z
        "Y": {"01": 500, "10": 500},        # 0 violations for Y (opposite outcomes!)
    }
    agg = run_dbev(full_counts)
    assert agg["total_violations"] == 0
    assert agg["e_Bell"] == 0.0


def test_dbev_uniform_matching_fails_on_honest_Y():
    """
    Verifies that a naive uniform 'outcomes must match' rule produces ~100% false violations
    on honest Y/Y Bell decoys, validating §9's explicit warning.
    """
    # Honest Y/Y Bell measurements produce opposite outcomes (01, 10)
    honest_Y_counts = {"01": 500, "10": 500}

    # Our correct basis-dependent DBEV:
    dbev_res = evaluate_dbev_for_basis("Y", honest_Y_counts)
    assert dbev_res["violations"] == 0
    assert dbev_res["violation_rate"] == 0.0

    # A broken uniform rule that expects matching outcomes would count 01 and 10 as violations:
    broken_violations = honest_Y_counts["01"] + honest_Y_counts["10"]
    assert broken_violations == 1000  # 100% false alarm rate on honest channel!


# -----------------------------------------------------------------------------
# 5. Forgery Bounds & Explanation Records (§11.2, §12.2)
# -----------------------------------------------------------------------------

def test_forgery_bound_calculation(mock_thresholds):
    """
    Verifies Hoeffding forgery bounds and conservative union bound calculation (§11.2).
    """
    # Case 1: Attack rate above threshold
    tau = 0.15
    mu_forge = 0.35
    n_ver = 500
    expected_bound = math.exp(-2.0 * n_ver * ((mu_forge - tau) ** 2))

    bound = compute_forgery_bound(mu_forge, tau, n_ver)
    assert math.isclose(bound, expected_bound, rel_tol=1e-12)
    assert bound < 1e-15

    # Case 2: Union bound across all 4 tests
    attack_rates = {"X": 0.35, "Y": 0.35, "Z": 0.35, "Bell": 0.35}
    n_vers = {"X": 500, "Y": 500, "Z": 500, "Bell": 500}
    union_bound = compute_union_bound_forgery_probability(attack_rates, mock_thresholds, n_vers)
    expected_sum = sum(
        compute_forgery_bound(attack_rates[b], mock_thresholds.get_tau(b), n_vers[b])
        for b in attack_rates
    )
    assert math.isclose(union_bound, expected_sum, rel_tol=1e-12)
    assert union_bound < 1e-10


def test_explanation_record_metadata(mock_thresholds):
    """
    Verifies that explanation records include all required non-ML declarations,
    primary hypothesis, alternative explanation, and rule IDs per §12.2.
    """
    d = EvidenceVector(
        e_X=0.01, e_Y=0.01, e_Z=0.01, e_Bell=mock_thresholds.Bell + 0.1,
        v_transcript=1, v_freshness=1, v_identity=1, v_hardware=1
    )
    rec = Q_TAM_classify(d, mock_thresholds)

    d_dict = rec.to_dict()
    assert d_dict["evidence_mode"] == "Deterministic rule-based hypothesis (Non-ML)"
    assert d_dict["is_model_based_hypothesis"] is True
    assert "not forensic certainty" in d_dict["disclaimer"]
    assert len(d_dict["primary_hypothesis"]) > 0
    assert len(d_dict["alternative_explanation"]) > 0
    assert d_dict["rule_id"] == "RULE_5_CHANNEL_INTEGRITY"


# -----------------------------------------------------------------------------
# 6. Honest Channel Calibration Engine Test (§11.1)
# -----------------------------------------------------------------------------

def test_calibration_run_measures_rates_and_computes_thresholds():
    """
    Executes a simulated honest calibration run using CalibrationEngine,
    verifying measured μ̂_b, calculated thresholds, and disclosure metadata.
    """
    engine = CalibrationEngine(
        n_cal={"X": 100, "Y": 100, "Z": 100, "Bell": 120},
        n_ver={"X": 50, "Y": 50, "Z": 50, "Bell": 50},
        depolarizing_prob=0.0,
        seed=42
    )
    report = engine.run_calibration()

    assert isinstance(report, CalibrationReport)
    # Under noiseless simulation, honest rates should be 0.0
    for b in ["X", "Y", "Z", "Bell"]:
        assert report.mu_hats[b] == 0.0
        # Derived threshold must equal 0.0 + delta_cal + delta_ver > 0
        tau_b = report.threshold_result.get_tau(b)
        assert tau_b > 0.0
        assert tau_b < 1.0

    assert "ideal noiseless simulator" in report.noise_model_description
    assert report.threshold_result.bound_type == "one-sided upper tail bound (Hoeffding)"
