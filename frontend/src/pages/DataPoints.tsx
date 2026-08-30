/**
 * Data Points — Full inventory of every signal, metric, and data point
 * that feeds the Max EV handicapping models and agents, organized by sport.
 *
 * Two views:
 *   LIVE  — currently wired, feeds into today's evaluations
 *   PLANNED — on the roadmap, not yet wired
 */
import { useState } from 'react';
import '../styles/analytics.css';

// ── Design tokens ─────────────────────────────────────────────────────────────
const EMERALD  = 'oklch(69.6% .17 162.48)';
const YELLOW   = 'oklch(79.5% .184 86.047)';
const BLUE     = 'oklch(62.3% .214 259.815)';
const RED      = 'oklch(63.7% .237 25.331)';
const PURPLE   = 'oklch(65% .18 290)';
const ORANGE   = 'oklch(72% .19 55)';
const MUTED    = 'oklch(70.8% 0 0)';
const BORDER   = 'oklch(100% 0 0 / .1)';
const CARD_BG  = 'oklch(24% 0 0)';

// ── Types ─────────────────────────────────────────────────────────────────────
type SignalStatus = 'live' | 'planned' | 'partial';

interface Signal {
  label: string;
  detail?: string;
  status: SignalStatus;
  source?: string;
  usedBy?: string; // which agent/persona uses it
}

interface SignalGroup {
  category: string;
  signals: Signal[];
}

interface SportConfig {
  label: string;
  color: string;
  season: string;
  grade: string;
  gradeColor: string;
  groups: SignalGroup[];
}

