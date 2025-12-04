# NHL Goalie Pull Betting Strategy System

A complete live-tracking system that predicts when NHL teams will pull their goalies and identifies positive expected value (EV) betting opportunities on game totals.

## System Overview

This system alerts you to bet OVER on game totals 30-90 seconds BEFORE goalies are pulled, when odds are still favorable. After the pull, odds shift to -110 or worse, eliminating the edge.

### Two Alert Types

1. **EARLY WARNING (5+ minutes remaining)**
   - Triggers when: Team is down 1-2 goals with 5+ minutes left in 3rd period
   - Purpose: Alerts you to prepare your betting books
   - Message: "POSSIBLE EMPTY NET GOAL PENDING - PREPARE YOUR BETTING BOOKS NOW"
   - Shows regardless of EV calculation

2. **IMMINENT (30-90 seconds before pull)**
   - Triggers when: Goalie pull expected in 30-90 seconds based on team/coach profile
   - Purpose: Place the bet NOW before odds shift
   - Message: "BET IMMEDIATELY! Odds will shift to -110 or worse after pull"
   - Only shows if positive EV (5%+ edge required)

## Architecture

### Database System (`nhl_goalie_pull_database.py`)

SQLite database storing:
- **goalie_pull_events**: Every historical pull event (game, team, time, outcome)
- **team_pull_profiles**: Aggregated stats per team (avg pull times, analytics scores)
- **coach_profiles**: Individual coach tendencies (coaches move between teams)
- **empty_net_stats**: Team performance with empty net (goals for/against, success rates)

### Predictor (`nhl_goalie_pull_predictor.py`)

- Fetches team/coach profiles from database (NO hardcoded data)
- Predicts pull timing based on historical behavior
- Calculates EV using team-specific empty net performance
- Falls back to league averages if no historical data exists

### Scraper (`nhl_goalie_pull_scraper.py`)

- Collects historical goalie pull events from NHL API
- Parses play-by-play data for "GOALIE PULLED" events
- Tracks outcomes: empty net goals scored, trailing team scores
- Builds team and coach profiles from real data

### Population Script (`populate_goalie_pull_data.py`)

- Initializes database with historical data (default: last 90 days)
- Rebuilds all team/coach profiles
- Can be run daily to update with recent games

## Database Schema

### goalie_pull_events
```sql
game_id TEXT
game_date TEXT
season TEXT
team TEXT                    -- Team that pulled goalie
opponent TEXT
is_home BOOLEAN
score_differential INTEGER  -- -1 (down 1), -2 (down 2), etc.
time_remaining_seconds INTEGER
period INTEGER
coach TEXT
empty_net_goal_scored BOOLEAN
empty_net_goal_by TEXT
trailing_team_scored BOOLEAN
game_outcome TEXT
```

### team_pull_profiles
```sql
team TEXT
current_coach TEXT
season TEXT
total_pulls INTEGER
pulls_down_1 INTEGER
pulls_down_2 INTEGER
avg_pull_time_down_1 INTEGER    -- Average seconds when down 1
avg_pull_time_down_2 INTEGER    -- Average seconds when down 2
earliest_pull_down_1 INTEGER
latest_pull_down_1 INTEGER
analytics_score REAL            -- 0-10 aggressiveness rating
en_goals_against INTEGER        -- Empty net goals allowed
en_goals_for INTEGER            -- Goals scored with EN
trailing_team_scored_count INTEGER
```

### empty_net_stats
```sql
team TEXT
season TEXT
en_goals_for INTEGER           -- Goals scored when pulling goalie
en_goals_against INTEGER       -- Goals allowed when other team pulls
en_opportunities INTEGER       -- Total times team pulled goalie
en_success_rate REAL           -- % of pulls where team scored
en_defense_rate REAL           -- % of pulls where team didn't allow EN goal
```

## EV Calculation

### Using Real Team Data

1. **Empty Net Goal Probability**
   - Uses team's actual EN defense rate from database
   - Example: If team allows EN goal 52% of time → `en_goal_prob = 0.52`
   - Falls back to league average (48%) if insufficient data

2. **Trailing Team Scoring Probability**
   - Uses team's actual EN success rate from database
   - Example: If team scores 15% of time when pulling goalie → `trailing_scores_prob = 0.15`
   - Falls back to score differential average (18% down 1, 8% down 2)

3. **Combined Probability**
   ```python
   prob_over_hits = en_goal_prob + (trailing_scores_prob * (1 - en_goal_prob))
   ```

4. **Edge Calculation**
   ```python
   edge = prob_over_hits - implied_probability_from_odds
   edge_percentage = edge * 100
   ```

5. **Expected Value**
   ```python
   ev = (prob_over_hits × payout) - ((1 - prob_over_hits) × stake)
   ev_percentage = ev * 100
   ```

### Minimum Requirements for Bet Alert

- IMMINENT alerts only: `ev_percentage >= 5.0` (5%+ edge required)
- EARLY_WARNING alerts: Always shown (to prepare books)

## Setup and Usage

### 1. Initialize Database

