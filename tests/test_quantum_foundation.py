"""
QUASAR-TDS Phase 01: Quantum Foundation Unit Test Suite

Mandatory pytest functions per MASTER_PROMPT.md §3 (Phase 01):
- test_bell_pair_generation_fidelity
- test_teleportation_correction_mapping
- test_x_basis_prep_and_measure
- test_y_basis_prep_and_measure
- test_z_basis_prep_and_measure
- test_honest_phi_plus_XX_correlation
- test_honest_phi_plus_ZZ_correlation
- test_honest_phi_plus_YY_anticorrelation (CRITICAL: asserts opposite outcomes for |Φ+⟩ in Y-basis)
"""

import pytest
import numpy as np
from qiskit.quantum_info import Statevector

from quantum_core.bell_state import (
    create_bell_pair,
    get_bell_pair_fidelity,
    measure_bell_correlation,
    evaluate_bell_decoy_correlation
)
from quantum_core.pauli_states import (
    PauliBasis,
    prepare_pauli_eigenstate,
    measure_pauli_basis,
    run_prep_and_measure_single_qubit,
    outcome_bit_to_eigenvalue,
    eigenvalue_to_outcome_bit
)
from quantum_core.teleportation import (
    CORRECTION_MAPPING,
    build_teleportation_circuit,
    verify_teleportation_correction_mapping,
    teleport_and_measure
)


def test_bell_pair_generation_fidelity():
    """
    Verifies that create_bell_pair prepares |Φ+⟩ = (|00⟩+|11⟩)/√2 with ideal fidelity = 1.0.
    """
    fidelity = get_bell_pair_fidelity()
    assert fidelity >= 0.999999, f"Bell pair fidelity {fidelity} is below acceptable threshold 0.999999"


def test_teleportation_correction_mapping():
    """
    Validates the (c0, c1) -> I/X/Z/XZ correction mapping table per QUASAR-TDS_Final.md §8.5.
    
    Checks:
    1. Mapping dictionary contains all four 2-bit Bell measurement outcomes.
    2. Algebraic branch-by-branch statevector fidelity is 1.0 across all four branches
       for an arbitrary superposition state |ψ⟩.
    3. AerSimulator dynamic feedforward execution succeeds with 100% accuracy for all
       6 Pauli eigenstates.
    """
    # Check mapping specification
    assert CORRECTION_MAPPING[(0, 0)] == "I"
    assert CORRECTION_MAPPING[(0, 1)] == "X"
    assert CORRECTION_MAPPING[(1, 0)] == "Z"
    assert CORRECTION_MAPPING[(1, 1)] == "XZ"
    
    # 1. Algebraic branch fidelity verification for an arbitrary test state
    test_state = Statevector([np.cos(0.52), np.exp(1j * 1.23) * np.sin(0.52)])
    branch_fidelities = verify_teleportation_correction_mapping(test_state)
    
    for branch, fid in branch_fidelities.items():
        assert fid >= 0.999999, (
            f"Teleportation branch {branch} with correction {CORRECTION_MAPPING[branch]} "
            f"failed fidelity test: {fid} < 0.999999"
        )
        
    # 2. AerSimulator circuit teleportation for all 6 Pauli eigenstates
    eigenstates = [
        ("Z", +1), ("Z", -1),
        ("X", +1), ("X", -1),
        ("Y", +1), ("Y", -1),
    ]
    
    for basis, eigenval in eigenstates:
        expected_bit = "0" if eigenval == +1 else "1"
        counts = teleport_and_measure(basis=basis, eigenvalue=eigenval, shots=500, seed=42)
        total_shots = sum(counts.values())
        correct_shots = counts.get(expected_bit, 0)
        assert correct_shots == total_shots, (
            f"Teleportation simulation failed for eigenstate ({basis}, {eigenval:+d}): "
            f"expected bit '{expected_bit}' but counts were {counts}"
        )


def test_x_basis_prep_and_measure():
    """
    Verifies X-basis eigenstate preparation and projective measurement per §10:
    - |+⟩ (+1 eigenvalue) prepared by H -> measured in X basis yields outcome 0.
    - |−⟩ (-1 eigenvalue) prepared by X then H -> measured in X basis yields outcome 1.
    """
    shots = 1000
    # Test |+⟩
    counts_plus = run_prep_and_measure_single_qubit(basis="X", eigenvalue=+1, shots=shots, seed=42)
    assert counts_plus.get("0", 0) == shots, f"|+⟩ in X basis failed: counts={counts_plus}"
    
    # Test |−⟩
    counts_minus = run_prep_and_measure_single_qubit(basis="X", eigenvalue=-1, shots=shots, seed=42)
    assert counts_minus.get("1", 0) == shots, f"|−⟩ in X basis failed: counts={counts_minus}"


