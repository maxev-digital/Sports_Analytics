import { MUTED_FG } from './tokens';

export function Section({ label, color, children }: { label: string; color: string; children: React.ReactNode }) {
  return (
    <div>
      <div style={{ fontSize: '0.6rem', color, fontWeight: 800, letterSpacing: '0.1em', marginBottom: 5 }}>{label}</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>{children}</div>
    </div>
  );
}

export function FlagRow({ text, color }: { text: string; color: string }) {
  return (
    <div style={{ display: 'flex', gap: 6, alignItems: 'flex-start', fontSize: '0.7rem' }}>
      <span style={{ color, flexShrink: 0 }}>·</span>
      <span style={{ color: MUTED_FG }}>{text}</span>
    </div>
  );
}
