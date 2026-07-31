/**
 * F5 Edge Engine — Main Page
 *
 * Baseball edge dashboard with tabbed layout:
 * - Today's Plays (bet slip)
 * - Game Breakdown (all games)
 * - Signals (performance)
 * - Edge Matrix (research)
 * - Venues (park edges)
 */
import { useState } from 'react';
import { Target, BarChart3, Layout, Database, MapPin } from 'lucide-react';
import { StatCard } from '../components/f5edge/StatCard';
import { PlayCard } from '../components/f5edge/PlayCard';
import { GameBreakdownCard } from '../components/f5edge/GameBreakdownCard';
import { SignalTable } from '../components/f5edge/SignalTable';
import { EdgeMatrix } from '../components/f5edge/EdgeMatrix';
import { VenueTable } from '../components/f5edge/VenueTable';
import { EMERALD, BRAND_RED, BLUE, MUTED_FG } from '../components/f5edge/tokens';
import type { F5GameWithPlays } from '../components/f5edge/types';
import '../styles/analytics.css';

type Tab = 'plays' | 'games' | 'signals' | 'matrix' | 'venues';

const TABS: { key: Tab; label: string; icon: React.ReactNode }[] = [
  { key: 'plays',   label: "TODAY'S PLAYS", icon: <Target size={14} /> },
  { key: 'games',   label: 'GAME BREAKDOWN', icon: <Layout size={14} /> },
  { key: 'signals', label: 'SIGNALS',        icon: <BarChart3 size={14} /> },
  { key: 'matrix',  label: 'EDGE MATRIX',    icon: <Database size={14} /> },
  { key: 'venues',  label: 'VENUES',         icon: <MapPin size={14} /> },
];

// Placeholder data — will be replaced by API calls to the daily scanner
const SAMPLE_PLAYS: F5GameWithPlays[] = [
  {
    game: {
      away_team: 'Boston Red Sox', home_team: 'Los Angeles Dodgers',
      venue: 'Dodger Stadium', away_pitcher: 'Ranger Suarez',
      home_pitcher: 'Edgardo Henriquez', away_era: 3.02, home_era: 2.79,
      era_diff: 0.23, hp_umpire: null, temp: '78', wind: '5 mph Out',
      commence: '', game_pk: 0,
    },
    plays: [
      { type: 'F5 Tie', book: 'BetMGM', tier: 1, unit: 100,
        signal: 'Ace vs Ace — ERA 3.02 vs 2.79', expected_hit: '22%',
        historical_roi: '+22.0%', needs_f5_odds: true },
      { type: 'F5 Under', book: 'Best line', tier: 1, unit: 100,
        signal: 'Both ERA < 3.50', expected_hit: '59%',
        historical_roi: '+10.7%', needs_f5_odds: true },
      { type: 'F5 Tie + Under SGP', book: 'DraftKings', tier: 1, unit: 25,
        signal: 'Correlated parlay (1.51x)', expected_hit: '18.2%',
        historical_roi: '+94.2%', needs_f5_odds: true },
      { type: 'F1 Tie + FG Under SGP', book: 'Bovada', tier: 2, unit: 25,
        signal: 'FG 8.5 / Both ERA < 3.50', expected_hit: '37%',
        historical_roi: '+50.3%', needs_f5_odds: false },
    ],
    odds: { fg_total: 8.5 },
  },
];

export function F5Edge() {
  const [activeTab, setActiveTab] = useState<Tab>('plays');

  const totalPlays = SAMPLE_PLAYS.reduce((s, g) => s + g.plays.length, 0);
  const totalRisk = SAMPLE_PLAYS.reduce((s, g) => s + g.plays.reduce((ps, p) => ps + p.unit, 0), 0);

  return (
    <div className="analytics-page">
      {/* Header */}
      <div className="analytics-header">
        <h1>F5 Edge Engine</h1>
        <p className="subtitle">
          MLB First 5 Innings — Signal-based edge detection across ties, unders, overs, and moneylines
        </p>

        {/* Stat row */}
        <div style={{ display: 'flex', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
          <StatCard label="Today's Plays" value={totalPlays.toString()} sub="across qualifying games" color={EMERALD} />
          <StatCard label="Total Risk" value={`$${totalRisk}`} sub="at recommended sizing" />
          <StatCard label="Season ROI" value="+11.2%" sub="backtest (2024)" color={EMERALD} />
          <StatCard label="Proven Signals" value="5" sub="p < 0.001" color={BLUE} />
          <StatCard label="Games Analyzed" value="4,857" sub="2023–2024" color={MUTED_FG} />
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

      {/* Content */}
      <div style={{ padding: '16px 24px', maxWidth: 1200 }}>

        {activeTab === 'plays' && (
          <div>
            {SAMPLE_PLAYS.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 40, color: MUTED_FG }}>
                No qualifying plays today. Run the scanner to check.
              </div>
            ) : (
              SAMPLE_PLAYS.flatMap((entry) =>
                entry.plays.map((play, i) => (
                  <PlayCard key={`${entry.game.game_pk}-${i}`} game={entry.game} play={play} />
                ))
              )
            )}
          </div>
        )}

        {activeTab === 'games' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {SAMPLE_PLAYS.map((entry) => (
              <GameBreakdownCard
                key={entry.game.game_pk}
                game={entry.game}
                plays={entry.plays}
                fgTotal={entry.odds.fg_total as number}
              />
            ))}
          </div>
        )}

        {activeTab === 'signals' && <SignalTable />}
        {activeTab === 'matrix' && <EdgeMatrix />}
        {activeTab === 'venues' && <VenueTable />}
      </div>
    </div>
  );
}

export default F5Edge;
