import { EMERALD, YELLOW, BRAND_RED } from './tokens';

export function ConfidenceBar({ value }: { value: number }) {
  const color = value >= 70 ? EMERALD : value >= 45 ? YELLOW : BRAND_RED;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{ flex: 1, height: 6, background: 'oklch(30% 0 0)', borderRadius: 3, overflow: 'hidden' }}>
        <div style={{ width: `${value}%`, height: '100%', background: color, borderRadius: 3 }} />
      </div>
      <span style={{ fontSize: '0.75rem', fontWeight: 800, color, fontFamily: 'monospace', minWidth: 36 }}>
        {value}%
      </span>
    </div>
  );
}
