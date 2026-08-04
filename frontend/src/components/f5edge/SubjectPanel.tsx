import { useState } from 'react';
import { Badge } from './Badge';
import { ConfidenceBar } from './ConfidenceBar';
import { ModelCell } from './ModelCell';
import { Section, FlagRow } from './VerificationParts';
import { EMERALD, BRAND_RED, YELLOW, MUTED_FG, BORDER, CARD_BG, FG } from './tokens';
import {
  type VerificationResult,
  verdictColor, severityColor, crossValColor,
} from './VerificationTypes';

export function SubjectPanel({ title, result }: { title: string; result: VerificationResult }) {
  const [open, setOpen] = useState(false);
  const flagCount = Object.values(result.pre_check_flags).flat().length;

  return (
    <div style={{ background: CARD_BG, border: `1px solid ${BORDER}`, borderRadius: 6, overflow: 'hidden' }}>
      {/* Header */}
      <div
        onClick={() => setOpen(o => !o)}
        style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '14px 18px', cursor: 'pointer', userSelect: 'none' }}
      >
        <Badge color={verdictColor(result.verdict)} label={result.verdict ?? 'PENDING'} />
        <span style={{ fontWeight: 800, fontSize: '0.88rem', color: FG, flex: 1 }}>{title}</span>
        <span style={{ fontSize: '0.72rem', color: MUTED_FG }}>
          {new Date(result.verified_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
        </span>
        {flagCount > 0 && <Badge color={YELLOW} label={`${flagCount} FLAG${flagCount > 1 ? 'S' : ''}`} />}
        <span style={{ color: MUTED_FG, fontSize: '0.8rem' }}>{open ? '▲' : '▼'}</span>
      </div>

      {/* Confidence bar (always visible) */}
      <div style={{ padding: '0 18px 12px', borderBottom: open ? `1px solid ${BORDER}` : 'none' }}>
        <div style={{ fontSize: '0.65rem', color: MUTED_FG, marginBottom: 4, letterSpacing: '0.07em' }}>OPUS CONFIDENCE</div>
        <ConfidenceBar value={result.confidence} />
      </div>

      {/* Expanded detail */}
      {open && (
        <div style={{ padding: '14px 18px', display: 'flex', flexDirection: 'column', gap: 14 }}>

          {/* Model pipeline row */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
            <ModelCell
              label="HAIKU"
              sublabel="Statistical gates"
              badge={result.haiku.severity?.toUpperCase()}
              badgeColor={severityColor(result.haiku.severity)}
            >
              {result.haiku.data_quality_score != null && (
                <div style={{ fontSize: '0.68rem', color: MUTED_FG }}>
                  Data quality: <span style={{ color: FG, fontWeight: 700 }}>{result.haiku.data_quality_score}/100</span>
                </div>
              )}
              {result.haiku.methodology_assessment && (
                <div style={{ fontSize: '0.68rem', color: MUTED_FG }}>{result.haiku.methodology_assessment}</div>
              )}
            </ModelCell>

            <ModelCell
              label="SONNET"
              sublabel="Cross-validation"
              badge={result.sonnet.cross_validation?.toUpperCase()}
              badgeColor={crossValColor(result.sonnet.cross_validation)}
            >
              {(result.sonnet.concerns ?? []).slice(0, 2).map((c, i) => (
                <div key={i} style={{ fontSize: '0.65rem', color: YELLOW }}>· {c}</div>
              ))}
            </ModelCell>

            <ModelCell
              label="OPUS"
              sublabel="Binding verdict"
              badge={result.verdict ?? undefined}
              badgeColor={verdictColor(result.verdict)}
            >
              {result.opus.user_display_note && (
                <div style={{ fontSize: '0.65rem', color: MUTED_FG, fontStyle: 'italic' }}>
                  {result.opus.user_display_note}
                </div>
              )}
            </ModelCell>
          </div>

          {/* Haiku flags */}
          {((result.haiku.critical_flags ?? []).length > 0 || (result.haiku.anomalies ?? []).length > 0) && (
            <Section label="HAIKU FLAGS" color={YELLOW}>
              {[...(result.haiku.critical_flags ?? []), ...(result.haiku.anomalies ?? [])].map((f, i) => (
                <FlagRow key={i} text={f} color={YELLOW} />
              ))}
            </Section>
          )}

          {/* Pre-check flags */}
          {flagCount > 0 && (
            <Section label={`PRE-CHECK FLAGS (${flagCount})`} color={YELLOW}>
              {Object.entries(result.pre_check_flags).map(([name, flags]) =>
                flags.map((f, i) => (
                  <FlagRow key={`${name}-${i}`} text={`${name}: ${f}`} color={YELLOW} />
                ))
              )}
            </Section>
          )}

          {/* Required corrections */}
          {(result.opus.required_corrections ?? []).length > 0 && (
            <Section label="REQUIRED CORRECTIONS" color={BRAND_RED}>
              {result.opus.required_corrections!.map((c, i) => (
                <FlagRow key={i} text={c} color={BRAND_RED} />
              ))}
            </Section>
          )}

          {/* Verified / trusted signals */}
          {(result.opus.verified_signals ?? result.opus.trusted_for ?? []).length > 0 && (
            <Section label="VERIFIED" color={EMERALD}>
              {(result.opus.verified_signals ?? result.opus.trusted_for ?? []).map((s, i) => (
                <FlagRow key={i} text={s} color={EMERALD} />
              ))}
            </Section>
          )}

          {/* Rejected / not trusted */}
          {(result.opus.rejected_signals ?? result.opus.not_trusted_for ?? []).length > 0 && (
            <Section label="NOT VERIFIED" color={BRAND_RED}>
              {(result.opus.rejected_signals ?? result.opus.not_trusted_for ?? []).map((s, i) => (
                <FlagRow key={i} text={s} color={BRAND_RED} />
              ))}
            </Section>
          )}

          {/* Sonnet systemic issues */}
          {(result.sonnet.systemic_issues ?? []).length > 0 && (
            <Section label="SYSTEMIC ISSUES (SONNET)" color={YELLOW}>
              {result.sonnet.systemic_issues!.map((s, i) => (
                <FlagRow key={i} text={s} color={YELLOW} />
              ))}
            </Section>
          )}
        </div>
      )}
    </div>
  );
}
