"""
QUASAR-TDS Phase 08 — API Layer Tests

14 named tests covering all 5 endpoints, error paths, a full honest round-trip,
the live-ledger double-submit replay rejection, attack scenario variants,
and §17.3 benchmark disclosure field coverage.

Uses FastAPI's TestClient (synchronous httpx wrapper) — no async machinery needed.

Test inventory:
    1.  test_create_session_returns_valid_sid
    2.  test_verify_honest_session_accepts
    3.  test_full_round_trip_explanation_matches_verify
    4.  test_verify_unknown_sid_returns_404
    5.  test_explanation_before_verify_returns_404
    6.  test_verify_same_session_twice_second_call_is_replay
    7.  test_attack_random_state_forgery
    8.  test_attack_replay
    9.  test_attack_impersonation
    10. test_attack_transcript_injection
    11. test_attack_commitment_substitution
    12. test_attack_invalid_name_returns_422
    13. test_benchmark_returns_18_rows
    14. test_benchmark_row_has_required_disclosure_fields
"""

import pytest
from fastapi.testclient import TestClient

# Import the app directly from api.main to avoid circular import through api.__init__
from api.main import app, _sessions, _results, _shared_ledger


@pytest.fixture()
def client():
    """
    Fresh TestClient per test.  TestClient drives the lifespan context manager,
    so each test gets a clean _shared_ledger and empty session/result stores.
    """
    with TestClient(app) as c:
        yield c


# ─────────────────────────────────────────────────────────────────────────────
# 1. Session creation
# ─────────────────────────────────────────────────────────────────────────────

