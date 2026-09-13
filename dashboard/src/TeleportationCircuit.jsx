/**
 * TeleportationCircuit — Flagship Animated SVG Quantum Protocol Visualizer
 *
 * Visualizes the full §6–§15 QUASAR-TDS pipeline:
 * Alice Signer → EPR Bell Source → Teleportation + Pauli Recovery
 * → PB-DTF Detection & DBEV Decoys → Q-TAM Attribution → Final Decision Verdict
 *
 * Key Capabilities:
 * 1. Default Inline View:
 *    - Balanced viewBox (0 0 1280 410) that scales responsively to standard laptop
 *      viewports (1000px–1536px) without horizontal scrolling or edge clipping.
 *    - 118px+ horizontal gaps between nodes — zero label/node border collision.
 *    - Glassmorphic translucent cards with glowing borders and quantum glyphs.
 * 2. Interactive Presentation / Fullscreen Mode:
 *    - Dedicated "⛶ Presentation Mode" button in the toolbar.
 *    - Smooth full-viewport glassmorphic lightbox with deep inspection view.
 *    - Stage-by-stage technical legend detailing protocol formulas and roles.
 *    - Keyboard accessible (Esc closes modal).
 */
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const NODES = [
  // ── Row 1: Signer & Main Quantum Verification Channel ──
  {
    id: 'alice',
    x: 120, y: 105,
    stage: 'STAGE 1 · SIGNER',
    title: 'Alice Signer',
    detail: 'State Material |ψ⟩ & C_A',
    color: '#00d4ff',
    iconType: 'bloch',
    role: 'Prepares BB84 state material and creates binding commitments',
  },
  {
    id: 'bell',
    x: 390, y: 105,
    stage: 'STAGE 2 · SOURCE',
    title: 'EPR Bell Source',
    detail: 'Pairs |Φ⁺⟩ = (|00⟩+|11⟩)/√2',
    color: '#a855f7',
    iconType: 'entangled',
    role: 'Distributes entangled Bell pairs between Alice and Bob',
  },
  {
    id: 'tele',
    x: 660, y: 105,
    stage: 'STAGE 3 · CHANNEL',
    title: 'Teleportation',
    detail: 'BSM + Pauli X^s_x Z^s_z',
    color: '#06b6d4',
    iconType: 'teleport',
    role: 'Bell-state measurement and conditional Pauli correction channel',
  },
  {
    id: 'pbtdf',
    x: 930, y: 105,
    stage: 'STAGE 4 · DECISION',
    title: 'PB-DTF Detection',
    detail: 'Hoeffding Gate (e_b ≤ τ_b)',
    color: '#3b82f6',
    iconType: 'threshold',
    role: 'Statistical threshold comparator testing test bases X, Y, Z against Hoeffding bound',
  },

  // ── Row 2: Decoy Surveillance & Threat Attribution ──
  {
    id: 'dbev',
    x: 660, y: 310,
    stage: 'SURVEILLANCE · DECOYS',
    title: 'DBEV Decoy Test',
    detail: 'Cross-Basis Audit (e_Bell)',
    color: '#f97316',
    iconType: 'crosshair',
    role: 'Decoy state audit detecting channel-integrity anomalies and eavesdropping',
  },
  {
    id: 'qtam',
    x: 930, y: 310,
    stage: 'FORENSICS · RULES',
    title: 'Q-TAM Engine',
    detail: 'Ordered Rules 1–9 Attribution',
    color: '#ec4899',
    iconType: 'tree',
    role: 'Deterministic ordered threat attribution attributing error patterns to specific attack models',
  },

  // ── Final Outcome Sink ──
  {
    id: 'verdict',
    x: 1185, y: 205,
    stage: 'FINAL OUTCOME',
    title: 'Verdict Gate',
    detail: 'ACCEPT · ALERT · REJECT',
    color: '#10b981',
    iconType: 'shield',
    role: 'Final protocol gate outputting acceptance or attack-hypothesis alert',
  },
];

