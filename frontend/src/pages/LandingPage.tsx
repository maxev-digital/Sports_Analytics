import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MetaTags } from '../components/MetaTags';

const ACCESS_CODE = 'MAXEV2026';

const FEATURES = [
  {
    icon: '📊',
    title: 'Live Matchup Cards',
    description: 'Real-time odds, power ratings, injury reports, and ATS records across NFL, CFB, MLB, NBA, and NHL — all on one card, updated every 5 minutes.',
    badge: 'Live',
    badgeBg: 'rgba(34,197,94,0.15)',
    badgeColor: '#4ADE80',
  },
  {
    icon: '📈',
    title: 'Multi-Book Odds Comparison',
    description: 'Compare lines across 15+ sportsbooks instantly. Spreads, totals, and moneylines side by side — find the best number in seconds.',
    badge: 'Live',
    badgeBg: 'rgba(34,197,94,0.15)',
    badgeColor: '#4ADE80',
  },
  {
    icon: '🤖',
    title: 'AI-Powered Analysis',
    description: 'Ask our AI analyst any sports question — game breakdowns, injury updates, Circa Survivor strategy. Powered by Claude with live web search and 7 data tools.',
    badge: 'AI',
    badgeBg: 'rgba(139,92,246,0.15)',
    badgeColor: '#A78BFA',
  },
  {
    icon: '🔬',
    title: 'SP+ & FPI Power Ratings',
    description: 'NFL and CFB power ratings from ESPN FPI and CFBD SP+ with offense, defense, and tier classifications. Edge detection when the market disagrees.',
    badge: 'Data',
    badgeBg: 'rgba(59,130,246,0.15)',
    badgeColor: '#60A5FA',
  },
  {
    icon: '🏥',
    title: 'Injury Intelligence',
    description: 'NFL injury heatmaps by position group, severity scoring, and head-to-head comparison. See which team is healthier before the market adjusts.',
    badge: 'Live',
    badgeBg: 'rgba(34,197,94,0.15)',
    badgeColor: '#4ADE80',
  },
  {
    icon: '🏆',
    title: 'Contest Tools',
    description: 'NFL Survivor pool optimizer with path builder, Monte Carlo simulation, and multi-entry strategy. Plus confidence pool rankings powered by power ratings.',
    badge: 'Pro',
    badgeBg: 'rgba(234,179,8,0.15)',
    badgeColor: '#FACC15',
  },
];

const STATS = [
  { val: '6+', lbl: 'Sports' },
  { val: '15+', lbl: 'Sportsbooks' },
  { val: 'AI', lbl: 'Analyst' },
  { val: '60', lbl: 'ML Models' },
];

