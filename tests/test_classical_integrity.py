"""
QUASAR-TDS Phase 03: Classical Integrity Layer Unit Test Suite

Mandatory pytest functions per MASTER_PROMPT.md §3 (Phase 03):
- test_commitment_hiding_and_binding
- test_commitment_domain_separation
- test_transcript_tamper_detected
- test_message_binding_requires_fixed_challenge
- test_replay_reservation_is_atomic_under_concurrency
- test_lease_expiry_releases_crashed_reservation
- test_blocked_retention_prevents_immediate_resubmission
"""

import threading
import time
import pytest
import secrets

from protocol_core.commitment import (
    create_commitment,
    verify_commitment,
    generate_commitment_material,
    DEFAULT_COMMITMENT_DOMAIN
)
from protocol_core.transcript import (
    TranscriptChain,
    DOMAIN_TRANSCRIPT_INIT,
    DOMAIN_TRANSCRIPT_STEP
)
from protocol_core.message_binding import (
    derive_challenge,
    compute_message_binding,
    verify_message_binding
)
from protocol_core.replay_ledger import (
    ReplayLedger,
    ReplayState,
    ReservationLease
)


def test_commitment_hiding_and_binding():
    """
    Verifies computational binding of the CB-BDS commitment:
    Once committed, a party cannot alter R or r without causing commitment
    verification to fail.
    """
    sid = "session-cb-bds-001"
    R_A, r_A = generate_commitment_material(size=32)
    C_A = create_commitment(sid, R_A, r_A)

    # Honest verification succeeds
    assert verify_commitment(C_A, sid, R_A, r_A) is True

    # Tampering with revealed value R must fail
    tampered_R = bytearray(R_A)
    tampered_R[0] ^= 0xFF
    assert verify_commitment(C_A, sid, bytes(tampered_R), r_A) is False

    # Tampering with blinding nonce r must fail
    tampered_r = bytearray(r_A)
    tampered_r[0] ^= 0xFF
    assert verify_commitment(C_A, sid, R_A, bytes(tampered_r)) is False

    # Complete substitution must fail
    substitute_R, substitute_r = generate_commitment_material(size=32)
    assert verify_commitment(C_A, sid, substitute_R, substitute_r) is False


def test_commitment_domain_separation():
    """
    Verifies domain separation:
    A commitment computed under one domain prefix or session identifier
    cannot be reused or verified under another.
    """
    sid_1 = "session-domain-001"
    sid_2 = "session-domain-002"
    R, r = generate_commitment_material(size=32)

    # Commitment under standard QDS-CB-BDS domain
    C_standard = create_commitment(sid_1, R, r, domain=DEFAULT_COMMITMENT_DOMAIN)
    assert verify_commitment(C_standard, sid_1, R, r, domain=DEFAULT_COMMITMENT_DOMAIN) is True

    # Verification under a different domain must fail
    assert verify_commitment(C_standard, sid_1, R, r, domain="DIFFERENT-DOMAIN") is False
    assert verify_commitment(C_standard, sid_1, R, r, domain="QDS-MESSAGE") is False

    # Commitment generated under a different domain cannot verify under QDS-CB-BDS
    C_other = create_commitment(sid_1, R, r, domain="OTHER-PURPOSE")
    assert verify_commitment(C_other, sid_1, R, r, domain=DEFAULT_COMMITMENT_DOMAIN) is False

    # Cross-session replay: valid commitment for sid_1 must fail verification under sid_2
    assert verify_commitment(C_standard, sid_2, R, r, domain=DEFAULT_COMMITMENT_DOMAIN) is False


