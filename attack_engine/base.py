"""
QUASAR-TDS Attack Engine: Base Attack Injector Interface

Defines the abstract interface for all 12 attack simulation injectors per
QUASAR-TDS_Final.md §14.
Every injector is isolated, independently invokable, and provides full metadata.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple
import numpy as np

from detection_engine.decision import EvidenceVector
from detection_engine.thresholds import ThresholdResult
from detection_engine.qtam import Q_TAM_classify


@dataclass(frozen=True)
class TrialResult:
    """Result of a single attack simulation trial."""
    attack_id: str
    attack_name: str
    evidence_vector: EvidenceVector
    verdict: str
    rule_id: str
    primary_hypothesis: str
    is_consistent_with_expected: bool
    details: Dict[str, Any]


class BaseAttackInjector(ABC):
    """
    Abstract base class for all 12 attack injectors in §14.
    """
    def __init__(
        self,
        attack_id: str,
        name: str,
        mechanism: str,
        expected_pattern: str,
        seed: Optional[int] = None
    ):
        self.attack_id = attack_id
        self.name = name
        self.mechanism = mechanism
        self.expected_pattern = expected_pattern
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    @abstractmethod
    def simulate_trial(
        self,
        thresholds: ThresholdResult,
        n_samples_per_basis: int = 500,
        **kwargs
    ) -> TrialResult:
        """
        Executes a single end-to-end trial of the attack simulation,
        returning the observed EvidenceVector and Q-TAM classification verdict.
        """
        pass
