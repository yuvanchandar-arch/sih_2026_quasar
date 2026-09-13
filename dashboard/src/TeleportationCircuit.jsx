/**
 * TeleportationCircuit — Animated SVG visualiser
 * Shows the qubit flow: Alice (state-material) → Bell pair → Teleportation
 * → Pauli correction → Bob (verification).
 * Animates on every new `sessionId` prop change.
 */
import { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const NODES = [
  { id: 'alice',    x: 60,  y: 90,  label: 'Alice\nSigner',     icon: '⬡', color: '#00d4ff' },
  { id: 'bell',     x: 220, y: 90,  label: 'Bell\nPair |Φ⁺⟩',  icon: '⬡', color: '#8b5cf6' },
  { id: 'tele',     x: 380, y: 90,  label: 'Teleport\n+Pauli',  icon: '⬡', color: '#06b6d4' },
  { id: 'dbev',     x: 380, y: 210, label: 'DBEV\nDecoy Test',  icon: '⬡', color: '#f97316' },
  { id: 'pbtdf',    x: 540, y: 90,  label: 'PB-DTF\nThreshold', icon: '⬡', color: '#3b82f6' },
  { id: 'qtam',     x: 540, y: 210, label: 'Q-TAM\nAttribution',icon: '⬡', color: '#a78bfa' },
  { id: 'verdict',  x: 700, y: 150, label: 'Verdict',           icon: '◈', color: '#10b981' },
];

const EDGES = [
  { from: 'alice',  to: 'bell',    label: 'State material' },
  { from: 'bell',   to: 'tele',    label: 'Entangled pair' },
  { from: 'tele',   to: 'dbev',    label: 'Decoy positions' },
  { from: 'tele',   to: 'pbtdf',   label: 'Test positions' },
  { from: 'dbev',   to: 'qtam',    label: 'Bell correlation' },
  { from: 'pbtdf',  to: 'qtam',    label: 'Error rates' },
  { from: 'qtam',   to: 'verdict', label: 'Decision D' },
  { from: 'pbtdf',  to: 'verdict', label: 'ACCEPT path' },
];

function getNode(id) { return NODES.find(n => n.id === id); }

function NodeBox({ node, isActive, animate }) {
  return (
    <motion.g
      initial={animate ? { opacity: 0, scale: 0.8 } : false}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: NODES.indexOf(node) * 0.07, duration: 0.3 }}
    >
      {/* glow */}
      <ellipse cx={node.x} cy={node.y} rx={34} ry={22}
        fill={node.color} opacity={isActive ? 0.18 : 0.06} />
      {/* box */}
      <rect x={node.x - 40} y={node.y - 22} width={80} height={44}
        rx={8} fill="#141929"
        stroke={node.color} strokeWidth={isActive ? 1.5 : 0.8}
        opacity={isActive ? 1 : 0.7} />
      {/* icon */}
      <text x={node.x} y={node.y - 4} textAnchor="middle"
        fontSize={12} fill={node.color} fontWeight="700">{node.icon}</text>
      {/* label — multi-line via tspan */}
      {node.label.split('\n').map((line, i) => (
        <text key={i} x={node.x} y={node.y + 8 + i * 12}
          textAnchor="middle" fontSize={9} fill="#94a3b8" fontFamily="Inter, sans-serif">
          {line}
        </text>
      ))}
    </motion.g>
  );
}

function EdgeLine({ edge, animate }) {
  const from = getNode(edge.from);
  const to   = getNode(edge.to);
  if (!from || !to) return null;
  const mx = (from.x + to.x) / 2;
  const my = (from.y + to.y) / 2;
  return (
    <motion.g
      initial={animate ? { opacity: 0 } : false}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.5, duration: 0.4 }}
    >
      <line x1={from.x + (to.x > from.x ? 40 : -40)}
            y1={from.y}
            x2={to.x + (to.x > from.x ? -40 : 40)}
            y2={to.y}
            stroke="rgba(255,255,255,0.08)" strokeWidth={1.5}
            markerEnd="url(#arrow)" />
      <text x={mx} y={my - 6} textAnchor="middle"
        fontSize={8} fill="#4a5568" fontFamily="Inter, sans-serif">
        {edge.label}
      </text>
    </motion.g>
  );
}

export default function TeleportationCircuit({ sessionId, verdict }) {
  const animate = !!sessionId;
  const verdictNode = NODES.find(n => n.id === 'verdict');
  if (verdictNode) {
    verdictNode.color =
      verdict === 'ACCEPT' ? '#10b981' :
      verdict === 'REJECT' ? '#ef4444' :
      verdict === 'ALERT'  ? '#f59e0b' : '#10b981';
  }

  return (
    <div className="circuit-container">
      <svg className="circuit-svg" viewBox="0 0 800 290" height={200}>
        <defs>
          <marker id="arrow" markerWidth="6" markerHeight="6"
            refX="5" refY="3" orient="auto">
            <path d="M0,0 L0,6 L6,3 z" fill="rgba(255,255,255,0.2)" />
          </marker>
        </defs>
        {EDGES.map(e => <EdgeLine key={`${e.from}-${e.to}`} edge={e} animate={animate} />)}
        {NODES.map(n => (
          <NodeBox key={n.id} node={n}
            isActive={animate}
            animate={animate} />
        ))}
        {/* Photon particle along edge when active */}
        {animate && (
          <motion.circle r={3} fill="#00d4ff" opacity={0.9}
            animate={{ cx: [60, 220, 380, 540, 700], cy: [90, 90, 90, 90, 150] }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }} />
        )}
      </svg>
    </div>
  );
}
