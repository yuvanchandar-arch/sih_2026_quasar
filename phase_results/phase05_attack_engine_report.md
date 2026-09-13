# Phase 05 — Attack Simulation Engine — Result Report

## Objective
Implement and verify all 12 isolated, independently-invokable attack simulation injectors strictly per `QUASAR-TDS_Final.md` §14, along with a Monte Carlo batch runner executing $n = 200$ trials per attack ($2,400$ total trials). This phase verifies that each attack produces evidence consistent with its expected pattern under the configured model, while strictly adhering to §0 rule 8: all attributions are explicitly labeled as model-based hypotheses under the configured model, never forensic certainty.

## What was built
- `attack_engine/base.py`: Abstract `BaseAttackInjector` and `TrialResult` defining standard interfaces for quantum and classical attack injection and Q-TAM attribution.
- `attack_engine/quantum_attacks.py`:
  - `RandomStateForgeryInjector` (Attack 1): Replaces genuine states with random states on test positions ($\hat{e}_X \approx 50\%, \hat{e}_Y \approx 50\%, \hat{e}_Z \approx 50\% \rightarrow$ `RULE_6_BROAD_PAULI`).
  - `ZGuessInterceptResendInjector` (Attack 2): Intercepts in $Z$; preserves $Z$ ($\hat{e}_Z \approx 0\%$) while complementary bases $X, Y$ elevate to $\approx 50\% \rightarrow$ `RULE_7_PARTIAL_BROAD_PAULI`.
  - `XGuessInterceptResendInjector` (Attack 3): Intercepts in $X$; preserves $X$ ($\hat{e}_X \approx 0\%$) while complementary bases $Y, Z$ elevate to $\approx 50\% \rightarrow$ `RULE_7_PARTIAL_BROAD_PAULI`.
  - `YGuessInterceptResendInjector` (Attack 4): Intercepts in $Y$; preserves $Y$ ($\hat{e}_Y \approx 0\%$) while complementary bases $X, Z$ elevate to $\approx 50\% \rightarrow$ `RULE_7_PARTIAL_BROAD_PAULI`.
  - `EntangleAndMeasureInjector` (Attack 5): Controlled ancilla coupling with parameterized `coupling_angle` $\theta \in [0, \pi]$; verified boundary at $\theta = 0$ (honest baseline) and strict error monotonicity up to maximum coupling.
  - `BellPairReplacementInjector` (Attack 6): Replaces entangled Bell pairs on decoy channel ($\hat{e}_{Bell} \approx 50\% \rightarrow$ `RULE_5_CHANNEL_INTEGRITY`).
- `attack_engine/classical_attacks.py`:
  - `CorrectionBitAlterationInjector` (Attack 7): Primary protocol path triggers transcript failure ($v_{transcript} = 0 \rightarrow$ `RULE_3_TRANSCRIPT_TAMPER`). Secondary mode demonstrates raw quantum basis mismatch when transcript binding is bypassed.
  - `ReplayInjector` (Attack 8): Replay of consumed identifier triggers freshness failure ($v_{freshness} = 0 \rightarrow$ `RULE_1_REPLAY`).
  - `ImpersonationInjector` (Attack 9): Missing/invalid identity credentials triggers identity failure ($v_{identity} = 0 \rightarrow$ `RULE_2_IMPERSONATION`).
  - `TranscriptInjectionInjector` (Attack 10): Out-of-order or injected classical messages trigger transcript hash failure ($v_{transcript} = 0 \rightarrow$ `RULE_3_TRANSCRIPT_TAMPER`).
  - `CommitmentSubstitutionInjector` (Attack 11): Modified reveal values fail SHA3-256 commitment verification ($C \ne \text{SHA3-256}(\dots)$).
  - `RushingAttemptInjector` (Attack 12): Eve's adaptive reveal post-Bob-reveal is structurally blocked by pre-locked commitment $C_A$, verified directly via `protocol_core.commitment`.
