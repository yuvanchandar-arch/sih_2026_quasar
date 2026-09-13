"""
QUASAR-TDS Protocol Core: State-Material Lifecycle Module

Implements Known-State Model A and state-material lifecycle management
strictly per QUASAR-TDS_Final.md §8.3 and §8.4 (MVP simplification N = N_D + N_T).

Specifications:
- Model A: Alice generates sequence of N qubits drawn from Pauli eigenstates
  {|0⟩, |1⟩, |+⟩, |−⟩, |+i⟩, |−i⟩}. Alice stores only the classical reference
  description K_A = {(b_i, x_i)}_{i=1}^N, retaining no quantum copy.
- Lifecycle partition: N = N_D + N_T (N_D decoy positions, N_T test positions).
- One-time-use enforcement: Each position can be measured at most once.
  Subsequent measurement attempts must raise PositionAlreadyConsumedError.
- Storage-until-challenge-phase behavior: Teleported states are preserved in
  quantum memory (STORED) until the challenge phase triggers projective measurement.
"""

from enum import Enum
from typing import Dict, List, Set, Tuple, Optional
import secrets
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from quantum_core.pauli_states import (
    PauliBasis,
    prepare_pauli_eigenstate,
    measure_pauli_basis,
    outcome_bit_to_eigenvalue
)
from quantum_core.teleportation import build_teleportation_circuit


class PositionAlreadyConsumedError(RuntimeError):
    """Raised when an attempt is made to measure a quantum position that has already been consumed."""
    pass


class InvalidPositionStateError(RuntimeError):
    """Raised when an operation is attempted on a position in an invalid lifecycle state."""
    pass


class PartitionMismatchError(ValueError):
    """Raised when total positions do not match N_D + N_T partition sizes."""
    pass


class PositionRole(str, Enum):
    DECOY = "DECOY"  # N_D positions for DBEV channel-integrity diagnostic
    TEST = "TEST"    # N_T positions for challenge verification


class PositionLifecycleState(str, Enum):
    UNPREPARED = "UNPREPARED"
    STORED = "STORED"        # Teleported and held in quantum register awaiting challenge
    CONSUMED = "CONSUMED"    # Measured exactly once; cannot be remeasured


class PauliDescriptor:
    """Classical reference description stored by Alice: (basis, eigenvalue)."""
    def __init__(self, basis: str, eigenvalue: int):
        if basis.upper() not in [PauliBasis.X.value, PauliBasis.Y.value, PauliBasis.Z.value]:
            raise ValueError(f"Invalid basis: {basis}")
        if eigenvalue not in (+1, -1):
            raise ValueError(f"Invalid eigenvalue: {eigenvalue}")
        self.basis = basis.upper()
        self.eigenvalue = eigenvalue

    def __repr__(self) -> str:
        return f"PauliDescriptor({self.basis}, {self.eigenvalue:+d})"

    def to_dict(self) -> Dict[str, any]:
        return {"basis": self.basis, "eigenvalue": self.eigenvalue}


class QuantumPosition:
    """Represents a single position in the state-material sequence at Bob."""
    def __init__(self, index: int, role: PositionRole):
        self.index = index
        self.role = role
        self.lifecycle_state = PositionLifecycleState.UNPREPARED
        self.circuit: Optional[QuantumCircuit] = None
        self.measured_outcome: Optional[int] = None
        self.measured_eigenvalue: Optional[int] = None
        self.measured_basis: Optional[str] = None

    def store_teleported_state(self, circuit: QuantumCircuit) -> None:
        """Stores the corrected qubit in Bob's register awaiting challenge."""
        if self.lifecycle_state != PositionLifecycleState.UNPREPARED:
            raise InvalidPositionStateError(
                f"Position {self.index} cannot transition to STORED from state {self.lifecycle_state}"
            )
        self.circuit = circuit
        self.lifecycle_state = PositionLifecycleState.STORED

    def measure(self, basis: str, seed: Optional[int] = None) -> int:
        """
        Performs one-time projective measurement in the requested basis.
        Enforces one-time-use rule: raises PositionAlreadyConsumedError if already CONSUMED.
        """
        if self.lifecycle_state == PositionLifecycleState.CONSUMED:
            raise PositionAlreadyConsumedError(
                f"Position {self.index} has already been consumed and cannot be measured again. "
                f"One-time-use violation detected."
            )
        if self.lifecycle_state != PositionLifecycleState.STORED:
            raise InvalidPositionStateError(
                f"Position {self.index} is not ready for measurement (current state: {self.lifecycle_state})."
            )

        basis_str = basis.upper()
        # Measure Bob's qubit (qubit 2 in 3-qubit teleportation circuit) into classical bit 2
        qc_measure = self.circuit.copy()
        cr_bob = qc_measure.cregs[-1] if len(qc_measure.cregs) > 1 else qc_measure.clbits
        measure_pauli_basis(qc_measure, qubit=2, clbit=qc_measure.clbits[-1], basis=basis_str)

        sim = AerSimulator()
        result = sim.run(qc_measure, shots=1, seed_simulator=seed).result()
        raw_counts = result.get_counts()
        bitstring = list(raw_counts.keys())[0].replace(" ", "")
        # Bob's measurement bit is the first bit (index 0)
        outcome_bit = int(bitstring[0])

        # Transition lifecycle state to CONSUMED
        self.lifecycle_state = PositionLifecycleState.CONSUMED
        self.measured_outcome = outcome_bit
        self.measured_eigenvalue = outcome_bit_to_eigenvalue(outcome_bit)
        self.measured_basis = basis_str
        # Discard quantum circuit representation post-measurement
        self.circuit = None

        return outcome_bit


