/**
 * Verification tab orchestrator.
 * Haiku (pre-checks) → Sonnet (cross-validation) → Opus (binding verdict).
 */
import { SubjectPanel } from './SubjectPanel';
import { useVerification } from './useVerification';
import { EMERALD, BLUE, MUTED_FG, BORDER, FG } from './tokens';

export function VerificationTab() {
  const { status, running, loading, triggerRun } = useVerification();

  const signals = status?.verifications.signals;
  const ratings = status?.verifications.ratings;
  const hasResults = signals || ratings;

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 40, color: MUTED_FG, fontSize: '0.85rem' }}>
        Loading verification status...
      </div>
    );
  }

  return (
    <div>
      {/* Header row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
        <div>
          <div style={{ fontSize: '0.85rem', fontWeight: 800, color: FG, marginBottom: 4 }}>
            Multi-Model Signal Verification
          </div>
          <div style={{ fontSize: '0.72rem', color: MUTED_FG }}>
            Haiku (statistical gates) → Sonnet (cross-validation) → Opus (binding verdict)
          </div>
        </div>
        <button
          onClick={triggerRun}
          disabled={running}
          style={{
            padding: '6px 14px', borderRadius: 6,
            background: running ? 'oklch(28% 0 0)' : 'color-mix(in oklch, oklch(69.6% .17 162.48) 15%, transparent)',
            border: `1px solid ${running ? BORDER : EMERALD}`,
            color: running ? MUTED_FG : EMERALD, fontSize: '0.75rem', fontWeight: 700,
            cursor: running ? 'not-allowed' : 'pointer', transition: 'all 0.15s',
          }}
        >
          {running ? 'RUNNING...' : 'RUN VERIFICATION'}
        </button>
      </div>

      {/* Running indicator */}
      {running && (
        <div style={{
          marginBottom: 12, padding: '10px 14px', borderRadius: 6,
          background: 'color-mix(in oklch, oklch(62.3% .214 259.815) 10%, transparent)',
          border: 'color-mix(in oklch, oklch(62.3% .214 259.815) 30%, transparent) 1px solid',
          fontSize: '0.75rem', color: BLUE, fontWeight: 600,
        }}>
          Calling Haiku → Sonnet → Opus pipeline... results appear below as they complete.
        </div>
      )}

      {/* No results yet */}
      {!hasResults && !running && (
        <div style={{ textAlign: 'center', padding: 40, color: MUTED_FG, fontSize: '0.85rem' }}>
          No verification results yet. Click RUN VERIFICATION to audit all signals and ratings.
        </div>
      )}

      {/* Results */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {signals && <SubjectPanel title="F5 MLB Edge Signals" result={signals} />}
        {ratings && <SubjectPanel title="NFL Walters Power Ratings" result={ratings} />}
      </div>

      {/* Legend */}
      {hasResults && (
        <div style={{
          marginTop: 16, padding: '12px 16px', borderRadius: 6,
          background: 'oklch(20% 0 0)', border: `1px solid ${BORDER}`,
          fontSize: '0.7rem', color: MUTED_FG, lineHeight: 1.6,
        }}>
          <span style={{ color: FG, fontWeight: 700 }}>How to read this: </span>
          VERIFIED = signals hold under independent cross-validation with no material corrections needed.
          CONDITIONAL = real signals exist but the presentation needs corrections (overstated edge, insufficient sample size, etc.).
          REJECTED = signals do not hold and should not be displayed.
          Verdicts are cached daily — click RUN VERIFICATION to refresh.
        </div>
      )}
    </div>
  );
}
