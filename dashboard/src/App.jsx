/**
 * QUASAR-TDS Dashboard — Main Application (Phase 09)
 * React 19 + Vite + Recharts + Framer Motion
 *
 * Panels:
 *   1. Verify (default)  — Create session, run verification, see live verdict
 *   2. Attack Lab        — Trigger any of 12 §14 attacks, see new result in real time
 *   3. Benchmarks        — Phase 07 performance data from GET /benchmark
 *   4. Session Ledger    — RESERVED→ACCEPTED/BLOCKED state-machine history
 *
 * Mandatory §12.2 / §23 disclaimer: visible on every screen via topbar and verdict panel.
 * All data sourced from Phase 08 FastAPI backend — no hardcoded / mock values.
 */
import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './index.css';

import { createSession, verifySession } from './api';
import TeleportationCircuit from './TeleportationCircuit';
import VerdictPanel from './VerdictPanel';
import ErrorRateChart from './ErrorRateChart';
import AttackPicker from './AttackPicker';
import SessionHistory from './SessionHistory';
import BenchmarkView from './BenchmarkView';

// ── Helpers ────────────────────────────────────────────────────────────────

function ts() {
  return new Date().toLocaleTimeString('en-IN', { hour12: false });
}

// ── Sidebar navigation ─────────────────────────────────────────────────────

const NAV = [
  { id: 'verify',   label: 'Verify Session',    icon: '⚖' },
  { id: 'attack',   label: 'Attack Lab',         icon: '⚔' },
  { id: 'bench',    label: 'Benchmarks',         icon: '📊' },
  { id: 'ledger',   label: 'Session Ledger',     icon: '📋' },
];

// ── Main App ───────────────────────────────────────────────────────────────