```bash
cd backend/scrapers/nba/backend
python nhl_goalie_pull_database.py
```

This creates the SQLite database at `backend/scrapers/nba/backend/data/nhl_goalie_pulls.db`

### 2. Populate Historical Data

```bash
# Collect last 90 days (default)
python populate_goalie_pull_data.py

# Or specify custom days
python populate_goalie_pull_data.py 30  # Last 30 days only
```

**Expected Output:**
```
Found 247 goalie pull events
Inserted 247 pull events for 28 teams
Rebuilding team profiles...
Rebuilding coach profiles...

Top 10 Most Aggressive Teams (by analytics score):
 1. Tampa Bay Lightning      | Score:  9.5/10 |  42 pulls | Coach: Jon Cooper
 2. Carolina Hurricanes      | Score:  9.0/10 |  38 pulls | Coach: Rod Brind'Amour
 3. Colorado Avalanche       | Score:  8.8/10 |  35 pulls | Coach: Jared Bednar
 ...
```

### 3. Run Live Tracking

The system is integrated into your existing NHL tracking via `game_tracker.py`. The predictor automatically uses the database for all predictions.

### 4. Daily Updates

Set up a cron job or scheduled task to update with recent games:

```bash
# Update with last 7 days
python populate_goalie_pull_data.py 7
```

## API Integration

### Endpoint: `/api/goalie-pull-opportunities`

Returns current betting opportunities:

```json
{
  "count": 2,
  "opportunities": [
    {
      "game_id": "2024020123",
      "game": "Tampa Bay Lightning @ Boston Bruins",
      "trailing_team": "Tampa Bay Lightning",
      "score": "2-3",
      "time_remaining": "6:30",
      "prediction": {
        "trailing_team": "Tampa Bay Lightning",
        "expected_pull_time": 135,
        "time_until_pull": 255,
        "confidence": 0.75,
        "analytics_rating": 9.5,
        "coach": "Jon Cooper",
        "is_early_warning": true,
        "is_imminent": false,
        "alert_type": "EARLY_WARNING",
        "alert_priority": "MEDIUM"
      },
      "ev_analysis": {
        "current_total": 5.5,
        "current_odds": 140,
        "probability_over_hits": 0.561,
        "edge_percentage": 14.7,
        "expected_value_percentage": 20.6,
        "is_positive_ev": true,
        "alert_user": true
      },
      "priority": "MEDIUM",
      "timestamp": "2025-01-17T19:45:23"
    }
  ]
}
```

## Frontend Display

Early Warning (Blue):
- Header: "⏰ EARLY WARNING"
- Message: "PREPARE YOUR BETTING BOOKS NOW"
- Shows expected edge and current odds
- Action: "STANDBY - Watch for imminent alert"

Imminent (Red/Yellow):
- Header: "🚨 GOALIE PULL ALERT - HIGH PRIORITY"
- Message: "BET NOW - OVER 5.5"
- Shows edge, EV, win probability
- Action: "⏰ BET IMMEDIATELY!"

## Analytics Score (0-10)

Measures coach/team aggressiveness:
- **10**: Most aggressive (pulls very early)
  - Down 1: Pulls at 2:00+ remaining
  - Down 2: Pulls at 3:00+ remaining
- **5**: League average
  - Down 1: Pulls at 1:30-1:45
  - Down 2: Pulls at 2:30-3:00
- **0**: Conservative
  - Down 1: Pulls at <1:30
  - Down 2: Pulls at <2:30

## Data Sources

1. **NHL API** (`https://statsapi.web.nhl.com/api/v1`)
   - Live game data
   - Play-by-play events
   - Historical goalie pull events

2. **Historical Database**
   - Team pull profiles (when/how often teams pull)
   - Coach profiles (individual tendencies)
   - Empty net performance (team-specific success/failure rates)

## No More Fake Data

✅ All predictions use REAL historical data from database
✅ Team profiles built from actual goalie pull events
✅ EV calculations use team-specific empty net stats
✅ Coach analytics based on their actual pull timing
✅ Falls back to league averages only when insufficient data

❌ NO hardcoded team profiles
❌ NO fake analytics scores
❌ NO assumed probabilities

## Maintenance

### Update Database Weekly

```bash
python populate_goalie_pull_data.py 7
```

### Rebuild All Profiles

```bash
python populate_goalie_pull_data.py 90
```

### View Database Stats

```python
from nhl_goalie_pull_database import get_database

db = get_database()
teams = db.get_all_teams_with_profiles('2024-25')

for team in teams:
    profile = db.get_team_profile(team, '2024-25')
    print(f"{team}: {profile['total_pulls']} pulls, {profile['analytics_score']}/10")
```

## Strategy Summary

**WHEN:** 3rd period, down 1-2 goals, 5+ minutes or imminent pull (30-90s)
**WHAT:** Bet OVER current total
**WHY:** 45-50% EN goal probability + 15-18% trailing team scores
**EDGE:** Odds are +140 to +160 before pull, shift to -110 after
**REQUIREMENT:** 5%+ expected value for imminent bets

This system gives you the edge by predicting pulls BEFORE they happen using real historical data.