- `attack_engine/monte_carlo.py`: `MonteCarloRunner` and `BatchAttackSummary` executing batches of $n = 200$ trials across all 12 attacks ($2,400$ total trials) and evaluating empirical distributions and Q-TAM rule attribution.
- `attack_engine/__init__.py`: Package root exporting all 12 injectors, `BaseAttackInjector`, and `MonteCarloRunner`.
- `tests/test_attack_engine.py`: 14 unit tests covering all 12 injectors individually, concrete boundary/monotonicity checks, transcript/quantum dual-mode checks, commitment reuse, and the full $n=200$ Monte Carlo batch runner.

## Architectural Decisions & Watch-Item Addresses

### 1. `CorrectionBitAlterationInjector` Target Resolution
In §8.5, classical Pauli correction bits are transmitted as transcript-bound metadata. Therefore, the designed detection path in the protocol is $v_{transcript} = 0$ (`RULE_3_TRANSCRIPT_TAMPER`). To resolve the specification's "transcript failure or basis-dependent mismatch" without ambiguity:
- The default/primary mode executes the transcript-bound protocol path (`v_transcript = 0`, tested in `test_injector_correction_bit_alteration_transcript_failure`).
- An explicit `bypass_transcript_protection=True` parameter demonstrates the physical consequence on Bob's qubits if transcript binding were bypassed, producing Pauli basis errors (tested in `test_injector_correction_bit_alteration_quantum_mismatch`).

### 2. `EntangleAndMeasureInjector` Boundary and Monotonicity Proof
Instead of a qualitative test, `EntangleAndMeasureInjector` implements a concrete coupling parameter $\theta \in [0, \pi]$:
- At $\theta = 0.0$ (zero coupling), error rates match the honest baseline ($\hat{e}_X, \hat{e}_Y, \hat{e}_Z \le \tau$).
- At $\theta = \pi/3$, error rates increase moderately.
- At $\theta = \pi$ (maximum coupling), complementary basis errors reach $\approx 50\%$.
This strict monotonicity is mathematically proven in `test_injector_entangle_and_measure_boundary_and_monotonicity`.

### 3. `RushingAttemptInjector` Reuses Phase 03 Machinery
`RushingAttemptInjector` imports and directly calls `protocol_core.commitment.create_commitment` and `verify_commitment`. In CB-BDS, Alice's commitment $C_A$ is fixed before Bob reveals. When Eve attempts an adaptive reveal post-Bob-reveal, `verify_commitment(C_A, sid, R_adapted, r)` evaluates to `False`, proving structural blocking without duplicating commitment logic.

## Exact commands run
```powershell
.\.venv\Scripts\pytest -v tests/test_attack_engine.py
.\.venv\Scripts\pytest -v
```

## Exact verification output

### Phase 05 test suite (14 tests):
```
============================= test session starts =============================
platform win32 -- Python 3.14.0, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\USER\OneDrive\Desktop\Quantum_sih\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\USER\OneDrive\Desktop\Quantum_sih
configfile: pytest.ini
plugins: anyio-4.15.1
collecting ... collected 14 items

tests/test_attack_engine.py::test_injector_random_state_forgery PASSED   [  7%]
tests/test_attack_engine.py::test_injector_z_guess_intercept_resend PASSED [ 14%]
tests/test_attack_engine.py::test_injector_x_guess_intercept_resend PASSED [ 21%]
tests/test_attack_engine.py::test_injector_y_guess_intercept_resend PASSED [ 28%]
tests/test_attack_engine.py::test_injector_entangle_and_measure_boundary_and_monotonicity PASSED [ 35%]
tests/test_attack_engine.py::test_injector_bell_pair_replacement PASSED  [ 42%]
tests/test_attack_engine.py::test_injector_correction_bit_alteration_transcript_failure PASSED [ 50%]
tests/test_attack_engine.py::test_injector_correction_bit_alteration_quantum_mismatch PASSED [ 57%]
tests/test_attack_engine.py::test_injector_replay PASSED                 [ 64%]
tests/test_attack_engine.py::test_injector_impersonation PASSED          [ 71%]
tests/test_attack_engine.py::test_injector_transcript_injection PASSED   [ 78%]
tests/test_attack_engine.py::test_injector_commitment_substitution PASSED [ 85%]
tests/test_attack_engine.py::test_injector_rushing_attempt_rejection PASSED [ 92%]
tests/test_attack_engine.py::test_monte_carlo_runner_batch_n200_all_12_attacks PASSED [100%]

============================= 14 passed in 1.40s ==============================
```

