/**
 * F5 Edge Engine — Main Page
 *
 * Baseball edge dashboard pulling live data from the F5 API.
 * Tabs: Today's Plays, Game Breakdown, Signals, Edge Matrix, Venues
 */
import { useState } from 'react';
import { Target, BarChart3, Layout, Database, MapPin, RefreshCw, Trophy, ShieldCheck } from 'lucide-react';
import { StatCard } from '../components/f5edge/StatCard';
import { PlayCard } from '../components/f5edge/PlayCard';
import { GameBreakdownCard } from '../components/f5edge/GameBreakdownCard';
import { SignalTable } from '../components/f5edge/SignalTable';
import { EdgeMatrix } from '../components/f5edge/EdgeMatrix';
import { VenueTable } from '../components/f5edge/VenueTable';
import { ResultsTab } from '../components/f5edge/ResultsTab';
import { VerificationTab } from '../components/f5edge/VerificationTab';
import { useF5Today } from '../components/f5edge/useF5Data';
import type { F5GameWithPlays } from '../components/f5edge/types';
import { EMERALD, BLUE, MUTED_FG } from '../components/f5edge/tokens';
import '../styles/analytics.css';

type Tab = 'plays' | 'games' | 'signals' | 'matrix' | 'venues' | 'results' | 'verify';

const TABS: { key: Tab; label: string; icon: React.ReactNode }[] = [
  { key: 'plays',   label: "TODAY'S PLAYS", icon: <Target size={14} /> },
  { key: 'games',   label: 'GAME BREAKDOWN', icon: <Layout size={14} /> },
  { key: 'signals', label: 'SIGNALS',        icon: <BarChart3 size={14} /> },
  { key: 'matrix',  label: 'EDGE MATRIX',    icon: <Database size={14} /> },
  { key: 'venues',  label: 'VENUES',         icon: <MapPin size={14} /> },
  { key: 'results', label: '2026 RESULTS',   icon: <Trophy size={14} /> },
  { key: 'verify',  label: 'VERIFICATION',  icon: <ShieldCheck size={14} /> },
];

export function F5Edge() {
  const [activeTab, setActiveTab] = useState<Tab>('plays');
  const { data, loading, error, refresh } = useF5Today();

  const results = data?.results ?? [];
  const withPlays = results.filter(r => r.has_plays);

  return (
    <div className="analytics-page">
      {/* Header */}
      <div className="analytics-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h1>F5 Edge Engine</h1>
            <p className="subtitle">
              MLB First 5 Innings — Signal-based edge detection across ties, unders, overs, and moneylines
            </p>
          </div>
          <button
            onClick={() => refresh(true)}
            disabled={loading}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '6px 14px', borderRadius: 6,
              background: 'var(--muted)', border: '1px solid var(--border)',
              color: 'var(--foreground)', fontSize: '0.75rem', fontWeight: 700,
              cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.5 : 1,
            }}
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
            {loading ? 'SCANNING...' : 'RESCAN'}
          </button>
        </div>

        {/* Stat row */}
        <div style={{ display: 'flex', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
          <StatCard
            label="Games Scanned"
            value={data?.games_scanned?.toString() ?? '—'}
            sub={data?.date ?? ''}
          />
          <StatCard
            label="Qualifying"
            value={data?.qualifying_games?.toString() ?? '—'}
            sub={`${data?.total_plays ?? 0} plays`}
            color={EMERALD}
          />
          <StatCard
            label="Total Risk"
            value={data ? `$${data.total_risk}` : '—'}
            sub="at recommended sizing"
          />
          <StatCard label="Season ROI" value="+11.2%" sub="backtest (2024)" color={EMERALD} />
          <StatCard label="Proven Signals" value="5" sub="p < 0.001" color={BLUE} />
          <StatCard
            label="API Credits"
            value={data?.credits_remaining?.toString() ?? '—'}
            sub="remaining"
            color={MUTED_FG}
          />
        </div>

        {/* Tabs */}
        <div className="sport-tabs">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              className={`sport-tab ${activeTab === tab.key ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.key)}
              style={{ display: 'flex', alignItems: 'center', gap: 6 }}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div style={{
          margin: '16px 24px', padding: '12px 16px', borderRadius: 6,
          background: 'color-mix(in oklch, oklch(63.7% .237 25.331) 15%, transparent)',
          border: '1px solid color-mix(in oklch, oklch(63.7% .237 25.331) 40%, transparent)',
          color: 'oklch(63.7% .237 25.331)', fontSize: '0.8rem', fontWeight: 600,
        }}>
          Scanner error: {error}. Make sure the F5 backend is running on port 8888.
        </div>
      )}

      {/* Content */}
      <div style={{ padding: '16px 24px', maxWidth: 1200 }}>
        {activeTab === 'plays' && (
          <TodaysPlays results={withPlays} loading={loading} />
        )}
        {activeTab === 'games' && (
          <GameBreakdown results={results} loading={loading} />
        )}
        {activeTab === 'signals' && <SignalTable />}
        {activeTab === 'matrix' && <EdgeMatrix />}
        {activeTab === 'venues' && <VenueTable />}
        {activeTab === 'results' && <ResultsTab />}
        {activeTab === 'verify' && <VerificationTab />}
      </div>
    </div>
  );
}

function TodaysPlays({ results, loading }: { results: F5GameWithPlays[]; loading: boolean }) {
  if (loading) return <LoadingState />;
  if (results.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: 40, color: MUTED_FG, fontSize: '0.85rem' }}>
        No qualifying plays found. Click RESCAN to check live games.
      </div>
    );
  }
  return (
    <div>
      {results.flatMap((entry) =>
        entry.plays.map((play, i) => (
          <PlayCard key={`${entry.game.game_pk}-${i}`} game={entry.game} play={play} odds={entry.odds} />
        ))
      )}
    </div>
  );
}

function GameBreakdown({ results, loading }: { results: F5GameWithPlays[]; loading: boolean }) {
  if (loading) return <LoadingState />;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {results.map((entry) => (
        <GameBreakdownCard
          key={entry.game.game_pk}
          game={entry.game}
          plays={entry.plays}
          odds={entry.odds}
        />
      ))}
    </div>
  );
}

function LoadingState() {
  return (
    <div style={{ textAlign: 'center', padding: 40, color: MUTED_FG, fontSize: '0.85rem' }}>
      Scanning games...
    </div>
  );
}

export default F5Edge;
