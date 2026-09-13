"""
QUASAR-TDS Protocol Core: Commitment-Bound Basis and Decoy Selection (CB-BDS)

Implements domain-separated SHA3-256 commit-before-reveal mechanisms strictly per
QUASAR-TDS_Final.md §8.6.

Formulas:
  C_A = SHA3-256("QDS-CB-BDS" || sid || R_A || r_A)
  C_B = SHA3-256("QDS-CB-BDS" || sid || R_B || r_B)
"""

import hashlib
import secrets
from typing import Tuple, Optional


DEFAULT_COMMITMENT_DOMAIN = "QDS-CB-BDS"


def format_commitment_payload(domain: str, sid: str, R: bytes, r: bytes) -> bytes:
    """Encodes commitment inputs into domain-separated canonical byte sequence."""
    domain_bytes = domain.encode("utf-8")
    sid_bytes = sid.encode("utf-8")
    # Length-prefixed encoding to prevent concatenation ambiguity
    return (
        len(domain_bytes).to_bytes(4, "big") + domain_bytes +
        len(sid_bytes).to_bytes(4, "big") + sid_bytes +
        len(R).to_bytes(4, "big") + R +
        len(r).to_bytes(4, "big") + r
    )


def create_commitment(
    sid: str,
    R: bytes,
    r: bytes,
    domain: str = DEFAULT_COMMITMENT_DOMAIN
) -> str:
    """
    Computes domain-separated SHA3-256 commitment:
        C = SHA3-256(domain || sid || R || r)
    """
    payload = format_commitment_payload(domain, sid, R, r)
    return hashlib.sha3_256(payload).hexdigest()


def verify_commitment(
    commitment: str,
    sid: str,
    R: bytes,
    r: bytes,
    domain: str = DEFAULT_COMMITMENT_DOMAIN
) -> bool:
    """
    Verifies that the revealed (R, r) matches the pre-established commitment C.
    Returns True if valid, False otherwise.
    """
    expected = create_commitment(sid, R, r, domain=domain)
    # Constant-time comparison to prevent timing side channels
    return secrets.compare_digest(expected.lower(), commitment.lower())


def generate_commitment_material(size: int = 32) -> Tuple[bytes, bytes]:
    """Generates cryptographic random challenge contribution R and blinding nonce r."""
    R = secrets.token_bytes(size)
    r = secrets.token_bytes(size)
    return R, r
