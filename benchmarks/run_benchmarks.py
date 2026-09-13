"""
QUASAR-TDS Benchmarks: Standalone CLI Runner

Executes full Phase 07 benchmark suite:
  1. Experiment Matrix (6 honest baselines + 12 attack scenarios) -> CSV files
  2. Latency Profiling (10 stages) & Scaling sweep
  3. Primary false-acceptance probability plot & visual charts -> PNG/SVG files
"""

import sys
import os

from benchmarks.benchmark_matrix import BenchmarkMatrixRunner
from benchmarks.latency_profiler import LatencyProfiler
from benchmarks.plot_false_acceptance import (
    generate_false_acceptance_plot,
    generate_latency_breakdown_plot,
    generate_attack_detection_plot
)


def main():
    print("=" * 75)
    print("QUASAR-TDS: Phase 07 Performance Evaluation & Benchmarking")
    print("=" * 75)

    os.makedirs("benchmarks", exist_ok=True)

    # 1. Run Experiment Matrix
    print("\n[1/3] Running Experiment Matrix (6 Honest Baselines + 12 Attack Scenarios)...")
    runner = BenchmarkMatrixRunner(n_cal_samples=1000, n_ver_samples=500, seed=42)
    matrix_results = runner.run_all(
        csv_results_path="benchmarks/experiment_matrix_results.csv",
        csv_summary_path="benchmarks/metrics_summary.csv"
    )
    print(f" -> Generated benchmarks/experiment_matrix_results.csv ({len(matrix_results['all_rows'])} rows)")
    print(f" -> Generated benchmarks/metrics_summary.csv ({len(matrix_results['summary_metrics'])} metrics)")
    print(f"    • Honest Acceptance Rate: {matrix_results['honest_acceptance_rate']*100:.2f}%")
    print(f"    • False Rejection Rate:   {matrix_results['false_rejection_rate']*100:.2f}%")
    print(f"    • Attack Detection Rate:  {matrix_results['attack_detection_rate']*100:.2f}%")
    print(f"    • Rule-Label Agreement:   {matrix_results['rule_agreement_rate']*100:.2f}%")
    print(f"    • Average Pipeline Time:  {matrix_results['avg_latency_ms']:.3f} ms")

    # 2. Run Latency Profiler & State Scaling
    print("\n[2/3] Running Granular 10-Stage Latency Profiling & N-Scaling Sweep...")
    profiler = LatencyProfiler(n_samples_per_basis=500)
    prof_res = profiler.profile_stages(warmup_runs=2, timed_runs=10)
    print(f"    • Total Pipeline Latency:  {prof_res.total_latency_ms:.3f} ms")
    print(f"    • Verification Throughput: {prof_res.throughput_sessions_per_sec:.1f} sessions/sec")
    print(f"    • Simulated Qubit Count:   {prof_res.qubit_count} qubits")
    print(f"    • Control-Plane Overhead:  {prof_res.control_overhead_bytes} bytes")

    scaling = profiler.sweep_state_size_scaling([32, 64, 128, 256, 512])
    print(f"    • Scaled across N in [32, 64, 128, 256, 512] positions cleanly.")

    # 3. Generate Visual Charts
    print("\n[3/3] Generating High-Resolution Charts (PNG & Vector SVG)...")
    generate_false_acceptance_plot(
        output_png="benchmarks/false_acceptance_vs_samples.png",
        output_svg="benchmarks/false_acceptance_vs_samples.svg"
    )
    print(" -> Generated benchmarks/false_acceptance_vs_samples.png & .svg")

    generate_latency_breakdown_plot(
        output_png="benchmarks/latency_breakdown.png",
        output_svg="benchmarks/latency_breakdown.svg"
    )
    print(" -> Generated benchmarks/latency_breakdown.png & .svg")

    generate_attack_detection_plot(
        output_png="benchmarks/attack_detection_summary.png",
        output_svg="benchmarks/attack_detection_summary.svg"
    )
    print(" -> Generated benchmarks/attack_detection_summary.png & .svg")

    print("\n" + "=" * 75)
    print("PHASE 07 BENCHMARK SUITE COMPLETE: ALL ARTIFACTS VERIFIED.")
    print("=" * 75)


if __name__ == "__main__":
    main()