def test_y_basis_prep_and_measure():
    """
    Verifies Y-basis eigenstate preparation and projective measurement per §10:
    - |+i⟩ (+1 eigenvalue) prepared by H then S -> measured in Y basis (S† then H) yields outcome 0.
    - |−i⟩ (-1 eigenvalue) prepared by X then H then S -> measured in Y basis yields outcome 1.
    """
    shots = 1000
    # Test |+i⟩
    counts_plus_i = run_prep_and_measure_single_qubit(basis="Y", eigenvalue=+1, shots=shots, seed=42)
    assert counts_plus_i.get("0", 0) == shots, f"|+i⟩ in Y basis failed: counts={counts_plus_i}"
    
    # Test |−i⟩
    counts_minus_i = run_prep_and_measure_single_qubit(basis="Y", eigenvalue=-1, shots=shots, seed=42)
    assert counts_minus_i.get("1", 0) == shots, f"|−i⟩ in Y basis failed: counts={counts_minus_i}"


def test_z_basis_prep_and_measure():
    """
    Verifies Z-basis eigenstate preparation and projective measurement per §10:
    - |0⟩ (+1 eigenvalue) prepared by Identity -> measured directly yields outcome 0.
    - |1⟩ (-1 eigenvalue) prepared by X -> measured directly yields outcome 1.
    """
    shots = 1000
    # Test |0⟩
    counts_zero = run_prep_and_measure_single_qubit(basis="Z", eigenvalue=+1, shots=shots, seed=42)
    assert counts_zero.get("0", 0) == shots, f"|0⟩ in Z basis failed: counts={counts_zero}"
    
    # Test |1⟩
    counts_one = run_prep_and_measure_single_qubit(basis="Z", eigenvalue=-1, shots=shots, seed=42)
    assert counts_one.get("1", 0) == shots, f"|1⟩ in Z basis failed: counts={counts_one}"


def test_honest_phi_plus_XX_correlation():
    """
    Verifies that honest |Φ+⟩ measured in X⊗X exhibits perfect correlation
    (identical outcomes for Alice and Bob, ⟨X⊗X⟩ = +1).
    """
    shots = 2000
    counts = measure_bell_correlation(basis_alice="X", basis_bob="X", shots=shots, seed=123)
    eval_res = evaluate_bell_decoy_correlation(counts, basis="X")
    
    assert eval_res["violations"] == 0, f"Unexpected correlation violations in X⊗X: {eval_res}"
    assert eval_res["violation_rate"] == 0.0
    assert eval_res["agreement_rate"] == 1.0


def test_honest_phi_plus_ZZ_correlation():
    """
    Verifies that honest |Φ+⟩ measured in Z⊗Z exhibits perfect correlation
    (identical outcomes for Alice and Bob, ⟨Z⊗Z⟩ = +1).
    """
    shots = 2000
    counts = measure_bell_correlation(basis_alice="Z", basis_bob="Z", shots=shots, seed=456)
    eval_res = evaluate_bell_decoy_correlation(counts, basis="Z")
    
    assert eval_res["violations"] == 0, f"Unexpected correlation violations in Z⊗Z: {eval_res}"
    assert eval_res["violation_rate"] == 0.0
    assert eval_res["agreement_rate"] == 1.0


def test_honest_phi_plus_YY_anticorrelation():
    """
    CRITICAL TEST per MASTER_PROMPT.md §1 & §3:
    Verifies that honest |Φ+⟩ measured in Y⊗Y exhibits perfect ANTI-CORRELATION
    (opposite outcomes for Alice and Bob, ⟨Y⊗Y⟩ = -1).
    
    If a naive DBEV implementation expects identical outcomes, it will produce
    100% false-alarm errors on honest sessions.
    """
    shots = 2000
    counts = measure_bell_correlation(basis_alice="Y", basis_bob="Y", shots=shots, seed=789)
    eval_res = evaluate_bell_decoy_correlation(counts, basis="Y")
    
    # Assert that all observed outcomes are opposite ('01' or '10')
    observed_anticorrelation_rate = eval_res["agreement_rate"]
    violation_rate = eval_res["violation_rate"]
    
    assert eval_res["violations"] == 0, (
        f"CRITICAL FAILURE: Y⊗Y measurement produced same outcomes in honest |Φ+⟩! "
        f"Counts: {counts}, Evaluation: {eval_res}. "
        f"Check that Y basis measurement uses S† then H and that DBEV expects opposite outcomes."
    )
    assert observed_anticorrelation_rate >= 0.99, (
        f"Anti-correlation rate {observed_anticorrelation_rate} dropped below 0.99!"
    )
    assert violation_rate == 0.0, f"Violation rate {violation_rate} must be 0.0 in ideal simulation."
