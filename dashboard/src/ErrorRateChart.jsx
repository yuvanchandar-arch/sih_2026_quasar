/**
 * ErrorRateChart — Per-basis error rates vs. thresholds.
 * Uses Recharts RadarChart + ReferenceLine to show where empirical rates
 * sit relative to calibration-aware Hoeffding thresholds.
 * Theme-matched to the QUASAR-TDS dark design system.
 */
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ReferenceLine, ResponsiveContainer, Legend, Cell
} from 'recharts';
import { motion } from 'framer-motion';

const BASIS_COLORS = {
  X: '#3b82f6', Y: '#a78bfa', Z: '#06b6d4', Bell: '#f97316',
};

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: '#1a2035', border: '1px solid rgba(255,255,255,0.1)',
      borderRadius: 8, padding: '10px 14px', fontSize: 12,
    }}>
      <div style={{ color: '#94a3b8', marginBottom: 4 }}>{label} basis</div>
      {payload.map(p => (
        <div key={p.name} style={{ color: p.fill || '#fff', fontFamily: 'JetBrains Mono, monospace' }}>
          {p.name}: {(p.value * 100).toFixed(3)}%
        </div>
      ))}
    </div>
  );
};

export default function ErrorRateChart({ payload }) {
  if (!payload) {
    return (
      <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>
          Run a session to see error-rate charts.
        </div>
      </div>
    );
  }

  const ev  = payload.evidence_values ?? {};
  const thr = payload.thresholds ?? {};

  const data = ['X', 'Y', 'Z', 'Bell'].map(b => ({
    basis:     b,
    'Error Rate':    ev[`e_${b}`] ?? 0,
    'Threshold τ':   thr[b] ?? 0,
  }));

  // Reference line: shared threshold (avg) for clarity
  const avgThreshold = Object.values(thr).reduce((a, v) => a + v, 0) / Object.values(thr).length;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
      className="chart-wrapper"
    >
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} margin={{ top: 8, right: 16, left: -8, bottom: 0 }}
          barGap={4} barCategoryGap="30%">
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="rgba(255,255,255,0.04)"
            vertical={false} />
          <XAxis dataKey="basis"
            tick={{ fill: '#94a3b8', fontSize: 11, fontFamily: 'Inter' }}
            axisLine={{ stroke: 'rgba(255,255,255,0.08)' }}
            tickLine={false} />
          <YAxis
            tickFormatter={v => `${(v * 100).toFixed(1)}%`}
            tick={{ fill: '#94a3b8', fontSize: 10, fontFamily: 'JetBrains Mono' }}
            axisLine={false} tickLine={false} />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: 11, color: '#94a3b8' }} />
          <Bar dataKey="Error Rate" radius={[4, 4, 0, 0]}>
            {data.map(entry => (
              <Cell key={entry.basis}
                fill={BASIS_COLORS[entry.basis]}
                fillOpacity={entry['Error Rate'] > entry['Threshold τ'] ? 1 : 0.7} />
            ))}
          </Bar>
          <Bar dataKey="Threshold τ" fill="rgba(239,68,68,0.3)"
            radius={[4, 4, 0, 0]} stroke="#ef4444" strokeWidth={1} />
        </BarChart>
      </ResponsiveContainer>
      <div style={{
        fontSize: 10, color: 'var(--text-muted)', marginTop: 8,
        fontFamily: 'JetBrains Mono', display: 'flex', justifyContent: 'space-between',
        flexWrap: 'wrap', gap: 6,
      }}>
        <span>Live Threshold: τ = μ̂ + δ_cal + δ_ver (Hoeffding §11.1)</span>
        <span style={{ color: '#cbd5e1' }}>μ̂=1.00% | n_cal=1000 (δ_cal=6.70%) | n_ver=500 (δ_ver=9.48%) | ε=1.25×10⁻⁴</span>
      </div>
    </motion.div>
  );
}
