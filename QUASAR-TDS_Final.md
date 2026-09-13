# QUASAR-TDS
## Quantum Unified Statistical Attack-Hypothesis Attribution & Response

### A Threat-Detection and Verification-Monitoring Layer for Teleportation-Based Quantum Digital Signatures

**Smart India Hackathon 2026 | Problem Statement ID: SIH26141**
**Theme:** Quantum-Inspired Cybersecurity | **Category:** Software
**Document status:** Implementation-ready technical specification. Describes a software prototype and does not claim a complete formal proof of QDS unforgeability, non-repudiation, or transferability.

---

## 1. Executive Summary

QUASAR-TDS is a deterministic, non-AI/ML verification and security-monitoring layer built around a simulated teleportation-based Quantum Digital Signature (QDS) protocol. It addresses SIH26141 by simulating Bell-state entanglement and quantum teleportation for QDS state-material preparation and distribution, applying Pauli corrections and projective measurements for signature verification, and producing rule-based, threshold-driven attack **hypotheses** for forgery, impersonation, replay, transcript manipulation, and quantum-channel-manipulation scenarios.

QUASAR-TDS is **not** a new QDS protocol, a certificate-authority replacement, or a TLS implementation. It is a monitoring and explanation layer around a precisely defined prototype QDS workflow. Its contribution is the integrated software architecture and evaluation methodology, not the invention of any single ingredient in isolation.

The framework contains six integrated mechanisms:

1. **PB-DTF — Per-Basis Deterministic Threshold Framework:** independent, calibration-aware statistical thresholds for X, Y, Z, and Bell-decoy statistics.
2. **Q-TAM — Quantum Threat Attribution Matrix:** a deterministic rule engine producing `ACCEPT`, `REJECT`, or `ALERT` with a primary hypothesis, an alternative explanation, and a full evidence record.
3. **CB-BDS — Commitment-Bound Basis and Decoy Selection:** domain-separated SHA3-256 commit-before-reveal for challenge and test-position selection.
4. **TC-QCB — Transcript-Chained Quantum–Classical Binding:** a transcript hash chained over classical control messages and a defined classical encoding of quantum events.
5. **DBEV — Decoy Bell-Pair Entanglement Verification:** a channel-integrity diagnostic using basis-dependent Bell correlations.
6. **HAIB — Hardware-Attested Identity Binding (optional):** a classical identity layer contributing only identity evidence, never information-theoretic security.

The system deliberately avoids machine learning end-to-end. Every decision comes from cryptographic checks, closed-form statistical estimates, threshold tests, and auditable rule tables.

---

## 2. Problem Statement Restated

| Field | Content |
|---|---|
| ID | SIH26141 |
| Ask | A quantum-inspired cyber-threat detection framework for teleportation-based QDS |
| Required threat scenarios | Forgery, impersonation, replay, unauthorized verification, quantum-channel manipulation |
| Required mechanisms | Pauli eigenstates, projective measurements, statistical thresholds |
| Prohibited approach | Artificial intelligence and machine learning |
| Security requirement | Preserve the underlying QDS protocol's information-theoretic security assumptions, without incorrectly extending them to classical components |
| Expected deliverables | Mathematical modelling, attack simulation, security analysis, performance evaluation |

QUASAR-TDS addresses this as a **verification-monitoring layer**: it supplies a minimal teleportation-based QDS simulation so that controlled attacks can be injected and observed through both quantum-statistical and classical-control evidence.

---

## 3. Scope and Boundaries

### 3.1 In scope
Bell-pair generation and teleportation simulation; known Pauli-eigenstate QDS key-material distribution; one-time-use quantum positions; X/Y/Z basis preparation and measurement; Bell-decoy correlation testing; commitment-bound challenge generation; message-binding metadata; transcript integrity and freshness checks; replay state management; rule-based statistical verification; controlled attack injection; performance and false-acceptance evaluation.

### 3.2 Out of scope for the MVP
A production-grade QDS protocol proof; a complete proof of non-repudiation or transferability; physical quantum-hardware deployment; quantum side-channel protection on real hardware; full arbitrator replacement; denial-of-service protection; anonymous routing and traffic-analysis resistance; a real email/TLS/certificate-authority system; machine-learning classification of any kind.

---

## 4. Related Work and Gap