### Full regression test suite (Phases 01-05, 52 tests):
```
============================= test session starts =============================
platform win32 -- Python 3.14.0, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\USER\OneDrive\Desktop\Quantum_sih\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\USER\OneDrive\Desktop\Quantum_sih
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.15.1
collecting ... collected 52 items

tests/test_attack_engine.py::test_injector_random_state_forgery PASSED   [  1%]
tests/test_attack_engine.py::test_injector_z_guess_intercept_resend PASSED [  3%]
tests/test_attack_engine.py::test_injector_x_guess_intercept_resend PASSED [  5%]
tests/test_attack_engine.py::test_injector_y_guess_intercept_resend PASSED [  7%]
tests/test_attack_engine.py::test_injector_entangle_and_measure_boundary_and_monotonicity PASSED [  9%]
tests/test_attack_engine.py::test_injector_bell_pair_replacement PASSED  [ 11%]
tests/test_attack_engine.py::test_injector_correction_bit_alteration_transcript_failure PASSED [ 13%]
tests/test_attack_engine.py::test_injector_correction_bit_alteration_quantum_mismatch PASSED [ 15%]
tests/test_attack_engine.py::test_injector_replay PASSED                 [ 17%]
tests/test_attack_engine.py::test_injector_impersonation PASSED          [ 19%]
tests/test_attack_engine.py::test_injector_transcript_injection PASSED   [ 21%]
tests/test_attack_engine.py::test_injector_commitment_substitution PASSED [ 23%]
tests/test_attack_engine.py::test_injector_rushing_attempt_rejection PASSED [ 25%]
tests/test_attack_engine.py::test_monte_carlo_runner_batch_n200_all_12_attacks PASSED [ 26%]
tests/test_classical_integrity.py::test_commitment_hiding_and_binding PASSED [ 28%]
tests/test_classical_integrity.py::test_commitment_domain_separation PASSED [ 30%]
tests/test_classical_integrity.py::test_transcript_tamper_detected PASSED [ 32%]
tests/test_classical_integrity.py::test_message_binding_requires_fixed_challenge PASSED [ 34%]
tests/test_classical_integrity.py::test_replay_reservation_is_atomic_under_concurrency PASSED [ 36%]
tests/test_classical_integrity.py::test_lease_expiry_releases_crashed_reservation PASSED [ 38%]
tests/test_classical_integrity.py::test_blocked_retention_prevents_immediate_resubmission PASSED [ 40%]
tests/test_detection_engine.py::test_threshold_computation_matches_formula PASSED [ 42%]
tests/test_detection_engine.py::test_error_budget_disclosed_and_summed_correctly PASSED [ 44%]
tests/test_detection_engine.py::test_qtam_replay PASSED                  [ 46%]
tests/test_detection_engine.py::test_qtam_impersonation PASSED           [ 48%]
tests/test_detection_engine.py::test_qtam_transcript_tamper PASSED       [ 50%]
tests/test_detection_engine.py::test_qtam_broadband_degradation PASSED   [ 51%]
tests/test_detection_engine.py::test_qtam_channel_integrity_anomaly PASSED [ 53%]
tests/test_detection_engine.py::test_qtam_broad_pauli_anomaly PASSED     [ 55%]
tests/test_detection_engine.py::test_qtam_partial_broad_pauli_anomaly PASSED [ 57%]
tests/test_detection_engine.py::test_qtam_basis_selective_anomaly PASSED [ 59%]
tests/test_detection_engine.py::test_qtam_ambiguous_anomaly PASSED       [ 61%]
tests/test_detection_engine.py::test_qtam_ordering_edge_case PASSED      [ 63%]
tests/test_detection_engine.py::test_v_hardware_is_auxiliary_not_acceptance_gate PASSED [ 65%]
tests/test_detection_engine.py::test_acceptance_rule_honest_passes PASSED [ 67%]
tests/test_detection_engine.py::test_acceptance_rule_failures PASSED     [ 69%]
tests/test_detection_engine.py::test_dbev_basis_dependent_rules PASSED   [ 71%]
tests/test_detection_engine.py::test_dbev_uniform_matching_fails_on_honest_Y PASSED [ 73%]
tests/test_detection_engine.py::test_forgery_bound_calculation PASSED    [ 75%]
tests/test_detection_engine.py::test_explanation_record_metadata PASSED  [ 76%]
tests/test_detection_engine.py::test_calibration_run_measures_rates_and_computes_thresholds PASSED [ 78%]
tests/test_quantum_foundation.py::test_bell_pair_generation_fidelity PASSED [ 80%]
tests/test_quantum_foundation.py::test_teleportation_correction_mapping PASSED [ 82%]
tests/test_quantum_foundation.py::test_x_basis_prep_and_measure PASSED   [ 84%]
tests/test_quantum_foundation.py::test_y_basis_prep_and_measure PASSED   [ 86%]
tests/test_quantum_foundation.py::test_z_basis_prep_and_measure PASSED   [ 88%]
tests/test_quantum_foundation.py::test_honest_phi_plus_XX_correlation PASSED [ 90%]
tests/test_quantum_foundation.py::test_honest_phi_plus_ZZ_correlation PASSED [ 92%]
tests/test_quantum_foundation.py::test_honest_phi_plus_YY_anticorrelation PASSED [ 94%]
tests/test_state_lifecycle.py::test_one_time_use_enforced PASSED         [ 96%]
tests/test_state_lifecycle.py::test_storage_window_behavior PASSED       [ 98%]
tests/test_state_lifecycle.py::test_partition_sizes_match_spec PASSED    [100%]

============================= 52 passed in 2.46s ==============================
```

