"""
QUASAR-TDS Detection Engine: Statistical Thresholds and Hoeffding Bounds

Implements calibration-aware threshold derivation and attack-model forgery bounds
strictly per QUASAR-TDS_Final.md §11.1 and §11.2.
All thresholds are derived from closed-form statistics; no hardcoded constants or ML.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
import math


@dataclass(frozen=True)
class ErrorBudget:
    """
    Error budget allocation satisfying:
    Σ_{b∈{X,Y,Z,Bell}} ( ε_b^cal + ε_b^ver ) ≤ ε_total
    """
    eps_total: float = 1e-3
    eps_cal: Dict[str, float] = field(default_factory=lambda: {
        "X": 1.25e-4,
        "Y": 1.25e-4,
        "Z": 1.25e-4,
        "Bell": 1.25e-4,
    })
    eps_ver: Dict[str, float] = field(default_factory=lambda: {
        "X": 1.25e-4,
        "Y": 1.25e-4,
        "Z": 1.25e-4,
        "Bell": 1.25e-4,
    })

    def validate(self) -> bool:
        """Validates that the sum of all individual error budgets does not exceed eps_total."""
        total_sum = sum(self.eps_cal.values()) + sum(self.eps_ver.values())
        if total_sum > self.eps_total + 1e-12:
            raise ValueError(
                f"Error budget violated: sum of components ({total_sum:.6e}) exceeds eps_total ({self.eps_total:.6e})"
            )
        return True

    @property
    def total_allocated(self) -> float:
        return sum(self.eps_cal.values()) + sum(self.eps_ver.values())

    def as_dict(self) -> Dict[str, Any]:
        return {
            "eps_total": self.eps_total,
            "eps_cal": dict(self.eps_cal),
            "eps_ver": dict(self.eps_ver)
        }


@dataclass(frozen=True)
class BasisThreshold:
    """Threshold and constituent statistical bounds for a single basis b ∈ {X, Y, Z, Bell}."""
    basis: str
    mu_hat: float
    n_cal: int
    n_ver: int
    eps_cal: float
    eps_ver: float
    delta_cal: float
    delta_ver: float
    tau: float
    bound_type: str = "one-sided upper tail bound (Hoeffding)"


@dataclass(frozen=True)
class ThresholdResult:
    """
    Complete calibration-aware threshold results across all test bases b ∈ {X, Y, Z, Bell},
    with full disclosure parameters.
    """
    thresholds: Dict[str, BasisThreshold]
    error_budget: ErrorBudget
    noise_model_description: str
    bound_type: str = "one-sided upper tail bound (Hoeffding)"

    @property
    def X(self) -> float:
        return self.thresholds["X"].tau

    @property
    def Y(self) -> float:
        return self.thresholds["Y"].tau

    @property
    def Z(self) -> float:
        return self.thresholds["Z"].tau

    @property
    def Bell(self) -> float:
        return self.thresholds["Bell"].tau

    def get_tau(self, basis: str) -> float:
        return self.thresholds[basis].tau


def compute_hoeffding_slack(eps: float, n: int) -> float:
    """
    Computes Hoeffding deviation slack term:
    δ = √( ln(1 / ε) / (2 * n) )
    
    Derived from one-sided Hoeffding inequality:
    Pr[ ê - μ ≥ δ ] ≤ exp( -2 * n * δ² ) = ε
    """
    if eps <= 0.0 or eps >= 1.0:
        raise ValueError(f"Failure budget ε must be in (0, 1), got {eps}")
    if n <= 0:
        raise ValueError(f"Sample count n must be positive, got {n}")
    return math.sqrt(math.log(1.0 / eps) / (2.0 * n))


def calculate_basis_threshold(
    basis: str,
    mu_hat: float,
    n_cal: int,
    n_ver: int,
    eps_cal: float,
    eps_ver: float
) -> BasisThreshold:
    """
    Computes τ_b = μ̂_b + δ_b^cal + δ_b^ver per §11.1.
    """
    if not (0.0 <= mu_hat <= 1.0):
        raise ValueError(f"Observed error rate μ̂ must be in [0, 1], got {mu_hat}")

    delta_cal = compute_hoeffding_slack(eps_cal, n_cal)
    delta_ver = compute_hoeffding_slack(eps_ver, n_ver)
    tau = mu_hat + delta_cal + delta_ver

    return BasisThreshold(
        basis=basis,
        mu_hat=float(mu_hat),
        n_cal=n_cal,
        n_ver=n_ver,
        eps_cal=float(eps_cal),
        eps_ver=float(eps_ver),
        delta_cal=float(delta_cal),
        delta_ver=float(delta_ver),
        tau=float(tau),
        bound_type="one-sided upper tail bound (Hoeffding)"
    )


def calculate_thresholds(
    mu_hats: Dict[str, float],
    n_cal: Dict[str, int],
    n_ver: Dict[str, int],
    budget: Optional[ErrorBudget] = None,
    noise_model_description: str = "Honest channel (ideal simulator)"
) -> ThresholdResult:
    """
    Derives calibration-aware thresholds for all bases b ∈ {X, Y, Z, Bell}
    with strict disclosure of budgets and sample counts per §11.1.
    """
    if budget is None:
        budget = ErrorBudget()
    budget.validate()

    bases = ["X", "Y", "Z", "Bell"]
    thresholds = {}
    for b in bases:
        if b not in mu_hats:
            raise KeyError(f"Missing empirical rate μ̂ for basis {b}")
        if b not in n_cal:
            raise KeyError(f"Missing calibration sample count n_cal for basis {b}")
        if b not in n_ver:
            raise KeyError(f"Missing verification sample count n_ver for basis {b}")

        thresholds[b] = calculate_basis_threshold(
            basis=b,
            mu_hat=mu_hats[b],
            n_cal=n_cal[b],
            n_ver=n_ver[b],
            eps_cal=budget.eps_cal[b],
            eps_ver=budget.eps_ver[b]
        )

    return ThresholdResult(
        thresholds=thresholds,
        error_budget=budget,
        noise_model_description=noise_model_description
    )


def compute_forgery_bound(
    mu_forge: float,
    tau: float,
    n_ver: int
) -> float:
    """
    Computes Hoeffding upper bound on forgery acceptance probability for a single test b:
    Pr[ ê_b ≤ τ_b ] ≤ exp( -2 * n_b * (μ_b^forge - τ_b)² )
    valid when μ_b^forge > τ_b (§11.2).
    """
    if mu_forge <= tau:
        return 1.0  # Hoeffding bound does not bound the lower tail when attack rate is below threshold
    gap = mu_forge - tau
    exponent = -2.0 * n_ver * (gap ** 2)
    return float(math.exp(exponent))


def compute_union_bound_forgery_probability(
    attack_model_rates: Dict[str, float],
    threshold_result: ThresholdResult,
    n_ver: Dict[str, int]
) -> float:
    """
    Computes the conservative union-bound policy (§11.2):
    Pr[false acceptance] ≤ Σ_{b∈{X,Y,Z,Bell}} Pr[test b passes under the attack model]
    """
    total_bound = 0.0
    for b, mu_forge in attack_model_rates.items():
        tau = threshold_result.get_tau(b)
        n = n_ver[b]
        bound_b = compute_forgery_bound(mu_forge, tau, n)
        total_bound += bound_b
    return min(1.0, total_bound)
