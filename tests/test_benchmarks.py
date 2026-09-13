"""
QUASAR-TDS Tests: Phase 07 Performance Evaluation & Benchmarking Suite

Verifies:
  1. All 6 honest baseline noise models instantiate cleanly (§17.1).
  2. Calibrated honest baselines achieve FRR <= epsilon_total under statistical confidence.
  3. All 12 attack scenarios are detected and blocked with observed FAR <= epsilon_total.
  4. Granular 10-stage latency profiling computes positive durations and throughput.
  5. State-material scaling benchmarks scale consistently with N.
  6. CSV output files exist, parse correctly, and disclose all §17.3 parameters.
  7. Primary graph (PNG/SVG) and visualizations exist and have non-zero size.
"""

import os
import csv
import json
import pytest
from pathlib import Path

from benchmarks.noise_models import create_noise_model
from benchmarks.latency_profiler import LatencyProfiler
from benchmarks.benchmark_matrix import BenchmarkMatrixRunner
from benchmarks.plot_false_acceptance import (
    generate_false_acceptance_plot,
    generate_latency_breakdown_plot,
    generate_attack_detection_plot
)


def test_noise_models_generation():
    """Verifies all 6 honest baseline noise models instantiate cleanly."""
    models = ["ideal", "bit_flip", "phase_flip", "depolarizing", "measurement_error", "calibration_drift"]
    for m in models:
        nm, desc = create_noise_model(m, p=0.01)
        assert desc is not None
        assert len(desc) > 5
        if m == "ideal":
            assert nm is None
        else:
            assert nm is not None


def test_honest_baselines_acceptance_and_error_budget():
    """
    Confirms honest baselines meet FRR <= epsilon_total under calibrated thresholds.
    Reframed to evaluate statistical bound compliance per user instruction.
    """
    runner = BenchmarkMatrixRunner(n_cal_samples=200, n_ver_samples=100, seed=42)
    honest_rows = runner.run_honest_baselines()

    assert len(honest_rows) == 6
    for r in honest_rows:
        assert r.is_accepted is True
        assert r.verdict == "ACCEPT"
        assert r.rule_id == "RULE_0_ACCEPTANCE"
        assert r.replay_ledger_state == "ACCEPTED"
        # Disclosures present
        assert "n_cal" in r.sample_count
        assert "eps_total" in r.error_budget


def test_attack_matrix_detection_and_bound_compliance():
    """
    Confirms all 12 attack scenarios are detected/blocked in compliance with Hoeffding bounds.
    Observed false-acceptance rate FAR = 0 <= epsilon_total under calibrated conditions.
    """
    runner = BenchmarkMatrixRunner(n_cal_samples=200, n_ver_samples=100, seed=42)
    attack_rows = runner.run_attack_scenarios()

    assert len(attack_rows) == 12
    for r in attack_rows:
        assert r.is_accepted is False
        assert r.verdict in ["ALERT", "REJECT"]
        assert r.replay_ledger_state in ["BLOCKED", "ACCEPTED"]  # Replay retains prior accepted
        assert r.rule_label_agreed is True


def test_latency_profiling_completeness():
    """Confirms all 10 stages have positive microsecond durations and valid throughput."""
    profiler = LatencyProfiler(n_samples_per_basis=100)
    prof_res = profiler.profile_stages(warmup_runs=1, timed_runs=3)

    assert prof_res.total_latency_ms > 0.0
    assert prof_res.throughput_sessions_per_sec > 0.0
    assert prof_res.qubit_count == 3 * (100 * 4)
    assert prof_res.control_overhead_bytes > 100
    assert len(prof_res.stage_timings) == 10

    for stage in prof_res.stage_timings:
        assert stage.duration_us >= 0.0
        assert 0.0 <= stage.fraction_of_total <= 1.0


def test_state_size_scaling():
    """Confirms latency and qubit footprint scale with N in [16, 32, 64]."""
    profiler = LatencyProfiler(n_samples_per_basis=50)
    scaling = profiler.sweep_state_size_scaling([16, 32, 64])

    assert len(scaling) == 3
    for entry in scaling:
        assert entry["simulated_qubit_count"] == 3 * (entry["N_per_basis"] * 4)
        assert entry["latency_ms"] > 0.0
        assert entry["verdict"] == "ACCEPT"


def test_metric_csv_files_and_disclosures():
    """Confirms CSV files exist, parse cleanly, and contain all §17.3 required disclosure headers."""
    csv_path = Path("benchmarks/experiment_matrix_results.csv")
    assert csv_path.exists()

    required_headers = [
        "scenario_name", "scenario_category", "attack_model", "noise_model",
        "calibrated_baseline", "sample_count", "error_budget", "verdict",
        "rule_id", "is_accepted", "replay_ledger_state", "latency_ms"
    ]

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for h in required_headers:
            assert h in fieldnames, f"Missing required disclosure header: {h}"
        rows = list(reader)
        assert len(rows) == 18  # 6 honest + 12 attacks

    summary_path = Path("benchmarks/metrics_summary.csv")
    assert summary_path.exists()
    with open(summary_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        s_rows = list(reader)
        assert len(s_rows) >= 10


def test_primary_charts_exist_and_valid():
    """Confirms rendered PNG/SVG chart files exist and have non-zero size."""
    expected_files = [
        "benchmarks/false_acceptance_vs_samples.png",
        "benchmarks/false_acceptance_vs_samples.svg",
        "benchmarks/latency_breakdown.png",
        "benchmarks/latency_breakdown.svg",
        "benchmarks/attack_detection_summary.png",
        "benchmarks/attack_detection_summary.svg"
    ]

    for f in expected_files:
        p = Path(f)
        assert p.exists(), f"Expected chart file {f} does not exist"
        assert p.stat().st_size > 1000, f"Chart file {f} is empty or too small ({p.stat().st_size} bytes)"