const EDGES = [
  // Upper flow (118px horizontal gaps)
  {
    from: 'alice', to: 'bell',
    label: 'State Material |ψ⟩',
    lx: 255, ly: 90,
  },
  {
    from: 'bell', to: 'tele',
    label: 'Entangled EPR Pairs',
    lx: 525, ly: 90,
  },
  {
    from: 'tele', to: 'pbtdf',
    label: 'Test Qubits (X, Y, Z)',
    lx: 795, ly: 90,
  },
  {
    from: 'pbtdf', to: 'verdict',
    label: 'All e_b ≤ τ_b (Pass)',
    lx: 1055, ly: 145,
    diagonal: true,
  },

  // Lower branch flow
  {
    from: 'tele', to: 'dbev',
    label: 'Decoy Positions',
    lx: 660, ly: 205,
    vertical: true,
  },
  {
    from: 'dbev', to: 'qtam',
    label: 'Bell Error (e_Bell)',
    lx: 795, ly: 295,
  },
  {
    from: 'pbtdf', to: 'qtam',
    label: 'Basis Error Rates',
    lx: 930, ly: 205,
    vertical: true,
  },
  {
    from: 'qtam', to: 'verdict',
    label: 'Decision D (Q-TAM)',
    lx: 1055, ly: 265,
    diagonal: true,
  },
];

function getNode(id) {
  return NODES.find(n => n.id === id);
}

/** Quantum-themed micro-glyphs (supporting visual accents) */
function QuantumGlyph({ type, color, cx, cy }) {
  switch (type) {
    case 'bloch':
      return (
        <g transform={`translate(${cx}, ${cy})`}>
          <circle r={8} fill="none" stroke={color} strokeWidth={1.3} strokeOpacity={0.9} />
          <ellipse rx={8} ry={3} fill="none" stroke={color} strokeWidth={1} strokeDasharray="2 2" strokeOpacity={0.7} />
          <line x1={0} y1={-10} x2={0} y2={10} stroke={color} strokeWidth={1.2} strokeOpacity={0.8} />
          <circle cx={3.5} cy={-4} r={1.8} fill={color} />
        </g>
      );

    case 'entangled':
      return (
        <g transform={`translate(${cx}, ${cy})`}>
          <circle cx={-3.5} cy={0} r={5.5} fill="none" stroke={color} strokeWidth={1.3} strokeOpacity={0.9} />
          <circle cx={3.5} cy={0} r={5.5} fill="none" stroke={color} strokeWidth={1.3} strokeOpacity={0.9} />
          <line x1={-1} y1={-2.5} x2={1} y2={2.5} stroke="#fff" strokeWidth={1.2} strokeOpacity={0.8} />
        </g>
      );

    case 'teleport':
      return (
        <g transform={`translate(${cx}, ${cy})`}>
          <path d="M-7,-5 Q-2,-1 -7,3" fill="none" stroke={color} strokeWidth={1.3} strokeOpacity={0.8} />
          <path d="M-3,-7 Q2,-1 -3,5" fill="none" stroke={color} strokeWidth={1.4} strokeOpacity={0.9} />
          <circle cx={2} cy={-1} r={2} fill={color} />
          <path d="M5,-4 L8,-1 L5,2" fill="none" stroke={color} strokeWidth={1.3} strokeOpacity={0.9} />
        </g>
      );

    case 'threshold':
      return (
        <g transform={`translate(${cx}, ${cy})`}>
          <rect x={-7} y={-5} width={14} height={10} rx={2} fill="none" stroke={color} strokeWidth={1.2} strokeOpacity={0.7} />
          <line x1={-7} y1={1} x2={7} y2={1} stroke={color} strokeWidth={1.5} strokeDasharray="3 2" />
          <rect x={-4} y={-2} width={3} height={5} fill={color} fillOpacity={0.6} />
          <line x1={2} y1={-5} x2={2} y2={5} stroke="#f59e0b" strokeWidth={1.5} />
        </g>
      );

    case 'crosshair':
      return (
        <g transform={`translate(${cx}, ${cy})`}>
          <circle r={7} fill="none" stroke={color} strokeWidth={1.2} strokeOpacity={0.8} />
          <line x1={-9.5} y1={0} x2={9.5} y2={0} stroke={color} strokeWidth={1.1} strokeOpacity={0.7} />
          <line x1={0} y1={-9.5} x2={0} y2={9.5} stroke={color} strokeWidth={1.1} strokeOpacity={0.7} />
          <circle r={2} fill={color} />
        </g>
      );

    case 'tree':
      return (
        <g transform={`translate(${cx}, ${cy})`}>
          <circle cx={0} cy={-6} r={2} fill={color} />
          <line x1={0} y1={-4} x2={-5} y2={3} stroke={color} strokeWidth={1.1} strokeOpacity={0.8} />
          <line x1={0} y1={-4} x2={0} y2={3} stroke={color} strokeWidth={1.1} strokeOpacity={0.8} />
          <line x1={0} y1={-4} x2={5} y2={3} stroke={color} strokeWidth={1.1} strokeOpacity={0.8} />
          <circle cx={-5} cy={4} r={1.8} fill={color} />
          <circle cx={0} cy={4} r={1.8} fill={color} />
          <circle cx={5} cy={4} r={1.8} fill={color} />
        </g>
      );

    case 'shield':
      return (
        <g transform={`translate(${cx}, ${cy})`}>
          <path d="M0,-8 L6,-4.5 L6,1.5 Q6,7 0,9.5 Q-6,7 -6,1.5 L-6,-4.5 Z" fill="none" stroke={color} strokeWidth={1.3} />
          <path d="M-2.5,0 L-0.5,2.5 L3.5,-2.5" fill="none" stroke={color} strokeWidth={1.3} strokeLinecap="round" strokeLinejoin="round" />
        </g>
      );

    default:
      return null;
  }
}