| Prior work | Main contribution | Gap relative to QUASAR-TDS |
|---|---|---|
| Lu et al. (2022), controlled-teleportation QDS | Entangled channels, decoys, arbitrated verification | No integrated runtime monitoring and attack-hypothesis engine |
| Collins et al. (2014), coherent-state QDS | Authentication and verification thresholds | Not teleportation-based; primarily an aggregate threshold |
| Donaldson et al. (2021), QDS with QKD components | Forgery bounds with QKD-derived material | Requires QKD infrastructure; no teleportation-specific detector |
| Yin et al. (2017), measurement-device-independent QDS | Detector-side-channel resistance | Relay-oriented model, not a monitoring layer |
| Continuous-variable QDS research | CV signatures and teleportation approaches | Not a discrete Pauli-eigenstate monitoring framework |
| Grasselli et al. (2025), practical QDS | Protocol hardening, parameter optimization | Not a runtime threat-monitoring software framework |
| Entanglement-based network QDS | Finite-size, network-oriented analysis | Does not present an integrated detector architecture |
| QYMail-TEF | Commit-reveal, transcript binding, replay state, hardware-attestation patterns | Secure-email key agreement, not teleportation-based QDS |

The defensible gap being addressed is the **integration** of: per-Pauli-basis and Bell-decoy evidence; a deterministic attack-hypothesis engine; commitment-bound QDS challenge selection; quantum–classical transcript binding; atomic replay handling; and a complete, benchmarked, non-ML software framework. None of these ingredients is claimed to be individually unprecedented.

---

## 5. Contribution Statement

QUASAR-TDS presents a deterministic, non-ML monitoring and verification layer for a teleportation-based QDS prototype whose state-material lifecycle, message-binding construction, Bell-decoy model, threshold model, and attack interface are all explicitly specified. The system combines: Bell-state and teleportation simulation; known Pauli-eigenstate material; one-time-use quantum positions; X/Y/Z projective measurements; correct Bell-decoy correlation signs; commitment-bound test selection; message-binding metadata; quantum–classical transcript hashing; atomic freshness and replay state; calibration-aware statistical thresholds; and deterministic attack hypotheses with an explicit ambiguous-alert state.

The project does not claim to prove complete QDS unforgeability, non-repudiation, transferability, or exact attacker identification.

---

## 6. Terminology

| Term | Meaning |
|---|---|
| Teleportation-based QDS state-material distribution | Transfer of known-to-Alice Pauli-eigenstate material via teleportation — not CA-style public-key distribution |
| QDS key material | Quantum states plus the associated classical reference data used by the prototype |
| Attack-hypothesis attribution | A rule-matched explanation, not certainty about the physical attacker |
| Rule-label agreement | Agreement between the rule engine's output and an injected controlled scenario |
| Bell-decoy channel-integrity diagnostic | A statistical test of expected Bell correlations |
| Replay ledger | The atomic state machine used for freshness and duplicate control |
| Information-theoretic claim | A claim scoped strictly to the assumptions of the underlying quantum protocol |

---

## 7. System Architecture

```
                        QUASAR-TDS PLATFORM

  Identity & HAIB (optional) <---> Session Controller
                                    session_id, nonce, roles
                                          |
                                          v
                          Commitment-Bound Challenge Layer
                          basis, decoy, test/auth partition
                                          |
                                          v
                     Teleportation-Based QDS State-Material Layer
                     Bell pairs, teleportation, Pauli correction,
                          X/Y/Z states, one-time-use qubits
                                          |
                                          v
                          Classical Event Transcript Layer
                     transcript hash over encoded protocol events
                                          |
                        +-----------------+------------------+
                        |                                    |
                        v                                    v
                Attack Injection Engine                Replay Ledger
             forgery, replay, noise,                atomic reserve, lease,
           impersonation, tampering                    accept / block
                        |                                    |
                        +-----------------+------------------+
                                          v
                          PB-DTF Statistical Engine
                        e_X, e_Y, e_Z, e_Bell, thresholds
                                          |
                                          v
                          Q-TAM Hypothesis Engine
                          ACCEPT / REJECT / ALERT
                                          |
                                          v
                          Explanation and Audit Record
```

### 7.1 Authoritative execution flow

