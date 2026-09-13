"""
QUASAR-TDS Test Suite: End-to-End Integration (§15)

Verifies:
- Complete honest verification pipeline (create_signing_session -> verify_submitted_signature -> ACCEPT)
- Full replay flow with correct state transitions
- All 12 attack scenarios run end-to-end through the complete pipeline using Phase 05 injectors
- Granular preservation of control-plane failure reasons (distinct rule IDs for transcript tamper,
  correction metadata tamper, commitment substitution, and rushing attempt)
"""

import pytest

from protocol_core.verifier import (
    create_signing_session,
    verify_submitted_signature,
    SubmittedSignature,
    VerificationResult
)
from protocol_core.replay_ledger import ReplayLedger, ReplayState
from detection_engine.thresholds import ErrorBudget, calculate_thresholds
from attack_engine import (
    RandomStateForgeryInjector,
    ZGuessInterceptResendInjector,
    XGuessInterceptResendInjector,
    YGuessInterceptResendInjector,
    EntangleAndMeasureInjector,
    BellPairReplacementInjector,
    CorrectionBitAlterationInjector,
    ReplayInjector,
    ImpersonationInjector,
    TranscriptInjectionInjector,
    CommitmentSubstitutionInjector,
    RushingAttemptInjector
)


@pytest.fixture
def default_thresholds():
    budget = ErrorBudget()
    mu_hats = {"X": 0.01, "Y": 0.01, "Z": 0.01, "Bell": 0.01}
    n_cal = {"X": 1000, "Y": 1000, "Z": 1000, "Bell": 1000}
    n_ver = {"X": 500, "Y": 500, "Z": 500, "Bell": 500}
    return calculate_thresholds(mu_hats, n_cal, n_ver, budget=budget)


# -----------------------------------------------------------------------------
# 1. Honest Flow & Replay State Machine Integration
# -----------------------------------------------------------------------------

def test_full_honest_flow_accepts(default_thresholds):
    """
    Verifies that a complete, valid signing session passes all verification gates
    and commits the reservation lease to ACCEPTED state in the replay ledger.
    """
    message = b"Transfer 50,000,000 INR from Vault A to Reserve B"
    sig, context = create_signing_session(message)
    ledger = ReplayLedger()

    result = verify_submitted_signature(
        submitted_signature=sig,
        message=message,
        attack_model=None,
        replay_ledger=ledger,
        thresholds=default_thresholds
    )

    assert result.is_accepted is True
    assert result.verdict == "ACCEPT"
    assert result.rule_id == "RULE_0_ACCEPTANCE"
    assert "Valid quantum digital signature" in result.primary_hypothesis
    assert result.details["ledger_state"] == "ACCEPTED"

    # Verify ledger state is committed to ACCEPTED
    state = ledger.get_state(sig.sid, sig.signature_id, sig.nonce)
    assert state == ReplayState.ACCEPTED


def test_full_replay_flow_rejects_with_correct_state_transition(default_thresholds):
    """
    Verifies that resubmitting a previously accepted signature is detected by the
    replay state machine, returns REJECT: Replay, and preserves the ACCEPTED record.
    """
    message = b"Authorize Settlement Batch #8812"
    sig, _ = create_signing_session(message)
    ledger = ReplayLedger()

    # 1. First submission: honest acceptance
    res1 = verify_submitted_signature(sig, message, replay_ledger=ledger, thresholds=default_thresholds)
    assert res1.is_accepted is True
    assert res1.verdict == "ACCEPT"

    # 2. Second submission: resubmission of the exact same signature
    res2 = verify_submitted_signature(sig, message, replay_ledger=ledger, thresholds=default_thresholds)
    assert res2.is_accepted is False
    assert res2.verdict == "REJECT"
    assert res2.rule_id == "RULE_1_REPLAY"
    assert "Replay" in res2.primary_hypothesis

    # Verify ledger retained the permanent ACCEPTED state
    state = ledger.get_state(sig.sid, sig.signature_id, sig.nonce)
    assert state == ReplayState.ACCEPTED