function GlassNodeCard({ node, isActive, animate }) {
  const isVerdict = node.id === 'verdict';
  const width = isVerdict ? 144 : 152;
  const height = isVerdict ? 90 : 80;
  const halfW = width / 2;
  const halfH = height / 2;

  return (
    <motion.g
      initial={animate ? { opacity: 0, scale: 0.88 } : false}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: NODES.indexOf(node) * 0.05, duration: 0.35 }}
    >
      {/* Ambient outer soft glow */}
      <rect
        x={node.x - halfW - 3}
        y={node.y - halfH - 3}
        width={width + 6}
        height={height + 6}
        rx={15}
        fill={node.color}
        opacity={isActive ? 0.22 : 0.08}
        filter="url(#glow-filter)"
      />

      {/* Glassmorphic card body */}
      <rect
        x={node.x - halfW}
        y={node.y - halfH}
        width={width}
        height={height}
        rx={12}
        fill="url(#glass-gradient)"
        stroke={node.color}
        strokeWidth={isActive ? 1.6 : 1.0}
        strokeOpacity={isActive ? 0.95 : 0.70}
      />

      {/* Glass rim top highlight */}
      <line
        x1={node.x - halfW + 10}
        y1={node.y - halfH + 1}
        x2={node.x + halfW - 10}
        y2={node.y - halfH + 1}
        stroke="rgba(255, 255, 255, 0.22)"
        strokeWidth={1}
      />

      {/* Top stage header pill */}
      <rect
        x={node.x - halfW + 8}
        y={node.y - halfH + 7}
        width={width - 16}
        height={16}
        rx={5}
        fill="rgba(255, 255, 255, 0.04)"
      />

      {/* Stage badge label */}
      <text
        x={node.x}
        y={node.y - halfH + 18.5}
        textAnchor="middle"
        fontSize={8}
        fontWeight="700"
        letterSpacing="0.08em"
        fill={node.color}
        fontFamily="Inter, sans-serif"
      >
        {node.stage}
      </text>

      {/* Quantum Glyphs accent (left of title) */}
      <QuantumGlyph
        type={node.iconType}
        color={node.color}
        cx={node.x - 52}
        cy={node.y + 3}
      />

      {/* Node title (prominent & bold) */}
      <text
        x={node.x + 7}
        y={node.y + 7.5}
        textAnchor="middle"
        fontSize={12.5}
        fontWeight="700"
        fill="#ffffff"
        fontFamily="Inter, sans-serif"
      >
        {node.title}
      </text>

      {/* Subtitle / technical detail */}
      <text
        x={node.x}
        y={node.y + 24}
        textAnchor="middle"
        fontSize={9}
        fontWeight="500"
        fill="#94a3b8"
        fontFamily="JetBrains Mono, monospace"
      >
        {node.detail}
      </text>
    </motion.g>
  );
}