```
1.  Validate input and message format.
2.  Validate identity and authorization if HAIB is enabled.
3.  Parse the submitted session and signature identifiers.
4.  Reserve the identifier atomically in the replay ledger.
5.  Validate the transcript prefix.
6.  Exchange and verify CB-BDS commitments.
7.  Reveal challenge material and derive the final challenge.
8.  Prepare and teleport one-time-use QDS state material.
9.  Run the Bell-decoy channel-integrity diagnostic.
10. Construct the message-binding value and signature declaration.
11. Apply attack injection if this is a test run.
12. Perform Pauli-basis verification.
13. Calculate calibration-aware thresholds.
14. Evaluate the acceptance rule.
15. If necessary, run Q-TAM classification.
16. Finalize the replay state and emit the explanation record.
```

---

## 8. Protocol Definition and Threat Model

### 8.1 Participants
Alice — signer and preparer of QDS state material. Bob — intended verifier. Optional Charlie — a future independent verifier, not implemented in the MVP. Adversary — injects quantum or classical attacks per the configured model. Monitoring engine — computes evidence and decisions.

### 8.2 Adversary capabilities
The prototype models an adversary that may: observe quantum-channel traffic; intercept, resend, attenuate, or depolarize transmitted states; attempt entangle-and-measure behaviour; alter classical Pauli-correction messages; reorder, duplicate, delete, or inject classical messages; replay previously valid signatures; attempt identity impersonation; attempt to bias challenge selection through rushing; submit invalid commitments.

The prototype does **not** model physical hardware side channels, host compromise, denial-of-service flooding, or real-device detector attacks.

### 8.3 Known-state Model A
Alice prepares a sequence of `N` qubits, each independently drawn from the Pauli eigenstates `{|0⟩,|1⟩,|+⟩,|−⟩,|+i⟩,|−i⟩}`. Alice stores only the classical description `K_A = {(b_i, x_i)}_{i=1}^N`, where `b_i ∈ {X,Y,Z}` and `x_i` is the corresponding eigenvalue. Alice does **not** retain a physical copy of the teleported qubit — teleportation destroys the original after the Bell measurement, and no-cloning is never violated.

### 8.4 State-material lifecycle
The session material is partitioned as:

```
N = N_D + N_T + N_M

N_D — decoy positions, used only by DBEV.
N_T — challenge-test positions, used by the current verification.
N_M — reserved authentication-material positions. In the MVP these positions are
       reserved and tracked but are NOT claimed to implement a complete,
       independent QDS authentication construction.
```

**Recommended MVP simplification:** implement `N = N_D + N_T` only, and omit `N_M` until a concrete authentication construction is designed and added.

All positions are one-time-use. Once a position is measured, it is discarded. A new, independent signature session requires a fresh teleportation-based distribution round — this bounds the number of challenge queries a verifier can make against a single distribution round.

### 8.5 Teleportation phase
For each position:

1. Alice and Bob share `|Φ+⟩`.
2. Alice performs a Bell-basis measurement on the prepared qubit and her half of the pair.
3. Alice obtains correction bits `(c0, c1)`.
4. Alice sends the correction bits with transcript-bound classical metadata.
5. Bob applies the simulator-validated Pauli correction.
6. Bob stores the corrected qubit until the challenge phase.
7. Bob measures it exactly once, according to its assigned role.

| Bell-measurement bits `(c0,c1)` | Correction (illustrative — validate against the simulator convention) |
|---|---|
| 00 | `I` |
| 01 | `X` |
| 10 | `Z` |
| 11 | `XZ`, equivalent to `ZX` up to global phase |

### 8.6 Commitment-bound challenge generation
Alice and Bob generate challenge material `R_A, R_B`, including the position partition and basis assignments:

```
C_A = SHA3-256( "QDS-CB-BDS" ‖ sid ‖ R_A ‖ r_A )
C_B = SHA3-256( "QDS-CB-BDS" ‖ sid ‖ R_B ‖ r_B )
```

Sequence: (1) Alice sends `C_A`. (2) Bob sends `C_B`. (3) Both commitments are fixed. (4) Alice reveals `R_A, r_A`. (5) Bob reveals `R_B, r_B`. (6) Both verify the commitments. (7) The final challenge is derived:

```
Challenge = SHA3-256( R_A ‖ R_B ‖ sid ‖ TH )
```

