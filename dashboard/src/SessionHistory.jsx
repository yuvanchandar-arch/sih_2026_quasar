/**
 * SessionHistory — Replay ledger / session history view.
 * Shows state-machine transitions per session:
 *   RESERVED → ACCEPTED | BLOCKED | RELEASED
 * Sourced from the in-component session log (no separate API endpoint
 * needed — we track every session created/verified in this browser session).
 */
import { motion, AnimatePresence } from 'framer-motion';

function StateBadge({ state }) {
  return <span className={`state-badge ${state}`}>{state}</span>;
}

function VerdicBadge({ verdict }) {
  if (!verdict) return null;
  return <span className={`state-badge ${verdict}`}>{verdict}</span>;
}

export default function SessionHistory({ sessions }) {
  return (
    <div>
      <div className="card-header">
        <span className="card-title">
          <span className="card-title-icon">📋</span>
          Session Ledger — State Machine History
        </span>
        <span style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          {sessions.length} entries
        </span>
      </div>

      {sessions.length === 0 && (
        <div style={{ color: 'var(--text-muted)', fontSize: 13, padding: '12px 0' }}>
          No sessions yet. Create and verify a session above.
        </div>
      )}

      {sessions.length > 0 && (
        <div style={{ overflowX: 'auto' }}>
          <table className="ledger-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Session ID</th>
                <th>Type</th>
                <th>Transition</th>
                <th>Verdict</th>
                <th>Rule</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              <AnimatePresence initial={false}>
                {[...sessions].reverse().map((s, i) => (
                  <motion.tr key={s.sid}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.2 }}>
                    <td>{sessions.length - i}</td>
                    <td style={{ color: 'var(--brand-cyan)', maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {s.sid}
                    </td>
                    <td>
                      <span style={{
                        fontSize: 10, fontWeight: 600, letterSpacing: '0.06em',
                        padding: '2px 6px', borderRadius: 4,
                        background: s.type === 'attack'
                          ? 'rgba(139,92,246,0.15)' : 'rgba(0,212,255,0.1)',
                        color: s.type === 'attack' ? '#a78bfa' : '#00d4ff',
                      }}>
                        {s.type === 'attack' ? `⚔ ${s.attackName ?? 'Attack'}` : '✓ Honest'}
                      </span>
                    </td>
                    <td>
                      <span style={{ color: 'var(--text-muted)' }}>RESERVED</span>
                      <span style={{ color: 'var(--text-muted)', margin: '0 4px' }}>→</span>
                      <StateBadge state={
                        s.verdict === 'ACCEPT'  ? 'ACCEPTED' :
                        s.verdict === 'REJECT'  ? 'BLOCKED'  :
                        s.verdict === 'ALERT'   ? 'BLOCKED'  : 'RESERVED'
                      } />
                    </td>
                    <td><VerdicBadge verdict={s.verdict} /></td>
                    <td style={{ color: 'var(--text-muted)', fontSize: 10, maxWidth: 200, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {s.ruleId}
                    </td>
                    <td style={{ color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                      {s.timestamp}
                    </td>
                  </motion.tr>
                ))}
              </AnimatePresence>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
