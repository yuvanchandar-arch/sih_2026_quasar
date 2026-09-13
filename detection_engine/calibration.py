"""
QUASAR-TDS Detection Engine: Calibration Engine

Implements calibration-run infrastructure measuring empirical honest-channel rates μ̂_b
and deriving calibration-aware thresholds per QUASAR-TDS_Final.md §11.1.
Discloses calibration sample counts, verification sample counts, honest noise model,
error budgets, and one-sided Hoeffding tail bounds.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

from quantum_core.pauli_states import PauliBasis, prepare_pauli_eigenstate, measure_pauli_basis
from quantum_core.bell_state import create_bell_pair
from quantum_core.teleportation import build_teleportation_circuit
from detection_engine.thresholds import ErrorBudget, ThresholdResult, calculate_thresholds
from detection_engine.dbev import evaluate_dbev_for_basis


@dataclass(frozen=True)
class CalibrationReport:
    """Complete disclosure report of an honest calibration run per §11.1."""
    mu_hats: Dict[str, float]
    n_cal: Dict[str, int]
    n_ver: Dict[str, int]
    threshold_result: ThresholdResult
    noise_model_description: str
    depolarizing_prob: float
    seed: Optional[int] = None


class CalibrationEngine:
    """
    Executes honest-channel calibration runs to empirically measure baseline error rates
    μ̂_X, μ̂_Y, μ̂_Z, μ̂_Bell under a specified noise model and sample budget.
    """

    def __init__(
        self,
        n_cal: Optional[Dict[str, int]] = None,
        n_ver: Optional[Dict[str, int]] = None,
        budget: Optional[ErrorBudget] = None,
        depolarizing_prob: float = 0.0,
        noise_model: Optional[NoiseModel] = None,
        noise_desc: Optional[str] = None,
        seed: Optional[int] = 42
    ):
        self.n_cal = n_cal or {"X": 1000, "Y": 1000, "Z": 1000, "Bell": 1000}
        self.n_ver = n_ver or {"X": 500, "Y": 500, "Z": 500, "Bell": 500}
        self.budget = budget or ErrorBudget()
        self.budget.validate()
        self.depolarizing_prob = float(depolarizing_prob)
        self.seed = seed

        # Build or use provided noise model
        if noise_model is not None:
            self.noise_model = noise_model
            self.noise_desc = noise_desc or "Custom quantum noise model"
        elif self.depolarizing_prob > 0.0:
            self.noise_model = NoiseModel()
            error_1q = depolarizing_error(self.depolarizing_prob, 1)
            error_2q = depolarizing_error(self.depolarizing_prob * 2, 2)
            self.noise_model.add_all_qubit_quantum_error(error_1q, ['h', 's', 'sdg', 'x', 'z'])
            self.noise_model.add_all_qubit_quantum_error(error_2q, ['cx'])
            self.noise_desc = f"Depolarizing noise (p_1q={self.depolarizing_prob}, p_2q={self.depolarizing_prob*2})"
        else:
            self.noise_model = None
            self.noise_desc = noise_desc or "Honest channel (ideal noiseless simulator)"

        self.simulator = AerSimulator(noise_model=self.noise_model)

    def calibrate_pauli_basis(self, basis: str, shots: int) -> float:
        """
        Measures honest error rate for a Pauli basis through honest state prep,
        honest Bell-pair teleportation, correction, and measurement.
        """
        basis_upper = basis.upper()
        # Test both eigenstates (+1 and -1) equally
        shots_plus = shots // 2
        shots_minus = shots - shots_plus
        errors = 0

        for eigenstate_bit, n_s in [(0, shots_plus), (1, shots_minus)]:
            if n_s <= 0:
                continue
            eigenvalue = +1 if eigenstate_bit == 0 else -1

            def state_prep(qc: QuantumCircuit, q: int):
                prepare_pauli_eigenstate(circuit=qc, qubit=q, basis=basis_upper, eigenvalue=eigenvalue)

            qc = build_teleportation_circuit(
                state_prep_fn=state_prep,
                bob_measurement_basis=basis_upper
            )

            res = self.simulator.run(qc, shots=n_s, seed_simulator=self.seed).result()
            counts = res.get_counts()
            for bitstring, count in counts.items():
                parts = bitstring.split()
                bob_bit = parts[0] if len(parts) == 2 else bitstring[0]
                if int(bob_bit) != eigenstate_bit:
                    errors += count

        return errors / shots

    def calibrate_bell_decoys(self, shots: int) -> float:
        """
        Measures honest Bell-decoy violation rate across equal partition of X, Y, Z decoys.
        """
        shots_per_basis = shots // 3
        remainder = shots % 3
        shots_alloc = {
            "X": shots_per_basis + (1 if remainder > 0 else 0),
            "Y": shots_per_basis + (1 if remainder > 1 else 0),
            "Z": shots_per_basis
        }

        total_violations = 0
        total_measured = 0

        for basis, n_s in shots_alloc.items():
            if n_s <= 0:
                continue
            qc = QuantumCircuit(2, 2)
            create_bell_pair(qc, q_alice=0, q_bob=1)
            measure_pauli_basis(qc, qubit=0, clbit=0, basis=basis)
            measure_pauli_basis(qc, qubit=1, clbit=1, basis=basis)

            res = self.simulator.run(qc, shots=n_s, seed_simulator=self.seed).result()
            counts = res.get_counts()
            dbev_res = evaluate_dbev_for_basis(basis=basis, counts_or_outcomes=counts)
            total_violations += dbev_res["violations"]
            total_measured += dbev_res["total_shots"]

        return total_violations / total_measured

    def run_calibration(self) -> CalibrationReport:
        """
        Executes calibration across X, Y, Z, and Bell decoys, and derives thresholds.
        """
        mu_hats = {
            "X": self.calibrate_pauli_basis("X", self.n_cal["X"]),
            "Y": self.calibrate_pauli_basis("Y", self.n_cal["Y"]),
            "Z": self.calibrate_pauli_basis("Z", self.n_cal["Z"]),
            "Bell": self.calibrate_bell_decoys(self.n_cal["Bell"]),
        }

        threshold_res = calculate_thresholds(
            mu_hats=mu_hats,
            n_cal=self.n_cal,
            n_ver=self.n_ver,
            budget=self.budget,
            noise_model_description=self.noise_desc
        )

        return CalibrationReport(
            mu_hats=mu_hats,
            n_cal=self.n_cal,
            n_ver=self.n_ver,
            threshold_result=threshold_res,
            noise_model_description=self.noise_desc,
            depolarizing_prob=self.depolarizing_prob,
            seed=self.seed
        )