This construction is computationally hiding and binding under the hash assumptions used by the prototype. It is **not** claimed to provide a quantum bit-commitment theorem.

### 8.7 Message-binding construction
After the challenge is fixed, define:

```
M_c = SHA3-256( "QDS-MESSAGE" ‖ m ‖ sid ‖ Challenge ‖ TH )
```

The prototype signature object is:

```
Sig_A(m) = ( M_c, sid, Challenge, declared_outcomes_on_N_T, TH_i )
```

The declaration is checked against Bob's one-time measurements of the challenge-selected positions.

**Scope limitation, stated explicitly:** `M_c` binds the message to the session and challenge, but a hash alone does **not** provide signer authentication. If classical signer authentication is required, the optional HAIB layer may sign the declaration (e.g. `σ_A = Sign_{sk_A}(M_c ‖ declared_outcomes_on_N_T ‖ TH_i)`) using a classical or post-quantum signature scheme. Such authentication is computational, not information-theoretic, and is reported separately from the quantum evidence.

### 8.8 Open QDS security items
The prototype does not provide complete formal proofs of: unforgeability; non-repudiation; transferability; multi-verifier consistency; arbitrator-free dispute resolution. These remain future research items requiring a full QDS security construction and proof (in the style of, e.g., Collins et al. or Gottesman–Chuang-type analyses).

---

## 9. Bell-Decoy Correlation Model

For the prepared Bell state `|Φ+⟩ = (|00⟩+|11⟩)/√2`:

```
⟨X⊗X⟩ = +1        ⟨Z⊗Z⟩ = +1        ⟨Y⊗Y⟩ = −1
```

| Decoy basis | Expected result |
|---|---|
| X/X | Same outcomes |
| Z/Z | Same outcomes |
| Y/Y | Opposite outcomes |

```
ê_Bell = (# correlation-rule violations, per the basis-dependent rule above) / n_Bell
```

A uniform "outcomes must match" rule is **incorrect for Y/Y decoys** and must fail the unit-test suite if implemented that way. DBEV is a channel-integrity diagnostic — it does not replace dispute resolution, transferability enforcement, identity authentication, or the other functions of a trusted arbitrator.

---

## 10. Measurement Model

- **Z basis:** measure directly in the computational basis.
- **X basis:** prepare with `H`; measure with `H` followed by a computational-basis measurement.
- **Y basis:** prepare using `H` then `S`; measure using `S†` then `H` followed by a computational-basis measurement. Gate ordering must match the target simulator's convention.

Required unit tests: X-basis eigenstate preparation and measurement; Y-basis eigenstate preparation and measurement; Z-basis eigenstate preparation and measurement; Pauli correction mappings; Bell-state correlation signs (including the honest Y/Y anti-correlation).

---

## 11. Statistical Detection Engine

### 11.1 Calibration-aware threshold
Let `μ̂_b` be the honest-channel rate measured during calibration, for `b ∈ {X,Y,Z,Bell}`. Define:

```
τ_b = μ̂_b + δ_b^cal + δ_b^ver
```

For calibration sample size `n_b^cal` and calibration failure budget `ε_b^cal`:

```
δ_b^cal = √( ln(1/ε_b^cal) / (2 n_b^cal) )
```

For verification sample size `n_b^ver` and verification failure budget `ε_b^ver`:

```
δ_b^ver = √( ln(1/ε_b^ver) / (2 n_b^ver) )
```

Every experiment must disclose: calibration sample count; verification sample count; honest noise model; calibration failure budget; verification failure budget; total error budget; and whether the bound is one-sided or two-sided. The default allocation must satisfy:

```
Σ_{b∈{X,Y,Z,Bell}} ( ε_b^cal + ε_b^ver )  ≤  ε_total
```

(calibration and verification budgets are not double-counted if they share the same underlying data).

### 11.2 Forgery bound
For a defined attack model with modelled rate `μ_b^forge > τ_b`, Hoeffding gives:

```
Pr[ ê_b ≤ τ_b ]  ≤  exp( −2 n_b (μ_b^forge − τ_b)² )
```

This is an attack-model-specific upper bound, not a universal forgery probability. For combining tests, QUASAR-TDS uses the **conservative union-bound policy by default**:

