"""
QUASAR-TDS Benchmarks: Quantum Noise Models

Implements the minimum honest baseline noise models specified in QUASAR-TDS_Final.md §17.1:
  1. Ideal simulator (noiseless)
  2. Bit-flip noise (Pauli X error channel)
  3. Phase-flip noise (Pauli Z error channel)
  4. Depolarizing noise (isotropic quantum depolarizing)
  5. Measurement readout error (classical bit-flip error matrix)
  6. Calibration drift (evaluates channel with shifted physical noise relative to calibration)
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from qiskit_aer.noise import (
    NoiseModel,
    depolarizing_error,
    pauli_error,
    ReadoutError
)


@dataclass(frozen=True)
class NoiseModelConfig:
    name: str
    noise_type: str
    param: float
    description: str


def create_noise_model(noise_type: str, p: float = 0.01) -> Tuple[Optional[NoiseModel], str]:
    """
    Constructs a Qiskit Aer NoiseModel for the specified honest baseline.

    Args:
        noise_type: One of 'ideal', 'bit_flip', 'phase_flip', 'depolarizing',
                    'measurement_error', 'calibration_drift'.
        p: Error probability parameter (default 0.01 = 1%).

    Returns:
        (noise_model, description_string)
    """
    nt = noise_type.lower().strip()

    if nt == "ideal":
        return None, "Ideal noiseless simulator (p=0.0)"

    noise_model = NoiseModel()

    if nt == "bit_flip":
        # Pauli X error with probability p, identity with 1-p
        error_1q = pauli_error([('X', p), ('I', 1.0 - p)])
        error_2q = pauli_error([('X', p * 1.5), ('I', 1.0 - p * 1.5)])
        error_2q = error_2q.tensor(error_2q)
        noise_model.add_all_qubit_quantum_error(error_1q, ['h', 's', 'sdg', 'x', 'z'])
        noise_model.add_all_qubit_quantum_error(error_2q, ['cx'])
        return noise_model, f"Bit-flip noise channel (p_1q={p:.4f}, p_2q={p*1.5:.4f})"

    elif nt == "phase_flip":
        # Pauli Z error with probability p, identity with 1-p
        error_1q = pauli_error([('Z', p), ('I', 1.0 - p)])
        error_2q = pauli_error([('Z', p * 1.5), ('I', 1.0 - p * 1.5)])
        error_2q = error_2q.tensor(error_2q)
        noise_model.add_all_qubit_quantum_error(error_1q, ['h', 's', 'sdg', 'x', 'z'])
        noise_model.add_all_qubit_quantum_error(error_2q, ['cx'])
        return noise_model, f"Phase-flip noise channel (p_1q={p:.4f}, p_2q={p*1.5:.4f})"

    elif nt == "depolarizing":
        # Isotropic depolarizing channel
        error_1q = depolarizing_error(p, 1)
        error_2q = depolarizing_error(p * 2.0, 2)
        noise_model.add_all_qubit_quantum_error(error_1q, ['h', 's', 'sdg', 'x', 'z'])
        noise_model.add_all_qubit_quantum_error(error_2q, ['cx'])
        return noise_model, f"Depolarizing noise channel (p_1q={p:.4f}, p_2q={p*2.0:.4f})"

    elif nt == "measurement_error":
        # Readout error matrix: P(meas|prep)
        # [[P(0|0), P(1|0)], [P(0|1), P(1|1)]] = [[1-p, p], [p, 1-p]]
        p_readout = [[1.0 - p, p], [p, 1.0 - p]]
        readout_err = ReadoutError(p_readout)
        noise_model.add_all_qubit_readout_error(readout_err)
        return noise_model, f"Measurement readout error channel (p_flip={p:.4f})"

    elif nt == "calibration_drift":
        # Drift model: combined depolarizing + measurement error simulating uncalibrated hardware drift
        p_drift = p * 1.8
        error_1q = depolarizing_error(p_drift, 1)
        error_2q = depolarizing_error(p_drift * 2.0, 2)
        noise_model.add_all_qubit_quantum_error(error_1q, ['h', 's', 'sdg', 'x', 'z'])
        noise_model.add_all_qubit_quantum_error(error_2q, ['cx'])
        readout_err = ReadoutError([[1.0 - p * 0.5, p * 0.5], [p * 0.5, 1.0 - p * 0.5]])
        noise_model.add_all_qubit_readout_error(readout_err)
        return noise_model, f"Calibration drift channel (p_drift={p_drift:.4f}, p_meas_drift={p*0.5:.4f})"

    else:
        raise ValueError(f"Unknown noise type '{noise_type}'. Must be one of: ideal, bit_flip, phase_flip, depolarizing, measurement_error, calibration_drift.")
