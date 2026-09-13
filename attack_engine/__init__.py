"""
QUASAR-TDS Attack Simulation Engine Package

Provides isolated, independently-invokable injectors for all 12 attack scenarios (§14):
1. RandomStateForgeryInjector
2. ZGuessInterceptResendInjector
3. XGuessInterceptResendInjector
4. YGuessInterceptResendInjector
5. EntangleAndMeasureInjector
6. BellPairReplacementInjector
7. CorrectionBitAlterationInjector
8. ReplayInjector
9. ImpersonationInjector
10. TranscriptInjectionInjector
11. CommitmentSubstitutionInjector
12. RushingAttemptInjector

Along with:
- BaseAttackInjector & TrialResult
- MonteCarloRunner & BatchAttackSummary
"""

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
from attack_engine.monte_carlo import (
    MonteCarloRunner,
    BatchAttackSummary,
)

__all__ = [
    "BaseAttackInjector",
    "TrialResult",
    "RandomStateForgeryInjector",
    "ZGuessInterceptResendInjector",
    "XGuessInterceptResendInjector",
    "YGuessInterceptResendInjector",
    "EntangleAndMeasureInjector",
    "BellPairReplacementInjector",
    "CorrectionBitAlterationInjector",
    "ReplayInjector",
    "ImpersonationInjector",
    "TranscriptInjectionInjector",
    "CommitmentSubstitutionInjector",
    "RushingAttemptInjector",
    "MonteCarloRunner",
    "BatchAttackSummary",
]
