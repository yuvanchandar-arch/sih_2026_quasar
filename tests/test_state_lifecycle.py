"""
QUASAR-TDS Phase 02: State-Material Lifecycle Unit Test Suite

Mandatory pytest functions per MASTER_PROMPT.md §3 (Phase 02):
- test_one_time_use_enforced
- test_storage_window_behavior
- test_partition_sizes_match_spec
"""

import pytest
from protocol_core.state_lifecycle import (
    StateMaterialManager,
    PositionRole,
    PositionLifecycleState,
    PositionAlreadyConsumedError,
    InvalidPositionStateError,
    PartitionMismatchError
)
from quantum_core.pauli_states import PauliBasis


def test_one_time_use_enforced():
    """
    Verifies that once a quantum position is measured, attempting any subsequent
    measurement on the consumed position fails loudly by raising
    PositionAlreadyConsumedError, rather than silently returning stale data.
    """
    n_d = 10
    n_t = 20
    manager = StateMaterialManager(n_d=n_d, n_t=n_t, seed=42)
    manager.generate_alice_key_material()
    manager.distribute_state_material()

    # 1. Test one-time-use on a challenge-test position
    test_idx = next(iter(manager.test_indices))
    pos_test = manager.bob_positions[test_idx]
    assert pos_test.lifecycle_state == PositionLifecycleState.STORED
    assert pos_test.measured_outcome is None

    # First measurement succeeds
    descriptor = manager.alice_key_material[test_idx]
    outcome_1 = manager.measure_test_position(test_idx, basis=descriptor.basis, seed=123)
    assert outcome_1 in (0, 1)
    assert pos_test.lifecycle_state == PositionLifecycleState.CONSUMED
    assert pos_test.measured_outcome == outcome_1
    assert pos_test.circuit is None  # Quantum state representation discarded

    # Second measurement attempt on the same test position MUST raise PositionAlreadyConsumedError
    with pytest.raises(PositionAlreadyConsumedError) as exc_info_1:
        manager.measure_test_position(test_idx, basis=descriptor.basis, seed=124)
    assert "already been consumed" in str(exc_info_1.value)

    # Direct measurement on the position object must also raise PositionAlreadyConsumedError
    with pytest.raises(PositionAlreadyConsumedError) as exc_info_2:
        pos_test.measure(basis=descriptor.basis, seed=125)
    assert "already been consumed" in str(exc_info_2.value)

    # 2. Test one-time-use on a decoy position
    decoy_idx = next(iter(manager.decoy_indices))
    pos_decoy = manager.bob_positions[decoy_idx]
    assert pos_decoy.lifecycle_state == PositionLifecycleState.STORED

    # First measurement succeeds
    outcome_decoy = manager.measure_decoy_position(decoy_idx, basis="Z", seed=200)
    assert outcome_decoy in (0, 1)
    assert pos_decoy.lifecycle_state == PositionLifecycleState.CONSUMED

    # Second measurement attempt on decoy position MUST raise PositionAlreadyConsumedError
    with pytest.raises(PositionAlreadyConsumedError) as exc_info_3:
        manager.measure_decoy_position(decoy_idx, basis="Z", seed=201)
    assert "already been consumed" in str(exc_info_3.value)


def test_storage_window_behavior():
    """
    Verifies the storage-until-challenge-phase behavior:
    1. Qubits are held unmeasured in the STORED state during the storage window.
    2. Alice stores only classical reference data K_A (no quantum copies).
    3. Positions are only measured when the challenge phase arrives.
    4. Upon measurement, outcomes strictly match Alice's prepared eigenstates.
    """
    n_d = 8
    n_t = 12
    manager = StateMaterialManager(n_d=n_d, n_t=n_t, seed=99)
    k_a = manager.generate_alice_key_material()

    # Check Alice holds classical reference descriptions
    assert len(k_a) == n_d + n_t
    for idx, desc in k_a.items():
        assert desc.basis in ["X", "Y", "Z"]
        assert desc.eigenvalue in [+1, -1]

    # Distribute state material
    manager.distribute_state_material()

    # During storage window (pre-challenge), verify all positions are held unmeasured
    for idx, pos in manager.bob_positions.items():
        assert pos.lifecycle_state == PositionLifecycleState.STORED
        assert pos.measured_outcome is None
        assert pos.measured_basis is None
        assert pos.circuit is not None  # Quantum state is held in register

    # Simulate arrival of challenge phase:
    # Verifier instructs Bob to measure all test positions in the bases specified by Alice's key
    for test_idx in manager.test_indices:
        descriptor = k_a[test_idx]
        pos = manager.bob_positions[test_idx]

        # Prior to measurement: position is still STORED
        assert pos.lifecycle_state == PositionLifecycleState.STORED

        # Execute one-time measurement in Alice's basis
        outcome = manager.measure_test_position(test_idx, basis=descriptor.basis, seed=42)

        # Expected outcome bit: 0 for eigenvalue +1, 1 for eigenvalue -1
        expected_bit = 0 if descriptor.eigenvalue == +1 else 1
        assert outcome == expected_bit, (
            f"Teleported state at position {test_idx} measured outcome {outcome} != expected {expected_bit} "
            f"for eigenstate ({descriptor.basis}, {descriptor.eigenvalue:+d})"
        )

        # Post-measurement: status is CONSUMED
        assert pos.lifecycle_state == PositionLifecycleState.CONSUMED
        assert pos.measured_outcome == outcome
        assert pos.measured_basis == descriptor.basis


def test_partition_sizes_match_spec():
    """
    Verifies that the session material partition strictly follows N = N_D + N_T
    without any off-by-one errors across varied partition dimensions.
    """
    test_cases = [
        (10, 20),
        (25, 75),
        (64, 128),
        (100, 200)
    ]

    for n_d, n_t in test_cases:
        expected_total = n_d + n_t
        manager = StateMaterialManager(n_d=n_d, n_t=n_t, seed=101)
        k_a = manager.generate_alice_key_material()

        # Check total counts
        assert manager.n_total == expected_total
        assert len(k_a) == expected_total
        assert len(manager.bob_positions) == expected_total

        # Check partition dimensions
        assert len(manager.decoy_indices) == n_d
        assert len(manager.test_indices) == n_t

        # Check disjointness and completeness
        assert manager.decoy_indices.isdisjoint(manager.test_indices), (
            f"Decoy and test sets overlap: {manager.decoy_indices & manager.test_indices}"
        )
        combined = manager.decoy_indices | manager.test_indices
        assert combined == set(range(expected_total)), (
            f"Partition union does not match range(N): missing={set(range(expected_total)) - combined}"
        )

        # Check role assignments
        for d_idx in manager.decoy_indices:
            assert manager.bob_positions[d_idx].role == PositionRole.DECOY
        for t_idx in manager.test_indices:
            assert manager.bob_positions[t_idx].role == PositionRole.TEST

    # Test error handling on invalid sizes
    with pytest.raises(ValueError):
        StateMaterialManager(n_d=0, n_t=10)
    with pytest.raises(ValueError):
        StateMaterialManager(n_d=10, n_t=-5)