```
Pr[false acceptance] ≤ Σ_{b∈{X,Y,Z,Bell}} Pr[test b passes under the attack model]
```

A product bound may be reported only when independence across tests is explicitly justified for that attack model.

---

## 12. Decision Vector and Q-TAM

### 12.1 Acceptance rule
```
D = ( ê_X, ê_Y, ê_Z, ê_Bell, v_transcript, v_freshness, v_identity, v_hardware )

Accept  ⇔  ê_X ≤ τ_X  AND  ê_Y ≤ τ_Y  AND  ê_Z ≤ τ_Z  AND  ê_Bell ≤ τ_Bell
           AND v_transcript = 1  AND v_freshness = 1  AND v_identity = 1
```

`v_hardware` is auxiliary evidence unless the deployment configuration explicitly requires it as a gate. The acceptance rule is evaluated first; Q-TAM runs only when acceptance fails.

### 12.2 Q-TAM rule order
```
1. Freshness failure                                 → REJECT: Replay
2. Identity failure                                  → REJECT: Impersonation suspicion
3. Transcript failure                                → REJECT: Control-plane tampering / reordering / injection
4. All Pauli tests AND Bell test elevated             → ALERT: Broadband degradation; re-run DBEV
5. Bell elevated, all Pauli tests within threshold    → ALERT: Channel-integrity anomaly
6. All three Pauli tests elevated, Bell normal        → ALERT: Broad Pauli-basis anomaly
7. Two Pauli tests elevated, Bell normal              → ALERT: Partial broad Pauli anomaly
8. Exactly one Pauli test elevated                    → ALERT: Basis-selective signature anomaly
9. Otherwise                                          → ALERT: Ambiguous anomaly
```

Every result includes: a primary hypothesis; an alternative explanation; evidence values; sample sizes; thresholds; a rule identifier; and an explicit non-ML "rule-based hypothesis" evidence mode. The output is always a **model-based hypothesis**, never forensic certainty.

---

## 13. Replay State Machine

```
ABSENT --reserve--> RESERVED --accept--> ACCEPTED
                        |                    |
                        |                    +--resubmission--> REPLAY
                        |
                        +--fail--> BLOCKED
                        |
                        +--lease expiry--> RELEASED

RESERVED + concurrent request for the same identifier --> DUPLICATE_IN_PROGRESS
```

Rules: accepted identifiers are permanently consumed; rejected identifiers enter a bounded `BLOCKED` retention window rather than being immediately released for reuse; every reservation carries a lease timeout, so a crashed verifier cannot permanently lock a session; the verifier reserves the **submitted** identifier, never a freshly generated local one; `sid`, `signature_id`, and `nonce` are parsed from the submitted signature object before reservation is attempted.

---

## 14. Attack Simulation Engine

| Attack simulation | Mechanism | Expected evidence under the configured model |
|---|---|---|
| Random-state forgery | Replace genuine states with random states | Broad Pauli mismatch; model-dependent Bell effect |
| Z-guess intercept–resend | Measure and resend using a Z guess | Near-baseline Z; elevated complementary-basis errors under the selected encoding |
| X-guess intercept–resend | Measure and resend using an X guess | Near-baseline X; elevated complementary-basis errors |
| Y-guess intercept–resend | Measure and resend using a Y guess | Near-baseline Y; elevated complementary-basis errors |
| Entangle-and-measure | Couple an ancilla and measure later | Model-dependent Pauli and Bell deviations |
| Bell-pair replacement | Replace or degrade the entangled channel | Elevated Bell-decoy error |
| Correction-bit alteration | Modify classical Pauli-correction metadata | Transcript failure or basis-dependent mismatch |
| Replay | Resubmit a previously valid object | Freshness failure |
| Impersonation | Use absent or invalid identity credentials | Identity failure |
| Transcript injection | Reorder or insert control messages | Transcript failure |
| Commitment substitution | Replace a committed value | Commitment verification failure |
| Rushing attempt | Adapt after observing an unrevealed contribution | Structurally blocked by CB-BDS |

All fingerprints are **expected patterns under the configured model**, not guaranteed unique physical signatures.

---

## 15. Verification Pseudocode