export function LandingPage() {
  const navigate = useNavigate();
  const [code, setCode] = useState('');
  const [error, setError] = useState('');

  const handleAccess = (e: React.FormEvent) => {
    e.preventDefault();
    if (code.trim().toUpperCase() === ACCESS_CODE) {
      localStorage.setItem('mes_access_granted', 'true');
      navigate('/live-games');
    } else {
      setError('Invalid access code. Contact us to request access.');
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: '#000', color: '#fff' }}>
      <MetaTags title="Max EV Sports — AI-Powered Sports Analytics Platform" description="Real-time odds comparison, AI matchup analysis, power ratings, injury intelligence, and contest tools across NFL, CFB, MLB, NBA, and NHL." />

      {/* Hero — Split Layout */}
      <section style={{
        minHeight: '90vh',
        display: 'flex',
        alignItems: 'stretch',
      }}>
        {/* Left — Copy */}
        <div style={{
          flex: '0 0 54%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          padding: 'clamp(60px, 8vw, 100px) clamp(32px, 5vw, 72px)',
          position: 'relative',
          zIndex: 1,
        }}>
          {/* Label */}
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            marginBottom: 20, width: 'fit-content',
            background: 'rgba(37,99,235,0.12)',
            border: '1px solid rgba(37,99,235,0.3)',
            borderRadius: 100, padding: '5px 14px',
          }}>
            <span style={{
              width: 7, height: 7, borderRadius: '50%',
              background: '#4ADE80', boxShadow: '0 0 6px #4ADE80',
              display: 'inline-block',
            }} />
            <span style={{
              fontSize: 11, fontWeight: 700, letterSpacing: '0.12em',
              textTransform: 'uppercase' as const, color: '#60A5FA',
            }}>
              Early Access — Invite Only
            </span>
          </div>

          {/* Headline */}
          <h1 style={{
            fontFamily: 'Georgia, serif',
            fontSize: 'clamp(2rem, 3.8vw, 3.4rem)',
            color: '#fff',
            lineHeight: 1.1,
            marginBottom: 20,
            fontWeight: 700,
          }}>
            Sports Intelligence<br />
            <span style={{ color: '#EF4444' }}>Powered by AI.</span>
          </h1>

          {/* Subtitle */}
          <p style={{
            color: '#a0a0a0',
            fontSize: 'clamp(0.95rem, 1.5vw, 1.05rem)',
            lineHeight: 1.75,
            maxWidth: 460,
            marginBottom: 36,
          }}>
            Real-time odds from 15+ sportsbooks, AI-powered matchup analysis, power ratings,
            injury intelligence, and 60 ML models — all in one platform built for the analytical sports fan.
          </p>

          {/* Access Code Form */}
          <form onSubmit={handleAccess} style={{ marginBottom: 44 }}>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' as const, marginBottom: 10 }}>
              <input
                type="text"
                value={code}
                onChange={e => { setCode(e.target.value); setError(''); }}
                placeholder="Enter access code"
                style={{
                  padding: '13px 18px',
                  borderRadius: 10,
                  border: '1px solid rgba(255,255,255,0.15)',
                  background: 'rgba(255,255,255,0.06)',
                  color: '#fff',
                  fontSize: '0.95rem',
                  outline: 'none',
                  minWidth: 220,
                  fontFamily: 'inherit',
                }}
              />
              <button
                type="submit"
                style={{
                  padding: '13px 28px',
                  borderRadius: 10,
                  fontWeight: 700,
                  fontSize: '0.95rem',
                  color: '#fff',
                  background: 'linear-gradient(135deg, #2563EB, #1D4ED8)',
                  boxShadow: '0 0 24px rgba(37,99,235,0.4)',
                  cursor: 'pointer',
                  border: 'none',
                  fontFamily: 'inherit',
                  transition: 'all 0.2s',
                }}
              >
                Access Platform
              </button>
            </div>
            {error && (
              <p style={{ color: '#EF4444', fontSize: '0.85rem', margin: 0 }}>{error}</p>
            )}
          </form>

          {/* Stats row */}
          <div style={{
            display: 'flex',
            gap: 0,
            borderTop: '1px solid rgba(255,255,255,0.07)',
            paddingTop: 28,
            maxWidth: 440,
          }}>
            {STATS.map((s, i) => (
              <div key={s.lbl} style={{
                flex: 1,
                paddingRight: 16,
                marginRight: 16,
                borderRight: i < STATS.length - 1 ? '1px solid rgba(255,255,255,0.07)' : 'none',
              }}>
                <div style={{
                  fontFamily: 'Georgia, serif',
                  fontSize: '1.5rem',
                  fontWeight: 700,
                  color: '#EF4444',
                  lineHeight: 1,
                }}>{s.val}</div>
                <div style={{
                  fontSize: '0.68rem',
                  color: '#666',
                  marginTop: 4,
                  fontWeight: 600,
                  letterSpacing: '0.06em',
                  textTransform: 'uppercase' as const,
                }}>{s.lbl}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Right — Sportsbook photo */}
        <div style={{
          flex: '0 0 46%',
          position: 'relative',
          overflow: 'hidden',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundImage: 'url(/sportsbook.png)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }}>
          <div style={{
            position: 'absolute',
            inset: 0,
            background: 'rgba(0,0,0,0.52)',
          }} />
          <img
            src="/3DMaxLogo.png"
            alt="Max EV Sports"
            style={{
              width: 'min(340px, 70%)',
              opacity: 0.92,
              position: 'relative',
              zIndex: 1,
              filter: 'drop-shadow(0 0 50px rgba(59,130,246,0.35))',
            }}
          />
          {/* Left-edge fade into dark left panel */}
          <div style={{
            position: 'absolute',
            left: 0, top: 0, bottom: 0, width: 80,
            background: 'linear-gradient(to right, #000, transparent)',
          }} />
        </div>
      </section>

      {/* Features Grid */}
      <section style={{
        borderTop: '1px solid rgba(255,255,255,0.06)',
        padding: 'clamp(60px, 8vw, 100px) clamp(24px, 5vw, 72px)',
      }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <h2 style={{
            fontFamily: 'Georgia, serif',
            fontSize: 'clamp(1.5rem, 2.5vw, 2.2rem)',
            color: '#fff',
            textAlign: 'center' as const,
            marginBottom: 12,
          }}>
            Data-driven sports analysis. Every angle covered.
          </h2>
          <p style={{
            color: '#666',
            textAlign: 'center' as const,
            fontSize: '0.95rem',
            marginBottom: 56,
          }}>
            Built for the analytical sports fan — data over guesswork.
          </p>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: 24,
          }}>
            {FEATURES.map(f => (
              <div
                key={f.title}
                style={{
                  background: 'rgba(255,255,255,0.025)',
                  border: '1px solid rgba(255,255,255,0.07)',
                  borderRadius: 16,
                  padding: '28px 24px',
                  transition: 'border-color 0.2s',
                }}
              >
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginBottom: 14,
                }}>
                  <span style={{ fontSize: 28 }}>{f.icon}</span>
                  <span style={{
                    fontSize: 10,
                    fontWeight: 700,
                    letterSpacing: '0.1em',
                    textTransform: 'uppercase' as const,
                    padding: '3px 10px',
                    borderRadius: 100,
                    background: f.badgeBg,
                    color: f.badgeColor,
                  }}>
                    {f.badge}
                  </span>
                </div>
                <h3 style={{
                  color: '#fff',
                  fontSize: '1.05rem',
                  fontWeight: 700,
                  marginBottom: 10,
                }}>{f.title}</h3>
                <p style={{
                  color: '#888',
                  fontSize: '0.9rem',
                  lineHeight: 1.65,
                  margin: 0,
                }}>{f.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Data Platform Section — split layout */}
      <section style={{
        display: 'flex',
        alignItems: 'stretch',
        minHeight: 560,
        borderTop: '1px solid rgba(255,255,255,0.06)',
      }}>
        {/* Left — image */}
        <div style={{
          flex: '0 0 50%',
          position: 'relative',
          overflow: 'hidden',
          backgroundImage: 'url(/sports_data_analytics.png)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }}>
          {/* Right-edge fade into text panel */}
          <div style={{ position: 'absolute', right: 0, top: 0, bottom: 0, width: 100, background: 'linear-gradient(to right, transparent, #000)' }} />
        </div>

        {/* Right — text */}
        <div style={{
          flex: '0 0 50%',
          background: '#000',
          display: 'flex',
          alignItems: 'center',
          padding: 'clamp(48px, 6vw, 80px) clamp(36px, 5vw, 72px)',
        }}>
          <div style={{ maxWidth: 520 }}>
            {/* Label */}
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              marginBottom: 20,
              background: 'rgba(239,68,68,0.12)',
              border: '1px solid rgba(239,68,68,0.3)',
              borderRadius: 100, padding: '5px 14px',
            }}>
              <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#EF4444', boxShadow: '0 0 6px #EF4444', display: 'inline-block' }} />
              <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase' as const, color: '#F87171' }}>
                Sports Prediction Markets
              </span>
            </div>

            <h2 style={{
              fontFamily: 'Georgia, serif',
              fontSize: 'clamp(1.8rem, 2.8vw, 2.8rem)',
              color: '#fff',
              lineHeight: 1.1,
              marginBottom: 20,
              fontWeight: 700,
            }}>
              Not just odds.<br />
              <span style={{ color: '#EF4444' }}>A sports analytics engine.</span>
            </h2>

            <p style={{
              color: '#a0a0a0',
              fontSize: 'clamp(0.9rem, 1.3vw, 1rem)',
              lineHeight: 1.8,
              marginBottom: 36,
            }}>
              Sports prediction markets are driven by information asymmetry. Max EV Sports aggregates
              real-time odds data, machine learning model outputs, and historical performance metrics
              to surface where the market is mispriced — before the line moves.
            </p>

            {/* Data pillars */}
            <div style={{ display: 'flex', flexDirection: 'column' as const, gap: 18 }}>
              {[
                { label: 'Market Pricing Intelligence', desc: 'Track real-time line movement across 6+ books and identify sharp money signals before they close.' },
                { label: 'ML Prediction Engine', desc: 'Proprietary models calculate win probabilities and compare against implied market odds to quantify your edge.' },
                { label: 'Historical Data Layer', desc: 'Strategy backtesting against actual closing lines — see what systems beat the market over time, not just in theory.' },
              ].map(item => (
                <div key={item.label} style={{ display: 'flex', gap: 14, alignItems: 'flex-start' }}>
                  <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#EF4444', marginTop: 7, flexShrink: 0, boxShadow: '0 0 6px #EF4444' }} />
                  <div>
                    <span style={{ color: '#fff', fontWeight: 700, fontSize: '0.95rem' }}>{item.label} </span>
                    <span style={{ color: '#666', fontSize: '0.88rem' }}>&mdash; {item.desc}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Bottom CTA */}
      <section style={{
        borderTop: '1px solid rgba(255,255,255,0.06)',
        padding: 'clamp(60px, 6vw, 80px) clamp(24px, 5vw, 72px)',
        textAlign: 'center' as const,
      }}>
        <p style={{ color: '#555', fontSize: '0.8rem', letterSpacing: '0.1em', textTransform: 'uppercase' as const, marginBottom: 16 }}>
          Max EV Sports &mdash; Powered by Max EV Digital
        </p>
        <p style={{ color: '#444', fontSize: '0.78rem' }}>
          &copy; 2026 Max EV Digital. For entertainment and informational purposes only.
        </p>
      </section>

    </div>
  );
}
