"""
QUASAR-TDS Protocol Core: Replay Ledger and Freshness State Machine

Implements the replay state machine strictly per QUASAR-TDS_Final.md §13,
backed by an atomic, thread-safe SQLite store.

State Transitions:
  ABSENT  --reserve-->  RESERVED  --accept-->  ACCEPTED  --resubmission--> REPLAY
                           |
                           +--fail-->  BLOCKED (with retention window)
                           |
                           +--lease expiry-->  RELEASED

  RESERVED + concurrent request for same identifier --> DUPLICATE_IN_PROGRESS
"""

import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple, Dict, Any


class ReplayState(str, Enum):
    ABSENT = "ABSENT"
    RESERVED = "RESERVED"
    ACCEPTED = "ACCEPTED"
    RELEASED = "RELEASED"
    BLOCKED = "BLOCKED"
    DUPLICATE_IN_PROGRESS = "DUPLICATE_IN_PROGRESS"


@dataclass(frozen=True)
class ReservationLease:
    lease_id: str
    identifier: str
    created_at: float
    expires_at: float


class ReplayLedger:
    """
    Thread-safe, atomic Replay Ledger backed by SQLite.
    
    Guarantees:
      - Atomic reservation under high concurrency.
      - Exactly one requester acquires lease; concurrent competitor gets DUPLICATE_IN_PROGRESS.
      - Lease expiration releases abandoned reservations.
      - BLOCKED retention window prevents immediate resubmission after verification failure.
      - Permanent consumption on ACCEPTED.
    """
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            isolation_level=None  # Explicit transaction control
        )
        self._create_tables()

    def _create_tables(self) -> None:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS replay_ledger (
                    identifier TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    lease_id TEXT,
                    lease_expires_at REAL,
                    blocked_until REAL,
                    updated_at REAL NOT NULL
                )
            """)

    @staticmethod
    def construct_identifier(sid: str, signature_id: str, nonce: str) -> str:
        """Derives canonical composite identifier string from submitted signature metadata."""
        return f"{sid}::{signature_id}::{nonce}"

    def reserve(
        self,
        sid: str,
        signature_id: str,
        nonce: str,
        lease_timeout: float = 5.0
    ) -> Tuple[Optional[ReservationLease], ReplayState]:
        """
        Atomically attempts to reserve the submitted identifier.
        
        Returns:
            (ReservationLease, ReplayState.RESERVED) on successful reservation.
            (None, state) where state is DUPLICATE_IN_PROGRESS, ACCEPTED, or BLOCKED on contention.
        """
        identifier = self.construct_identifier(sid, signature_id, nonce)
        now = time.time()

        with self._lock:
            cur = self._conn.cursor()
            cur.execute("BEGIN IMMEDIATE")
            try:
                cur.execute(
                    "SELECT state, lease_id, lease_expires_at, blocked_until FROM replay_ledger WHERE identifier = ?",
                    (identifier,)
                )
                row = cur.fetchone()

                if row is None:
                    # ABSENT -> Create new reservation
                    lease_id = uuid.uuid4().hex
                    expires_at = now + lease_timeout
                    cur.execute(
                        """
                        INSERT INTO replay_ledger (identifier, state, lease_id, lease_expires_at, blocked_until, updated_at)
                        VALUES (?, ?, ?, ?, NULL, ?)
                        """,
                        (identifier, ReplayState.RESERVED.value, lease_id, expires_at, now)
                    )
                    cur.execute("COMMIT")
                    return ReservationLease(lease_id, identifier, now, expires_at), ReplayState.RESERVED

                current_state_str, current_lease_id, lease_expires_at, blocked_until = row
                current_state = ReplayState(current_state_str)

                # Check for lease expiry on RESERVED
                if current_state == ReplayState.RESERVED and lease_expires_at is not None and now >= lease_expires_at:
                    current_state = ReplayState.RELEASED

                # Check for retention window expiry on BLOCKED
                if current_state == ReplayState.BLOCKED and blocked_until is not None and now >= blocked_until:
                    current_state = ReplayState.RELEASED

                if current_state == ReplayState.RELEASED:
                    # Can be re-reserved
                    lease_id = uuid.uuid4().hex
                    expires_at = now + lease_timeout
                    cur.execute(
                        """
                        UPDATE replay_ledger
                        SET state = ?, lease_id = ?, lease_expires_at = ?, blocked_until = NULL, updated_at = ?
                        WHERE identifier = ?
                        """,
                        (ReplayState.RESERVED.value, lease_id, expires_at, now, identifier)
                    )
                    cur.execute("COMMIT")
                    return ReservationLease(lease_id, identifier, now, expires_at), ReplayState.RESERVED

                if current_state == ReplayState.RESERVED:
                    # Concurrent request collision
                    cur.execute("COMMIT")
                    return None, ReplayState.DUPLICATE_IN_PROGRESS

                if current_state == ReplayState.ACCEPTED:
                    cur.execute("COMMIT")
                    return None, ReplayState.ACCEPTED

                if current_state == ReplayState.BLOCKED:
                    cur.execute("COMMIT")
                    return None, ReplayState.BLOCKED

                cur.execute("COMMIT")
                return None, current_state

            except Exception:
                cur.execute("ROLLBACK")
                raise

    def commit(self, lease: ReservationLease) -> bool:
        """
        Finalizes signature acceptance: transitions state from RESERVED to ACCEPTED.
        Permanently consumes the identifier.
        """
        now = time.time()
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("BEGIN IMMEDIATE")
            try:
                cur.execute(
                    "SELECT state, lease_id FROM replay_ledger WHERE identifier = ?",
                    (lease.identifier,)
                )
                row = cur.fetchone()
                if row and row[0] == ReplayState.RESERVED.value and row[1] == lease.lease_id:
                    cur.execute(
                        """
                        UPDATE replay_ledger
                        SET state = ?, lease_id = NULL, lease_expires_at = NULL, updated_at = ?
                        WHERE identifier = ?
                        """,
                        (ReplayState.ACCEPTED.value, now, lease.identifier)
                    )
                    cur.execute("COMMIT")
                    return True
                cur.execute("COMMIT")
                return False
            except Exception:
                cur.execute("ROLLBACK")
                raise

    def release(self, lease: ReservationLease) -> bool:
        """Voluntarily releases a reservation upon clean cancellation or abort."""
        now = time.time()
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("BEGIN IMMEDIATE")
            try:
                cur.execute(
                    "SELECT state, lease_id FROM replay_ledger WHERE identifier = ?",
                    (lease.identifier,)
                )
                row = cur.fetchone()
                if row and row[0] == ReplayState.RESERVED.value and row[1] == lease.lease_id:
                    cur.execute(
                        """
                        UPDATE replay_ledger
                        SET state = ?, lease_id = NULL, lease_expires_at = NULL, updated_at = ?
                        WHERE identifier = ?
                        """,
                        (ReplayState.RELEASED.value, now, lease.identifier)
                    )
                    cur.execute("COMMIT")
                    return True
                cur.execute("COMMIT")
                return False
            except Exception:
                cur.execute("ROLLBACK")
                raise

    def block_for_retention(
        self,
        identifier_or_lease: Any,
        retention_period: float = 30.0
    ) -> bool:
        """
        Transitions identifier to BLOCKED state with retention window upon verification failure
        (e.g., transcript tampering or invalid commitments).
        """
        if isinstance(identifier_or_lease, ReservationLease):
            identifier = identifier_or_lease.identifier
        else:
            identifier = str(identifier_or_lease)

        now = time.time()
        blocked_until = now + retention_period

        with self._lock:
            cur = self._conn.cursor()
            cur.execute("BEGIN IMMEDIATE")
            try:
                cur.execute(
                    """
                    INSERT INTO replay_ledger (identifier, state, lease_id, lease_expires_at, blocked_until, updated_at)
                    VALUES (?, ?, NULL, NULL, ?, ?)
                    ON CONFLICT(identifier) DO UPDATE SET
                        state = excluded.state,
                        lease_id = NULL,
                        lease_expires_at = NULL,
                        blocked_until = excluded.blocked_until,
                        updated_at = excluded.updated_at
                    """,
                    (identifier, ReplayState.BLOCKED.value, blocked_until, now)
                )
                cur.execute("COMMIT")
                return True
            except Exception:
                cur.execute("ROLLBACK")
                raise

    def get_state(self, sid: str, signature_id: str, nonce: str) -> ReplayState:
        """Inspects current state of an identifier."""
        identifier = self.construct_identifier(sid, signature_id, nonce)
        now = time.time()
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                "SELECT state, lease_expires_at, blocked_until FROM replay_ledger WHERE identifier = ?",
                (identifier,)
            )
            row = cur.fetchone()
            if row is None:
                return ReplayState.ABSENT

            state_str, lease_expires_at, blocked_until = row
            state = ReplayState(state_str)

            if state == ReplayState.RESERVED and lease_expires_at is not None and now >= lease_expires_at:
                return ReplayState.RELEASED
            if state == ReplayState.BLOCKED and blocked_until is not None and now >= blocked_until:
                return ReplayState.RELEASED

            return state
