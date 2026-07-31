# Max EV Sports — F5 Edge Engine Architecture

## What We've Proven

| Signal | Bet Type | ROI | Games/Season | Stat. Sig |
|--------|----------|-----|-------------|-----------|
| Ace vs Ace (ERA < 3.50) | F5 Tie | +22% | ~190 | p=0.10 |
| Both ERA < 4.50 | F5 Under | +3.2% | ~1,150 | p=0.0004 |
| ERA diff >= 1.0 | F5 Fav ML | +6.4% | ~1,160 | p=0.0004 |
| High-tie venue + ERA<4.0 | F5 Tie | +45% | ~130 | needs 2nd season |
| Tie + Under SGP | Same-game parlay | +94% | ~290 | correlated 1.51x |
| Power suppression | Fewer ties | N/A | N/A | Signal closed |

## What We Don't Know Yet

- Bullpen quality, recent form, lineup-specific, umpire effects
- F1 market edges (Bovada SGP angle)
- Whether additional data sources reveal the other 82% of ties
- Full-game market edges using the same signal framework

## System Design

### 5 Layers

```
┌─────────────────────────────────────────────────┐
│  LAYER 5: FRONTEND — Dashboard + Alerts         │
├─────────────────────────────────────────────────┤
│  LAYER 4: EXECUTION — Sizing, Book Routing, SGP │
├─────────────────────────────────────────────────┤
│  LAYER 3: SIGNAL ENGINE — Score & Rank Games    │
├─────────────────────────────────────────────────┤
│  LAYER 2: BOOK MONITOR — Live Odds Scanner      │
├─────────────────────────────────────────────────┤
│  LAYER 1: DATA LAYER — Games, Odds, Stats       │
└─────────────────────────────────────────────────┘
```

### Layer 1: Data Layer

Single source of truth. PostgreSQL on VPS for production,
SQLite for local backtesting.

**Tables:**
- `games` — every MLB game with inning-by-inning scores, outcomes
- `odds_snapshots` — historical + live odds from every book, every market
- `team_profiles` — season batting stats (ISO, HR rate, K rate, etc.)
- `pitcher_profiles` — individual pitcher stats (ERA, WHIP, K/9, etc.)
- `venues` — park factors, dimensions, altitude
- `weather` — temp, wind speed/direction, condition per game
- `signals` — registered signal definitions (pluggable)
- `signal_results` — backtest results per signal
- `bets` — placed bets with odds, sizing, outcome, P&L

**Data Sources:**
- MLB Stats API (free) — games, pitchers, teams, weather
- The Odds API (paid) — book odds, F5/F1/FG markets
- Team/park reference data — static lookup tables

### Layer 2: Book Monitor

Runs during MLB season. Polls odds at configurable intervals.

**Responsibilities:**
- Pull live F5/F1/FG odds from all books via Odds API
- Store snapshots for line movement tracking
- Detect line disagreements between books
- Feed current odds to Signal Engine

**Markets Monitored:**
- h2h_3_way_1st_5_innings (F5 tie)
- totals_1st_5_innings (F5 total)
- h2h_1st_5_innings (F5 2-way ML)
- h2h, totals, spreads (full-game)
- h2h_3_way_1st_1_innings (F1 tie — for SGP)
- totals_1st_1_innings (F1 total)

### Layer 3: Signal Engine (THE CORE)

Pluggable system where any hypothesis can be registered,
backtested, and deployed without touching other code.

**Signal Interface:**
```python
class Signal:
    name: str
    description: str
    bet_type: str           # "tie", "under", "over", "fav_ml", "dog_ml"
    market: str             # "f5_3way", "f5_total", "f5_ml", "fg_total"

    def qualifies(game) -> bool:
        """Does this game match the signal conditions?"""

    def edge(game, odds) -> float:
        """Estimated edge given current odds"""

    def backtest_stats() -> dict:
        """Historical performance from data layer"""
```

**Registered Signals (proven):**
1. ACE_TIE — Both ERA < 3.50 → bet F5 tie
2. ACE_UNDER — Both ERA < 3.50 → bet F5 under
3. GOOD_PITCHING_UNDER — Both ERA < 4.50 → bet F5 under
4. MISMATCH_FAV — ERA diff >= 1.0 → bet F5 fav ML
5. MISMATCH_FAV_HITTER — ERA diff >= 1.5 + hitter park → bet F5 fav ML
6. VENUE_TIE — High-tie venue + ERA < 4.0 → bet F5 tie
7. TIE_UNDER_SGP — Qualifies for both tie + under → parlay

**Testing New Signals:**
Any new hypothesis (bullpen quality, lineup data, umpire, etc.)
gets registered as a signal, backtested against historical data,
and only deployed if it passes significance testing.

**Signal Scoring:**
Each game gets scored by ALL active signals. Output:
- Which signals fire
- Estimated edge per signal
- Recommended bet type + sizing
- Which book has best odds

### Layer 4: Execution

**Responsibilities:**
- Kelly/fractional Kelly bet sizing
- Book routing (which book for which bet)
- SGP compatibility checking (Bovada blocks F5+FG total, etc.)
- Bankroll management + daily limits
- Bet slip generation

**Book Routing Rules:**
```
F5 Tie:       Best odds across FanDuel, BetMGM, Caesars, ESPN BET, BetRivers, Wind Creek
F5 Under:     Best line across all books (some at 4.5, some at 5.0)
F5 Fav ML:    Best price across 14 books
SGP Tie+Under: DraftKings or FanDuel (allow F5 SGP)
SGP F1+FG:    Bovada (allows F1+FG total)
```

### Layer 5: Frontend

React page on Max EV Sports platform.

**Views:**
- Today's Plays — ranked by edge, with book routing
- Signal Dashboard — which signals are active, historical stats
- Backtest Lab — test new hypotheses against data
- P&L Tracker — running results by signal, by book, by month
- Book Comparison — odds by book for today's games
- Alert Feed — real-time when a qualifying game appears