```text
FUNCTION verify_submitted_signature(submitted_signature, message, attack_model=None):

    validate_message_format(message)
    sid, signature_id, nonce = parse_identifiers(submitted_signature)

    v_identity = verify_identity_if_enabled(submitted_signature)
    IF v_identity == 0:
        RETURN REJECT("Impersonation suspicion")

    lease = replay_ledger.reserve(sid, signature_id, nonce)
    IF lease is None:
        RETURN REJECT_OR_DUPLICATE(classify_replay_state(sid, signature_id, nonce))

    TH = initialize_transcript(sid)
    v_transcript = validate_transcript_prefix(submitted_signature, TH)
    IF v_transcript == 0:
        replay_ledger.block_for_retention(lease)
        RETURN REJECT("Control-plane tampering")

    CA, CB = exchange_commitments()
    RA, rA, RB, rB = reveal_commitments()
    IF NOT verify_commitment(CA, RA, rA, sid) OR NOT verify_commitment(CB, RB, rB, sid):
        replay_ledger.block_for_retention(lease)
        RETURN REJECT("Commitment substitution")

    Challenge = SHA3_256("QDS-CHALLENGE" || RA || RB || sid || TH)

    material = prepare_one_time_use_material(N)
    teleported_register = teleport_and_store(material, TH)

    e_Bell = run_DBEV(
        teleported_register.decoy_positions,
        Challenge,
        correlation_signs_for_prepared_bell_state
    )

    M_c = SHA3_256("QDS-MESSAGE" || message || sid || Challenge || TH)
    signature = load_or_generate_bound_declaration(submitted_signature, M_c, Challenge)

    IF attack_model is not None:
        signature = attack_model.inject(signature, teleported_register)

    e_X, e_Y, e_Z, TH = verify_test_positions(
        signature, teleported_register.test_positions, Challenge
    )

    thresholds = calculate_calibration_aware_thresholds()

    D = EvidenceVector(e_X, e_Y, e_Z, e_Bell,
                        v_transcript, freshness=1, v_identity,
                        v_hardware=optional_hardware_flag())

    IF accept_rule(D, thresholds):
        replay_ledger.commit(lease)
        RETURN ACCEPT, D, explanation(D, thresholds)

    replay_ledger.block_for_retention(lease)
    result = Q_TAM_classify(D, thresholds)
    RETURN result, D, explanation(D, thresholds)
```

```text
FUNCTION Q_TAM_classify(D, thresholds):
    IF D.freshness == 0:  RETURN REJECT("Replay")
    IF D.identity == 0:   RETURN REJECT("Impersonation suspicion")
    IF D.transcript == 0: RETURN REJECT("Control-plane tampering / reordering / injection")

    all_pauli = (D.e_X > thresholds.X) AND (D.e_Y > thresholds.Y) AND (D.e_Z > thresholds.Z)
    bell = D.e_Bell > thresholds.Bell
    pauli_count = count_exceeding_pauli_bases(D, thresholds)

    IF all_pauli AND bell:
        RETURN ALERT("Broadband degradation", alternative="common noise or simulator instability")
    IF bell AND pauli_count == 0:
        RETURN ALERT("Channel-integrity anomaly", alternative="elevated simulator or hardware noise")
    IF all_pauli AND NOT bell:
        RETURN ALERT("Broad Pauli-basis anomaly", alternative="correlated calibration drift")
    IF pauli_count == 2 AND NOT bell:
        RETURN ALERT("Partial broad Pauli anomaly",
                     alternative="basis-correlated noise or entangle-and-measure attempt")
    IF pauli_count == 1:
        RETURN ALERT("Basis-selective signature anomaly",
                     alternative="consistent with, but not proof of, intercept-resend")

    RETURN ALERT("Ambiguous anomaly", alternative="manual audit required")
```

---

## 16. Software Stack

| Layer | Components | Suggested technology |
|---|---|---|
| Quantum simulation | Bell states, teleportation, Pauli corrections, X/Y/Z measurement, noise | Python, Qiskit Aer or Cirq |
| Statistics | Mismatch rates, calibration, Hoeffding thresholds | NumPy, SciPy |
| Control plane | SHA3, HMAC, AEAD, transcript hash | Python standard library, PyCryptodome |
| Identity | Optional classical or PQ attestation | RSA/ECDSA or ML-DSA bindings |
| Replay ledger | Reservation, lease, acceptance, blocking | SQLite or Redis |
| Attack engine | Circuit/protocol transforms, Monte Carlo | Python, pytest |
| Rule engine | PB-DTF and Q-TAM | Pure Python |
| API | Sessions and benchmarks | FastAPI |
| Dashboard | Circuit and evidence visualisation | React, Plotly, or Recharts |
| Deployment | Reproducible demo | Docker, docker-compose |
| Classical formal model | Commitments, transcript, replay | Optional ProVerif or Tamarin |

