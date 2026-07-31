/**
 * Stat card matching the analytics design system.
 */
import { MUTED_FG, FG } from './tokens';

interface StatCardProps {
  label: string;
  value: string;
  sub?: string;
  color?: string;
}

export function StatCard({ label, value, sub, color }: StatCardProps) {
  return (
    <div className="stat-card" style={{ minWidth: 0 }}>
      <div style={{
        fontSize: '0.65rem',
        fontWeight: 700,
        color: MUTED_FG,
        letterSpacing: '0.1em',
        textTransform: 'uppercase',
        marginBottom: 6,
      }}>
        {label}
      </div>
      <div className="stat-value" style={{ color: color ?? FG, fontSize: '1.45rem' }}>
        {value}
      </div>
      {sub && (
        <div style={{ fontSize: '0.68rem', color: MUTED_FG, marginTop: 4 }}>
          {sub}
        </div>
      )}
    </div>
  );
}
