"""
QUASAR-TDS Quantum Core Package

Provides the foundational quantum mechanics operations for teleportation-based QDS:
- Bell-pair generation and Bell-decoy correlation diagnostics (DBEV)
- Pauli eigenstate preparation and projective measurements (X, Y, Z)
- Quantum teleportation protocol with dynamic feedforward Pauli corrections
"""

from quantum_core.pauli_states import (
    PauliBasis,
    prepare_pauli_eigenstate,
    measure_pauli_basis,
    run_prep_and_measure_single_qubit,
    outcome_bit_to_eigenvalue,
    eigenvalue_to_outcome_bit
)

from quantum_core.bell_state import (
    create_bell_pair,
    get_bell_pair_fidelity,
    measure_bell_correlation,
    evaluate_bell_decoy_correlation
)

from quantum_core.teleportation import (
    CORRECTION_MAPPING,
    build_teleportation_circuit,
    verify_teleportation_correction_mapping,
    teleport_and_measure
)

__all__ = [
    "PauliBasis",
    "prepare_pauli_eigenstate",
    "measure_pauli_basis",
    "run_prep_and_measure_single_qubit",
    "outcome_bit_to_eigenvalue",
    "eigenvalue_to_outcome_bit",
    "create_bell_pair",
    "get_bell_pair_fidelity",
    "measure_bell_correlation",
    "evaluate_bell_decoy_correlation",
    "CORRECTION_MAPPING",
    "build_teleportation_circuit",
    "verify_teleportation_correction_mapping",
    "teleport_and_measure"
]