function EdgeConnection({ edge, animate }) {
  const from = getNode(edge.from);
  const to = getNode(edge.to);
  if (!from || !to) return null;

  let x1, y1, x2, y2;
  const isVerdict = to.id === 'verdict';
  const fromW = 76;
  const fromH = 40;
  const toW = isVerdict ? 72 : 76;
  const toH = isVerdict ? 45 : 40;

  if (edge.vertical) {
    x1 = from.x;
    y1 = from.y + fromH;
    x2 = to.x;
    y2 = to.y - toH;
  } else if (edge.diagonal) {
    x1 = from.x + fromW;
    y1 = from.y;
    x2 = to.x - toW;
    y2 = to.y;
  } else {
    x1 = from.x + fromW;
    y1 = from.y;
    x2 = to.x - toW;
    y2 = to.y;
  }

  // Measured width to guarantee zero overlap with adjacent node borders
  const labelWidth = edge.label.length * 6.0 + 14;

  return (
    <motion.g
      initial={animate ? { opacity: 0 } : false}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.35, duration: 0.4 }}
    >
      {/* Edge connector line */}
      <line
        x1={x1} y1={y1} x2={x2} y2={y2}
        stroke="rgba(148, 163, 184, 0.32)"
        strokeWidth={1.8}
        strokeDasharray={edge.vertical ? '4 4' : undefined}
        markerEnd="url(#circuit-arrow)"
      />

      {/* Pill background behind label */}
      <rect
        x={edge.lx - labelWidth / 2}
        y={edge.ly - 9}
        width={labelWidth}
        height={18}
        rx={5}
        fill="#0b1120"
        stroke="rgba(255, 255, 255, 0.14)"
        strokeWidth={1}
      />

      {/* Label text */}
      <text
        x={edge.lx}
        y={edge.ly + 3.5}
        textAnchor="middle"
        fontSize={9.5}
        fontWeight="600"
        fill="#e2e8f0"
        fontFamily="Inter, sans-serif"
      >
        {edge.label}
      </text>
    </motion.g>
  );
}

function CircuitSvgContent({ animate, verdict }) {
  const verdictNode = NODES.find(n => n.id === 'verdict');
  if (verdictNode) {
    if (verdict === 'ACCEPT') {
      verdictNode.color = '#10b981';
      verdictNode.title = 'ACCEPT Gate';
      verdictNode.detail = 'Signature Verified ✓';
    } else if (verdict === 'ALERT') {
      verdictNode.color = '#f59e0b';
      verdictNode.title = 'ALERT Gate';
      verdictNode.detail = 'Q-TAM Attribution ⚠';
    } else if (verdict === 'REJECT') {
      verdictNode.color = '#ef4444';
      verdictNode.title = 'REJECT Gate';
      verdictNode.detail = 'Tamper Blocked ✗';
    } else {
      verdictNode.color = '#10b981';
      verdictNode.title = 'Verdict Gate';
      verdictNode.detail = 'ACCEPT · ALERT · REJECT';
    }
  }

  return (
    <svg
      className="circuit-svg"
      viewBox="0 0 1280 410"
      style={{ width: '100%', height: 'auto', display: 'block', margin: '0 auto' }}
    >
      <defs>
        <linearGradient id="glass-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#141c2f" stopOpacity="0.92" />
          <stop offset="100%" stopColor="#0a0f1d" stopOpacity="0.96" />
        </linearGradient>

        <filter id="glow-filter" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="5" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>

        <marker
          id="circuit-arrow"
          markerWidth="7"
          markerHeight="7"
          refX="6"
          refY="3.5"
          orient="auto"
        >
          <path d="M0,1 L0,6 L6,3.5 z" fill="#94a3b8" />
        </marker>
      </defs>

      {/* Static and animated edges */}
      {EDGES.map(e => (
        <EdgeConnection key={`${e.from}-${e.to}`} edge={e} animate={animate} />
      ))}

      {/* Glassmorphic Nodes */}
      {NODES.map(n => (
        <GlassNodeCard
          key={n.id}
          node={n}
          isActive={animate}
          animate={animate}
        />
      ))}

      {/* Animated quantum photon pulses along paths */}
      {animate && (
        <>
          {/* Upper primary path pulse */}
          <motion.circle
            r={4.5}
            fill="#00d4ff"
            filter="url(#glow-filter)"
            animate={{
              cx: [120, 390, 660, 930, 1185],
              cy: [105, 105, 105, 105, 205],
            }}
            transition={{ duration: 2.5, repeat: Infinity, ease: 'easeInOut' }}
          />

          {/* Lower decoy surveillance pulse */}
          <motion.circle
            r={4}
            fill="#f97316"
            filter="url(#glow-filter)"
            animate={{
              cx: [660, 660, 930, 1185],
              cy: [105, 310, 310, 205],
            }}
            transition={{ duration: 2.8, repeat: Infinity, ease: 'easeInOut', delay: 0.6 }}
          />
        </>
      )}
    </svg>
  );
}