// ── Signal data ───────────────────────────────────────────────────────────────
const SPORTS: Record<string, SportConfig> = {
  MLB: {
    label: 'MLB', color: RED, season: 'IN SEASON', grade: 'C+', gradeColor: YELLOW,
    groups: [
      {
        category: 'Market Lines',
        signals: [
          { label: 'Spread (open + current)', status: 'live', source: 'Odds API', usedBy: 'Sonnet agent, Statistician' },
          { label: 'Run line O/U (open + current)', status: 'live', source: 'Odds API', usedBy: 'Sonnet agent, Totals Specialist' },
          { label: 'Moneyline (home + away)', status: 'live', source: 'Odds API', usedBy: 'Sonnet agent' },
          { label: 'Morning line at 7am build time', status: 'live', source: 'Odds API', usedBy: 'Model Projections page' },
          { label: 'Best available line per book (8 books)', status: 'live', source: 'Odds API', usedBy: 'Line shopping, unit rec' },
          { label: 'Line movement open→current + steam flags', status: 'live', source: 'game_lines DB', usedBy: 'Sharp persona' },
        ],
      },
      {
        category: 'Starting Pitcher Matchup',
        signals: [
          { label: 'Probable starter (home + away)', status: 'live', source: 'MLB Stats API', usedBy: 'Sonnet agent, Matchup Analyst' },
          { label: 'ERA, WHIP, K/9, BB/9', status: 'live', source: 'MLB Stats API', usedBy: 'Sonnet agent' },
          { label: 'IP (current season)', status: 'live', source: 'MLB Stats API', usedBy: 'Sonnet agent' },
          { label: 'Last 3 starts (date, opponent, IP, ER)', status: 'live', source: 'MLB Stats API', usedBy: 'Sonnet agent' },
          { label: 'xERA vs ERA gap (luck regression signal)', status: 'live', source: 'hist_mlb_statcast_pitching DB', usedBy: 'MLB projection builder, Matchup Analyst' },
          { label: 'xFIP / SIERA', status: 'partial', source: 'hist_mlb_statcast_pitching DB', usedBy: 'MLB projection builder' },
          { label: 'Stuff+ (velocity + movement + spin composite)', status: 'planned', source: 'FanGraphs scraper' },
          { label: 'Pitch mix + velocity trend game-to-game', status: 'planned', source: 'Baseball Savant' },
          { label: 'Days rest between starts', status: 'planned', source: 'MLB Stats API' },
          { label: 'Pitch count last start', status: 'planned', source: 'MLB Stats API' },
        ],
      },
      {
        category: 'Team Offense / Lineup',
        signals: [
          { label: 'Team OPS (season)', status: 'live', source: 'ESPN Stats', usedBy: 'MLB projection builder' },
          { label: 'Team wOBA (computed from linear weights)', status: 'partial', source: 'MLB Stats API', usedBy: 'MLB projection builder' },
          { label: 'Platoon splits: wOBA vs LHP / vs RHP', status: 'live', source: 'MLB Stats API statSplits', usedBy: 'mlb_platoon_splits.py' },
          { label: 'K% and BB% per lineup', status: 'live', source: 'MLB Stats API statSplits', usedBy: 'mlb_platoon_splits.py' },
          { label: 'Barrel rate matchup (offense vs SP tendency)', status: 'partial', source: 'Statcast DB', usedBy: 'MLB projection builder' },
          { label: 'xwOBA per team (strips luck)', status: 'planned', source: 'Baseball Savant' },
          { label: 'BABIP per team (luck indicator)', status: 'planned', source: 'Baseball Savant' },
          { label: 'Recent team wOBA last 10 games', status: 'planned', source: 'MLB Stats API' },
          { label: 'wRC+ (park-adjusted offense)', status: 'planned', source: 'FanGraphs' },
          { label: 'Batter vs Pitcher matchups (career OPS / K% / wOBA)', status: 'planned', source: 'Baseball Savant BvP' },
          { label: 'Confirmed lineup posted before projection fires', status: 'planned', source: 'MLB Stats API' },
        ],
      },
      {
        category: 'Bullpen',
        signals: [
          { label: 'Bullpen pitches thrown last 3 days per reliever', status: 'live', source: 'mlb_bullpen.py → MLB Stats API', usedBy: 'mlb_bullpen.py' },
          { label: 'Closer availability (used yesterday / 2 of last 3)', status: 'live', source: 'mlb_bullpen.py', usedBy: 'mlb_bullpen.py' },
          { label: 'Bullpen fatigue index (0-100)', status: 'live', source: 'mlb_bullpen.py', usedBy: 'mlb_bullpen.py' },
          { label: 'Setup man usage tracking', status: 'live', source: 'mlb_bullpen.py', usedBy: 'mlb_bullpen.py' },
          { label: 'Bullpen ERA / xFIP separate from starter', status: 'planned', source: 'FanGraphs' },
          { label: 'Inherited runner strand % (clutch metric)', status: 'planned', source: 'FanGraphs' },
        ],
      },
      {
        category: 'Park & Environment',
        signals: [
          { label: 'Park factor (all 30 MLB parks)', status: 'live', source: 'mlb_park_factors.py (static)', usedBy: 'MLB projection builder, Totals Specialist' },
          { label: 'Wind speed + direction + factor (±runs)', status: 'live', source: 'weather_service.py → Open-Meteo', usedBy: 'MLB projection builder, Totals Specialist' },
          { label: 'Temperature', status: 'live', source: 'weather_service.py', usedBy: 'MLB projection builder' },
          { label: 'Day vs night game flag', status: 'planned', source: 'MLB Stats API' },
          { label: 'Barometric pressure + humidity', status: 'planned', source: 'Weather API' },
        ],
      },
      {
        category: 'Umpire Tendencies',
        signals: [
          { label: 'HP umpire assignment', status: 'live', source: 'mlb_umpires.py → MLB Stats API', usedBy: 'mlb_umpires.py' },
          { label: 'K rate vs average (wide zone = pitcher-friendly)', status: 'live', source: 'mlb_umpires.py → UmpScorecards', usedBy: 'mlb_umpires.py' },
          { label: 'Run impact vs average ump (±1.5 run edge)', status: 'live', source: 'mlb_umpires.py → UmpScorecards', usedBy: 'mlb_umpires.py' },
          { label: 'Home/away umpire bias', status: 'planned', source: 'UmpScorecards' },
          { label: 'Catcher framing runs above average', status: 'planned', source: 'Baseball Savant' },
        ],
      },
      {
        category: 'Model Projections (game_projections table)',
        signals: [
          { label: 'Projected home runs / away runs / total', status: 'live', source: 'mlb_projection_builder.py', usedBy: 'Sonnet agent, Statistician, Totals Specialist' },
          { label: 'Projected F5 total', status: 'live', source: 'mlb_projection_builder.py', usedBy: 'Sonnet agent' },
          { label: 'Model confidence (LOW/MEDIUM/HIGH)', status: 'live', source: 'mlb_projection_builder.py', usedBy: 'Statistician persona' },
          { label: 'Data completeness score (0–1)', status: 'live', source: 'mlb_projection_builder.py', usedBy: 'Statistician persona' },
          { label: 'Projection notes (natural language signals)', status: 'live', source: 'mlb_projection_builder.py', usedBy: 'Sonnet agent' },
        ],
      },
      {
        category: 'Situational & ATS',
        signals: [
          { label: 'ATS record overall / home / away / O-U', status: 'live', source: 'ats_trends.py', usedBy: 'Sonnet agent' },
          { label: 'Situational ATS notes', status: 'live', source: 'ats_trends.py', usedBy: 'Sonnet agent' },
          { label: 'Historical accuracy (30-day self-aware calibration)', status: 'live', source: 'game_evaluations DB', usedBy: 'Sonnet agent' },
        ],
      },
    ],
  },

  NFL: {
    label: 'NFL', color: BLUE, season: 'SEP 2026', grade: 'C+', gradeColor: YELLOW,
    groups: [
      {
        category: 'Market Lines',
        signals: [
          { label: 'Spread + total + moneyline (open + current)', status: 'live', source: 'Odds API', usedBy: 'Sonnet agent' },
          { label: 'Morning line at 7am build time', status: 'live', source: 'Odds API', usedBy: 'Model Projections page' },
          { label: 'Line movement + steam flags', status: 'live', source: 'game_lines DB', usedBy: 'Sharp persona' },
          { label: 'Best line shopping (8 books)', status: 'live', source: 'Odds API', usedBy: 'Line shopping' },
        ],
      },
      {
        category: 'Team Efficiency',
        signals: [
          { label: 'Yards per play (offense + defense) season', status: 'live', source: 'ESPN Stats', usedBy: 'Sonnet agent, NFL projection builder' },
          { label: 'Yards per play last 3 games (form)', status: 'live', source: 'ESPN Stats', usedBy: 'Sonnet agent' },
          { label: 'Yards per carry (rush offense)', status: 'live', source: 'ESPN Stats', usedBy: 'Sonnet agent' },
          { label: 'Plays per game (pace)', status: 'live', source: 'ESPN Stats', usedBy: 'NFL projection builder' },
          { label: 'Pass rate (% of plays that are passes)', status: 'live', source: 'ESPN Stats', usedBy: 'NFL projection builder' },
          { label: 'Red zone TD conversion % (offense)', status: 'live', source: 'ESPN Stats', usedBy: 'NFL projection builder, Matchup Analyst' },
          { label: '3rd down conversion % (offense)', status: 'live', source: 'ESPN Stats', usedBy: 'NFL projection builder' },
          { label: 'EPA per play (offensive + defensive)', status: 'planned', source: 'nflfastr / ESPN' },
          { label: 'DVOA (situation-adjusted efficiency)', status: 'planned', source: 'Football Outsiders' },
          { label: 'CPOE (completion % over expected — QB accuracy)', status: 'planned', source: 'nflfastr' },
          { label: 'Success rate (% plays gaining positive EPA)', status: 'planned', source: 'nflfastr' },
          { label: 'QB pressure rate (pressures per dropback)', status: 'planned', source: 'PFF / ESPN' },
        ],
      },
      {
        category: 'Turnovers & Luck',
        signals: [
          { label: 'Turnover margin (actual, season)', status: 'live', source: 'turnover_margin.py', usedBy: 'Sonnet agent, NFL projection builder' },
          { label: 'Luck flag (inflated by TO margin regression)', status: 'live', source: 'turnover_margin.py', usedBy: 'Sonnet agent, Situationalist' },
          { label: 'Regression signal note (fade signal)', status: 'live', source: 'turnover_margin.py', usedBy: 'Sonnet agent' },
          { label: 'Fumble luck / INT luck separate', status: 'planned', source: 'nflfastr' },
        ],
      },
      {
        category: 'Situational & Schedule',
        signals: [
          { label: 'Off bye week flag', status: 'live', source: 'schedule_context', usedBy: 'Situationalist, Sonnet agent' },
          { label: 'Post blowout win (letdown risk)', status: 'live', source: 'schedule_context', usedBy: 'Situationalist' },
          { label: 'Post upset win (letdown risk)', status: 'live', source: 'schedule_context', usedBy: 'Situationalist' },
          { label: 'Road streak (fatigue)', status: 'live', source: 'schedule_context', usedBy: 'Situationalist' },
          { label: 'Coaching tier (1–4 scale)', status: 'live', source: 'coach_ratings.py', usedBy: 'Sonnet agent, Situationalist' },
          { label: 'ATS trends (overall / home / away / O-U)', status: 'live', source: 'ats_trends.py', usedBy: 'Sonnet agent' },
          { label: 'Divisional game flag (lines tighter historically)', status: 'planned', source: 'schedule data' },
          { label: 'Playoff seeding / division clinch motivation', status: 'planned', source: 'schedule data' },
          { label: 'Timezone cross + travel flag', status: 'planned', source: 'schedule data' },
        ],
      },
      {
        category: 'Power Index',
        signals: [
          { label: 'ESPN FPI overall', status: 'live', source: 'espn_fpi.py', usedBy: 'Sonnet agent, NFL projection builder' },
          { label: 'FPI offensive / defensive efficiency', status: 'live', source: 'espn_fpi.py', usedBy: 'Sonnet agent' },
          { label: 'Projected wins', status: 'live', source: 'espn_fpi.py', usedBy: 'Sonnet agent' },
          { label: 'Playoffs probability %', status: 'live', source: 'espn_fpi.py', usedBy: 'Sonnet agent' },
        ],
      },
      {
        category: 'Weather',
        signals: [
          { label: 'Temperature + wind speed + direction', status: 'live', source: 'weather_service.py', usedBy: 'NFL projection builder, Totals Specialist' },
          { label: 'Precipitation probability', status: 'live', source: 'weather_service.py', usedBy: 'NFL projection builder' },
          { label: 'Weather impact score (additive pts)', status: 'live', source: 'weather_service.py', usedBy: 'NFL projection builder' },
          { label: 'Dome / outdoor venue flag', status: 'live', source: 'mlb_park_factors.py (venue table)', usedBy: 'weather_service.py' },
        ],
      },
      {
        category: 'Model Projections',
        signals: [
          { label: 'Projected home/away score + total + spread', status: 'live', source: 'nfl_projection_builder.py', usedBy: 'Sonnet agent, Statistician' },
          { label: 'YPP matchup delta (offense vs defense)', status: 'live', source: 'nfl_projection_core.py', usedBy: 'Matchup Analyst' },
          { label: 'TO margin projected differential', status: 'live', source: 'nfl_projection_core.py', usedBy: 'Statistician' },
          { label: 'Projected plays per game (pace)', status: 'live', source: 'nfl_projection_core.py', usedBy: 'Totals Specialist' },
          { label: 'Pass rate matchup signal', status: 'live', source: 'nfl_projection_core.py', usedBy: 'Matchup Analyst' },
        ],
      },
    ],
  },

  CFB: {
    label: 'CFB', color: ORANGE, season: 'AUG 30', grade: 'B-', gradeColor: EMERALD,
    groups: [
      {
        category: 'Power Ratings',
        signals: [
          { label: 'SP+ overall (138 teams)', status: 'live', source: 'cfb_ratings.py', usedBy: 'CFB projection builder, Matchup Analyst' },
          { label: 'SP+ offensive component', status: 'live', source: 'cfb_ratings.py', usedBy: 'CFB projection builder' },
          { label: 'SP+ defensive component', status: 'live', source: 'cfb_ratings.py', usedBy: 'CFB projection builder' },
          { label: 'ESPN FPI (138 teams)', status: 'live', source: 'espn_fpi.py', usedBy: 'CFB projection builder' },
          { label: 'AP Poll / Coaches Poll rank', status: 'live', source: 'ESPN Stats', usedBy: 'Sonnet agent' },
          { label: 'Strength of schedule rank', status: 'live', source: 'ESPN FPI', usedBy: 'Sonnet agent' },
          { label: 'Projected wins + CFP %', status: 'live', source: 'ESPN FPI', usedBy: 'Sonnet agent' },
        ],
      },
      {
        category: 'Team Efficiency',
        signals: [
          { label: 'Yards per play (offense + defense) season', status: 'live', source: 'ESPN Stats', usedBy: 'CFB projection builder, Matchup Analyst' },
          { label: 'Yards per play last 3 games', status: 'live', source: 'ESPN Stats', usedBy: 'Sonnet agent' },
          { label: 'YPP matchup delta (offense vs defense allowed)', status: 'live', source: 'cfb_projection_core.py', usedBy: 'Matchup Analyst' },
          { label: 'Plays per game (pace / tempo)', status: 'live', source: 'ESPN Stats', usedBy: 'CFB projection builder, Totals Specialist' },
          { label: 'Red zone TD conversion %', status: 'live', source: 'ESPN Stats', usedBy: 'CFB projection builder' },
          { label: '3rd down conversion %', status: 'live', source: 'ESPN Stats', usedBy: 'CFB projection builder' },
          { label: 'EPA per play for college', status: 'planned', source: 'ESPN Stats API' },
          { label: 'Returning production % from prior year', status: 'planned', source: 'ESPN / CFB Reference' },
          { label: 'Recruiting class rank (2-yr rolling)', status: 'planned', source: '247Sports' },
          { label: 'QB returning starter + experience flag', status: 'planned', source: 'schedule data' },
        ],
      },
      {
        category: 'Situational & Schedule',
        signals: [
          { label: 'Off bye week flag', status: 'live', source: 'schedule_context', usedBy: 'Situationalist, CFB projection builder' },
          { label: 'Post upset win (letdown risk)', status: 'live', source: 'schedule_context', usedBy: 'Situationalist' },
          { label: 'Schedule spot delta (combined situational edge)', status: 'live', source: 'cfb_projection_core.py', usedBy: 'Situationalist' },
          { label: 'Coaching tier (1–4 scale)', status: 'live', source: 'coach_ratings.py', usedBy: 'Sonnet agent, Situationalist' },
          { label: 'Talent gap via FPI differential', status: 'live', source: 'cfb_projection_core.py', usedBy: 'Matchup Analyst' },
          { label: 'Conference game flag (tighter historical lines)', status: 'live', source: 'cfb_projection_core.py', usedBy: 'Matchup Analyst' },
          { label: 'Blowout risk flag (SP+ gap > 25)', status: 'live', source: 'cfb_projection_core.py', usedBy: 'Sonnet agent' },
          { label: 'ATS trends (overall / home / away / O-U)', status: 'live', source: 'ats_trends.py', usedBy: 'Sonnet agent' },
        ],
      },
      {
        category: 'Model Projections',
        signals: [
          { label: 'Projected home/away score + total + spread', status: 'live', source: 'cfb_projection_builder.py', usedBy: 'Sonnet agent, Statistician' },
          { label: 'SP+ gap + YPP matchup combined projection', status: 'live', source: 'cfb_projection_core.py', usedBy: 'Statistician' },
          { label: 'Home field advantage adjustment (+3.5 pts)', status: 'live', source: 'cfb_projection_core.py', usedBy: 'Sonnet agent' },
          { label: 'Momentum score (YPP trend last 3 vs season)', status: 'live', source: 'cfb_projection_core.py', usedBy: 'Situationalist' },
        ],
      },
    ],
  },

  NBA: {
    label: 'NBA', color: PURPLE, season: 'OCT 2026', grade: 'D', gradeColor: RED,
    groups: [
      {
        category: 'Market Lines',
        signals: [
          { label: 'Spread + total + moneyline (open + current)', status: 'live', source: 'Odds API', usedBy: 'Sonnet agent' },
          { label: 'Line movement + steam flags', status: 'live', source: 'game_lines DB', usedBy: 'Sharp persona' },
        ],
      },
      {
        category: 'Team Ratings',
        signals: [
          { label: 'ESPN BPI overall', status: 'live', source: 'espn_fpi.py', usedBy: 'Sonnet agent' },
          { label: 'BPI offensive / defensive efficiency', status: 'live', source: 'espn_fpi.py', usedBy: 'Sonnet agent' },
          { label: 'Points per game / points allowed (season)', status: 'live', source: 'ESPN Stats', usedBy: 'Sonnet agent' },
          { label: 'Possessions per 48 (pace)', status: 'planned', source: 'NBA Stats API', usedBy: 'NBA projection builder' },
          { label: 'Offensive rating (pts/100 possessions)', status: 'planned', source: 'NBA Stats API' },
          { label: 'Defensive rating', status: 'planned', source: 'NBA Stats API' },
          { label: 'Net rating', status: 'planned', source: 'NBA Stats API' },
          { label: 'eFG% (effective field goal %)', status: 'planned', source: 'NBA Stats API' },
          { label: 'TOV% (turnover rate)', status: 'planned', source: 'NBA Stats API' },
          { label: 'FTr (free throw attempt rate)', status: 'planned', source: 'NBA Stats API' },
          { label: 'OREB% (offensive rebound rate)', status: 'planned', source: 'NBA Stats API' },
        ],
      },
      {
        category: 'Schedule / Rest / Travel',
        signals: [
          { label: 'ATS trends (overall / home / away)', status: 'live', source: 'ats_trends.py', usedBy: 'Sonnet agent' },
          { label: 'Coaching tier', status: 'live', source: 'coach_ratings.py', usedBy: 'Sonnet agent' },
          { label: 'Back-to-back flag (B2B)', status: 'planned', source: 'schedule parser' },
          { label: '3-in-4 / 4-in-6 fatigue flags', status: 'planned', source: 'schedule parser' },
          { label: 'Rest day delta (home - away)', status: 'planned', source: 'schedule parser' },
          { label: 'Road B2B flag (strongest single signal in NBA)', status: 'planned', source: 'schedule parser' },
          { label: 'West→East travel penalty', status: 'planned', source: 'schedule parser' },
        ],
      },
      {
        category: 'Injury / Lineup',
        signals: [
          { label: 'Injury report (from news_intel feed)', status: 'live', source: 'news_intel table', usedBy: 'Sonnet agent' },
          { label: 'Injury severity scoring (star = 5-8 real rating pts)', status: 'planned', source: 'custom model' },
          { label: 'Rotation player minutes / usage data', status: 'planned', source: 'NBA Stats API' },
          { label: 'Referee foul tendency (35-55 fouls/game variance)', status: 'planned', source: 'NBA Ref DB' },
        ],
      },
    ],
  },

  NHL: {
    label: 'NHL', color: EMERALD, season: 'OCT 2026', grade: 'D-', gradeColor: RED,
    groups: [
      {
        category: 'Market Lines',
        signals: [
          { label: 'Puck line + total + moneyline (open + current)', status: 'live', source: 'Odds API', usedBy: 'Sonnet agent' },
          { label: 'Line movement + steam flags', status: 'live', source: 'game_lines DB', usedBy: 'Sharp persona' },
        ],
      },
      {
        category: 'Basic Team Stats',
        signals: [
          { label: 'Goals for / goals against per game (season)', status: 'live', source: 'ESPN Stats', usedBy: 'Sonnet agent' },
          { label: 'ATS trends', status: 'live', source: 'ats_trends.py', usedBy: 'Sonnet agent' },
          { label: 'Empty net scraper', status: 'live', source: 'custom scraper', usedBy: 'Sonnet agent' },
          { label: 'Corsi-for % (CF%) — shot attempt share', status: 'planned', source: 'Natural Stat Trick / MoneyPuck' },
          { label: 'Fenwick % (unblocked shots)', status: 'planned', source: 'Natural Stat Trick' },
          { label: 'Expected goals for / against (xG)', status: 'planned', source: 'Natural Stat Trick' },
          { label: 'xG gap (home xG for minus away xG for)', status: 'planned', source: 'Natural Stat Trick' },
          { label: 'Power play % (offense)', status: 'planned', source: 'NHL Stats API' },
          { label: 'Penalty kill % (defense)', status: 'planned', source: 'NHL Stats API' },
          { label: 'High-danger chance % (shot quality)', status: 'planned', source: 'Natural Stat Trick' },
        ],
      },
      {
        category: 'Goalie',
        signals: [
          { label: 'Starting goalie (confirmed)', status: 'planned', source: 'NHL Stats API' },
          { label: 'SV% vs xSV% (actual vs expected — luck indicator)', status: 'planned', source: 'Natural Stat Trick' },
          { label: 'GSAX (goals saved above expected)', status: 'planned', source: 'MoneyPuck API' },
          { label: 'Goalie back-to-back start flag', status: 'planned', source: 'NHL Stats API' },
          { label: 'Career SV% at this arena', status: 'planned', source: 'Hockey-Reference' },
        ],
      },
    ],
  },

  NCAAB: {
    label: 'NCAAB', color: YELLOW, season: 'NOV 2026', grade: 'F', gradeColor: RED,
    groups: [
      {
        category: 'Market Lines',
        signals: [
          { label: 'Spread + total + moneyline (open + current)', status: 'live', source: 'Odds API', usedBy: 'Sonnet agent' },
          { label: 'Line movement + steam flags', status: 'live', source: 'game_lines DB', usedBy: 'Sharp persona' },
        ],
      },
      {
        category: 'Team Ratings',
        signals: [
          { label: 'ESPN BPI (25 preseason teams)', status: 'live', source: 'espn_fpi.py', usedBy: 'Sonnet agent' },
          { label: 'Basic PPG / PPG allowed', status: 'live', source: 'ESPN Stats', usedBy: 'Sonnet agent' },
          { label: 'ATS trends', status: 'live', source: 'ats_trends.py', usedBy: 'Sonnet agent' },
          { label: 'BartTorvik T-Rank (AdjEM / AdjO / AdjD)', status: 'planned', source: 'barttorvik.com (free API)' },
          { label: 'Tempo (possessions per 40 min)', status: 'planned', source: 'BartTorvik' },
          { label: 'Luck rating (inflated record = regression candidate)', status: 'planned', source: 'BartTorvik / KenPom' },
          { label: 'GameScript metric (Torvik situational eff)', status: 'planned', source: 'BartTorvik' },
          { label: 'Wins Above Bubble (WAB)', status: 'planned', source: 'BartTorvik' },
          { label: 'Strength of schedule rank', status: 'planned', source: 'BartTorvik / KenPom' },
          { label: 'Home court value per specific arena (2–6 pts)', status: 'planned', source: 'BartTorvik' },
          { label: 'Conference game flag + conference eff adjustment', status: 'planned', source: 'schedule data' },
          { label: 'Referee foul tendency (35-55 fouls/game variance)', status: 'planned', source: 'college ref DB' },
        ],
      },
    ],
  },
};

