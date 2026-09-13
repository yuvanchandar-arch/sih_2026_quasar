"""
QUASAR-TDS Protocol Core: Classical Event Transcript Layer (TC-QCB)

Implements domain-separated SHA3-256 transcript hash chaining strictly per
QUASAR-TDS_Final.md §7.1 and §8.6.

Chaining model:
  TH_0 = SHA3-256("QDS-TRANSCRIPT-INIT" || sid)
  TH_k = SHA3-256("QDS-TRANSCRIPT-STEP" || TH_{k-1} || event_type || event_data)
"""

import hashlib
import secrets
from typing import List, Tuple, Optional


DOMAIN_TRANSCRIPT_INIT = "QDS-TRANSCRIPT-INIT"
DOMAIN_TRANSCRIPT_STEP = "QDS-TRANSCRIPT-STEP"


class TranscriptEvent:
    def __init__(self, step: int, event_type: str, event_data: bytes, transcript_hash: str):
        self.step = step
        self.event_type = event_type
        self.event_data = event_data
        self.transcript_hash = transcript_hash

    def __repr__(self) -> str:
        return f"TranscriptEvent(step={self.step}, type={self.event_type}, hash={self.transcript_hash[:8]}...)"


class TranscriptChain:
    """
    Manages a tamper-evident hash chain over classical control messages and quantum events.
    """
    def __init__(self, sid: str):
        self.sid = sid
        self.events: List[TranscriptEvent] = []
        
        # Initialize TH_0
        init_payload = (
            DOMAIN_TRANSCRIPT_INIT.encode("utf-8") +
            b"::" +
            sid.encode("utf-8")
        )
        self.current_hash = hashlib.sha3_256(init_payload).hexdigest()

    def append_event(self, event_type: str, event_data: bytes) -> str:
        """
        Appends an event to the transcript chain, updating the cumulative transcript hash TH.
        """
        step = len(self.events) + 1
        event_type_bytes = event_type.encode("utf-8")
        
        step_payload = (
            DOMAIN_TRANSCRIPT_STEP.encode("utf-8") +
            b"::" +
            self.current_hash.encode("utf-8") +
            b"::" +
            len(event_type_bytes).to_bytes(4, "big") + event_type_bytes +
            b"::" +
            len(event_data).to_bytes(4, "big") + event_data
        )
        new_hash = hashlib.sha3_256(step_payload).hexdigest()
        
        event = TranscriptEvent(
            step=step,
            event_type=event_type,
            event_data=event_data,
            transcript_hash=new_hash
        )
        self.events.append(event)
        self.current_hash = new_hash
        return new_hash

    def get_current_hash(self) -> str:
        """Returns the current head transcript hash TH."""
        return self.current_hash

    def verify_integrity(self, candidate_events: Optional[List[Tuple[str, bytes]]] = None) -> bool:
        """
        Verifies that replaying the event sequence from TH_0 yields exactly the recorded hashes.
        If any event was altered, reordered, deleted, or injected, verification returns False.
        """
        events_to_verify = candidate_events if candidate_events is not None else [
            (e.event_type, e.event_data) for e in self.events
        ]
        
        init_payload = (
            DOMAIN_TRANSCRIPT_INIT.encode("utf-8") +
            b"::" +
            self.sid.encode("utf-8")
        )
        h = hashlib.sha3_256(init_payload).hexdigest()
        
        for idx, (ev_type, ev_data) in enumerate(events_to_verify):
            ev_type_bytes = ev_type.encode("utf-8")
            step_payload = (
                DOMAIN_TRANSCRIPT_STEP.encode("utf-8") +
                b"::" +
                h.encode("utf-8") +
                b"::" +
                len(ev_type_bytes).to_bytes(4, "big") + ev_type_bytes +
                b"::" +
                len(ev_data).to_bytes(4, "big") + ev_data
            )
            h = hashlib.sha3_256(step_payload).hexdigest()
            if candidate_events is None:
                if not secrets.compare_digest(h.lower(), self.events[idx].transcript_hash.lower()):
                    return False
                    
        return True