export default function TeleportationCircuit({ sessionId, verdict }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const animate = !!sessionId;

  // Listen for Escape key to close modal
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape') setIsExpanded(false);
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div style={{ position: 'relative' }}>
      {/* Circuit Header Toolbar */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 4px 10px 4px', borderBottom: '1px solid rgba(255,255,255,0.06)',
        marginBottom: 8,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11, color: 'var(--text-muted)' }}>
          <span style={{ color: 'var(--brand-cyan)' }}>● Live Flow</span>
          <span>Dual-branch Quantum Teleportation + DBEV Surveillance Pipeline</span>
        </div>
        <button
          id="circuit-fullscreen-btn"
          className="btn btn-secondary"
          onClick={() => setIsExpanded(true)}
          style={{
            fontSize: 11, padding: '5px 10px', display: 'flex', alignItems: 'center',
            gap: 6, background: 'rgba(255,255,255,0.05)', borderColor: 'rgba(255,255,255,0.12)'
          }}
          title="Open large presentation mode"
        >
          <span>⛶</span>
          <span>Presentation Mode (Fullscreen)</span>
        </button>
      </div>

      {/* Default Inline View (Responsive, Never Clipped) */}
      <div className="circuit-container" style={{ padding: '4px 0', overflowX: 'auto' }}>
        <CircuitSvgContent animate={animate} verdict={verdict} />
      </div>

      {/* Presentation Mode / Fullscreen Modal Overlay */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            id="circuit-modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              position: 'fixed',
              inset: 0,
              zIndex: 9999,
              background: 'rgba(4, 7, 15, 0.95)',
              backdropFilter: 'blur(16px)',
              display: 'flex',
              flexDirection: 'column',
              padding: '24px 32px',
              overflowY: 'auto',
            }}
          >
            {/* Modal Header */}
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              paddingBottom: 16, borderBottom: '1px solid rgba(255,255,255,0.1)',
            }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ fontSize: 20 }}>⚛</span>
                  <span style={{ fontSize: 18, fontWeight: 700, color: '#fff' }}>
                    QUASAR-TDS Quantum Teleportation Protocol & Threat Detection Pipeline
                  </span>
                  <span style={{
                    fontSize: 10, padding: '2px 8px', borderRadius: 4,
                    background: 'rgba(0, 212, 255, 0.15)', color: '#00d4ff', border: '1px solid rgba(0, 212, 255, 0.3)'
                  }}>
                    Specification §6–§15
                  </span>
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                  Interactive presentation view · End-to-end qubit lifecycle from state preparation to attribution verdict
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                {sessionId && (
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)' }}>
                    Session: {sessionId}
                  </span>
                )}
                <button
                  id="circuit-modal-close-btn"
                  className="btn btn-secondary"
                  onClick={() => setIsExpanded(false)}
                  style={{ fontSize: 12, padding: '6px 14px' }}
                >
                  ✕ Close (Esc)
                </button>
              </div>
            </div>

            {/* Modal SVG Stage Display */}
            <div style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '24px 0',
              minHeight: '440px',
            }}>
              <div style={{ width: '100%', maxWidth: '1360px' }}>
                <CircuitSvgContent animate={animate} verdict={verdict} />
              </div>
            </div>

            {/* Stage-by-Stage Technical Breakdown Legend */}
            <div style={{
              background: 'rgba(15, 23, 42, 0.65)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: 10,
              padding: '16px 20px',
              marginTop: 'auto',
            }}>
              <div style={{
                fontSize: 11, fontWeight: 700, textTransform: 'uppercase',
                letterSpacing: '0.08em', color: 'var(--text-muted)', marginBottom: 12
              }}>
                📖 Protocol Stage Architecture (§6–§15)
              </div>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                gap: 12,
              }}>
                {NODES.map(node => (
                  <div key={node.id} style={{
                    padding: '8px 10px',
                    borderRadius: 6,
                    background: 'rgba(255,255,255,0.02)',
                    borderLeft: `3px solid ${node.color}`,
                  }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: '#fff', display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span>{node.title}</span>
                    </div>
                    <div style={{ fontSize: 10, color: node.color, fontFamily: 'JetBrains Mono', marginTop: 2 }}>
                      {node.stage}
                    </div>
                    <div style={{ fontSize: 9.5, color: '#94a3b8', marginTop: 4, lineHeight: 1.4 }}>
                      {node.role}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