The entire stack is plain, file-based Python/JavaScript with no external model weights or GPU dependency, so it is directly buildable inside **Antigravity IDE**'s agentic "write → run tests → iterate" workflow — the quantum-simulation, statistics, and rule-engine modules as testable Python packages, and the FastAPI/React demo layer as a conventional multi-file scaffold the IDE's agent can generate and run end-to-end.

---

## 17. Performance Evaluation

### 17.1 Minimum experiment matrix
**Honest baselines:** ideal simulator; bit-flip noise; phase-flip noise; depolarizing noise; measurement error; calibration drift.

**Attack scenarios:** random forged states; X-, Y-, and Z-guess intercept–resend; Bell-pair replacement; Pauli-correction alteration; transcript reordering; replay; unauthorized verifier; commitment substitution; rushing attempt.

### 17.2 Metrics
Honest acceptance rate; false-rejection rate; false-acceptance rate per attack model; replay rejection rate; transcript-tamper rejection rate; Bell-decoy anomaly rate; rule-label agreement under controlled scenarios; ambiguous-alert rate; runtime; simulated qubit count; classical control-plane overhead; sessions per second.

### 17.3 Primary graph
Plot false-acceptance probability against the number of verification samples, separately for the X basis, Y basis, Z basis, Bell decoys, and the combined union-bound verification. Every result must disclose the attack model, calibrated baseline, sample count, error budget, and noise model.

---

## 18. Expected Deliverables

| No. | Deliverable | Description | Format |
|---|---|---|---|
| 1 | Working prototype | Teleportation-based QDS state-material simulator with PB-DTF and Q-TAM | Source code and Docker image |
| 2 | Attack suite | Forgery, impersonation, replay, channel, transcript, and rushing scenarios | Python package and CLI |
| 3 | Dashboard | Circuits, evidence charts, rule explanations, attack selector | React web application |
| 4 | Mathematical report | Protocol, thresholds, bounds, assumptions, and limitations | PDF/Markdown |
| 5 | Benchmark report | Latency, qubit count, false-acceptance curves, rule-label agreement | PDF and CSV |
| 6 | Test suite | Bell mapping, Y anti-correlation, replay lease, commitment, transcript, threshold tests | pytest suite |
| 7 | Demonstration video | Honest acceptance and attack-hypothesis demonstrations | MP4 |
| 8 | Presentation deck | SIH problem, architecture, novelty, results, limitations | PPTX |
| 9 | Protocol and threat-model specification | State lifecycle, message binding, adversary capabilities, thresholds, acceptance semantics | PDF/Markdown |

---

## 19. Implementation Plan

**Phase 1 — Quantum foundation:** Bell-state generation; teleportation circuit; correction-mapping validation; X/Y/Z preparation and measurement; honest teleportation tests.

**Phase 2 — State lifecycle:** position partitioning; one-time-use enforcement; storage-until-challenge behaviour; measurement and disposal.

**Phase 3 — Classical integrity:** session identifiers; CB-BDS commitments; transcript hash chain; message binding; replay state machine.

**Phase 4 — Detection:** DBEV; calibration runs; PB-DTF thresholds; Q-TAM rules; explanation records.

**Phase 5 — Attack evaluation:** attack injectors; Monte Carlo runner; false-acceptance curves; rule-label agreement tables.

**Phase 6 — Demonstration layer:** FastAPI endpoints; dashboard; Docker packaging; demo video; SIH presentation.

---

## 20. Implementation Priorities

**Must-have:** correct Bell-state teleportation circuit; simulator-specific correction-mapping tests; correct X/Y/Z preparation and measurement; honest Y-basis anti-correlation test; one-time-use state-material enforcement; message-binding construction; calibration-aware thresholds; atomic replay reservation and lease timeout; domain-separated transcript hash; correct Q-TAM order; ambiguous-alert category; attack explanation record.