// ── Shared signals used across all sports ─────────────────────────────────────
const SHARED_SIGNALS: Signal[] = [
  { label: '5 handicapper persona agents evaluate every game', status: 'live', source: 'services/personas/', usedBy: 'The Sharp, Statistician, Situationalist, Matchup Analyst, Totals Specialist' },
  { label: 'Persona convergence score (how many of 5 agree)', status: 'live', source: 'persona_orchestrator.py', usedBy: 'Today\'s Plays convergence bar' },
  { label: 'Opus verification on all STRONG_LEAN plays ≥4 units', status: 'live', source: 'game_evaluator.py', usedBy: 'game_evaluations table' },
  { label: 'Haiku pre-classification of situational flags', status: 'live', source: 'signal_classifier.py', usedBy: 'All sports' },
  { label: 'Historical accuracy self-awareness (30-day calibration)', status: 'live', source: 'game_evaluations DB', usedBy: 'Sonnet agent threshold calibration' },
  { label: 'Best line shopping across 8 books', status: 'live', source: 'Odds API', usedBy: 'unit_rec, Today\'s Plays' },
  { label: 'Morning line capture at 7am (market_total, market_spread)', status: 'live', source: 'projection builders', usedBy: 'Model Projections page' },
  { label: 'News intel with betting action tags', status: 'live', source: 'news_intel table', usedBy: 'Sonnet agent' },
];

