"""
QUASAR-TDS Detection Engine: Decoy-State Bell Error Verification (DBEV)

Implements Decoy-State Bell Error Verification strictly per QUASAR-TDS_Final.md §9.
To ensure a single source of truth and prevent logic duplication across modules,
this module directly imports and wraps the basis-dependent Bell decoy correlation
rules implemented in quantum_core.bell_state.evaluate_bell_decoy_correlation.
"""

from typing import Dict, List, Tuple, Optional, Union
from quantum_core.bell_state import evaluate_bell_decoy_correlation
from quantum_core.pauli_states import PauliBasis


def compute_dbev_basis_counts(
    alice_outcomes: List[int],
    bob_outcomes: List[int]
) -> Dict[str, int]:
    """
    Constructs a two-bit outcome count dictionary from aligned measurement lists:
    Format: {"<b_bob><b_alice>": count}, matching Qiskit's standard bitstring convention.
    """
    if len(alice_outcomes) != len(bob_outcomes):
        raise ValueError(
            f"Mismatched outcome lengths: Alice has {len(alice_outcomes)}, Bob has {len(bob_outcomes)}"
        )
    if len(alice_outcomes) == 0:
        raise ValueError("Outcome lists cannot be empty")

    counts: Dict[str, int] = {}
    for a, b in zip(alice_outcomes, bob_outcomes):
        key = f"{b}{a}"
        counts[key] = counts.get(key, 0) + 1
    return counts


def evaluate_dbev_for_basis(
    basis: str,
    counts_or_outcomes: Union[Dict[str, int], Tuple[List[int], List[int]]]
) -> Dict[str, float]:
    """
    Evaluates DBEV for a specific decoy basis by directly delegating to
    quantum_core.bell_state.evaluate_bell_decoy_correlation.
    
    Rules enforced by single source of truth:
        - X/X: Expected same outcomes (violations: 01, 10)
        - Z/Z: Expected same outcomes (violations: 01, 10)
        - Y/Y: Expected opposite outcomes (anti-correlated; violations: 00, 11)
    """
    if isinstance(counts_or_outcomes, tuple):
        alice_outs, bob_outs = counts_or_outcomes
        counts = compute_dbev_basis_counts(alice_outs, bob_outs)
    else:
        counts = counts_or_outcomes

    return evaluate_bell_decoy_correlation(counts=counts, basis=basis)


def run_dbev(
    basis_counts: Dict[str, Dict[str, int]]
) -> Dict[str, Union[float, int, Dict[str, Dict[str, float]]]]:
    """
    Runs full DBEV diagnostic across multiple Bell-decoy basis partitions
    (e.g. {"X": counts_X, "Y": counts_Y, "Z": counts_Z}).
    
    Returns:
        dict containing:
            - total_decoy_shots: total decoy measurements across all decoy bases
            - total_violations: total rule violations
            - e_Bell: ê_Bell = total_violations / total_decoy_shots
            - basis_breakdown: detailed results per basis
    """
    total_shots = 0
    total_violations = 0
    breakdown = {}

    for basis, counts in basis_counts.items():
        res = evaluate_bell_decoy_correlation(counts=counts, basis=basis)
        breakdown[basis] = res
        total_shots += res["total_shots"]
        total_violations += res["violations"]

    if total_shots == 0:
        raise ValueError("Total decoy shots across all bases cannot be zero")

    e_Bell = total_violations / total_shots

    return {
        "total_decoy_shots": total_shots,
        "total_violations": total_violations,
        "e_Bell": float(e_Bell),
        "basis_breakdown": breakdown
    }
