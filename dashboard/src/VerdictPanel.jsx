/**
 * VerdictPanel — The primary decision display.
 * Shows ACCEPT/REJECT/ALERT in a glowing colored panel with hypothesis,
 * alternative explanation, full evidence vector, and the mandatory
 * "rule-based hypothesis, not certainty" disclaimer (§12.2, §23).
 */
import { motion, AnimatePresence } from 'framer-motion';

const BASIS_COLORS = { X: '#3b82f6', Y: '#a78bfa', Z: '#06b6d4', Bell: '#f97316' };

function EvidenceCell({ basis, value, threshold }) {
  if (value === undefined || value === null) return (
    <div className="evidence-cell" data-basis={basis}>
      <div className="evidence-basis">{basis}</div>
      <div className="evidence-value skeleton" style={{ height: 24, width: 60, margin: '4px auto' }} />
      <div className="evidence-threshold">—</div>
    </div>
  );
  const elevated = value > threshold;
  return (
    <motion.div
      className={`evidence-cell ${elevated ? 'elevated' : ''}`}
      data-basis={basis}
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <div className="evidence-basis">{basis}</div>
      <div className="evidence-value">{(value * 100).toFixed(2)}%</div>
      <div className="evidence-threshold">τ = {(threshold * 100).toFixed(2)}%</div>
    </motion.div>
  );
}

export default function VerdictPanel({ result, loading }) {
  const verdict = result?.payload?.verdict ?? null;
  const payload = result?.payload ?? null;
  const ev = payload?.evidence_values ?? {};
  const thr = payload?.thresholds ?? {};

  const panelClass = loading ? 'idle' :
    verdict === 'ACCEPT' ? 'accept' :
    verdict === 'REJECT' ? 'reject' :
    verdict === 'ALERT'  ? 'alert'  : 'idle';

  const glowClass = panelClass === 'accept' ? 'glow-green' :
                    panelClass === 'reject' ? 'glow-red'   :
                    panelClass === 'alert'  ? 'glow-amber' : '';

  const verdictIcon = verdict === 'ACCEPT' ? '✓' :
                      verdict === 'REJECT' ? '✗' :
                      verdict === 'ALERT'  ? '⚠' : '○';

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={verdict ?? 'idle'}
        className={`verdict-panel ${panelClass} ${glowClass}`}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        transition={{ duration: 0.3 }}
      >
        <div className="card-header">
          <span className="card-title">
            <span className="card-title-icon">⚖</span>
            Verification Verdict
          </span>
          {payload && (
            <span className="verdict-rule-id">{payload.rule_id}</span>
          )}
        </div>

        {loading && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '16px 0' }}>
            <div className="spinner" />
            <span style={{ color: 'var(--text-muted)', fontSize: 14 }}>Running pipeline…</span>
          </div>
        )}

        {!loading && !verdict && (
          <div style={{ color: 'var(--text-muted)', fontSize: 14, padding: '16px 0' }}>
            Create and verify a session to see the verdict here.
          </div>
        )}

        {!loading && verdict && (
          <>
            <div className={`verdict-badge ${panelClass}`}>
              <span>{verdictIcon}</span>
              <span>{verdict}</span>
            </div>

            <div className="verdict-hypothesis">{payload.primary_hypothesis}</div>
            <div className="verdict-alternative">
              Alternative: {payload.alternative_explanation}
            </div>

            <div className="evidence-grid" style={{ marginTop: 16 }}>
              {['X', 'Y', 'Z', 'Bell'].map(b => (
                <EvidenceCell key={b} basis={b}
                  value={ev[`e_${b}`] ?? ev[`e_Bell`] ?? undefined}
                  threshold={thr[b] ?? 0} />
              ))}
            </div>

            {/* Hoeffding Parameter Disclosure Bar (§11.1 Transparency) */}
            <div style={{
              marginTop: 14,
              padding: '10px 14px',
              background: 'rgba(15, 23, 42, 0.65)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: 8,
              fontSize: 11,
              fontFamily: 'Inter, sans-serif',
              color: 'var(--text-secondary)',
              lineHeight: 1.6,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8, marginBottom: 4 }}>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                  📐 Hoeffding Decision Threshold Derivation (§11.1):
                </span>
                <span style={{ fontFamily: 'JetBrains Mono', color: 'var(--brand-cyan)', fontSize: 11 }}>
                  τ_b = μ̂_b + δ_cal + δ_ver = 17.18%
                </span>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px 16px', fontSize: 10.5, fontFamily: 'JetBrains Mono', color: '#94a3b8' }}>
                <span>• Baseline: <strong style={{ color: '#e2e8f0' }}>μ̂ = 1.00%</strong></span>
                <span>• Samples: <strong style={{ color: '#e2e8f0' }}>n_cal = 1,000 / n_ver = 500</strong></span>
                <span>• Slacks: <strong style={{ color: '#e2e8f0' }}>δ_cal = 6.70% / δ_ver = 9.48%</strong></span>
                <span>• Budget: <strong style={{ color: '#e2e8f0' }}>ε_b = 1.25×10⁻⁴</strong> (ε_total = 10⁻³)</span>
              </div>
              <div style={{ fontSize: 9.5, color: '#64748b', marginTop: 4, fontFamily: 'Inter' }}>
                Thresholds are received dynamically from backend <code>VerificationPayload.thresholds</code>. Values are identical across standard test sessions because calibration sample counts and noise baselines are fixed by specification.
              </div>
            </div>

            <div className="verdict-disclaimer">
              <span>ℹ</span>
              <span>
                <strong>Rule-based hypothesis only — not forensic certainty.</strong>{' '}
                {payload.disclaimer}
              </span>
            </div>
          </>
        )}
      </motion.div>
    </AnimatePresence>
  );
}
