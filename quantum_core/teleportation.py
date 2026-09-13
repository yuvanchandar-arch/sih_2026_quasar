"""
QUASAR-TDS Quantum Core: Teleportation Protocol Module

Implements simulated quantum teleportation of known Pauli-eigenstate QDS state material
with fixed, documented Pauli correction mapping per QUASAR-TDS_Final.md §8.5.

CORRECTION MAPPING CONVENTION:
------------------------------
Circuit layout:
  - Qubit 0: Alice's input state |ψ⟩
  - Qubit 1: Alice's half of Bell pair |Φ+⟩
  - Qubit 2: Bob's half of Bell pair |Φ+⟩

Bell measurement:
  - CNOT(control=0, target=1)
  - H(qubit=0)
  - Alice measures qubit 0 -> Classical bit c0
  - Alice measures qubit 1 -> Classical bit c1

Bob's Pauli correction on Qubit 2:
  - Bit c1 controls X correction (bit flip)
  - Bit c0 controls Z correction (phase flip)

Mapping Table:
  (c0, c1) = (0, 0) -> I  (no operation)
  (c0, c1) = (0, 1) -> X  (bit flip)
  (c0, c1) = (1, 0) -> Z  (phase flip)
  (c0, c1) = (1, 1) -> XZ (or ZX up to global phase)
"""

from typing import Callable, Dict, Tuple, Optional
import numpy as np
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
from qiskit.quantum_info import Statevector, state_fidelity, Operator
from qiskit_aer import AerSimulator

from quantum_core.bell_state import create_bell_pair
from quantum_core.pauli_states import (
    prepare_pauli_eigenstate,
    measure_pauli_basis,
    PauliBasis
)

CORRECTION_MAPPING: Dict[Tuple[int, int], str] = {
    (0, 0): "I",
    (0, 1): "X",
    (1, 0): "Z",
    (1, 1): "XZ"
}


def build_teleportation_circuit(
    state_prep_fn: Optional[Callable[[QuantumCircuit, int], None]] = None,
    bob_measurement_basis: Optional[str] = None
) -> QuantumCircuit:
    """
    Constructs a complete 3-qubit teleportation circuit with dynamic feedforward
    corrections for Bob's qubit.
    
    Registers:
      - QuantumRegister(3): [q0: Alice state, q1: Alice Bell, q2: Bob Bell]
      - ClassicalRegister(2, name='c_alice'): [c0, c1]
      - ClassicalRegister(1, name='c_bob'): [c2] (if bob_measurement_basis provided)
    """
    qr = QuantumRegister(3, name="q")
    cr_alice = ClassicalRegister(2, name="c_alice")
    
    if bob_measurement_basis is not None:
        cr_bob = ClassicalRegister(1, name="c_bob")
        qc = QuantumCircuit(qr, cr_alice, cr_bob)
    else:
        qc = QuantumCircuit(qr, cr_alice)
        
    # 1. State preparation on Alice's qubit q0
    if state_prep_fn is not None:
        state_prep_fn(qc, 0)
        
    # 2. Bell pair generation |Φ+⟩ on q1 and q2
    create_bell_pair(qc, q_alice=1, q_bob=2)
    
    # 3. Alice's Bell-basis measurement on (q0, q1)
    qc.cx(0, 1)
    qc.h(0)
    qc.measure(0, cr_alice[0])  # c0
    qc.measure(1, cr_alice[1])  # c1
    
    # 4. Bob applies conditional Pauli corrections on q2
    # c1 == 1 -> X
    with qc.if_test((cr_alice[1], 1)):
        qc.x(2)
    # c0 == 1 -> Z
    with qc.if_test((cr_alice[0], 1)):
        qc.z(2)
        
    # 5. Bob's measurement if requested
    if bob_measurement_basis is not None:
        measure_pauli_basis(qc, qubit=2, clbit=cr_bob[0], basis=bob_measurement_basis)
        
    return qc


