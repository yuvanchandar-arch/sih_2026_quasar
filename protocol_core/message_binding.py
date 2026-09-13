"""
QUASAR-TDS Protocol Core: Challenge Derivation and Message Binding Layer

Implements Challenge derivation and message-binding hash M_c strictly per
QUASAR-TDS_Final.md §8.6 and §8.7.

Formulas:
  Challenge = SHA3-256("QDS-CHALLENGE" || R_A || R_B || sid || TH)
  M_c       = SHA3-256("QDS-MESSAGE"   || m   || sid || Challenge || TH)
"""

import hashlib
import secrets
from typing import Optional


DOMAIN_CHALLENGE = "QDS-CHALLENGE"
DOMAIN_MESSAGE_BINDING = "QDS-MESSAGE"


def derive_challenge(
    R_A: bytes,
    R_B: bytes,
    sid: str,
    transcript_hash: str
) -> str:
    """
    Derives the unified Challenge value from Alice and Bob's verified contributions:
        Challenge = SHA3-256("QDS-CHALLENGE" || R_A || R_B || sid || TH)
    """
    sid_bytes = sid.encode("utf-8")
    th_bytes = transcript_hash.encode("utf-8")
    
    payload = (
        DOMAIN_CHALLENGE.encode("utf-8") +
        b"::" +
        len(R_A).to_bytes(4, "big") + R_A +
        b"::" +
        len(R_B).to_bytes(4, "big") + R_B +
        b"::" +
        len(sid_bytes).to_bytes(4, "big") + sid_bytes +
        b"::" +
        len(th_bytes).to_bytes(4, "big") + th_bytes
    )
    return hashlib.sha3_256(payload).hexdigest()


def compute_message_binding(
    message: str,
    sid: str,
    challenge: str,
    transcript_hash: str
) -> str:
    """
    Computes message-binding hash M_c per §8.7:
        M_c = SHA3-256("QDS-MESSAGE" || m || sid || Challenge || TH)
        
    CRITICAL SPEC REQUIREMENT:
    Challenge must be pre-established and non-empty. M_c cannot be computed
    before Challenge exists.
    """
    if not challenge or not isinstance(challenge, str):
        raise ValueError("Challenge must be a non-empty string derived from commitment reveal phase.")
    if not sid or not isinstance(sid, str):
        raise ValueError("Session identifier (sid) must be provided.")
    if not transcript_hash or not isinstance(transcript_hash, str):
        raise ValueError("Transcript hash (TH) must be provided.")
        
    msg_bytes = message.encode("utf-8")
    sid_bytes = sid.encode("utf-8")
    chal_bytes = challenge.encode("utf-8")
    th_bytes = transcript_hash.encode("utf-8")
    
    payload = (
        DOMAIN_MESSAGE_BINDING.encode("utf-8") +
        b"::" +
        len(msg_bytes).to_bytes(4, "big") + msg_bytes +
        b"::" +
        len(sid_bytes).to_bytes(4, "big") + sid_bytes +
        b"::" +
        len(chal_bytes).to_bytes(4, "big") + chal_bytes +
        b"::" +
        len(th_bytes).to_bytes(4, "big") + th_bytes
    )
    return hashlib.sha3_256(payload).hexdigest()


def verify_message_binding(
    m_c: str,
    message: str,
    sid: str,
    challenge: str,
    transcript_hash: str
) -> bool:
    """
    Verifies that the candidate message-binding hash matches the expected M_c.
    """
    try:
        expected_m_c = compute_message_binding(
            message=message,
            sid=sid,
            challenge=challenge,
            transcript_hash=transcript_hash
        )
        return secrets.compare_digest(expected_m_c.lower(), m_c.lower())
    except ValueError:
        return False
