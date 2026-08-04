/**
 * Verification pipeline — shared types and color helpers.
 */

export const VERIFICATION_API_BASE = import.meta.env.DEV
  ? 'http://localhost:8888/api/f5'
  : '/api/f5';

export type VerdictType = 'VERIFIED' | 'CONDITIONAL' | 'REJECTED' | null;

export interface OpusResult {
  verdict?: VerdictType;
  confidence?: number;
  verified_signals?: string[];
  rejected_signals?: string[];
  required_corrections?: string[];
  user_display_note?: string;
  trusted_for?: string[];
  not_trusted_for?: string[];
  notes?: string;
}

export interface HaikuResult {
  severity?: 'ok' | 'warn' | 'fail';
  critical_flags?: string[];
  data_quality_score?: number;
  anomalies?: string[];
  methodology_assessment?: string;
}

export interface SonnetResult {
  cross_validation?: 'pass' | 'partial' | 'fail';
  concerns?: string[];
  systemic_issues?: string[];
}

export interface VerificationResult {
  subject: string;
  verified_at: string;
  verdict: VerdictType;
  confidence: number;
  haiku: HaikuResult;
  sonnet: SonnetResult;
  opus: OpusResult;
  pre_check_flags: Record<string, string[]>;
}

export interface VerificationStatus {
  status: string;
  verifications: {
    signals: VerificationResult | null;
    ratings: VerificationResult | null;
  };
  running?: boolean;
}

import { EMERALD, BRAND_RED, YELLOW, MUTED_FG } from './tokens';

export function verdictColor(v: VerdictType): string {
  if (v === 'VERIFIED') return EMERALD;
  if (v === 'CONDITIONAL') return YELLOW;
  if (v === 'REJECTED') return BRAND_RED;
  return MUTED_FG;
}

export function severityColor(s?: string): string {
  if (s === 'ok') return EMERALD;
  if (s === 'warn') return YELLOW;
  if (s === 'fail') return BRAND_RED;
  return MUTED_FG;
}

export function crossValColor(v?: string): string {
  if (v === 'pass') return EMERALD;
  if (v === 'partial') return YELLOW;
  if (v === 'fail') return BRAND_RED;
  return MUTED_FG;
}