def verify_teleportation_correction_mapping(
    target_state: Optional[Statevector] = None
) -> Dict[Tuple[int, int], float]:
    """
    Directly validates the (c0, c1) -> I/X/Z/XZ correction mapping algebraically
    against all four Bell measurement outcomes.
    
    For any target state |ψ⟩, after Alice's Bell projection into outcome (c0, c1),
    Bob's unnormalized sub-state is projected. Applying the corresponding Pauli
    correction from the table must yield fidelity = 1.0 against |ψ⟩.
    """
    if target_state is None:
        # Default to a non-trivial arbitrary superposition |ψ⟩ = cos(θ)|0⟩ + e^(iφ)sin(θ)|1⟩
        theta = 0.618
        phi = 1.414
        target_state = Statevector([np.cos(theta), np.exp(1j * phi) * np.sin(theta)])
        
    qc = QuantumCircuit(3)
    qc.initialize(target_state, 0)
    # Bell pair on q1, q2
    qc.h(1)
    qc.cx(1, 2)
    # Alice Bell measurement gates
    qc.cx(0, 1)
    qc.h(0)
    
    # Get 3-qubit statevector prior to measurement collapse
    sv_full = Statevector.from_instruction(qc)
    
    # Pauli correction operators
    op_I = Operator.from_label('I')
    op_X = Operator.from_label('X')
    op_Z = Operator.from_label('Z')
    op_XZ = op_Z @ op_X  # X applied first, then Z
    
    corrections_ops = {
        (0, 0): op_I,
        (0, 1): op_X,
        (1, 0): op_Z,
        (1, 1): op_XZ,
    }
    
    branch_fidelities: Dict[Tuple[int, int], float] = {}
    
    # In Qiskit standard indexing: sv index k corresponds to |q2 q1 q0> binary
    for c0 in (0, 1):
        for c1 in (0, 1):
            # Extract Bob's amplitudes when q0=c0 and q1=c1
            # q2=0: binary (0, c1, c0) -> index = 0*4 + c1*2 + c0 = 2*c1 + c0
            # q2=1: binary (1, c1, c0) -> index = 1*4 + c1*2 + c0 = 4 + 2*c1 + c0
            idx0 = 2 * c1 + c0
            idx1 = 4 + 2 * c1 + c0
            amp0 = sv_full.data[idx0]
            amp1 = sv_full.data[idx1]
            
            bob_unnorm = Statevector([amp0, amp1])
            norm = np.linalg.norm(bob_unnorm.data)
            bob_norm = Statevector(bob_unnorm.data / norm)
            
            # Apply correction
            corr_op = corrections_ops[(c0, c1)]
            corrected_bob = bob_norm.evolve(corr_op)
            
            fid = float(state_fidelity(target_state, corrected_bob))
            branch_fidelities[(c0, c1)] = fid
            
    return branch_fidelities


def teleport_and_measure(
    basis: str,
    eigenvalue: int,
    measure_basis: Optional[str] = None,
    shots: int = 1000,
    seed: Optional[int] = 42
) -> Dict[str, int]:
    """
    Executes an end-to-end teleportation run for a specific Pauli eigenstate,
    with Bob measuring in `measure_basis` (defaults to same basis as prep).
    
    Returns counts of Bob's measurement outcome ('0' or '1').
    """
    if measure_basis is None:
        measure_basis = basis
        
    def state_prep(qc: QuantumCircuit, qubit: int):
        prepare_pauli_eigenstate(qc, qubit, basis, eigenvalue)
        
    qc = build_teleportation_circuit(state_prep_fn=state_prep, bob_measurement_basis=measure_basis)
    
    sim = AerSimulator()
    result = sim.run(qc, shots=shots, seed_simulator=seed).result()
    counts = result.get_counts()
    
    # Process counts to isolate Bob's classical bit
    bob_counts: Dict[str, int] = {}
    for bitstring, count in counts.items():
        # In Qiskit, multiple registers are separated by spaces: "c_bob c_alice" e.g. "0 10"
        # If not separated, the first bit (highest index) corresponds to c_bob
        parts = bitstring.split()
        if len(parts) == 2:
            bob_bit = parts[0]
        else:
            bob_bit = bitstring[0]
            
        bob_counts[bob_bit] = bob_counts.get(bob_bit, 0) + count
        
    return bob_counts
