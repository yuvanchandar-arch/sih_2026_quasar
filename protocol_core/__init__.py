"""
QUASAR-TDS Protocol Core Package

Provides protocol lifecycle management, commitment schemes, transcript binding,
message-binding hash construction, and the atomic replay state machine.
"""

from protocol_core.state_lifecycle import (
    PositionRole,
    PositionLifecycleState,
    PauliDescriptor,
    QuantumPosition,
    StateMaterialManager,
    PositionAlreadyConsumedError,
    InvalidPositionStateError,
    PartitionMismatchError
)

from protocol_core.commitment import (
    create_commitment,
    verify_commitment,
    generate_commitment_material,
    DEFAULT_COMMITMENT_DOMAIN
)

from protocol_core.transcript import (
    TranscriptChain,
    TranscriptEvent,
    DOMAIN_TRANSCRIPT_INIT,
    DOMAIN_TRANSCRIPT_STEP
)

from protocol_core.message_binding import (
    derive_challenge,
    compute_message_binding,
    verify_message_binding,
    DOMAIN_CHALLENGE,
    DOMAIN_MESSAGE_BINDING
)

from protocol_core.replay_ledger import (
    ReplayState,
    ReservationLease,
    ReplayLedger
)

from protocol_core.verifier import (
    SubmittedSignature,
    VerificationResult,
    create_signing_session,
    verify_submitted_signature
)

__all__ = [
    # State-material lifecycle
    "PositionRole",
    "PositionLifecycleState",
    "PauliDescriptor",
    "QuantumPosition",
    "StateMaterialManager",
    "PositionAlreadyConsumedError",
    "InvalidPositionStateError",
    "PartitionMismatchError",
    # Commitments
    "create_commitment",
    "verify_commitment",
    "generate_commitment_material",
    "DEFAULT_COMMITMENT_DOMAIN",
    # Transcript
    "TranscriptChain",
    "TranscriptEvent",
    "DOMAIN_TRANSCRIPT_INIT",
    "DOMAIN_TRANSCRIPT_STEP",
    # Message binding
    "derive_challenge",
    "compute_message_binding",
    "verify_message_binding",
    "DOMAIN_CHALLENGE",
    "DOMAIN_MESSAGE_BINDING",
    # Replay ledger
    "ReplayState",
    "ReservationLease",
    "ReplayLedger",
    # End-to-end verifier
    "SubmittedSignature",
    "VerificationResult",
    "create_signing_session",
    "verify_submitted_signature"
]