def test_create_session_returns_valid_sid(client):
    """POST /session returns HTTP 200, non-empty sid/signature_id, status == CREATED."""
    resp = client.post("/session", json={"message_text": "test message"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "CREATED"
    assert len(body["sid"]) > 0
    assert len(body["signature_id"]) > 0
    assert len(body["nonce"]) > 0
    assert len(body["message_hex"]) > 0


# ─────────────────────────────────────────────────────────────────────────────
# 2. Honest verification
# ─────────────────────────────────────────────────────────────────────────────

def test_verify_honest_session_accepts(client):
    """POST /session → POST /session/{sid}/verify returns ACCEPT + RULE_0_ACCEPTANCE."""
    create_resp = client.post("/session", json={"message_text": "honest acceptance test"})
    assert create_resp.status_code == 200
    sid = create_resp.json()["sid"]

    verify_resp = client.post(f"/session/{sid}/verify")
    assert verify_resp.status_code == 200, verify_resp.text
    body = verify_resp.json()
    assert body["sid"] == sid
    payload = body["payload"]
    assert payload["verdict"] == "ACCEPT"
    assert payload["rule_id"] == "RULE_0_ACCEPTANCE"
    assert payload["is_model_based_hypothesis"] is True
    assert "not forensic certainty" in payload["disclaimer"]


# ─────────────────────────────────────────────────────────────────────────────
# 3. Full round-trip: create → verify → explain
# ─────────────────────────────────────────────────────────────────────────────

def test_full_round_trip_explanation_matches_verify(client):
    """
    POST /session → POST /session/{sid}/verify → GET /session/{sid}/explanation.
    Explanation must return identical rule_id and primary_hypothesis as verify.
    """
    sid = client.post("/session", json={"message_text": "round-trip"}).json()["sid"]
    verify_payload = client.post(f"/session/{sid}/verify").json()["payload"]

    expl_resp = client.get(f"/session/{sid}/explanation")
    assert expl_resp.status_code == 200, expl_resp.text
    expl_body = expl_resp.json()
    assert expl_body["session_found"] is True
    expl_payload = expl_body["payload"]

    # Explanation record must be identical to what verify returned
    assert expl_payload["rule_id"] == verify_payload["rule_id"]
    assert expl_payload["primary_hypothesis"] == verify_payload["primary_hypothesis"]
    assert expl_payload["verdict"] == verify_payload["verdict"]


# ─────────────────────────────────────────────────────────────────────────────
# 4. 404 — verify unknown sid
# ─────────────────────────────────────────────────────────────────────────────

def test_verify_unknown_sid_returns_404(client):
    """POST /session/nonexistent/verify → HTTP 404."""
    resp = client.post("/session/nonexistent_sid_xyz/verify")
    assert resp.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# 5. 404 — explanation before verify
# ─────────────────────────────────────────────────────────────────────────────

def test_explanation_before_verify_returns_404(client):
    """GET /session/{sid}/explanation before verifying → HTTP 404."""
    sid = client.post("/session", json={"message_text": "unverified"}).json()["sid"]
    resp = client.get(f"/session/{sid}/explanation")
    assert resp.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# 6. Live-ledger double-submit replay rejection (HTTP-level proof)
# ─────────────────────────────────────────────────────────────────────────────

def test_verify_same_session_twice_second_call_is_replay(client):
    """
    POST /session → POST /session/{sid}/verify (expect ACCEPT) →
    POST /session/{sid}/verify again (same sid) → expect REJECT + RULE_1_REPLAY.

    This proves the shared replay ledger rejects a double-submit at the live
    HTTP endpoint level, with no injector involved — per §0 rule 11, this is
    the evidence that 'should work by design' actually works.
    """
    sid = client.post("/session", json={"message_text": "replay test"}).json()["sid"]

    # First verification: must ACCEPT
    first = client.post(f"/session/{sid}/verify")
    assert first.status_code == 200, first.text
    assert first.json()["payload"]["verdict"] == "ACCEPT"

    # Second verification on the identical sid: must REJECT via shared ledger
    second = client.post(f"/session/{sid}/verify")
    assert second.status_code == 200, second.text
    second_payload = second.json()["payload"]
    assert second_payload["verdict"] == "REJECT", (
        f"Expected REJECT on second verify, got {second_payload['verdict']}"
    )
    assert "RULE_1_REPLAY" in second_payload["rule_id"], (
        f"Expected RULE_1_REPLAY in rule_id, got {second_payload['rule_id']}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 7–11. Named attack scenarios
# ─────────────────────────────────────────────────────────────────────────────

def test_attack_random_state_forgery(client):
    """POST /attack with RandomStateForgery returns a non-ACCEPT verdict."""
    resp = client.post("/attack", json={"attack_name": "RandomStateForgery"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["attack_name"] == "RandomStateForgery"
    assert body["payload"]["verdict"] != "ACCEPT"
    assert body["payload"]["is_model_based_hypothesis"] is True


def test_attack_replay(client):
    """POST /attack with Replay returns RULE_1_REPLAY in rule_id."""
    resp = client.post("/attack", json={"attack_name": "Replay"})
    assert resp.status_code == 200, resp.text
    payload = resp.json()["payload"]
    assert "RULE_1_REPLAY" in payload["rule_id"], (
        f"Expected RULE_1_REPLAY, got {payload['rule_id']}"
    )
    assert payload["verdict"] in ("REJECT", "ALERT")


def test_attack_impersonation(client):
    """POST /attack with Impersonation returns RULE_2_IMPERSONATION in rule_id."""
    resp = client.post("/attack", json={"attack_name": "Impersonation"})
    assert resp.status_code == 200, resp.text
    payload = resp.json()["payload"]
    assert "RULE_2_IMPERSONATION" in payload["rule_id"], (
        f"Expected RULE_2_IMPERSONATION, got {payload['rule_id']}"
    )
    assert payload["verdict"] == "REJECT"


def test_attack_transcript_injection(client):
    """POST /attack with TranscriptInjection returns REJECT."""
    resp = client.post("/attack", json={"attack_name": "TranscriptInjection"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["payload"]["verdict"] == "REJECT"


def test_attack_commitment_substitution(client):
    """POST /attack with CommitmentSubstitution returns REJECT."""
    resp = client.post("/attack", json={"attack_name": "CommitmentSubstitution"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["payload"]["verdict"] == "REJECT"


# ─────────────────────────────────────────────────────────────────────────────
# 12. 422 — invalid attack name
# ─────────────────────────────────────────────────────────────────────────────

def test_attack_invalid_name_returns_422(client):
    """POST /attack with an unknown attack_name → HTTP 422 Unprocessable Entity."""
    resp = client.post("/attack", json={"attack_name": "NonExistentAttack"})
    assert resp.status_code == 422, resp.text


# ─────────────────────────────────────────────────────────────────────────────
# 13–14. Benchmark data
# ─────────────────────────────────────────────────────────────────────────────

def test_benchmark_returns_18_rows(client):
    """GET /benchmark → HTTP 200, row_count == 18 (6 honest + 12 attack)."""
    resp = client.get("/benchmark")
    if resp.status_code == 503:
        pytest.skip("Phase 07 benchmark CSV not generated yet — run benchmarks/run_benchmarks.py")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["row_count"] == 18, f"Expected 18 rows, got {body['row_count']}"
    assert len(body["rows"]) == 18


def test_benchmark_row_has_required_disclosure_fields(client):
    """Each benchmark row has the 5 §17.3 required disclosure fields (non-empty)."""
    resp = client.get("/benchmark")
    if resp.status_code == 503:
        pytest.skip("Phase 07 benchmark CSV not generated yet — run benchmarks/run_benchmarks.py")
    assert resp.status_code == 200, resp.text
    rows = resp.json()["rows"]
    required_fields = ["attack_model", "noise_model", "calibrated_baseline", "sample_count", "error_budget"]
    for row in rows:
        for field in required_fields:
            assert field in row, f"Missing disclosure field '{field}' in row {row.get('scenario_id')}"
            assert row[field] is not None and str(row[field]).strip() != "", (
                f"Empty disclosure field '{field}' in row {row.get('scenario_id')}"
            )