**Strong differentiators:** commitment-bound partition and basis selection; correlation-sign-aware DBEV; the two-layer verification model; union-bound-by-default evaluation; threshold-sweep tooling.

**Optional:** ProVerif control-plane model; React dashboard; ML-KEM control-channel protection; ML-DSA hardware attestation; multi-verifier transferability; Tamarin cross-check; physical quantum hardware.

---

## 21. Impact and Use Cases

Quantum-communication testbeds requiring auditable monitoring; academic laboratories evaluating teleportation-based QDS experiments; security auditors needing explainable accept/reject/alert records; critical-infrastructure pilots exploring quantum-resistant authentication; regulated environments where black-box ML security decisions are unsuitable.

---

## 22. Limitations and Future Work

1. The implementation is a simulator, not a physical quantum deployment.
2. The system does not provide a complete QDS security proof.
3. Attack hypotheses may be ambiguous because attacks and noise can overlap.
4. Bell-decoy testing does not replace every arbitrator function.
5. HAIB is computational and does not extend information-theoretic security.
6. Transferability and multi-verifier consistency are not implemented.
7. The authentication-material construction (`N_M`) is reserved future work unless a concrete QDS authentication protocol is added.
8. Denial-of-service and classical-host side-channel attacks are out of scope.
9. Hoeffding bounds depend on disclosed calibration, sample, and independence assumptions.
10. Qiskit/Cirq simulator behaviour must be validated rather than assumed.

---

## 23. Final Project Positioning

**QUASAR-TDS should be presented as:** a deterministic, non-ML, explainable monitoring layer that combines quantum measurement evidence with classical protocol-integrity and freshness evidence for teleportation-based QDS simulations.

**It should not be presented as:** a replacement for TLS or certificate authorities; a complete production QDS protocol; a proof that teleportation by itself creates a digital signature; a universal attack classifier; a replacement for every arbitrator function; or a system whose classical identity layer is information-theoretically secure.

---

## 24. References

1. Lu et al., "A Verifiable Arbitrated Quantum Signature Scheme Based on Controlled Quantum Teleportation," *Entropy*, 2022.
2. Collins et al., "Experimental demonstration of quantum digital signatures using phase-encoded coherent states," 2014.
3. Donaldson et al., "Quantum digital signatures with quantum key distribution components," 2021.
4. Yin et al., "Measurement-Device-Independent Quantum Digital Signatures," 2017.
5. "Teleportation-based continuous-variable quantum digital signature," 2023–2025.
6. Grasselli et al., "Secure and Practical Quantum Digital Signatures," 2025.
7. "Quantum Digital Signature Using Entangled States for Network," 2025.
8. Smart India Hackathon 2026 Problem Statement SIH26141.
9. Bell-state joint-correlation characterization references used for DBEV.
10. QYMail-TEF, "A Post-Quantum, Hardware-Attested, Dual-Entropy-Anchored Key Agreement Protocol for Secure Electronic Mail" — source of the adapted commit-reveal, transcript, freshness, and attestation design patterns.

---

## 25. Final Readiness Checklist

- [ ] The teleportation circuit passes ideal-state tests.
- [ ] The correction mapping matches the selected simulator convention.
- [ ] X, Y, and Z measurements pass eigenstate tests.
- [ ] Honest Y/Y decoys are anti-correlated.
- [ ] All quantum positions are measured at most once.
- [ ] The submitted signature supplies the replay identifiers.
- [ ] Replay reservation is atomic.
- [ ] Lease expiry works after simulated crashes.
- [ ] Message binding is recomputed correctly.
- [ ] Commitment substitution is rejected.
- [ ] Transcript modification is rejected.
- [ ] Honest calibration data are disclosed.
- [ ] Threshold calculations disclose their error budgets.
- [ ] Forgery bounds identify the attack model.
- [ ] Union bounds are used unless independence is justified.
- [ ] Q-TAM has an ambiguous category.
- [ ] Dashboard output distinguishes hypothesis from certainty.
- [ ] No AI/ML component appears anywhere in the pipeline.
- [ ] The presentation states that QUASAR-TDS is a monitoring layer, not a complete QDS proof.

---

*QUASAR-TDS — Smart India Hackathon 2026, Problem Statement SIH26141.*