class StateMaterialManager:
    """
    Coordinates state-material generation, partitioning, teleportation distribution,
    and lifecycle enforcement for Alice and Bob.
    """
    def __init__(self, n_d: int, n_t: int, seed: Optional[int] = None):
        if n_d <= 0 or n_t <= 0:
            raise ValueError(f"Partition sizes must be positive integers: n_d={n_d}, n_t={n_t}")
        self.n_d = n_d
        self.n_t = n_t
        self.n_total = n_d + n_t
        self._rng = np.random.default_rng(seed)

        # Alice's classical key material K_A (stores only descriptions, no qubits)
        self.alice_key_material: Dict[int, PauliDescriptor] = {}

        # Partition index sets
        self.decoy_indices: Set[int] = set()
        self.test_indices: Set[int] = set()

        # Bob's position records
        self.bob_positions: Dict[int, QuantumPosition] = {}

        self._initialize_partition()

    def _initialize_partition(self) -> None:
        """Establishes the disjoint decoy (N_D) and test (N_T) partitions."""
        all_indices = list(range(self.n_total))
        decoy_list = list(self._rng.choice(all_indices, size=self.n_d, replace=False))
        self.decoy_indices = set(decoy_list)
        self.test_indices = set(i for i in all_indices if i not in self.decoy_indices)

        if len(self.decoy_indices) != self.n_d:
            raise PartitionMismatchError(f"Decoy partition size mismatch: {len(self.decoy_indices)} != {self.n_d}")
        if len(self.test_indices) != self.n_t:
            raise PartitionMismatchError(f"Test partition size mismatch: {len(self.test_indices)} != {self.n_t}")
        if self.decoy_indices.intersection(self.test_indices):
            raise PartitionMismatchError("Decoy and test partitions must be strictly disjoint.")

        # Initialize Bob's positions with assigned roles
        for idx in range(self.n_total):
            role = PositionRole.DECOY if idx in self.decoy_indices else PositionRole.TEST
            self.bob_positions[idx] = QuantumPosition(index=idx, role=role)

    def generate_alice_key_material(self) -> Dict[int, PauliDescriptor]:
        """
        Prepares Alice's classical key material K_A for all N positions per Model A (§8.3).
        Each position is independently drawn from {|0⟩, |1⟩, |+⟩, |−⟩, |+i⟩, |−i⟩}.
        """
        bases = [PauliBasis.X.value, PauliBasis.Y.value, PauliBasis.Z.value]
        eigenvalues = [+1, -1]

        for idx in range(self.n_total):
            chosen_basis = self._rng.choice(bases)
            chosen_eigenval = int(self._rng.choice(eigenvalues))
            self.alice_key_material[idx] = PauliDescriptor(basis=chosen_basis, eigenvalue=chosen_eigenval)

        return self.alice_key_material

    def distribute_state_material(self) -> None:
        """
        Simulates teleportation-based QDS state-material distribution (§8.5).
        For each position, teleports Alice's eigenstate to Bob. Bob applies feedforward
        Pauli corrections and retains the qubit in STORED state awaiting the challenge phase.
        Alice retains NO quantum state, only classical K_A.
        """
        if not self.alice_key_material:
            self.generate_alice_key_material()

        for idx in range(self.n_total):
            descriptor = self.alice_key_material[idx]
            
            # Teleportation circuit with feedforward Pauli correction
            def state_prep(qc: QuantumCircuit, q_idx: int):
                prepare_pauli_eigenstate(qc, qubit=q_idx, basis=descriptor.basis, eigenvalue=descriptor.eigenvalue)

            qc_teleport = build_teleportation_circuit(state_prep_fn=state_prep, bob_measurement_basis=None)
            self.bob_positions[idx].store_teleported_state(qc_teleport)

    def measure_decoy_position(self, index: int, basis: str, seed: Optional[int] = None) -> int:
        """Measures a decoy position for the DBEV channel-integrity diagnostic."""
        pos = self.bob_positions[index]
        if pos.role != PositionRole.DECOY:
            raise ValueError(f"Position {index} is not a decoy position (role={pos.role}).")
        return pos.measure(basis=basis, seed=seed)

    def measure_test_position(self, index: int, basis: str, seed: Optional[int] = None) -> int:
        """Measures a challenge-test position during signature verification."""
        pos = self.bob_positions[index]
        if pos.role != PositionRole.TEST:
            raise ValueError(f"Position {index} is not a test position (role={pos.role}).")
        return pos.measure(basis=basis, seed=seed)
