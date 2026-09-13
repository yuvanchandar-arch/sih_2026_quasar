"""
QUASAR-TDS Quantum Core: Pauli State Preparation and Measurement Module

Implements Pauli eigenstate preparation and projective measurements for X, Y, and Z
bases strictly following QUASAR-TDS_Final.md §10.

Specifications per §10:
- Z basis: measure directly in the computational basis.
- X basis: prepare with H; measure with H followed by a computational-basis measurement.
- Y basis: prepare using H then S; measure using S† then H followed by a computational-basis measurement.
"""

from enum import Enum
from typing import Optional, Dict, Tuple
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


class PauliBasis(str, Enum):
    X = "X"
    Y = "Y"
    Z = "Z"


def prepare_pauli_eigenstate(
    circuit: QuantumCircuit,
    qubit: int,
    basis: str,
    eigenvalue: int
) -> QuantumCircuit:
    """
    Prepares a qubit in one of the six Pauli eigenstates {|0⟩, |1⟩, |+⟩, |−⟩, |+i⟩, |−i⟩}.
    
    Args:
        circuit: QuantumCircuit to append preparation gates to
        qubit: Index of target qubit
        basis: 'X', 'Y', or 'Z'
        eigenvalue: +1 or -1
        
    Gate sequences per §10:
        Z, +1 (|0⟩):  Identity (starts in |0⟩)
        Z, -1 (|1⟩):  X
        X, +1 (|+⟩):  H
        X, -1 (|−⟩):  X then H (H|1⟩ = |−⟩)
        Y, +1 (|+i⟩): H then S
        Y, -1 (|−i⟩): X then H then S (S H|1⟩ = |−i⟩)
    """
    basis_str = basis.upper()
    if eigenvalue not in (+1, -1):
        raise ValueError(f"Invalid eigenvalue: {eigenvalue}. Must be +1 or -1.")
        
    if basis_str == PauliBasis.Z.value:
        if eigenvalue == -1:
            circuit.x(qubit)
    elif basis_str == PauliBasis.X.value:
        if eigenvalue == -1:
            circuit.x(qubit)
        circuit.h(qubit)
    elif basis_str == PauliBasis.Y.value:
        if eigenvalue == -1:
            circuit.x(qubit)
        circuit.h(qubit)
        circuit.s(qubit)
    else:
        raise ValueError(f"Unsupported Pauli basis: {basis}. Expected 'X', 'Y', or 'Z'.")
        
    return circuit


def measure_pauli_basis(
    circuit: QuantumCircuit,
    qubit: int,
    clbit: int,
    basis: str
) -> QuantumCircuit:
    """
    Applies the basis-transformation gates and projective computational-basis measurement
    per QUASAR-TDS_Final.md §10.
    
    Gate transformations per §10:
        Z basis: Measure directly in computational basis.
        X basis: H then measure.
        Y basis: S† (sdg) then H then measure.
    """
    basis_str = basis.upper()
    if basis_str == PauliBasis.Z.value:
        circuit.measure(qubit, clbit)
    elif basis_str == PauliBasis.X.value:
        circuit.h(qubit)
        circuit.measure(qubit, clbit)
    elif basis_str == PauliBasis.Y.value:
        circuit.sdg(qubit)
        circuit.h(qubit)
        circuit.measure(qubit, clbit)
    else:
        raise ValueError(f"Unsupported Pauli basis: {basis}. Expected 'X', 'Y', or 'Z'.")
        
    return circuit


def run_prep_and_measure_single_qubit(
    basis: str,
    eigenvalue: int,
    shots: int = 1000,
    seed: Optional[int] = 42
) -> Dict[str, int]:
    """
    Utility function to prepare an eigenstate and immediately measure it in the same basis.
    
    Returns counts dict e.g. {'0': 1000} or {'1': 1000}.
    """
    qc = QuantumCircuit(1, 1)
    prepare_pauli_eigenstate(qc, qubit=0, basis=basis, eigenvalue=eigenvalue)
    measure_pauli_basis(qc, qubit=0, clbit=0, basis=basis)
    
    sim = AerSimulator()
    result = sim.run(qc, shots=shots, seed_simulator=seed).result()
    return result.get_counts()


def outcome_bit_to_eigenvalue(bit: int) -> int:
    """
    Maps standard computational measurement outcome bit to Pauli eigenvalue:
    Outcome 0 -> Eigenvalue +1
    Outcome 1 -> Eigenvalue -1
    """
    return +1 if bit == 0 else -1


def eigenvalue_to_outcome_bit(eigenvalue: int) -> int:
    """
    Maps Pauli eigenvalue to expected measurement bit:
    Eigenvalue +1 -> Outcome 0
    Eigenvalue -1 -> Outcome 1
    """
    if eigenvalue == +1:
        return 0
    elif eigenvalue == -1:
        return 1
    raise ValueError(f"Invalid eigenvalue {eigenvalue}. Expected +1 or -1.")
