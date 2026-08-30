import { useState } from 'react';
import { BookOpen, ExternalLink, CheckCircle, DollarSign } from 'lucide-react';
import '../styles/analytics.css';

// ── Types ─────────────────────────────────────────────────────────────────────
interface Source {
  name: string;
  description: string;
  provides: string[];
  url: string;
  cost: 'Free' | 'Free (scraper)' | 'Paid' | '$20/yr';
  wired: boolean;
}

interface SportData {
  label: string;
  color: string;
  season: string;
  grade: string;
  gradeColor: string;
  gaps: string[];
  sources: Source[];
}

// ── Design tokens ─────────────────────────────────────────────────────────────
const BRAND_RED = 'oklch(63.7% .237 25.331)';
const BLUE      = 'oklch(62.3% .214 259.815)';
const EMERALD   = 'oklch(69.6% .17 162.48)';
const YELLOW    = 'oklch(79.5% .184 86.047)';
const PURPLE    = 'oklch(65% .18 290)';
const ORANGE    = 'oklch(72% .19 55)';
const MUTED_FG  = 'oklch(70.8% 0 0)';
const BORDER    = 'oklch(100% 0 0 / .1)';
const BORDER_STR = 'oklch(100% 0 0 / .18)';

// ── Data ──────────────────────────────────────────────────────────────────────
const SPORTS: Record<string, SportData> = {
  MLB: {
    label: 'MLB', color: BRAND_RED, season: 'In Season Now',
    grade: 'C+', gradeColor: YELLOW,
    gaps: [
      'Bullpen fatigue index (pitches thrown last 3 days per reliever)',
      'Closer + setup man availability tracking',
      'Platoon splits: team wOBA vs LHP and vs RHP',
      'HP umpire tendencies: K rate + run impact (1.5 run edge)',
      'Batter vs Pitcher matchups: career OPS/K%/wOBA (Baseball Savant)',
      'Stuff+ per starting pitcher: velocity + movement + spin composite',
      'Pitch mix + velocity trend game-to-game (fatigue signal)',
      'Catcher framing runs above average',
      'Confirmed lineup check before firing projection',
      'Barometric pressure + humidity in weather model',
      'Day vs night game flag',
      'Rolling team wOBA last 10 games (hot/cold streak)',
      'xwOBA + BABIP per team (luck / regression indicators)',
    ],
    sources: [
      {
        name: 'Baseball Savant',
        description: 'Official MLB Statcast data portal. The most complete free baseball data source in existence.',
        provides: ['Statcast: exit velo, barrel rate, launch angle', 'Batter vs Pitcher career matchups', 'Catcher framing runs', 'Pitch mix + velocity per pitcher', 'Platoon splits (wOBA vs LHP/RHP)', 'xwOBA, BABIP per player/team'],
        url: 'https://baseballsavant.mlb.com',
        cost: 'Free', wired: false,
      },
      {
        name: 'MLB Stats API',
        description: 'Official MLB data API. Lineups, schedules, bullpen usage, game logs, rest days.',
        provides: ['Official confirmed lineups', 'Bullpen pitcher appearances + pitch counts', 'Days rest per pitcher', 'Schedule: series game number, home/away', 'Injury list (IL transactions)'],
        url: 'https://statsapi.mlb.com',
        cost: 'Free', wired: false,
      },
      {
        name: 'UmpScorecards',
        description: 'Tracks every home plate umpire\'s zone tendencies, run impact, and bias metrics. Gap between best and worst ump = 1.5 runs per game.',
        provides: ['HP umpire K rate vs average', 'Run impact per umpire', 'Home/away bias tendency', 'Strike zone size metrics'],
        url: 'https://umpscorecards.com',
        cost: 'Free', wired: false,
      },
      {
        name: 'FanGraphs',
        description: 'Premier sabermetrics database. Stuff+, SIERA, pitch values, and advanced splits.',
        provides: ['Stuff+ per pitcher (velocity + movement + spin)', 'SIERA (best ERA predictor)', 'K%, BB%, K-BB% rate stats', 'Pitch type values (wFB, wSL, wCH)', 'wRC+ park-adjusted offense'],
        url: 'https://fangraphs.com',
        cost: 'Free (scraper)', wired: false,
      },
      {
        name: 'Open-Meteo',
        description: 'Free weather API. Already wired for wind and temperature. Adding humidity and barometric pressure.',
        provides: ['Wind speed + direction', 'Temperature', 'Humidity (to add)', 'Barometric pressure (to add)', 'Precipitation probability'],
        url: 'https://open-meteo.com',
        cost: 'Free', wired: true,
      },
    ],
  },

  CFB: {
    label: 'CFB', color: YELLOW, season: 'Aug 30 Kickoff',
    grade: 'B-', gradeColor: EMERALD,
    gaps: [
      'EPA per play (situation-adjusted efficiency) — ESPN Stats API',
      'Returning production % (how much of last year\'s output is back)',
      'Recruiting class rank 2-year rolling average — 247Sports',
      'Pace: plays per game (tempo driver for totals)',
      'QB returning starter flag + experience level',
      'Red zone TD conversion % offense + defense',
      '3rd down conversion % offense + defense',
      'Turnover margin actual + fumble luck regression',
      'Home/away SP+ splits (some programs collapse on road)',
      'Transfer portal key additions/losses',
      'True home field value per stadium (ranges 1.5–6 pts, not generic 3.5)',
      'Computer consensus power rating (SP+, FPI, Sagarin, Massey average)',
    ],
    sources: [
      {
        name: 'ESPN Stats API',
        description: 'Powers the SP+ and FPI ratings — already partially wired. Needs EPA, red zone, 3rd down, and pace endpoints.',
        provides: ['SP+ (138 FBS teams)', 'FPI game predictions', 'EPA per play', 'Red zone conversion %', '3rd down conversion %', 'Plays per game (pace)', 'YPP offense + defense'],
        url: 'https://site.api.espn.com/apis/site/v2/sports/football/college-football',
        cost: 'Free', wired: true,
      },
      {
        name: '247Sports',
        description: 'Recruiting class rankings — the best two-year rolling class rank is a strong proxy for program talent and depth.',
        provides: ['Recruiting class rank per program', 'Transfer portal additions/losses', 'Composite recruit ratings'],
        url: 'https://247sports.com',
        cost: 'Free (scraper)', wired: false,
      },
      {
        name: 'Massey Ratings',
        description: 'Free computer consensus ratings. Average of Massey, Sagarin, and SP+ creates a cleaner signal than any single system.',
        provides: ['Computer consensus power ratings', 'Strength of schedule', 'Predicted score margins'],
        url: 'https://masseyratings.com',
        cost: 'Free', wired: false,
      },
      {
        name: 'College Football Reference',
        description: 'Historical ATS trends, returning production, and advanced box score data.',
        provides: ['Returning production % (off + def)', 'Historical ATS records', 'Turnover margin history', 'Red zone data'],
        url: 'https://www.sports-reference.com/cfb',
        cost: 'Free (scraper)', wired: false,
      },
    ],
  },

  NFL: {
    label: 'NFL', color: BLUE, season: 'Sep 2026',
    grade: 'C+', gradeColor: YELLOW,
    gaps: [
      'EPA per play offense + defense — nflfastr (free)',
      'DVOA: Defense-Adjusted Value Over Average — Football Outsiders',
      'CPOE: Completion % Over Expected (QB true accuracy)',
      'Pass/run split per team',
      'Pressure rate: QB pressures per dropback',
      'Red zone conversion % offense + defense',
      '3rd down conversion % offense + defense',
      'Full weather model: temp + wind + humidity + precipitation combined',
      'Timezone travel penalty (West→East suppresses road performance)',
      'Home/away EPA split',
      'PFF OL pass block grade vs DL pass rush grade',
      'Division clinch / playoff motivation flag',
    ],
    sources: [
      {
        name: 'nflfastr',
        description: 'Free open-source NFL play-by-play data with EPA, CPOE, success rate, and more. The industry standard for advanced NFL analytics.',
        provides: ['EPA per play (offense + defense)', 'CPOE (QB accuracy)', 'Success rate', 'Air yards', 'Home/away splits', 'Weekly updated CSVs'],
        url: 'https://www.nflfastr.com',
        cost: 'Free', wired: false,
      },
      {
        name: 'Football Outsiders (DVOA)',
        description: 'DVOA grades every play vs what an average team would do in the same situation. The most context-adjusted metric in football.',
        provides: ['DVOA overall + situation splits', 'Offensive DVOA', 'Defensive DVOA', 'Special teams DVOA', 'Variance metrics'],
        url: 'https://www.footballoutsiders.com',
        cost: 'Paid', wired: false,
      },
      {
        name: 'ESPN Stats API',
        description: 'Red zone, 3rd down, pass rate, and other team-level metrics. Already partially wired.',
        provides: ['Pass/run split', 'Red zone conversion %', '3rd down conversion %', 'Turnovers', 'Sacks + pressures'],
        url: 'https://site.api.espn.com/apis/site/v2/sports/football/nfl',
        cost: 'Free', wired: true,
      },
      {
        name: 'PFF (Pro Football Focus)',
        description: 'Play-by-play grading of every player. OL pass block grade vs DL pass rush grade is the best pressure prediction metric.',
        provides: ['OL pass block grade', 'DL pass rush grade', 'QB pressure rate', 'Coverage grades', 'Run blocking / run defense'],
        url: 'https://www.pff.com',
        cost: 'Paid', wired: false,
      },
      {
        name: 'Open-Meteo',
        description: 'NFL has the most weather variance of any sport. Cold + wind games suppress scoring significantly.',
        provides: ['Temperature (cold <35°F = -3 pts)', 'Wind (>20mph = -4 pts)', 'Humidity', 'Precipitation', 'Stadium type (dome/outdoor)'],
        url: 'https://open-meteo.com',
        cost: 'Free', wired: true,
      },
    ],
  },

  NBA: {
    label: 'NBA', color: EMERALD, season: 'Oct 2026',
    grade: 'D', gradeColor: BRAND_RED,
    gaps: [
      'Possessions per 48 (pace) — single biggest total driver in NBA',
      'Offensive rating: points per 100 possessions',
      'Defensive rating: points allowed per 100 possessions',
      'Net rating: ORtg - DRtg overall quality',
      'Four factors: eFG%, TOV%, FTr, OREB%',
      '3-in-4 / 4-in-6 schedule fatigue flags (beyond B2B)',
      'West→East travel penalty (~0.5–1.0 point suppression)',
      'Home/away net rating split',
      'Injury severity scoring (star = 5–8 real rating points)',
      'Minutes/usage per key rotation player',
      'Referee foul tendency (35 to 50+ fouls/game is a real range)',
      'Team 3-point variance (high-3pt = high outcome variance)',
    ],
    sources: [
      {
        name: 'NBA Stats API',
        description: 'Official NBA data API. Pace, four factors, net rating, lineup data, injury reports — all free.',
        provides: ['Possessions per 48 per team', 'Offensive + defensive rating', 'Net rating', 'eFG%, TOV%, FTr, OREB% (four factors)', 'Lineup data: who plays together', 'Minutes + usage per player'],
        url: 'https://stats.nba.com/stats/',
        cost: 'Free', wired: false,
      },
      {
        name: 'Basketball Reference',
        description: 'Historical database for referee foul tendencies, team splits, and advanced metrics.',
        provides: ['Referee foul rates per official', 'Home/away splits', 'Historical four factors', 'Net rating trends'],
        url: 'https://www.basketball-reference.com',
        cost: 'Free (scraper)', wired: false,
      },
    ],
  },

  NHL: {
    label: 'NHL', color: BLUE, season: 'Oct 2026',
    grade: 'D-', gradeColor: BRAND_RED,
    gaps: [
      'Corsi-for % (CF%): shot attempt share — possession proxy',
      'Fenwick: unblocked shot attempts (purer than Corsi)',
      'xG for / xG against: expected goals, quality-adjusted',
      'GSAX: goals saved above expected — true goalie quality',
      'Goalie SV% vs xSV%: actual vs expected (luck indicator)',
      'Goalie back-to-back start flag',
      'Goalie confirmed starter (teams rotate without announcement)',
      'Power play % offense + penalty kill % defense',
      'High-danger chance %: shots from prime scoring areas',
      'Score-adjusted Corsi (removes score effects)',
      'Zone entry: controlled entry vs dump-in %',
    ],
    sources: [
      {
        name: 'Natural Stat Trick',
        description: 'Best free NHL advanced stats site. Corsi, Fenwick, xG, high-danger chances, zone entries.',
        provides: ['Corsi-for % (CF%)', 'Fenwick-for %', 'xG for / xG against', 'High-danger chance %', 'Zone entry: controlled vs dump-in', 'Score-adjusted possession'],
        url: 'https://www.naturalstattrick.com',
        cost: 'Free (scraper)', wired: false,
      },
      {
        name: 'MoneyPuck API',
        description: 'Free NHL analytics API with GSAX (goals saved above expected) and team xG models.',
        provides: ['GSAX per goalie', 'Team xG for / against', 'xG model probabilities', 'Historical goalie performance'],
        url: 'https://moneypuck.com',
        cost: 'Free', wired: false,
      },
      {
        name: 'NHL Stats API',
        description: 'Official NHL data. Starting goalies, schedules, power play %, penalty kill %, and roster data.',
        provides: ['Starting goalie confirmation', 'Back-to-back schedule flag', 'Power play %', 'Penalty kill %', 'Roster + injury data'],
        url: 'https://statsapi.web.nhl.com',
        cost: 'Free', wired: false,
      },
    ],
  },

  NCAAB: {
    label: 'NCAAB', color: PURPLE, season: 'Nov 2026',
    grade: 'F', gradeColor: BRAND_RED,
    gaps: [
      'BartTorvik AdjEM, AdjO, AdjD — best free KenPom alternative',
      'Tempo (possessions per 40 min) — single biggest total driver',
      'Luck rating — artificially inflated records flag regression',
      'GameScript metric (Torvik situational efficiency)',
      'Wins Above Bubble (WAB) — quality of wins',
      'SOS rank — strength of schedule adjustment',
      'Last 40 days weighting vs full-season recency',
      'Returning production % from prior year',
      'Home court value per specific arena (2–6 pt range)',
      'Conference game flag with conference-specific adjustments',
      'Referee foul tendency (35–55+ fouls/game range)',
      'Transfer portal key additions mid-offseason',
    ],
    sources: [
      {
        name: 'BartTorvik',
        description: 'Free KenPom alternative. Adjusted efficiency, tempo, luck rating, GameScript, and WAB for all D1 teams. Build this scraper first.',
        provides: ['AdjEM, AdjO, AdjD (all D1 teams)', 'Tempo: possessions per 40', 'Luck rating', 'GameScript metric', 'Wins Above Bubble (WAB)', 'Last 40 days form weighting'],
        url: 'https://barttorvik.com',
        cost: 'Free', wired: false,
      },
      {
        name: 'KenPom',
        description: 'The gold standard for college basketball efficiency ratings. Used by every sharp shop. $20/yr.',
        provides: ['AdjEM, AdjO, AdjD', 'Tempo', 'Luck rating', 'Strength of schedule rank', 'Home court values', 'Conference efficiency'],
        url: 'https://kenpom.com',
        cost: '$20/yr', wired: false,
      },
      {
        name: 'RefAudit',
        description: 'Tracks referee foul tendencies in college basketball. The range from 35 to 55+ fouls/game is a major total signal.',
        provides: ['Referee foul rate', 'Over/under tendency per official', 'Conference-specific patterns'],
        url: 'https://refaudit.com',
        cost: 'Free', wired: false,
      },
    ],
  },
};