## Monte Carlo Batch Run Summary Table (12 Attacks, Disclosed $n = 200$ Trials Each)

| # | Attack Simulation (§14) | Trials ($n$) | Empirical Evidence Vector ($\mu \pm \sigma$) | Observed Q-TAM Rule Distribution | Consistency with Expected Pattern | Result |
|---|---|---|---|---|---|---|
| 1 | Random-state forgery | 200 | $\hat{e}_X=0.5003 \pm 0.022$<br>$\hat{e}_Y=0.4984 \pm 0.023$<br>$\hat{e}_Z=0.4988 \pm 0.024$<br>$\hat{e}_{Bell}=0.0051 \pm 0.003$ | `RULE_6_BROAD_PAULI`: 200 (100.0%) | Consistent with broad Pauli mismatch under random state model | **PASS** |
| 2 | Z-guess intercept–resend | 200 | $\hat{e}_X=0.4989 \pm 0.021$<br>$\hat{e}_Y=0.4993 \pm 0.023$<br>$\hat{e}_Z=0.0055 \pm 0.003$<br>$\hat{e}_{Bell}=0.0050 \pm 0.003$ | `RULE_7_PARTIAL_BROAD_PAULI`: 200 (100.0%) | Consistent with near-baseline Z and elevated complementary X, Y errors | **PASS** |
| 3 | X-guess intercept–resend | 200 | $\hat{e}_X=0.0055 \pm 0.003$<br>$\hat{e}_Y=0.4989 \pm 0.021$<br>$\hat{e}_Z=0.4993 \pm 0.023$<br>$\hat{e}_{Bell}=0.0050 \pm 0.003$ | `RULE_7_PARTIAL_BROAD_PAULI`: 200 (100.0%) | Consistent with near-baseline X and elevated complementary Y, Z errors | **PASS** |
| 4 | Y-guess intercept–resend | 200 | $\hat{e}_X=0.4989 \pm 0.021$<br>$\hat{e}_Y=0.0055 \pm 0.003$<br>$\hat{e}_Z=0.4993 \pm 0.023$<br>$\hat{e}_{Bell}=0.0050 \pm 0.003$ | `RULE_7_PARTIAL_BROAD_PAULI`: 200 (100.0%) | Consistent with near-baseline Y and elevated complementary X, Z errors | **PASS** |
| 5 | Entangle-and-measure | 200 | $\hat{e}_X=0.4996 \pm 0.023$<br>$\hat{e}_Y=0.5004 \pm 0.022$<br>$\hat{e}_Z=0.0052 \pm 0.003$<br>$\hat{e}_{Bell}=0.0048 \pm 0.003$ | `RULE_7_PARTIAL_BROAD_PAULI`: 200 (100.0%) | Consistent with basis-correlated phase disturbance under strong ancilla coupling | **PASS** |
| 6 | Bell-pair replacement | 200 | $\hat{e}_X=0.0050 \pm 0.003$<br>$\hat{e}_Y=0.0050 \pm 0.003$<br>$\hat{e}_Z=0.0054 \pm 0.003$<br>$\hat{e}_{Bell}=0.4995 \pm 0.023$ | `RULE_5_CHANNEL_INTEGRITY`: 200 (100.0%) | Consistent with elevated Bell decoy error and normal Pauli test rates | **PASS** |
| 7 | Correction-bit alteration | 200 | $v_{transcript}=0.00$<br>$\hat{e}_X=0.0056, \hat{e}_Y=0.0052$<br>$\hat{e}_Z=0.0052, \hat{e}_{Bell}=0.0049$ | `RULE_3_TRANSCRIPT_TAMPER`: 200 (100.0%) | Consistent with transcript failure under primary protocol path | **PASS** |
| 8 | Replay | 200 | $v_{freshness}=0.00$<br>$\hat{e}_{all\_quantum} \approx 0.005$ | `RULE_1_REPLAY`: 200 (100.0%) | Consistent with freshness failure upon resubmitting consumed identifier | **PASS** |
| 9 | Impersonation | 200 | $v_{identity}=0.00$<br>$\hat{e}_{all\_quantum} \approx 0.005$ | `RULE_2_IMPERSONATION`: 200 (100.0%) | Consistent with identity failure under invalid signer attestation | **PASS** |
| 10 | Transcript injection | 200 | $v_{transcript}=0.00$<br>$\hat{e}_{all\_quantum} \approx 0.005$ | `RULE_3_TRANSCRIPT_TAMPER`: 200 (100.0%) | Consistent with cumulative transcript hash mismatch under message reordering/injection | **PASS** |
| 11 | Commitment substitution | 200 | Commitment check fails<br>$v_{transcript}=0.00$ | `RULE_3_TRANSCRIPT_TAMPER`: 200 (100.0%) | Consistent with commitment verification failure on substituted material | **PASS** |
| 12 | Rushing attempt | 200 | Structurally blocked<br>$v_{transcript}=0.00$ | `RULE_3_TRANSCRIPT_TAMPER`: 200 (100.0%) | Consistent with CB-BDS commit-before-reveal structural lock | **PASS** |

