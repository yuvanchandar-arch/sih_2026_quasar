"""
QUASAR-TDS Detection Engine Package (PB-DTF: Per-Basis Deterministic Threshold Framework + Q-TAM: Quantum Threat Attribution Matrix)

Provides:
- Statistical Hoeffding thresholds and error budgeting per §11.1
- Attack model forgery bounds and union bounds per §11.2
- Basis-dependent Bell decoy error verification (DBEV) per §9
- Honest channel calibration engine
- Acceptance rule evaluation and decision vectors per §12.1
- Strictly-ordered Quantum Threat Attribution Matrix (Q-TAM) rule engine per §12.2 and §15
"""

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

from detection_engine.calibration import (
    CalibrationEngine,
    CalibrationReport,
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

__all__ = [
    "ErrorBudget",
    "BasisThreshold",
    "ThresholdResult",
    "compute_hoeffding_slack",
    "calculate_basis_threshold",
    "calculate_thresholds",
    "compute_forgery_bound",
    "compute_union_bound_forgery_probability",
    "compute_dbev_basis_counts",
    "evaluate_dbev_for_basis",
    "run_dbev",
    "CalibrationEngine",
    "CalibrationReport",
    "EvidenceVector",
    "ExplanationRecord",
    "evaluate_acceptance",
    "Q_TAM_classify",
    "count_exceeding_pauli_bases",
]
