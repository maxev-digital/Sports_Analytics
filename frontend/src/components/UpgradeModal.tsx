import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface UpgradeModalProps {
  featureLabel: string;
  requiredTier: 'member' | 'pro';
  onClose: () => void;
}

export function UpgradeModal({ featureLabel, requiredTier, onClose }: UpgradeModalProps) {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  const goTo = (path: string) => { onClose(); navigate(path); };

  const handleBackdrop = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) onClose();
  };

  return (
    <div
      onClick={handleBackdrop}
      style={{
        position: 'fixed', inset: 0, zIndex: 9999,
        background: 'rgba(0,0,0,0.72)',
        backdropFilter: 'blur(4px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 24,
      }}
    >
      <div style={{
        background: '#0f172a',
        border: '1px solid #1e293b',
        borderRadius: 16,
        padding: '32px 28px',
        maxWidth: 460,
        width: '100%',
        position: 'relative',
        boxShadow: '0 24px 64px rgba(0,0,0,0.6)',
      }}>
        {/* Close */}
        <button
          onClick={onClose}
          style={{ position: 'absolute', top: 14, right: 16, color: '#475569', background: 'none', border: 'none', cursor: 'pointer', fontSize: 18, lineHeight: 1 }}
        >✕</button>

        {/* Lock icon */}
        <div style={{
          width: 52, height: 52, borderRadius: '50%',
          background: 'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          margin: '0 auto 18px',
        }}>
          <svg width="24" height="24" fill="none" stroke="white" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>

        <h2 style={{ color: '#f1f5f9', fontSize: '1.2rem', fontWeight: 800, textAlign: 'center', marginBottom: 8, fontStyle: 'italic' }}>
          {requiredTier === 'member' ? 'Free Account Required' : 'Pro Access Required'}
        </h2>
        <p style={{ color: '#64748b', fontSize: '0.83rem', textAlign: 'center', marginBottom: 28, lineHeight: 1.5 }}>
          <span style={{ color: '#94a3b8', fontWeight: 600 }}>{featureLabel}</span>
          {' '}requires {requiredTier === 'member' ? 'a free account' : 'a Pro subscription ($99/yr)'}.
        </p>

        {/* Cards */}
        {requiredTier === 'member' && !isAuthenticated ? (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
              {/* Free card */}
              <div style={{ border: '1px solid #1e293b', borderRadius: 12, padding: '16px 12px', textAlign: 'center' }}>
                <div style={{ color: '#22c55e', fontWeight: 800, fontSize: '0.95rem', letterSpacing: '0.05em', marginBottom: 4 }}>FREE</div>
                <div style={{ color: '#475569', fontSize: '0.72rem', marginBottom: 14, lineHeight: 1.4 }}>
                  Sign up and unlock member features
                </div>
                <button
                  onClick={() => goTo('/signup')}
                  style={{
                    width: '100%', padding: '8px 0',
                    background: '#16a34a', color: 'white',
                    fontWeight: 700, fontSize: '0.78rem',
                    borderRadius: 8, border: 'none', cursor: 'pointer',
                    letterSpacing: '0.04em',
                  }}
                >
                  SIGN UP FREE
                </button>
              </div>
              {/* Pro card */}
              <div style={{ border: '1px solid #2563eb', borderRadius: 12, padding: '16px 12px', textAlign: 'center', background: 'rgba(37,99,235,0.07)' }}>
                <div style={{ color: '#60a5fa', fontWeight: 800, fontSize: '0.95rem', letterSpacing: '0.05em', marginBottom: 4 }}>PRO</div>
                <div style={{ color: '#475569', fontSize: '0.72rem', marginBottom: 14, lineHeight: 1.4 }}>
                  $99/yr — every feature unlocked
                </div>
                <button
                  onClick={() => goTo('/pricing')}
                  style={{
                    width: '100%', padding: '8px 0',
                    background: '#2563eb', color: 'white',
                    fontWeight: 700, fontSize: '0.78rem',
                    borderRadius: 8, border: 'none', cursor: 'pointer',
                    letterSpacing: '0.04em',
                  }}
                >
                  GET PRO
                </button>
              </div>
            </div>
            <p style={{ textAlign: 'center', fontSize: '0.75rem', color: '#334155' }}>
              Already have an account?{' '}
              <button onClick={() => goTo('/login')} style={{ color: '#60a5fa', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 600, fontSize: '0.75rem' }}>
                Sign in
              </button>
            </p>
          </>
        ) : (
          // Signed in but need pro, OR requiredTier is pro
          <div style={{ border: '1px solid #2563eb', borderRadius: 12, padding: '22px 20px', textAlign: 'center', background: 'rgba(37,99,235,0.07)' }}>
            <div style={{ color: '#60a5fa', fontWeight: 800, fontSize: '1.3rem', letterSpacing: '0.05em', marginBottom: 6 }}>
              PRO · $99 / year
            </div>
            <div style={{ color: '#64748b', fontSize: '0.83rem', marginBottom: 20, lineHeight: 1.5 }}>
              Unlock everything — model projections, F5 edge engine, advanced metrics, injury tools, prediction database, and more.
            </div>
            <button
              onClick={() => goTo('/pricing')}
              style={{
                padding: '11px 36px',
                background: 'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)',
                color: 'white', fontWeight: 800, fontSize: '0.9rem',
                borderRadius: 10, border: 'none', cursor: 'pointer',
                letterSpacing: '0.04em',
                boxShadow: '0 4px 20px rgba(37,99,235,0.35)',
              }}
            >
              UPGRADE TO PRO
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
