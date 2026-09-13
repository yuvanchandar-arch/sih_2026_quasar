"""
QUASAR-TDS Quantum Core: Bell State and Decoy Correlation Module

Implements Bell-pair (|Φ+⟩) generation, fidelity verification, and basis-dependent
Bell-decoy correlation diagnostics according to QUASAR-TDS_Final.md §9 and §10.
"""

from typing import Dict, Tuple, Optional
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, state_fidelity
from qiskit_aer import AerSimulator

from quantum_core.pauli_states import measure_pauli_basis, PauliBasis


def create_bell_pair(
    circuit: Optional[QuantumCircuit] = None,
    q_alice: int = 0,
    q_bob: int = 1
) -> QuantumCircuit:
    """
    Applies the canonical gate sequence to prepare the maximally entangled
    Bell state |Φ+⟩ = (|00⟩ + |11⟩) / √2 across two qubits.

    Sequence:
        1. Hadamard (H) on Alice's qubit
        2. Controlled-NOT (CNOT / cx) with control Alice, target Bob
    """
    if circuit is None:
        circuit = QuantumCircuit(2)
    circuit.h(q_alice)
    circuit.cx(q_alice, q_bob)
    return circuit


def get_bell_pair_fidelity(circuit: Optional[QuantumCircuit] = None) -> float:
    """
    Computes the quantum state fidelity of the prepared Bell pair against the
    theoretical target statevector |Φ+⟩ = [1/√2, 0, 0, 1/√2].
    """
    if circuit is None:
        circuit = create_bell_pair()
    
    prepared_sv = Statevector.from_instruction(circuit)
    ideal_phi_plus = Statevector([1.0 / np.sqrt(2.0), 0.0, 0.0, 1.0 / np.sqrt(2.0)])
    fidelity = float(state_fidelity(prepared_sv, ideal_phi_plus))
    return fidelity


def measure_bell_correlation(
    basis_alice: str,
    basis_bob: str,
    shots: int = 2000,
    seed: Optional[int] = 42
) -> Dict[str, int]:
    """
    Prepares |Φ+⟩ and measures Alice's and Bob's qubits in the specified Pauli bases.
    
    Args:
        basis_alice: 'X', 'Y', or 'Z'
        basis_bob: 'X', 'Y', or 'Z'
        shots: Number of measurement shots
        seed: Optional random seed for simulator reproducibility
    
    Returns:
        dict: Counts of two-bit measurement outcomes, formatted as {f"{b_bob}{b_alice}": count}
              matching Qiskit's standard bitstring convention (clbit 1, clbit 0).
    """
    qc = QuantumCircuit(2, 2)
    create_bell_pair(qc, q_alice=0, q_bob=1)
    
    # Alice measures qubit 0 into classical bit 0
    measure_pauli_basis(qc, qubit=0, clbit=0, basis=basis_alice)
    # Bob measures qubit 1 into classical bit 1
    measure_pauli_basis(qc, qubit=1, clbit=1, basis=basis_bob)
    
    sim = AerSimulator()
    result = sim.run(qc, shots=shots, seed_simulator=seed).result()
    counts = result.get_counts()
    return counts


def evaluate_bell_decoy_correlation(counts: Dict[str, int], basis: str) -> Dict[str, float]:
    """
    Evaluates the Bell-decoy channel-integrity diagnostic per QUASAR-TDS_Final.md §9.
    
    CORRELATION RULES:
        - X⊗X: Expected same outcomes (⟨X⊗X⟩ = +1). Violations: 01, 10.
        - Z⊗Z: Expected same outcomes (⟨Z⊗Z⟩ = +1). Violations: 01, 10.
        - Y⊗Y: Expected opposite outcomes (⟨Y⊗Y⟩ = -1). Violations: 00, 11.
    
    Returns:
        dict containing:
            - basis: basis tested
            - total_shots: total measurement samples
            - violations: count of rule-violating outcomes
            - violation_rate: ê_Bell = violations / total_shots
            - correlation_rate: 1 - violation_rate (for Y/Y this is anti-correlation rate)
    """
    basis = basis.upper()
    total_shots = sum(counts.values())
    if total_shots == 0:
        raise ValueError("Counts dictionary cannot be empty")
        
    same_count = 0
    opposite_count = 0
    for bitstring, count in counts.items():
        cleaned = bitstring.replace(" ", "")
        # Qiskit bitstring order: bit 1 (Bob), bit 0 (Alice)
        b_bob = cleaned[-2]
        b_alice = cleaned[-1]
        if b_bob == b_alice:
            same_count += count
        else:
            opposite_count += count
            
    if basis in [PauliBasis.X.value, PauliBasis.Z.value]:
        # Same outcomes expected
        violations = opposite_count
        agreement = same_count
    elif basis == PauliBasis.Y.value:
        # Opposite outcomes expected (anti-correlated)
        violations = same_count
        agreement = opposite_count
    else:
        raise ValueError(f"Unsupported Bell decoy basis: {basis}. Expected X, Y, or Z.")
        
    violation_rate = violations / total_shots
    agreement_rate = agreement / total_shots
    
    return {
        "basis": basis,
        "total_shots": total_shots,
        "violations": violations,
        "violation_rate": float(violation_rate),
        "agreement_count": agreement,
        "agreement_rate": float(agreement_rate)
    }
