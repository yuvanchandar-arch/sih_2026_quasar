/**
 * QUASAR-TDS Dashboard — API Client
 * Thin axios wrapper for all Phase 08 endpoints.
 * Base URL auto-detects dev (localhost:8000) vs prod (same origin).
 */
import axios from 'axios';

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

const api = axios.create({ baseURL: BASE, timeout: 30000 });

export async function createSession(messageText = 'Hello, QUASAR-TDS!', nSamples = 500) {
  const { data } = await api.post('/session', {
    message_text: messageText,
    n_samples_per_basis: nSamples,
  });
  return data;
}

export async function verifySession(sid) {
  const { data } = await api.post(`/session/${sid}/verify`);
  return data;
}

export async function getExplanation(sid) {
  const { data } = await api.get(`/session/${sid}/explanation`);
  return data;
}

export async function runAttack(attackName, nSamples = 500) {
  const { data } = await api.post('/attack', {
    attack_name: attackName,
    n_samples_per_basis: nSamples,
  });
  return data;
}

export async function getBenchmark() {
  const { data } = await api.get('/benchmark');
  return data;
}

export default api;