export default function App() {
  const [activeNav, setActiveNav] = useState('verify');

  // Verify panel state
  const [message,   setMessage]   = useState('Hello, QUASAR-TDS!');
  const [verifying, setVerifying] = useState(false);
  const [verifyErr, setVerifyErr] = useState(null);
  const [honestResult, setHonestResult] = useState(null);   // VerificationResponse
  const [currentSid,   setCurrentSid]   = useState(null);

  // Attack panel state
  const [attackResult, setAttackResult] = useState(null);   // AttackScenarioResponse

  // Shared session history log
  const [sessions, setSessions] = useState([]);

  // The "active" result shown in the circuit/verdict — may be honest or attack
  const displayResult = activeNav === 'attack' ? attackResult : honestResult;

  // ── Create + Verify session ──────────────────────────────────────────────
  async function handleVerify() {
    setVerifying(true);
    setVerifyErr(null);
    setHonestResult(null);
    try {
      const created = await createSession(message);
      const sid = created.sid;
      setCurrentSid(sid);
      const result = await verifySession(sid);
      setHonestResult(result);
      setSessions(prev => [...prev, {
        sid,
        type: 'honest',
        verdict: result.payload.verdict,
        ruleId:  result.payload.rule_id,
        timestamp: ts(),
      }]);
    } catch (e) {
      const msg = e?.response?.data?.detail ?? e.message ?? 'Verification failed';
      setVerifyErr(msg);
    } finally {
      setVerifying(false);
    }
  }

  // ── Attack result callback ───────────────────────────────────────────────
  const handleAttackResult = useCallback((result) => {
    setAttackResult(result);
    setSessions(prev => [...prev, {
      sid:       result.sid,
      type:      'attack',
      attackName: result.attack_name,
      verdict:   result.payload.verdict,
      ruleId:    result.payload.rule_id,
      timestamp: ts(),
    }]);
  }, []);

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="app-shell">
      {/* Top bar */}
      <header className="app-topbar">
        <div className="logo-mark">
          <div className="logo-icon">⬡</div>
          <div>
            <div className="logo-text">QUASAR-TDS</div>
            <span className="logo-sub">Quantum Threat Detection · SIH26141</span>
          </div>
        </div>

        <div className="topbar-status">
          <div className="status-dot" />
          <span>API: localhost:8000</span>
        </div>

        <div className="topbar-disclaimer">
          ⚠ All verdicts are rule-based hypotheses — not forensic certainty (§12.2)
        </div>
      </header>

      {/* Sidebar */}
      <nav className="app-sidebar" role="navigation" aria-label="Main navigation">
        <div className="sidebar-section-label">Navigation</div>
        {NAV.map(item => (
          <div
            key={item.id}
            id={`nav-${item.id}`}
            role="button"
            tabIndex={0}
            className={`nav-item ${activeNav === item.id ? 'active' : ''}`}
            onClick={() => setActiveNav(item.id)}
            onKeyDown={e => e.key === 'Enter' && setActiveNav(item.id)}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </div>
        ))}

        {/* Live session count */}
        <div style={{ marginTop: 'auto', padding: '20px', borderTop: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 8 }}>
            Session Ledger
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 20, fontWeight: 700, color: 'var(--text-primary)' }}>
            {sessions.length}
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>sessions this run</div>
          <div style={{ marginTop: 8, display: 'flex', gap: 6, fontSize: 11 }}>
            <span style={{ color: 'var(--accept-green)' }}>
              ✓ {sessions.filter(s => s.verdict === 'ACCEPT').length}
            </span>
            <span style={{ color: 'var(--alert-amber)' }}>
              ⚠ {sessions.filter(s => s.verdict === 'ALERT').length}
            </span>
            <span style={{ color: 'var(--reject-red)' }}>
              ✗ {sessions.filter(s => s.verdict === 'REJECT').length}
            </span>
          </div>
        </div>
      </nav>

      {/* Main content */}
      <main className="app-main" role="main">
        <AnimatePresence mode="wait">

          {/* ── VERIFY PANEL ──────────────────────────────────────────── */}
          {activeNav === 'verify' && (
            <motion.div key="verify"
              initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -12 }} transition={{ duration: 0.2 }}
              style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

              <div>
                <div className="page-title">Verification Pipeline</div>
                <div className="page-subtitle">
                  Create a QDS signing session and run the full §15 verification pipeline end-to-end.
                </div>
              </div>

              {/* Circuit visualizer */}
              <div className="card">
                <div className="card-header">
                  <span className="card-title">
                    <span className="card-title-icon">⚛</span>
                    Teleportation Circuit & Bell-Decoy Flow
                  </span>
                  {currentSid && (
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}>
                      SID: {currentSid}
                    </span>
                  )}
                </div>
                <TeleportationCircuit
                  sessionId={currentSid}
                  verdict={honestResult?.payload?.verdict} />
              </div>

              {/* Session creation */}
              <div className="card">
                <div className="card-header">
                  <span className="card-title">
                    <span className="card-title-icon">✉</span>
                    Message &amp; Session
                  </span>
                </div>
                <div style={{ display: 'flex', gap: 10, marginBottom: 12 }}>
                  <input
                    id="message-input"
                    className="input-field"
                    value={message}
                    onChange={e => setMessage(e.target.value)}
                    placeholder="Enter message to sign…"
                  />
                  <button
                    id="verify-btn"
                    className="btn btn-primary"
                    onClick={handleVerify}
                    disabled={verifying || !message.trim()}
                    style={{ whiteSpace: 'nowrap' }}
                  >
                    {verifying ? (
                      <><div className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} /> Verifying…</>
                    ) : '▶ Run Verification'}
                  </button>
                </div>
                {verifyErr && <div className="error-box">⚠ {verifyErr}</div>}
              </div>

              {/* Verdict */}
              <VerdictPanel result={honestResult} loading={verifying} />

              {/* Error rate charts */}
              <div className="card">
                <div className="card-header">
                  <span className="card-title">
                    <span className="card-title-icon">📈</span>
                    Per-Basis Error Rates vs. Hoeffding Thresholds
                  </span>
                  <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>PB-DTF §11.1</span>
                </div>
                <ErrorRateChart payload={honestResult?.payload} />
              </div>
            </motion.div>
          )}

          {/* ── ATTACK LAB ─────────────────────────────────────────────── */}
          {activeNav === 'attack' && (
            <motion.div key="attack"
              initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -12 }} transition={{ duration: 0.2 }}
              style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

              <div>
                <div className="page-title">Attack Scenario Lab</div>
                <div className="page-subtitle">
                  Trigger any of the 12 §14 attack injectors and watch the Q-TAM attribution update in real time.
                </div>
              </div>

              <div className="two-col">
                {/* Left: picker */}
                <div className="card">
                  <AttackPicker onResult={handleAttackResult} />
                </div>

                {/* Right: live result */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  {attackResult && (
                    <div className="card" style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: -8 }}>
                      <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--brand-violet)' }}>
                        ⚔ {attackResult.attack_name}
                      </span>
                      {' '}→ Session{' '}
                      <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                        {attackResult.sid}
                      </span>
                    </div>
                  )}
                  <VerdictPanel result={attackResult} loading={false} />
                  <div className="card">
                    <div className="card-header">
                      <span className="card-title">
                        <span className="card-title-icon">📈</span>
                        Attack Evidence — Error Rates vs. Thresholds
                      </span>
                    </div>
                    <ErrorRateChart payload={attackResult?.payload} />
                  </div>
                </div>
              </div>

              {/* Circuit for attack session */}
              {attackResult && (
                <div className="card">
                  <div className="card-header">
                    <span className="card-title">
                      <span className="card-title-icon">⚛</span>
                      Attack Session Circuit Flow
                    </span>
                  </div>
                  <TeleportationCircuit
                    sessionId={attackResult.sid}
                    verdict={attackResult.payload?.verdict} />
                </div>
              )}
            </motion.div>
          )}

          {/* ── BENCHMARKS ────────────────────────────────────────────── */}
          {activeNav === 'bench' && (
            <motion.div key="bench"
              initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -12 }} transition={{ duration: 0.2 }}
              style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

              <div>
                <div className="page-title">Performance Benchmarks</div>
                <div className="page-subtitle">
                  Phase 07 §17.1 experiment matrix — 6 honest baselines + 12 attack scenarios.
                  All §17.3 required disclosures shown. Live data from GET /benchmark.
                </div>
              </div>
              <BenchmarkView />
            </motion.div>
          )}

          {/* ── LEDGER ───────────────────────────────────────────────── */}
          {activeNav === 'ledger' && (
            <motion.div key="ledger"
              initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -12 }} transition={{ duration: 0.2 }}
              style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

              <div>
                <div className="page-title">Session Ledger</div>
                <div className="page-subtitle">
                  Replay state-machine transitions for all sessions created in this browser session.
                  RESERVED → ACCEPTED (honest) or BLOCKED (attack/replay).
                </div>
              </div>

              <div className="card">
                <SessionHistory sessions={sessions} />
              </div>

              {/* Global disclaimer — must be visible on every screen */}
              <div className="card" style={{ background: 'rgba(245,158,11,0.05)', borderColor: 'rgba(245,158,11,0.2)' }}>
                <div style={{ fontSize: 12, color: '#fbbf24', lineHeight: 1.7 }}>
                  <strong>⚠ Mandatory Disclaimer (QUASAR-TDS §12.2, §23)</strong><br />
                  All verdicts produced by this system are <em>model-based, rule-based hypotheses</em> under
                  a configured statistical model. They are not forensic certainty. QUASAR-TDS uses
                  deterministic threshold tests and an ordered rule table — no AI or machine learning is
                  used at any point in the pipeline. Verdicts should be interpreted as attack-hypothesis
                  attributions, not proof of malicious intent.
                </div>
              </div>
            </motion.div>
          )}

        </AnimatePresence>
      </main>
    </div>
  );
}
