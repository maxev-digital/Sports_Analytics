/**
 * Evaluations API client — fetches pregame handicapping evaluations.
 */
import { API_BASE_URL } from '../config';

function authHeaders(): HeadersInit {
  const token = localStorage.getItem('auth_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export interface Evaluation {
  id: number;
  game_id: string;
  sport: string;
  home_team: string;
  away_team: string;
  game_time_cst: string | null;
  lean_level: 'no_edge' | 'slight_lean' | 'favorable_lean' | 'strong_lean';
  lean_side: string | null;
  lean_market: 'spread' | 'total' | 'moneyline' | null;
  game_script: string | null;
  unit_rec: number;
  best_book: string | null;
  best_line: number | null;
  best_odds: number | null;
  opus_verdict: 'PASS' | 'HOLD' | null;
  signals_used: string[];
  confidence_note: string;
  created_at: string;
  is_best_bet?: boolean;
}

export interface TodayEvaluationsResponse {
  evaluations: Evaluation[];
  count: number;
  best_bet_id: number | null;
  generated_at: string;
}

export interface AtsRecord {
  lean_level: string;
  sport: string;
  record: string;
  win_rate: string;
  graded: number;
  total: number;
}

export interface RecordResponse {
  record: AtsRecord[];
  days: number;
  generated_at: string;
}

export async function fetchTodayEvaluations(
  sport?: string,
  minLean: string = 'favorable_lean',
): Promise<TodayEvaluationsResponse> {
  const params = new URLSearchParams({ min_lean: minLean });
  if (sport) params.set('sport', sport);

  const res = await fetch(
    `${API_BASE_URL}/v1/evaluations/today?${params}`,
    { headers: authHeaders() },
  );
  if (!res.ok) throw new Error(`Evaluations API ${res.status}`);
  return res.json();
}

export async function fetchEvaluationRecord(
  sport?: string,
  days: number = 30,
): Promise<RecordResponse> {
  const params = new URLSearchParams({ days: String(days) });
  if (sport) params.set('sport', sport);

  const res = await fetch(
    `${API_BASE_URL}/v1/evaluations/record?${params}`,
    { headers: authHeaders() },
  );
  if (!res.ok) throw new Error(`Record API ${res.status}`);
  return res.json();
}

// ── Persona leans ─────────────────────────────────────────────────────────────

export interface PersonaResult {
  persona: string;
  fired: boolean;
  lean_level: string;
  lean_side: string | null;
  lean_market: string | null;
  reasoning: string;
  signals_cited: string[];
}

export interface PersonaLean {
  game_id: string;
  sport: string;
  home_team: string;
  away_team: string;
  convergence_count: number;
  consensus_lean: string;
  consensus_side: string | null;
  consensus_market: string | null;
  dissent_flag: boolean;
  convergence_note: string | null;
  persona_results: PersonaResult[];
}

export interface PersonaLeansResponse {
  date: string;
  count: number;
  games: PersonaLean[];
}

export async function fetchPersonaLeans(date?: string): Promise<PersonaLeansResponse> {
  const params = date ? `?date=${date}` : '';
  const res = await fetch(
    `${API_BASE_URL}/v1/personas/${params}`,
    { headers: authHeaders() },
  );
  if (!res.ok) throw new Error(`Personas API ${res.status}`);
  return res.json();
}