const SPORT_KEYS = ['MLB', 'CFB', 'NFL', 'NBA', 'NHL', 'NCAAB'];

// ── Components ────────────────────────────────────────────────────────────────
function CostBadge({ cost }: { cost: Source['cost'] }) {
  const isPaid = cost === 'Paid';
  const isScaper = cost === 'Free (scraper)';
  const color = isPaid ? ORANGE : isScaper ? YELLOW : EMERALD;
  return (
    <span style={{
      padding: '1px 7px', borderRadius: 10,
      fontSize: '0.6rem', fontWeight: 700, letterSpacing: '0.06em',
      textTransform: 'uppercase' as const,
      background: `color-mix(in oklch, ${color} 18%, transparent)`,
      color,
      border: `1px solid color-mix(in oklch, ${color} 35%, transparent)`,
    }}>
      {isPaid ? <><DollarSign size={8} style={{ display: 'inline', verticalAlign: 'middle' }} /> {cost}</> : cost}
    </span>
  );
}

function WiredBadge({ wired }: { wired: boolean }) {
  if (!wired) return null;
  return (
    <span style={{
      display: 'flex', alignItems: 'center', gap: 3,
      padding: '1px 7px', borderRadius: 10,
      fontSize: '0.6rem', fontWeight: 700,
      background: `color-mix(in oklch, ${EMERALD} 15%, transparent)`,
      color: EMERALD,
      border: `1px solid color-mix(in oklch, ${EMERALD} 30%, transparent)`,
    }}>
      <CheckCircle size={9} /> Wired
    </span>
  );
}