# -----------------------------------------------------------------------------
# 2. All 12 Attacks End-to-End Through Full Pipeline
# -----------------------------------------------------------------------------

def test_e2e_random_state_forgery(default_thresholds):
    """Attack 1 E2E: Random-state forgery through full pipeline -> Broad Pauli-basis anomaly."""
    message = b"E2E Test Message 1"
    sig, _ = create_signing_session(message)
    injector = RandomStateForgeryInjector(seed=101)

    result = verify_submitted_signature(sig, message, attack_model=injector, thresholds=default_thresholds)
    assert result.is_accepted is False
    assert result.verdict == "ALERT"
    assert result.rule_id == "RULE_6_BROAD_PAULI"
    assert "Broad Pauli-basis anomaly" in result.primary_hypothesis
    assert result.explanation.is_model_based_hypothesis is True


def test_e2e_z_guess_intercept_resend(default_thresholds):
    """Attack 2 E2E: Z-guess intercept-resend through full pipeline -> Partial broad Pauli anomaly."""
    message = b"E2E Test Message 2"
    sig, _ = create_signing_session(message)
    injector = ZGuessInterceptResendInjector(seed=102)

    result = verify_submitted_signature(sig, message, attack_model=injector, thresholds=default_thresholds)
    assert result.is_accepted is False
    assert result.verdict == "ALERT"
    assert result.rule_id == "RULE_7_PARTIAL_BROAD_PAULI"
    assert "Partial broad Pauli anomaly" in result.primary_hypothesis


def test_e2e_x_guess_intercept_resend(default_thresholds):
    """Attack 3 E2E: X-guess intercept-resend through full pipeline -> Partial broad Pauli anomaly."""
    message = b"E2E Test Message 3"
    sig, _ = create_signing_session(message)
    injector = XGuessInterceptResendInjector(seed=103)

    result = verify_submitted_signature(sig, message, attack_model=injector, thresholds=default_thresholds)
    assert result.is_accepted is False
    assert result.verdict == "ALERT"
    assert result.rule_id == "RULE_7_PARTIAL_BROAD_PAULI"
    assert "Partial broad Pauli anomaly" in result.primary_hypothesis


def test_e2e_y_guess_intercept_resend(default_thresholds):
    """Attack 4 E2E: Y-guess intercept-resend through full pipeline -> Partial broad Pauli anomaly."""
    message = b"E2E Test Message 4"
    sig, _ = create_signing_session(message)
    injector = YGuessInterceptResendInjector(seed=104)

    result = verify_submitted_signature(sig, message, attack_model=injector, thresholds=default_thresholds)
    assert result.is_accepted is False
    assert result.verdict == "ALERT"
    assert result.rule_id == "RULE_7_PARTIAL_BROAD_PAULI"
    assert "Partial broad Pauli anomaly" in result.primary_hypothesis


def test_e2e_entangle_and_measure(default_thresholds):
    """Attack 5 E2E: Entangle-and-measure through full pipeline -> Partial broad Pauli anomaly."""
    message = b"E2E Test Message 5"
    sig, _ = create_signing_session(message)
    injector = EntangleAndMeasureInjector(seed=105)

    result = verify_submitted_signature(sig, message, attack_model=injector, thresholds=default_thresholds)
    assert result.is_accepted is False
    assert result.verdict == "ALERT"
    assert result.rule_id == "RULE_7_PARTIAL_BROAD_PAULI"


def test_e2e_bell_pair_replacement(default_thresholds):
    """Attack 6 E2E: Bell-pair replacement through full pipeline -> Channel-integrity anomaly."""
    message = b"E2E Test Message 6"
    sig, _ = create_signing_session(message)
    injector = BellPairReplacementInjector(seed=106)

    result = verify_submitted_signature(sig, message, attack_model=injector, thresholds=default_thresholds)
    assert result.is_accepted is False
    assert result.verdict == "ALERT"
    assert result.rule_id == "RULE_5_CHANNEL_INTEGRITY"
    assert "Channel-integrity anomaly" in result.primary_hypothesis


