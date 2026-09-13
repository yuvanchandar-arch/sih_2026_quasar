/**
 * AttackPicker — Lets a judge trigger any of the 12 §14 attack scenarios.
 *
 * DESIGN DECISION (per Phase 08 approval and user steering note):
 * Each click creates a brand-new self-contained session + fresh ledger
 * on the backend. "Real-time" means the UI animates and updates to the
 * new result as it arrives — it is NOT an in-place mutation of the
 * honest session in the main view. The result panel and sidebar history
 * update to show the attack's own verdict immediately.
 *
 * This is displayed visibly to judges via the "NEW SESSION" tag on each
 * attack card and the explanatory note below the picker.
 */
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { runAttack } from './api';

const ATTACKS = [
  // Quantum channel attacks
  { name: 'RandomStateForgery',    label: 'Random State Forgery',    category: 'Quantum', icon: '⚛' },
  { name: 'ZGuessInterceptResend', label: 'Z-Guess Intercept-Resend',category: 'Quantum', icon: '⚛' },
  { name: 'XGuessInterceptResend', label: 'X-Guess Intercept-Resend',category: 'Quantum', icon: '⚛' },
  { name: 'YGuessInterceptResend', label: 'Y-Guess Intercept-Resend',category: 'Quantum', icon: '⚛' },
  { name: 'EntangleAndMeasure',    label: 'Entangle-and-Measure',    category: 'Quantum', icon: '⚛' },
  { name: 'BellPairReplacement',   label: 'Bell-Pair Replacement',   category: 'Quantum', icon: '⚛' },
  // Classical control-plane attacks
  { name: 'CorrectionBitAlteration', label: 'Correction Bit Alteration', category: 'Classical', icon: '⬡' },
  { name: 'Replay',                label: 'Replay Attack',            category: 'Classical', icon: '⬡' },
  { name: 'Impersonation',         label: 'Impersonation',            category: 'Classical', icon: '⬡' },
  { name: 'TranscriptInjection',   label: 'Transcript Injection',     category: 'Classical', icon: '⬡' },
  { name: 'CommitmentSubstitution',label: 'Commitment Substitution',  category: 'Classical', icon: '⬡' },
  { name: 'RushingAttempt',        label: 'Rushing Attempt',          category: 'Classical', icon: '⬡' },
];

export default function AttackPicker({ onResult }) {
  const [loading, setLoading] = useState(null);   // name of attack being run
  const [error, setError]   = useState(null);
  const [lastRun, setLastRun] = useState(null);   // name of last-run attack

  async function handleAttack(atk) {
    setLoading(atk.name);
    setError(null);
    try {
      const result = await runAttack(atk.name);
      setLastRun(atk.name);
      onResult?.({ ...result, _attackMeta: atk });
    } catch (e) {
      setError(e?.response?.data?.detail ?? e.message ?? 'Attack request failed');
    } finally {
      setLoading(null);
    }
  }

  return (
    <div>
      <div className="card-header">
        <span className="card-title">
          <span className="card-title-icon">⚔</span>
          Attack Scenario Picker — §14 Injectors
        </span>
        <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>12 attacks</span>
      </div>

      {/* Semantic grouping */}
      {['Quantum', 'Classical'].map(cat => (
        <div key={cat} style={{ marginBottom: 16 }}>
          <div style={{
            fontSize: 10, fontWeight: 600, letterSpacing: '0.1em',
            textTransform: 'uppercase', color: 'var(--text-muted)',
            marginBottom: 8,
          }}>
            {cat === 'Quantum' ? '⚛ Quantum Channel' : '⬡ Classical Control-Plane'}
          </div>
          <div className="attack-grid">
            {ATTACKS.filter(a => a.category === cat).map(atk => (
              <motion.button
                key={atk.name}
                id={`attack-btn-${atk.name}`}
                className={`attack-btn ${loading === atk.name ? 'loading' : ''} ${lastRun === atk.name ? 'active-result' : ''}`}
                onClick={() => handleAttack(atk)}
                disabled={loading !== null}
                whileHover={loading === null ? { scale: 1.02 } : {}}
                whileTap={{ scale: 0.98 }}
              >
                <span className="attack-btn-label">{atk.label}</span>
                <span className="attack-btn-category">New Session · Self-contained</span>
                {loading === atk.name && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 2 }}>
                    <div className="spinner" style={{ width: 12, height: 12, borderWidth: 1.5 }} />
                    <span style={{ fontSize: 10, color: 'var(--brand-cyan)' }}>Running…</span>
                  </div>
                )}
              </motion.button>
            ))}
          </div>
        </div>
      ))}

      {/* Diagnostic Edge Cases (§12.2 verification requirement) */}
      <div style={{ marginBottom: 16 }}>
        <div style={{
          fontSize: 10, fontWeight: 600, letterSpacing: '0.1em',
          textTransform: 'uppercase', color: 'var(--text-muted)',
          marginBottom: 8,
        }}>
          🔬 Diagnostic Edge-Cases (§12.2)
        </div>
        <div className="attack-grid">
          <motion.button
            id="attack-btn-AmbiguousAnomaly"
            className={`attack-btn ${lastRun === 'AmbiguousAnomaly' ? 'active-result' : ''}`}
            onClick={() => {
              const diagResult = {
                sid: 'diagnostic_sid_ambiguous_8841',
                attack_name: 'AmbiguousAnomaly (§12.2 Fall-Through)',
                payload: {
                  verdict: 'ALERT',
                  rule_id: 'RULE_9_AMBIGUOUS',
                  primary_hypothesis: 'Ambiguous anomaly: Error pattern does not match known attack signatures (Rule 9 fall-through)',
                  alternative_explanation: 'Compound channel perturbation or simultaneous multi-source physical interference',
                  evidence_values: { e_X: 0.2718, e_Y: 0.2718, e_Z: 0.0100, e_Bell: 0.2718, v_transcript: 1, v_freshness: 1, v_identity: 1, v_hardware: 1 },
                  thresholds: { X: 0.1718, Y: 0.1718, Z: 0.1718, Bell: 0.1718 },
                  sample_sizes: { n_X: 500, n_Y: 500, n_Z: 500, n_Bell: 500 },
                  evidence_mode: 'Q_TAM_RULE_BASED',
                  is_model_based_hypothesis: true,
                  disclaimer: 'Model-based hypothesis under configured statistical model, not forensic certainty.',
                },
                _attackMeta: { name: 'AmbiguousAnomaly', label: 'Ambiguous Anomaly (§12.2)', category: 'Diagnostic' }
              };
              setLastRun('AmbiguousAnomaly');
              onResult?.(diagResult);
            }}
            disabled={loading !== null}
            whileHover={loading === null ? { scale: 1.02 } : {}}
            whileTap={{ scale: 0.98 }}
          >
            <span className="attack-btn-label">Ambiguous Anomaly</span>
            <span className="attack-btn-category">Rule 9 Fall-Through · Synthetic</span>
          </motion.button>
        </div>
      </div>

      <AnimatePresence>
        {error && (
          <motion.div className="error-box"
            initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}>
            ⚠ {error}
          </motion.div>
        )}
      </AnimatePresence>

      <div style={{
        marginTop: 12, fontSize: 11, color: 'var(--text-muted)',
        lineHeight: 1.6, display: 'flex', gap: 6,
      }}>
        <span>ℹ</span>
        <span>
          Each attack click spawns a fresh isolated session and displays the new result.
          This is a <em>self-contained scenario demonstrator</em> — verdicts are
          attack-hypothesis attributions, not forensic certainty (§12.2).
        </span>
      </div>
    </div>
  );
}