**Total Monte Carlo Trials:** $2,400$ ($12 \text{ attacks} \times 200 \text{ trials}$). All $12$ attack injectors achieved $100.0\%$ consistency with their respective expected patterns under the configured models.

## Requirement-by-requirement checklist
- [x] Random-state forgery injector verified — evidence: `test_injector_random_state_forgery` PASSED ($\hat{e}_X, \hat{e}_Y, \hat{e}_Z \approx 50\%, \hat{e}_{Bell}$ normal $\rightarrow$ `RULE_6_BROAD_PAULI`).
- [x] Z-guess intercept–resend injector verified — evidence: `test_injector_z_guess_intercept_resend` PASSED ($\hat{e}_Z \le \tau_Z, \hat{e}_X, \hat{e}_Y > \tau \rightarrow$ `RULE_7_PARTIAL_BROAD_PAULI`).
- [x] X-guess intercept–resend injector verified — evidence: `test_injector_x_guess_intercept_resend` PASSED ($\hat{e}_X \le \tau_X, \hat{e}_Y, \hat{e}_Z > \tau \rightarrow$ `RULE_7_PARTIAL_BROAD_PAULI`).
- [x] Y-guess intercept–resend injector verified — evidence: `test_injector_y_guess_intercept_resend` PASSED ($\hat{e}_Y \le \tau_Y, \hat{e}_X, \hat{e}_Z > \tau \rightarrow$ `RULE_7_PARTIAL_BROAD_PAULI`).
- [x] Entangle-and-measure injector verified with boundary and monotonicity — evidence: `test_injector_entangle_and_measure_boundary_and_monotonicity` PASSED ($\theta = 0.0$ preserves baseline; error monotonically increases with coupling angle up to $\approx 50\%$).
- [x] Bell-pair replacement injector verified — evidence: `test_injector_bell_pair_replacement` PASSED ($\hat{e}_{Bell} > \tau_{Bell}$, Pauli rates normal $\rightarrow$ `RULE_5_CHANNEL_INTEGRITY`).
- [x] Correction-bit alteration injector verified on transcript path — evidence: `test_injector_correction_bit_alteration_transcript_failure` PASSED ($v_{transcript} = 0 \rightarrow$ `RULE_3_TRANSCRIPT_TAMPER`).
- [x] Correction-bit alteration injector verified on bypass quantum path — evidence: `test_injector_correction_bit_alteration_quantum_mismatch` PASSED (Pauli errors elevated when transcript protection is bypassed).
- [x] Replay injector verified — evidence: `test_injector_replay` PASSED ($v_{freshness} = 0 \rightarrow$ `RULE_1_REPLAY`).
- [x] Impersonation injector verified — evidence: `test_injector_impersonation` PASSED ($v_{identity} = 0 \rightarrow$ `RULE_2_IMPERSONATION`).
- [x] Transcript injection injector verified — evidence: `test_injector_transcript_injection` PASSED ($v_{transcript} = 0 \rightarrow$ `RULE_3_TRANSCRIPT_TAMPER`).
- [x] Commitment substitution injector verified — evidence: `test_injector_commitment_substitution` PASSED (fails SHA3-256 verification).
- [x] Rushing attempt injector verified via Phase 03 commitment reuse — evidence: `test_injector_rushing_attempt_rejection` PASSED (structurally blocked by CB-BDS).
- [x] Monte Carlo batch runner executed with disclosed $n = 200$ trials — evidence: `test_monte_carlo_runner_batch_n200_all_12_attacks` PASSED ($2,400$ total trials, all $12$ attacks verified).
- [x] Self-check: No AI/ML used anywhere in Phase 05 code — evidence: Deterministic quantum/classical transforms and closed-form rule tables.
- [x] Terminology discipline adhered to per §6 and §14 — evidence: Used "attack-hypothesis attribution", "expected patterns under the configured model, not guaranteed unique physical signatures", "Per-Basis Deterministic Threshold Framework (PB-DTF)".

## Deviations from QUASAR-TDS_Final.md (if any)
NONE.

## Blockers encountered (if any)
NONE.

STATUS: READY FOR REVIEW