def test_transcript_tamper_detected():
    """
    Verifies that the transcript hash chain is tamper-evident:
    Modifying, deleting, or injecting any event invalidates all subsequent
    transcript hashes.
    """
    sid = "transcript-session-100"
    chain = TranscriptChain(sid)

    # Append 4 sequential protocol events
    h1 = chain.append_event("COMMITMENT_EXCHANGE", b"C_A:C_B:data")
    h2 = chain.append_event("COMMITMENT_REVEAL", b"R_A:r_A:R_B:r_B")
    h3 = chain.append_event("CORRECTION_METADATA", b"corrections:010011")
    h4 = chain.append_event("MESSAGE_DECLARATION", b"sig_decl:valid")

    # Honest chain verifies
    assert chain.verify_integrity() is True
    assert chain.get_current_hash() == h4

    # 1. Tamper with an event in the middle (Event 2)
    tampered_events = [
        ("COMMITMENT_EXCHANGE", b"C_A:C_B:data"),
        ("COMMITMENT_REVEAL", b"R_A:r_A:R_B:r_B:TAMPERED"),  # modified
        ("CORRECTION_METADATA", b"corrections:010011"),
        ("MESSAGE_DECLARATION", b"sig_decl:valid")
    ]
    # Replaying tampered sequence does NOT match recorded hashes
    chain_tampered = TranscriptChain(sid)
    chain_tampered.append_event(tampered_events[0][0], tampered_events[0][1])
    th2_tampered = chain_tampered.append_event(tampered_events[1][0], tampered_events[1][1])
    th3_tampered = chain_tampered.append_event(tampered_events[2][0], tampered_events[2][1])
    th4_tampered = chain_tampered.append_event(tampered_events[3][0], tampered_events[3][1])

    assert th2_tampered != h2
    assert th3_tampered != h3
    assert th4_tampered != h4

    # 2. Tamper by event deletion (omitting event 2)
    deleted_events = [
        ("COMMITMENT_EXCHANGE", b"C_A:C_B:data"),
        ("CORRECTION_METADATA", b"corrections:010011"),
        ("MESSAGE_DECLARATION", b"sig_decl:valid")
    ]
    chain_deleted = TranscriptChain(sid)
    for ev_type, ev_data in deleted_events:
        chain_deleted.append_event(ev_type, ev_data)
    assert chain_deleted.get_current_hash() != h4


def test_message_binding_requires_fixed_challenge():
    """
    Verifies that M_c cannot be computed before Challenge exists,
    and that M_c is strictly bound to the specific Challenge and transcript hash.
    """
    sid = "msg-bind-session-200"
    message = "CRITICAL_FINANCIAL_TRANSACTION_AUTHORIZATION"
    transcript_hash = "f1e2d3c4b5a697887766554433221100ffeeddccbbaa99887766554433221100"

    # 1. Attempting to compute M_c without a valid Challenge must raise ValueError
    with pytest.raises(ValueError):
        compute_message_binding(message=message, sid=sid, challenge="", transcript_hash=transcript_hash)

    with pytest.raises(ValueError):
        compute_message_binding(message=message, sid=sid, challenge=None, transcript_hash=transcript_hash)

    # 2. Proper derivation once Challenge is established
    R_A, r_A = generate_commitment_material(32)
    R_B, r_B = generate_commitment_material(32)
    challenge_valid = derive_challenge(R_A, R_B, sid, transcript_hash)
    assert len(challenge_valid) == 64  # SHA3-256 hex string

    m_c = compute_message_binding(message, sid, challenge_valid, transcript_hash)
    assert verify_message_binding(m_c, message, sid, challenge_valid, transcript_hash) is True

    # 3. Using a different/pre-challenge value fails verification
    challenge_fake = "0000000000000000000000000000000000000000000000000000000000000000"
    assert verify_message_binding(m_c, message, sid, challenge_fake, transcript_hash) is False

    # 4. Modifying message fails verification
    assert verify_message_binding(m_c, message + "_ALTERED", sid, challenge_valid, transcript_hash) is False

    # 5. Modifying transcript hash fails verification
    altered_th = transcript_hash[:-2] + "ff"
    assert verify_message_binding(m_c, message, sid, challenge_valid, altered_th) is False


