import { Badge } from './Badge';
import { BLUE, MUTED_FG } from './tokens';

interface ModelCellProps {
  label: string;
  sublabel: string;
  badge?: string;
  badgeColor?: string;
  children?: React.ReactNode;
}

export function ModelCell({ label, sublabel, badge, badgeColor, children }: ModelCellProps) {
  return (
    <div style={{ background: 'oklch(20% 0 0)', borderRadius: 5, padding: '10px 12px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
        <span style={{ fontSize: '0.65rem', fontWeight: 800, color: BLUE, letterSpacing: '0.08em' }}>{label}</span>
        {badge && <Badge color={badgeColor ?? MUTED_FG} label={badge} />}
      </div>
      <div style={{ fontSize: '0.62rem', color: MUTED_FG, marginBottom: 6, letterSpacing: '0.05em' }}>{sublabel}</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>{children}</div>
    </div>
  );
}