function SourceCard({ source, sportColor }: { source: Source; sportColor: string }) {
  return (
    <div style={{
      background: 'oklch(18% 0 0 / 0.6)',
      border: `1px solid ${BORDER_STR}`,
      borderRadius: 8,
      padding: '14px 16px',
      display: 'flex',
      flexDirection: 'column' as const,
      gap: 10,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
        <div>
          <div style={{ fontSize: '0.85rem', fontWeight: 800, color: 'oklch(96% 0 0)', marginBottom: 3 }}>
            {source.name}
          </div>
          <p style={{ fontSize: '0.73rem', color: MUTED_FG, margin: 0, lineHeight: 1.5 }}>
            {source.description}
          </p>
        </div>
        <a
          href={source.url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={e => e.stopPropagation()}
          style={{
            display: 'flex', alignItems: 'center', gap: 4, flexShrink: 0,
            padding: '4px 10px', borderRadius: 6,
            border: `1px solid color-mix(in oklch, ${sportColor} 40%, transparent)`,
            background: `color-mix(in oklch, ${sportColor} 10%, transparent)`,
            color: sportColor, fontSize: '0.65rem', fontWeight: 700,
            textDecoration: 'none',
          }}
        >
          <ExternalLink size={10} /> Visit
        </a>
      </div>

      <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' as const }}>
        <CostBadge cost={source.cost} />
        <WiredBadge wired={source.wired} />
      </div>

      <div>
        <div style={{ fontSize: '0.6rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.08em', textTransform: 'uppercase' as const, marginBottom: 6 }}>
          Provides
        </div>
        <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column' as const, gap: 3 }}>
          {source.provides.map((p, i) => (
            <li key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 6, fontSize: '0.7rem', color: 'oklch(84% 0 0)' }}>
              <span style={{ color: sportColor, marginTop: 2, flexShrink: 0 }}>›</span>
              {p}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export function ModelResearch() {
  const [activeSport, setActiveSport] = useState('MLB');
  const sport = SPORTS[activeSport];

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
          <BookOpen size={20} style={{ color: BLUE, marginTop: 2 }} />
          <div>
            <h1>MODEL RESEARCH & DATA SOURCES</h1>
            <p className="subtitle">
              Data sources, advanced analytics references, and model gap audit across all 6 sports.
              Green = wired into projection models. Everything else is on the build roadmap.
            </p>
          </div>
        </div>
      </div>

      <div className="analytics-content">

        {/* Sport tabs */}
        <div style={{ display: 'flex', gap: 4, marginBottom: 24, flexWrap: 'wrap' as const, borderBottom: `1px solid ${BORDER_STR}`, paddingBottom: 14 }}>
          {SPORT_KEYS.map(key => {
            const s = SPORTS[key];
            const active = key === activeSport;
            return (
              <button
                key={key}
                onClick={() => setActiveSport(key)}
                style={{
                  padding: '6px 16px', borderRadius: 8,
                  border: `1px solid ${active ? `color-mix(in oklch, ${s.color} 60%, transparent)` : BORDER_STR}`,
                  background: active ? `color-mix(in oklch, ${s.color} 18%, transparent)` : 'transparent',
                  color: active ? s.color : MUTED_FG,
                  fontSize: '0.72rem', fontWeight: 800, letterSpacing: '0.06em',
                  cursor: 'pointer', transition: 'all 0.15s',
                  fontFamily: 'var(--d3-font)',
                }}
              >
                {key}
                <span style={{
                  marginLeft: 6, fontSize: '0.58rem', fontWeight: 700,
                  color: s.gradeColor,
                  opacity: 0.9,
                }}>
                  {s.grade}
                </span>
              </button>
            );
          })}
        </div>

        {/* Sport header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <h2 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 900, color: sport.color, letterSpacing: '0.04em' }}>
                {sport.label}
              </h2>
              <span style={{ fontSize: '0.68rem', color: MUTED_FG, fontWeight: 600 }}>{sport.season}</span>
              <span style={{
                fontSize: '0.7rem', fontWeight: 900, color: sport.gradeColor,
                padding: '1px 8px', borderRadius: 6,
                background: `color-mix(in oklch, ${sport.gradeColor} 15%, transparent)`,
                border: `1px solid color-mix(in oklch, ${sport.gradeColor} 35%, transparent)`,
              }}>
                Model Grade: {sport.grade}
              </span>
            </div>
          </div>
        </div>

        {/* Two-column layout */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>

          {/* Left: Data sources */}
          <div>
            <div style={{ fontSize: '0.62rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.1em', textTransform: 'uppercase' as const, marginBottom: 12 }}>
              Data Sources ({sport.sources.length})
            </div>
            <div style={{ display: 'flex', flexDirection: 'column' as const, gap: 10 }}>
              {sport.sources.map(s => (
                <SourceCard key={s.name} source={s} sportColor={sport.color} />
              ))}
            </div>
          </div>

          {/* Right: Gap audit */}
          <div>
            <div style={{ fontSize: '0.62rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.1em', textTransform: 'uppercase' as const, marginBottom: 12 }}>
              Model Gaps — Build Roadmap ({sport.gaps.length} items)
            </div>
            <div style={{
              background: 'oklch(18% 0 0 / 0.6)',
              border: `1px solid ${BORDER_STR}`,
              borderRadius: 8,
              padding: '14px 16px',
            }}>
              <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column' as const, gap: 8 }}>
                {sport.gaps.map((gap, i) => (
                  <li key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                    <span style={{
                      flexShrink: 0, width: 16, height: 16, borderRadius: 3,
                      border: `1px solid color-mix(in oklch, ${sport.color} 50%, transparent)`,
                      background: `color-mix(in oklch, ${sport.color} 8%, transparent)`,
                      marginTop: 1,
                    }} />
                    <span style={{ fontSize: '0.73rem', color: 'oklch(84% 0 0)', lineHeight: 1.45 }}>{gap}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