def test_replay_reservation_is_atomic_under_concurrency():
    """
    CRITICAL CONCURRENCY TEST:
    Fires two simultaneous threads racing against the exact same identifier
    using a synchronization barrier (threading.Barrier).
    
    Verifies that SQLite atomic transactions guarantee:
    - Exactly ONE thread acquires a valid ReservationLease (status RESERVED).
    - Exactly ONE thread receives DUPLICATE_IN_PROGRESS (lease is None).
    - No race condition or double-allocation ever occurs.
    """
    ledger = ReplayLedger(db_path=":memory:")
    num_trials = 25  # Run 25 independent simultaneous race trials

    for trial in range(num_trials):
        sid = f"concurrency-sid-{trial}"
        sig_id = f"sig-{trial}"
        nonce = f"nonce-{trial}"

        barrier = threading.Barrier(2)
        results = [None, None]

        def worker(thread_idx: int):
            # Both threads hit the barrier and release simultaneously
            barrier.wait()
            lease, state = ledger.reserve(sid=sid, signature_id=sig_id, nonce=nonce, lease_timeout=5.0)
            results[thread_idx] = (lease, state)

        t0 = threading.Thread(target=worker, args=(0,))
        t1 = threading.Thread(target=worker, args=(1,))

        t0.start()
        t1.start()
        t0.join()
        t1.join()

        leases = [r[0] for r in results]
        states = [r[1] for r in results]

        # Exactly one thread must have acquired the lease
        successful_leases = [l for l in leases if l is not None]
        assert len(successful_leases) == 1, (
            f"Trial {trial} failed concurrency atomicity: expected 1 lease, got {len(successful_leases)}. "
            f"States: {states}"
        )

        # Exactly one state must be RESERVED and the other DUPLICATE_IN_PROGRESS
        assert sorted(states) == [ReplayState.DUPLICATE_IN_PROGRESS, ReplayState.RESERVED], (
            f"Trial {trial} states mismatch: {states}"
        )


def test_lease_expiry_releases_crashed_reservation():
    """
    Verifies lease timeout recovery:
    If a verifier reserves an identifier but crashes without committing or releasing,
    the lease expires after lease_timeout and allows a subsequent reservation to succeed.
    """
    ledger = ReplayLedger(db_path=":memory:")
    sid = "crash-recovery-sid-1"
    sig_id = "sig-001"
    nonce = "nonce-001"

    short_timeout = 0.3  # 300ms lease
    lease, state = ledger.reserve(sid, sig_id, nonce, lease_timeout=short_timeout)
    assert lease is not None
    assert state == ReplayState.RESERVED

    # Immediate second attempt while lease is active MUST fail with DUPLICATE_IN_PROGRESS
    lease_immediate, state_immediate = ledger.reserve(sid, sig_id, nonce)
    assert lease_immediate is None
    assert state_immediate == ReplayState.DUPLICATE_IN_PROGRESS

    # Wait past lease expiration window
    time.sleep(0.35)

    # After expiry, crashed reservation is treated as RELEASED and re-reservation succeeds
    lease_recovered, state_recovered = ledger.reserve(sid, sig_id, nonce, lease_timeout=5.0)
    assert lease_recovered is not None
    assert state_recovered == ReplayState.RESERVED
    assert lease_recovered.lease_id != lease.lease_id  # Fresh lease assigned


def test_blocked_retention_prevents_immediate_resubmission():
    """
    Verifies that rejected identifiers enter a bounded BLOCKED retention window,
    preventing immediate resubmission or retry attacks.
    """
    ledger = ReplayLedger(db_path=":memory:")
    sid = "tamper-blocked-sid-1"
    sig_id = "sig-blocked-001"
    nonce = "nonce-blocked-001"

    # Initially reserve
    lease, state = ledger.reserve(sid, sig_id, nonce, lease_timeout=5.0)
    assert state == ReplayState.RESERVED

    # Verification fails (e.g. transcript tamper) -> block for retention window
    retention_period = 0.4  # 400ms retention
    ledger.block_for_retention(lease, retention_period=retention_period)

    # While in retention window, state must report BLOCKED
    assert ledger.get_state(sid, sig_id, nonce) == ReplayState.BLOCKED

    # Reservation attempt during retention window MUST fail
    lease_blocked, state_blocked = ledger.reserve(sid, sig_id, nonce)
    assert lease_blocked is None
    assert state_blocked == ReplayState.BLOCKED

    # Wait past retention window
    time.sleep(0.45)

    # After retention window, identifier is freed to RELEASED and can be re-reserved
    lease_after, state_after = ledger.reserve(sid, sig_id, nonce)
    assert lease_after is not None
    assert state_after == ReplayState.RESERVED
