"""
QUASAR-TDS Attack Engine: Monte Carlo Batch Runner

Executes batches of n ≥ 200 trials across each of the 12 attack injectors
per QUASAR-TDS_Final.md §14.
Aggregates empirical evidence-vector distributions and Q-TAM attribution labels.
Explicitly labels all outputs as model-based hypotheses, not forensic certainty.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import numpy as np

from attack_engine.base import BaseAttackInjector, TrialResult
from attack_engine.quantum_attacks import (
    RandomStateForgeryInjector,
    ZGuessInterceptResendInjector,
    XGuessInterceptResendInjector,
    YGuessInterceptResendInjector,
    EntangleAndMeasureInjector,
    BellPairReplacementInjector,
)
from attack_engine.classical_attacks import (
    CorrectionBitAlterationInjector,
    ReplayInjector,
    ImpersonationInjector,
    TranscriptInjectionInjector,
    CommitmentSubstitutionInjector,
    RushingAttemptInjector,
)
from detection_engine.thresholds import ThresholdResult


@dataclass(frozen=True)
class BatchAttackSummary:
    """Summary of Monte Carlo batch run for a single attack injector."""
    attack_id: str
    attack_name: str
    n_trials: int
    mean_e_X: float
    std_e_X: float
    mean_e_Y: float
    std_e_Y: float
    mean_e_Z: float
    std_e_Z: float
    mean_e_Bell: float
    std_e_Bell: float
    v_transcript_pass_rate: float
    v_freshness_pass_rate: float
    v_identity_pass_rate: float
    rule_label_distribution: Dict[str, int]
    verdict_distribution: Dict[str, int]
    consistency_rate: float
    is_consistent: bool
    disclaimer: str = "Expected pattern under configured model, not forensic certainty"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attack_id": self.attack_id,
            "attack_name": self.name if hasattr(self, "name") else self.attack_name,
            "n_trials": self.n_trials,
            "mean_evidence": {
                "e_X": self.mean_e_X,
                "e_Y": self.mean_e_Y,
                "e_Z": self.mean_e_Z,
                "e_Bell": self.mean_e_Bell
            },
            "rule_label_distribution": self.rule_label_distribution,
            "verdict_distribution": self.verdict_distribution,
            "consistency_rate": self.consistency_rate,
            "is_consistent": self.is_consistent,
            "disclaimer": self.disclaimer
        }


class MonteCarloRunner:
    """
    Monte Carlo batch runner executing configurable n trials across attack injectors.
    """
    def __init__(self, seed: Optional[int] = 42):
        self.seed = seed

    def run_attack_batch(
        self,
        injector: BaseAttackInjector,
        thresholds: ThresholdResult,
        n_trials: int = 200,
        **kwargs
    ) -> BatchAttackSummary:
        """
        Runs n_trials for a specific injector and aggregates observed distributions.
        """
        if n_trials < 1:
            raise ValueError(f"n_trials must be at least 1, got {n_trials}")

        e_Xs = []
        e_Ys = []
        e_Zs = []
        e_Bells = []
        v_transcripts = []
        v_freshnesses = []
        v_identities = []
        rule_labels: Dict[str, int] = {}
        verdicts: Dict[str, int] = {}
        consistent_count = 0

        for _ in range(n_trials):
            res: TrialResult = injector.simulate_trial(thresholds, **kwargs)
            d = res.evidence_vector
            e_Xs.append(d.e_X)
            e_Ys.append(d.e_Y)
            e_Zs.append(d.e_Z)
            e_Bells.append(d.e_Bell)
            v_transcripts.append(d.v_transcript)
            v_freshnesses.append(d.v_freshness)
            v_identities.append(d.v_identity)

            rule_labels[res.rule_id] = rule_labels.get(res.rule_id, 0) + 1
            verdicts[res.verdict] = verdicts.get(res.verdict, 0) + 1
            if res.is_consistent_with_expected:
                consistent_count += 1

        consistency_rate = consistent_count / n_trials

        return BatchAttackSummary(
            attack_id=injector.attack_id,
            attack_name=injector.name,
            n_trials=n_trials,
            mean_e_X=float(np.mean(e_Xs)),
            std_e_X=float(np.std(e_Xs)),
            mean_e_Y=float(np.mean(e_Ys)),
            std_e_Y=float(np.std(e_Ys)),
            mean_e_Z=float(np.mean(e_Zs)),
            std_e_Z=float(np.std(e_Zs)),
            mean_e_Bell=float(np.mean(e_Bells)),
            std_e_Bell=float(np.std(e_Bells)),
            v_transcript_pass_rate=float(np.mean(v_transcripts)),
            v_freshness_pass_rate=float(np.mean(v_freshnesses)),
            v_identity_pass_rate=float(np.mean(v_identities)),
            rule_label_distribution=rule_labels,
            verdict_distribution=verdicts,
            consistency_rate=consistency_rate,
            is_consistent=(consistency_rate >= 0.95)
        )

    def run_all_12_attacks(
        self,
        thresholds: ThresholdResult,
        n_trials_per_attack: int = 200
    ) -> List[BatchAttackSummary]:
        """
        Executes n_trials_per_attack across all 12 isolated attack injectors.
        """
        injectors = [
            RandomStateForgeryInjector(seed=self.seed),
            ZGuessInterceptResendInjector(seed=self.seed),
            XGuessInterceptResendInjector(seed=self.seed),
            YGuessInterceptResendInjector(seed=self.seed),
            EntangleAndMeasureInjector(seed=self.seed),
            BellPairReplacementInjector(seed=self.seed),
            CorrectionBitAlterationInjector(seed=self.seed),
            ReplayInjector(seed=self.seed),
            ImpersonationInjector(seed=self.seed),
            TranscriptInjectionInjector(seed=self.seed),
            CommitmentSubstitutionInjector(seed=self.seed),
            RushingAttemptInjector(seed=self.seed),
        ]

        summaries = []
        for inj in injectors:
            summary = self.run_attack_batch(inj, thresholds, n_trials=n_trials_per_attack)
            summaries.append(summary)

        return summaries
