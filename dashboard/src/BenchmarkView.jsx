/**
 * BenchmarkView — Phase 07 performance data from GET /benchmark.
 * Displays the 18-row experiment matrix (6 honest + 12 attack)
 * with all §17.3 required disclosure fields, plus a summary chart
 * of latency across scenarios.
 */
import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { getBenchmark } from './api';

const VERDICT_COLORS = { ACCEPT: '#10b981', ALERT: '#f59e0b', REJECT: '#ef4444' };

export default function BenchmarkView() {
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState(null);

  useEffect(() => {
    getBenchmark()
      .then(d => setData(d))
      .catch(e => setError(e?.response?.data?.detail ?? e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--text-muted)' }}>
      <div className="spinner" /> Loading Phase 07 benchmark data…
    </div>
  );

  if (error) return <div className="error-box">⚠ {error}</div>;
  if (!data) return null;

  const chartData = data.rows.map(r => ({
    name: r.scenario_name.replace('Honest Baseline (', '').replace('Attack: ', '').replace(')', ''),
    latency: r.latency_ms,
    verdict: r.verdict,
  }));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Summary metric tiles */}
      <div className="three-col">
        <div className="metric-tile">
          <div className="metric-label">Total Scenarios</div>
          <div className="metric-value">{data.row_count}</div>
          <div className="metric-sub">6 honest + 12 attack</div>
        </div>
        <div className="metric-tile">
          <div className="metric-label">Classical Fast-Path</div>
          <div className="metric-value" style={{ fontSize: 22 }}>~0.29ms</div>
          <div className="metric-sub">~3,500 sessions/sec</div>
        </div>
        <div className="metric-tile">
          <div className="metric-label">Full Quantum Pipeline</div>
          <div className="metric-value" style={{ fontSize: 22 }}>~5.04ms</div>
          <div className="metric-sub">~198.6 sessions/sec</div>
        </div>
      </div>

      {/* Latency chart */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">
            <span className="card-title-icon">⏱</span>
            Verification Latency by Scenario (ms)
          </span>
        </div>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={chartData} margin={{ top: 8, right: 12, left: -12, bottom: 70 }}>
            <XAxis dataKey="name" tick={{ fontSize: 9.5, fill: '#94a3b8', fontFamily: 'Inter, sans-serif' }}
              angle={-38} textAnchor="end" interval={0} height={65} />
            <YAxis tickFormatter={v => `${v.toFixed(1)}ms`}
              tick={{ fontSize: 10, fill: '#94a3b8', fontFamily: 'JetBrains Mono' }}
              axisLine={false} tickLine={false} />
            <Tooltip
              formatter={(v) => [`${v.toFixed(3)} ms`, 'Latency']}
              contentStyle={{ background: '#1a2035', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }} />
            <Bar dataKey="latency" radius={[4, 4, 0, 0]}>
              {chartData.map((entry, i) => (
                <Cell key={i} fill={VERDICT_COLORS[entry.verdict] ?? '#3b82f6'} fillOpacity={0.85} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>
          Color: <span style={{ color: '#10b981' }}>■ ACCEPT</span>{' '}
          <span style={{ color: '#f59e0b' }}>■ ALERT</span>{' '}
          <span style={{ color: '#ef4444' }}>■ REJECT</span>
        </div>
      </div>

      {/* Full matrix table */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">
            <span className="card-title-icon">📊</span>
            Phase 07 Experiment Matrix — §17.1 (with §17.3 Disclosures)
          </span>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table className="bench-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Scenario</th>
                <th>Category</th>
                <th>Noise Model</th>
                <th>Verdict</th>
                <th>Rule</th>
                <th>e_X</th><th>e_Y</th><th>e_Z</th><th>e_Bell</th>
                <th>Latency</th>
                <th>n_cal / n_ver</th>
              </tr>
            </thead>
            <tbody>
              {data.rows.map(r => {
                let sampleCount = {};
                try { sampleCount = JSON.parse(r.sample_count); } catch (_) {}
                const nCal = sampleCount.n_cal ? (typeof sampleCount.n_cal === 'object' ? sampleCount.n_cal.X : sampleCount.n_cal) : '1000';
                const nVer = sampleCount.n_ver ? (typeof sampleCount.n_ver === 'object' ? sampleCount.n_ver.X : sampleCount.n_ver) : '500';
                return (
                  <tr key={r.scenario_id}>
                    <td>{r.scenario_id}</td>
                    <td style={{ color: 'var(--text-primary)', maxWidth: 180, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{r.scenario_name}</td>
                    <td style={{ color: r.scenario_category === 'Honest Baseline' ? '#10b981' : '#a78bfa', fontSize: 10 }}>{r.scenario_category}</td>
                    <td style={{ fontSize: 10 }}>{r.noise_model}</td>
                    <td><span className={`state-badge ${r.verdict}`}>{r.verdict}</span></td>
                    <td style={{ fontSize: 10 }}>{r.rule_id}</td>
                    <td>{(r.empirical_e_X * 100).toFixed(2)}%</td>
                    <td>{(r.empirical_e_Y * 100).toFixed(2)}%</td>
                    <td>{(r.empirical_e_Z * 100).toFixed(2)}%</td>
                    <td>{(r.empirical_e_Bell * 100).toFixed(2)}%</td>
                    <td>{r.latency_ms.toFixed(2)}ms</td>
                    <td style={{ fontSize: 10 }}>
                      {nCal} / {nVer}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 8 }}>
          Cross-reference: rows 7–18 are single confirmatory runs (Phase 06 e2e consistency),
          not the n=200 statistical batches from Phase 05. See phase07_performance_report.md.
        </div>
      </div>
    </div>
  );
}
