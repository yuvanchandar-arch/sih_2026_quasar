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