def test_e2e_correction_bit_alteration(default_thresholds):
    """
    Attack 7 E2E: Correction-bit alteration through full pipeline ->
    Preserves distinct rule_id: RULE_3_CORRECTION_METADATA_TAMPER.
    """
    message = b"E2E Test Message 7"
    sig, _ = create_signing_session(message)
    injector = CorrectionBitAlterationInjector(seed=107)

    result = verify_submitted_signature(sig, message, attack_model=injector, thresholds=default_thresholds)
    assert result.is_accepted is False
    assert result.verdict == "REJECT"
    assert result.rule_id == "RULE_3_CORRECTION_METADATA_TAMPER"
    assert "Pauli correction metadata" in result.primary_hypothesis


def test_e2e_replay(default_thresholds):
    """Attack 8 E2E: Replay through full pipeline -> REJECT: Replay."""
    message = b"E2E Test Message 8"
    sig, _ = create_signing_session(message)
    injector = ReplayInjector(seed=108)

    result = verify_submitted_signature(sig, message, attack_model=injector, thresholds=default_thresholds)
    assert result.is_accepted is False
    assert result.verdict == "REJECT"
    assert result.rule_id == "RULE_1_REPLAY"
    assert "Replay" in result.primary_hypothesis


def test_e2e_impersonation(default_thresholds):
    """Attack 9 E2E: Impersonation through full pipeline -> REJECT: Impersonation suspicion."""
    message = b"E2E Test Message 9"
    sig, _ = create_signing_session(message)
    injector = ImpersonationInjector(seed=109)

    result = verify_submitted_signature(sig, message, attack_model=injector, thresholds=default_thresholds)
    assert result.is_accepted is False
    assert result.verdict == "REJECT"
    assert result.rule_id == "RULE_2_IMPERSONATION"
    assert "Impersonation suspicion" in result.primary_hypothesis


def test_e2e_transcript_injection(default_thresholds):
    """Attack 10 E2E: Transcript injection through full pipeline -> REJECT: Control-plane tampering."""
    message = b"E2E Test Message 10"
    sig, _ = create_signing_session(message)
    injector = TranscriptInjectionInjector(seed=110)

    result = verify_submitted_signature(sig, message, attack_model=injector, thresholds=default_thresholds)
    assert result.is_accepted is False
    assert result.verdict == "REJECT"
    assert result.rule_id == "RULE_3_TRANSCRIPT_TAMPER"
    assert "Control-plane tampering" in result.primary_hypothesis


def test_e2e_commitment_substitution(default_thresholds):
    """
    Attack 11 E2E: Commitment substitution through full pipeline ->
    Preserves distinct rule_id: RULE_3_COMMITMENT_SUBSTITUTION.
    """
    message = b"E2E Test Message 11"
    sig, _ = create_signing_session(message)
    injector = CommitmentSubstitutionInjector(seed=111)

    result = verify_submitted_signature(sig, message, attack_model=injector, thresholds=default_thresholds)
    assert result.is_accepted is False
    assert result.verdict == "REJECT"
    assert result.rule_id == "RULE_3_COMMITMENT_SUBSTITUTION"
    assert "Commitment substitution" in result.primary_hypothesis


def test_e2e_rushing_attempt(default_thresholds):
    """
    Attack 12 E2E: Rushing attempt through full pipeline ->
    Preserves distinct rule_id: RULE_3_RUSHING_ATTEMPT_BLOCKED.
    """
    message = b"E2E Test Message 12"
    sig, _ = create_signing_session(message)
    injector = RushingAttemptInjector(seed=112)

    result = verify_submitted_signature(sig, message, attack_model=injector, thresholds=default_thresholds)
    assert result.is_accepted is False
    assert result.verdict == "REJECT"
    assert result.rule_id == "RULE_3_RUSHING_ATTEMPT_BLOCKED"
    assert "Structurally blocked by CB-BDS" in result.primary_hypothesis