// ── Components ────────────────────────────────────────────────────────────────
const STATUS_CONFIG = {
  live:    { label: 'LIVE',    color: EMERALD, bg: 'oklch(69.6% .17 162.48 / .15)' },
  partial: { label: 'PARTIAL', color: YELLOW,  bg: 'oklch(79.5% .184 86.047 / .15)' },
  planned: { label: 'PLANNED', color: MUTED,   bg: 'oklch(30% 0 0)' },
};

function StatusBadge({ status }: { status: SignalStatus }) {
  const cfg = STATUS_CONFIG[status];
  return (
    <span style={{
      fontSize: '0.55rem', fontWeight: 800, letterSpacing: '0.08em',
      color: cfg.color, background: cfg.bg,
      border: `1px solid ${cfg.color}40`,
      padding: '1px 6px', borderRadius: 3, flexShrink: 0,
    }}>
      {cfg.label}
    </span>
  );
}

function SignalRow({ s }: { s: Signal }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'flex-start', gap: 10,
      padding: '7px 0', borderBottom: `1px solid ${BORDER}`,
    }}>
      <StatusBadge status={s.status} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: '0.82rem', color: 'var(--foreground)', fontWeight: s.status === 'live' ? 600 : 400 }}>
          {s.label}
        </div>
        {(s.source || s.usedBy) && (
          <div style={{ display: 'flex', gap: 12, marginTop: 2, flexWrap: 'wrap' }}>
            {s.source && (
              <span style={{ fontSize: '0.62rem', color: MUTED }}>
                src: {s.source}
              </span>
            )}
            {s.usedBy && s.status === 'live' && (
              <span style={{ fontSize: '0.62rem', color: BLUE }}>
                → {s.usedBy}
              </span>
            )}
          </div>
        )}
        {s.detail && (
          <div style={{ fontSize: '0.7rem', color: MUTED, marginTop: 2, fontStyle: 'italic' }}>
            {s.detail}
          </div>
        )}
      </div>
    </div>
  );
}

