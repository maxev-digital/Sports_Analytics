/**
 * Reusable badge component matching the analytics design system.
 */

interface BadgeProps {
  color: string;
  label: string;
}

export function Badge({ color, label }: BadgeProps) {
  return (
    <span style={{
      padding: '2px 9px',
      borderRadius: 20,
      fontSize: '0.67rem',
      fontWeight: 700,
      letterSpacing: '0.08em',
      textTransform: 'uppercase',
      background: `color-mix(in oklch, ${color} 18%, transparent)`,
      color,
      border: `1px solid color-mix(in oklch, ${color} 40%, transparent)`,
    }}>
      {label}
    </span>
  );
}