function SportPanel({ config }: { config: SportConfig }) {
  const [filter, setFilter] = useState<'all' | 'live' | 'planned'>('all');

  const liveCount    = config.groups.flatMap(g => g.signals).filter(s => s.status === 'live').length;
  const partialCount = config.groups.flatMap(g => g.signals).filter(s => s.status === 'partial').length;
  const plannedCount = config.groups.flatMap(g => g.signals).filter(s => s.status === 'planned').length;
  const totalCount   = liveCount + partialCount + plannedCount;

  return (
    <div>
      {/* Sport header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        marginBottom: 16, flexWrap: 'wrap', gap: 10,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            fontSize: '0.9rem', fontWeight: 900, letterSpacing: '0.08em',
            color: config.color,
          }}>
            {config.label}
          </div>
          <div style={{
            fontSize: '0.75rem', fontWeight: 800,
            color: config.gradeColor,
            border: `1px solid ${config.gradeColor}50`,
            padding: '1px 8px', borderRadius: 4,
          }}>
            Model Grade: {config.grade}
          </div>
          <div style={{ fontSize: '0.65rem', color: MUTED }}>
            {config.season}
          </div>
        </div>

        {/* Filter toggles */}
        <div style={{ display: 'flex', gap: 6 }}>
          {(['all', 'live', 'planned'] as const).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              style={{
                fontSize: '0.62rem', fontWeight: 800, letterSpacing: '0.06em',
                padding: '3px 10px', borderRadius: 4, border: 'none',
                background: filter === f ? 'oklch(35% 0 0)' : 'oklch(28% 0 0)',
                color: filter === f ? 'var(--foreground)' : MUTED,
                cursor: 'pointer',
              }}
            >
              {f.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Signal counts */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 16, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: EMERALD }} />
          <span style={{ fontSize: '0.7rem', color: MUTED }}>{liveCount + partialCount} live / partial of {totalCount} total</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: MUTED }} />
          <span style={{ fontSize: '0.7rem', color: MUTED }}>{plannedCount} on roadmap</span>
        </div>
        <div style={{
          fontSize: '0.7rem', color: MUTED,
          background: 'oklch(28% 0 0)', border: `1px solid ${BORDER}`,
          padding: '2px 10px', borderRadius: 10,
        }}>
          Coverage: {Math.round((liveCount + partialCount) / totalCount * 100)}%
        </div>
      </div>

      {/* Groups */}
      {config.groups.map(group => {
        const filteredSignals = filter === 'all'
          ? group.signals
          : filter === 'live'
          ? group.signals.filter(s => s.status === 'live' || s.status === 'partial')
          : group.signals.filter(s => s.status === 'planned');
        if (filteredSignals.length === 0) return null;
        return (
          <div key={group.category} style={{ marginBottom: 20 }}>
            <div style={{
              fontSize: '0.62rem', fontWeight: 800, letterSpacing: '0.1em',
              color: config.color, marginBottom: 6, paddingBottom: 4,
              borderBottom: `1px solid ${config.color}30`,
            }}>
              {group.category}
            </div>
            {filteredSignals.map(s => <SignalRow key={s.label} s={s} />)}
          </div>
        );
      })}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export function DataPoints() {
  const [activeSport, setActiveSport] = useState('MLB');

  const sportKeys = Object.keys(SPORTS);

  return (
    <div className="analytics-container">
      {/* Page header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{
          fontSize: '1.5rem', fontWeight: 900, letterSpacing: '0.06em',
          color: 'var(--foreground)', margin: 0,
        }}>
          DATA POINTS
        </h1>
        <p style={{ fontSize: '0.82rem', color: MUTED, marginTop: 6 }}>
          Every signal, metric, and data point wired into the Max EV handicapping models and agent pipeline.
        </p>
      </div>

      {/* Shared infrastructure */}
      <div style={{
        background: CARD_BG, border: `1px solid ${BORDER}`,
        borderRadius: 10, padding: '16px 20px', marginBottom: 20,
      }}>
        <div style={{
          fontSize: '0.62rem', fontWeight: 800, letterSpacing: '0.1em',
          color: BLUE, marginBottom: 10,
        }}>
          SHARED ACROSS ALL SPORTS — AGENT INFRASTRUCTURE
        </div>
        {SHARED_SIGNALS.map(s => <SignalRow key={s.label} s={s} />)}
      </div>

      {/* Sport tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 16, flexWrap: 'wrap' }}>
        {sportKeys.map(key => {
          const cfg = SPORTS[key];
          return (
            <button
              key={key}
              onClick={() => setActiveSport(key)}
              style={{
                padding: '6px 14px', borderRadius: 6, border: 'none',
                background: activeSport === key ? cfg.color : 'oklch(28% 0 0)',
                color: activeSport === key ? 'oklch(10% 0 0)' : MUTED,
                fontSize: '0.72rem', fontWeight: 800, letterSpacing: '0.06em',
                cursor: 'pointer', transition: 'background 0.15s',
              }}
            >
              {cfg.label}
            </button>
          );
        })}
      </div>

      {/* Sport panel */}
      <div style={{
        background: CARD_BG, border: `1px solid ${BORDER}`,
        borderRadius: 10, padding: '20px',
      }}>
        <SportPanel config={SPORTS[activeSport]} />
      </div>

      {/* Legend */}
      <div style={{
        display: 'flex', gap: 20, marginTop: 16, flexWrap: 'wrap',
        fontSize: '0.65rem', color: MUTED,
      }}>
        <span style={{ color: EMERALD, fontWeight: 700 }}>● LIVE</span>
        <span>— Currently wired, feeds into today's evaluations</span>
        <span style={{ color: YELLOW, fontWeight: 700 }}>● PARTIAL</span>
        <span>— Data exists but not fully integrated</span>
        <span style={{ fontWeight: 700 }}>● PLANNED</span>
        <span>— On roadmap, not yet built</span>
      </div>
    </div>
  );
}
