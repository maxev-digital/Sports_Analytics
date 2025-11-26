# Player Props ML Implementation Plan
**Created:** November 13, 2025
**Status:** 📋 PLANNING PHASE
**Target Timeline:** 4-6 months for full implementation

---

## EXECUTIVE SUMMARY

**Current State:**
- ✅ Frontend UI complete and production-ready
- ✅ Props odds fetching from The Odds API (all 6 sports)
- ✅ NBA rule-based projections (no ML, slow API)
- ❌ No ML models trained or deployed
- ❌ No historical props outcomes database
- ❌ Only NBA has projections (5 sports are odds-only)

**Goal:**
Integrate player props into the autonomous ML system to generate daily predictions with confidence levels, similar to the existing game totals system (87 models across 5 sports).

**Estimated Effort:**
- **Phase 1 (NBA):** 8-10 weeks
- **Phase 2 (NFL):** 6-8 weeks
- **Phase 3 (NHL):** 6-8 weeks
- **Phase 4 (MLB/NCAAB):** 4-6 weeks each

---

## ARCHITECTURE OVERVIEW

### Current Game Totals ML System (Template to Follow)

```
[Data Sources] → [Scrapers] → [Feature Engineering] → [ML Models]
                                                            ↓
                                                    [Daily Predictions]
                                                            ↓
                                                    [Weekly Retraining]
                                                            ↓
                                                    [Live Alerts]
```

**What Works:**
- 87 ML models (6 types × 5 sports × 3 bet types)
- XGBoost, LightGBM, Random Forest, Linear/Logistic Regression, Ensemble
- Weekly retraining (Mondays 4-9am CST)
- Daily predictions (9-11am CST)
- Live alerts (6-11pm CST, every 5 min)
- Performance tracking with CSV logs

### Target Player Props ML System

```
[Player Stats APIs] → [Stats Scrapers] → [Historical DB]
                                                ↓
                                        [Feature Engineering]
                                                ↓
                    [XGBoost] [LightGBM] [Random Forest] [Ensemble]
                                                ↓
                                    [Daily Props Predictions]
                                                ↓
                                    [Weekly Model Retraining]
                                                ↓
                                    [Live Props Alerts]
                                                ↓
                                    [Results Tracking & Grading]
```

---

## PHASE 1: NBA PLAYER PROPS ML (8-10 WEEKS)

### Week 1-2: Data Infrastructure Setup

#### 1.1 Create Historical Props Database Schema

**File:** `backend/database/player_props_schema.sql`

```sql
CREATE TABLE player_props_lines (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    game_id VARCHAR(50),
    player_id VARCHAR(50) NOT NULL,
    player_name VARCHAR(100) NOT NULL,
    team VARCHAR(10) NOT NULL,
    opponent VARCHAR(10) NOT NULL,
    home_away VARCHAR(4), -- 'HOME' or 'AWAY'
    prop_type VARCHAR(20) NOT NULL, -- 'points', 'rebounds', 'assists', etc.
    market_line DECIMAL(5,2) NOT NULL,
    over_odds INTEGER, -- American odds
    under_odds INTEGER,
    bookmaker VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, player_id, prop_type, bookmaker)
);

CREATE TABLE player_props_results (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    game_id VARCHAR(50),
    player_id VARCHAR(50) NOT NULL,
    player_name VARCHAR(100) NOT NULL,
    team VARCHAR(10) NOT NULL,
    opponent VARCHAR(10) NOT NULL,
    prop_type VARCHAR(20) NOT NULL,
    market_line DECIMAL(5,2) NOT NULL,
    actual_value DECIMAL(5,2) NOT NULL,
    hit BOOLEAN NOT NULL, -- TRUE if actual > line (for OVER)
    difference DECIMAL(5,2), -- actual - line
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, player_id, prop_type)
);

CREATE TABLE player_props_predictions (
    id SERIAL PRIMARY KEY,
    prediction_date DATE NOT NULL,
    game_date DATE NOT NULL,
    player_id VARCHAR(50) NOT NULL,
    player_name VARCHAR(100) NOT NULL,
    team VARCHAR(10) NOT NULL,
    opponent VARCHAR(10) NOT NULL,
    prop_type VARCHAR(20) NOT NULL,
    market_line DECIMAL(5,2) NOT NULL,
    predicted_value DECIMAL(5,2) NOT NULL,
    confidence DECIMAL(5,2), -- 0-100
    model_type VARCHAR(50), -- 'xgboost', 'lightgbm', 'ensemble'
    edge_pct DECIMAL(5,2),
    recommendation VARCHAR(10), -- 'OVER', 'UNDER', 'PASS'
    actual_value DECIMAL(5,2), -- Filled after game
    result VARCHAR(10), -- 'WIN', 'LOSS', 'PUSH'
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_props_lines_date ON player_props_lines(date);
CREATE INDEX idx_props_lines_player ON player_props_lines(player_id, prop_type);
CREATE INDEX idx_props_results_date ON player_props_results(date);
CREATE INDEX idx_props_predictions_date ON player_props_predictions(game_date);
```

**Implementation:**
- Use PostgreSQL (recommended) or SQLite for development
- Add database connection to `backend/config.py`
- Create ORM models using SQLAlchemy

---

#### 1.2 Replace Slow NBA.com API with BallDontLie

**Current Issue:**
- `nba_player_props_stats.py` uses NBA.com API (10-30s per request)
- Marked as "DISABLED" in NBA_DATA_SOURCES.md

**Solution:**
- Replace with BallDontLie API (30x faster)
- API Key already available: `9ca7e6df-853f-4ac4-a964-2eafa7627b8d`

**File:** `backend/scrapers/nba/balldontlie_player_stats.py`

```python
"""
Fast NBA player statistics using BallDontLie API
30x faster than NBA.com API
"""
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

class BallDontLieClient:
    """
    Client for BallDontLie API - Fast NBA stats
    Docs: https://docs.balldontlie.io/
    """

    BASE_URL = "https://api.balldontlie.io/v1"
    API_KEY = "9ca7e6df-853f-4ac4-a964-2eafa7627b8d"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": self.API_KEY
        })
        self.cache = {}

    def get_player_season_averages(self, player_id: int, season: int) -> Dict:
        """
        Get player's season averages
        Fast: <500ms response time
        """
        cache_key = f"season_avg_{player_id}_{season}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        url = f"{self.BASE_URL}/season_averages"
        params = {
            "season": season,
            "player_ids[]": player_id
        }

        response = self.session.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("data"):
            stats = data["data"][0]
            self.cache[cache_key] = stats
            return stats
        return None

    def get_player_recent_games(self, player_id: int, last_n_days: int = 30) -> List[Dict]:
        """
        Get player's recent game logs
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=last_n_days)

        url = f"{self.BASE_URL}/stats"
        params = {
            "player_ids[]": player_id,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "per_page": 100
        }

        response = self.session.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        return data.get("data", [])

    def get_team_defensive_stats(self, team_id: int, season: int) -> Dict:
        """
        Get team defensive ratings
        """
        # BallDontLie doesn't have team defense directly
        # We'll calculate from opponent stats
        cache_key = f"team_def_{team_id}_{season}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Implementation: Aggregate opponent scoring vs this team
        # This would require fetching games and calculating
        # For now, return placeholder
        return {
            "team_id": team_id,
            "opp_ppg": None,  # To be calculated
            "def_rating": None
        }
```

**API Endpoints:**
- `GET /season_averages` - Season stats (PPG, RPG, APG, etc.)
- `GET /stats` - Game logs with date filtering
- `GET /games` - Game information
- `GET /players` - Player search and info

**Rate Limits:**
- Free tier: 10 requests per minute
- Pro tier ($10/mo): 60 requests per minute
- Response time: ~200-500ms (vs 10-30s for NBA.com)

**Data Fields Available:**
```json
{
  "games_played": 45,
  "min": "34.2",
  "fgm": 9.8,
  "fga": 20.1,
  "fg3m": 2.1,
  "fg3a": 6.4,
  "ftm": 5.6,
  "fta": 6.8,
  "oreb": 0.9,
  "dreb": 6.1,
  "reb": 7.0,
  "ast": 5.2,
  "stl": 1.1,
  "blk": 0.4,
  "turnover": 3.1,
  "pf": 2.3,
  "pts": 27.3
}
```

---

#### 1.3 Build Props Lines Daily Scraper

**File:** `backend/scrapers/props/daily_props_scraper.py`

```python
"""
Daily scraper to store props lines for historical tracking
Runs at 8am CST before games start
"""
import asyncio
from datetime import datetime
from backend.player_props_client import PlayerPropsClient
from backend.database.models import PlayerPropsLine
from backend.database.connection import get_db_session

async def scrape_daily_nba_props():
    """
    Fetch all NBA props for today and store in database
    """
    client = PlayerPropsClient()
    db = get_db_session()

    # Fetch all NBA props
    nba_props = await client.fetch_all_player_props("basketball_nba")

    stored_count = 0
    for game_id, markets in nba_props.items():
        for market_key, props in markets.items():
            for player_name, prop_data in props.items():
                # Extract best odds
                best_over = max(prop_data["bookmakers"],
                               key=lambda x: x["over_odds"])
                best_under = max(prop_data["bookmakers"],
                                key=lambda x: x["under_odds"])

                # Store in database
                prop_line = PlayerPropsLine(
                    date=datetime.now().date(),
                    game_id=game_id,
                    player_id=prop_data.get("player_id"),
                    player_name=player_name,
                    team=prop_data["team"],
                    opponent=prop_data["opponent"],
                    home_away=prop_data.get("home_away", "AWAY"),
                    prop_type=market_key,
                    market_line=prop_data["line"],
                    over_odds=best_over["over_odds"],
                    under_odds=best_under["under_odds"],
                    bookmaker="BEST_LINE"
                )

                db.add(prop_line)
                stored_count += 1

    db.commit()
    print(f"✓ Stored {stored_count} NBA props lines for {datetime.now().date()}")

if __name__ == "__main__":
    asyncio.run(scrape_daily_nba_props())
```

**Schedule:**
- Run daily at 8:00am CST via cron
- Captures opening lines before significant movement
- Stores best available odds across all bookmakers

---

#### 1.4 Build Results Tracking Scraper

**File:** `backend/scrapers/props/results_tracker.py`

```python
"""
Scrapes final game stats and matches to props lines
Runs at 2am CST after all games complete
"""
from datetime import datetime, timedelta
from backend.scrapers.nba.balldontlie_player_stats import BallDontLieClient
from backend.database.models import PlayerPropsLine, PlayerPropsResult
from backend.database.connection import get_db_session

def track_previous_day_results():
    """
    Fetch yesterday's game results and grade all props
    """
    db = get_db_session()
    yesterday = (datetime.now() - timedelta(days=1)).date()

    # Get all props lines from yesterday
    props_lines = db.query(PlayerPropsLine).filter(
        PlayerPropsLine.date == yesterday
    ).all()

    client = BallDontLieClient()
    graded_count = 0

    for prop_line in props_lines:
        # Fetch actual game stats for player
        games = client.get_player_recent_games(
            player_id=prop_line.player_id,
            last_n_days=1
        )

        if not games:
            print(f"⚠️ No game found for {prop_line.player_name}")
            continue

        game_stats = games[0]

        # Map prop type to stat field
        stat_map = {
            "points": "pts",
            "rebounds": "reb",
            "assists": "ast",
            "threes": "fg3m",
            "blocks": "blk",
            "steals": "stl"
        }

        stat_field = stat_map.get(prop_line.prop_type)
        if not stat_field:
            continue

        actual_value = game_stats.get(stat_field, 0)
        hit = actual_value > prop_line.market_line
        difference = actual_value - prop_line.market_line

        # Store result
        result = PlayerPropsResult(
            date=yesterday,
            game_id=prop_line.game_id,
            player_id=prop_line.player_id,
            player_name=prop_line.player_name,
            team=prop_line.team,
            opponent=prop_line.opponent,
            prop_type=prop_line.prop_type,
            market_line=prop_line.market_line,
            actual_value=actual_value,
            hit=hit,
            difference=difference
        )

        db.add(result)
        graded_count += 1

    db.commit()
    print(f"✓ Graded {graded_count} props for {yesterday}")

if __name__ == "__main__":
    track_previous_day_results()
```

**Schedule:**
- Run daily at 2:00am CST via cron
- Grades all props from previous day
- Builds historical dataset for training

---

### Week 3-4: Feature Engineering

#### 2.1 Player Feature Extraction

**File:** `backend/ml/feature_engineering/nba_props_features.py`

```python
"""
Feature engineering for NBA player props
Extracts 40-60 features per player prop
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
from backend.scrapers.nba.balldontlie_player_stats import BallDontLieClient

class NBAPropsFeatureEngineer:
    """
    Generates ML features for NBA player props predictions
    """

    def __init__(self):
        self.stats_client = BallDontLieClient()

    def extract_features(self,
                        player_id: int,
                        prop_type: str,
                        opponent_team_id: int,
                        game_date: datetime,
                        home_away: str) -> Dict:
        """
        Extract all features for a single player prop prediction

        Returns dict with 50+ features:
        - Player recent form (last 5, 10, 20 games)
        - Trend analysis (improving/declining)
        - Usage rates
        - Matchup history vs opponent
        - Rest days
        - Home/away splits
        - Opponent defensive stats
        - Game context (pace, total)
        """
        features = {}

        # 1. PLAYER BASELINE STATS
        season_avg = self.stats_client.get_player_season_averages(
            player_id,
            season=game_date.year
        )

        stat_map = {
            "points": "pts",
            "rebounds": "reb",
            "assists": "ast",
            "threes": "fg3m",
            "blocks": "blk",
            "steals": "stl"
        }
        stat_key = stat_map.get(prop_type, "pts")

        features[f"season_avg_{stat_key}"] = season_avg.get(stat_key, 0)
        features["season_games_played"] = season_avg.get("games_played", 0)
        features["season_minutes"] = season_avg.get("min", 0)
        features["season_fg_pct"] = season_avg.get("fgm", 0) / max(season_avg.get("fga", 1), 1)
        features["season_usage_rate"] = self._calculate_usage(season_avg)

        # 2. RECENT FORM (Last 5, 10, 20 games)
        recent_games = self.stats_client.get_player_recent_games(player_id, last_n_days=60)

        for window in [5, 10, 20]:
            recent_window = recent_games[:window]
            if recent_window:
                values = [g.get(stat_key, 0) for g in recent_window]
                features[f"last_{window}_avg_{stat_key}"] = np.mean(values)
                features[f"last_{window}_std_{stat_key}"] = np.std(values)
                features[f"last_{window}_max_{stat_key}"] = np.max(values)
                features[f"last_{window}_min_{stat_key}"] = np.min(values)

        # 3. TREND ANALYSIS
        if len(recent_games) >= 10:
            first_5_avg = np.mean([g.get(stat_key, 0) for g in recent_games[5:10]])
            last_5_avg = np.mean([g.get(stat_key, 0) for g in recent_games[:5]])
            features["trend_direction"] = (last_5_avg - first_5_avg) / max(first_5_avg, 0.1)
            features["improving"] = 1 if last_5_avg > first_5_avg else 0

        # 4. REST DAYS
        if recent_games:
            last_game_date = datetime.fromisoformat(recent_games[0]["game"]["date"])
            rest_days = (game_date - last_game_date).days
            features["rest_days"] = rest_days
            features["is_back_to_back"] = 1 if rest_days == 1 else 0
            features["is_rested"] = 1 if rest_days >= 3 else 0

        # 5. HOME/AWAY SPLITS
        home_games = [g for g in recent_games if self._is_home_game(g, player_id)]
        away_games = [g for g in recent_games if not self._is_home_game(g, player_id)]

        if home_games:
            features[f"home_avg_{stat_key}"] = np.mean([g.get(stat_key, 0) for g in home_games])
        if away_games:
            features[f"away_avg_{stat_key}"] = np.mean([g.get(stat_key, 0) for g in away_games])

        features["is_home"] = 1 if home_away == "HOME" else 0

        # 6. MATCHUP HISTORY VS OPPONENT
        vs_opponent_games = [g for g in recent_games
                            if self._is_vs_team(g, opponent_team_id)]
        if vs_opponent_games:
            features[f"vs_opp_avg_{stat_key}"] = np.mean([g.get(stat_key, 0)
                                                          for g in vs_opponent_games])
            features["vs_opp_games_count"] = len(vs_opponent_games)
        else:
            features[f"vs_opp_avg_{stat_key}"] = features[f"season_avg_{stat_key}"]
            features["vs_opp_games_count"] = 0

        # 7. OPPONENT DEFENSIVE STATS
        opp_def_stats = self._get_opponent_defense_stats(opponent_team_id, prop_type)
        features["opp_def_rating"] = opp_def_stats.get("def_rating", 100)
        features[f"opp_{stat_key}_allowed_per_game"] = opp_def_stats.get(f"{stat_key}_allowed", 0)
        features["opp_pace"] = opp_def_stats.get("pace", 100)

        # 8. GAME CONTEXT
        features["day_of_week"] = game_date.weekday()
        features["is_weekend"] = 1 if game_date.weekday() >= 5 else 0
        features["month"] = game_date.month

        # 9. MINUTES TREND (injury risk)
        if len(recent_games) >= 5:
            recent_minutes = [g.get("min", 0) for g in recent_games[:5]]
            features["recent_avg_minutes"] = np.mean(recent_minutes)
            features["minutes_declining"] = 1 if recent_minutes[0] < recent_minutes[-1] - 3 else 0

        # 10. CONSISTENCY SCORE
        if len(recent_games) >= 10:
            values = [g.get(stat_key, 0) for g in recent_games[:10]]
            mean_val = np.mean(values)
            std_val = np.std(values)
            features["consistency_score"] = std_val / max(mean_val, 0.1)

        return features

    def _calculate_usage(self, stats: Dict) -> float:
        """Estimate usage rate from box score stats"""
        fga = stats.get("fga", 0)
        fta = stats.get("fta", 0)
        turnovers = stats.get("turnover", 0)
        minutes = stats.get("min", 0)

        if minutes == 0:
            return 0

        # Simplified usage rate formula
        usage = (fga + 0.44 * fta + turnovers) / max(minutes, 1)
        return usage

    def _is_home_game(self, game: Dict, player_id: int) -> bool:
        """Determine if game was home or away for player"""
        # Implementation depends on BallDontLie data structure
        return True  # Placeholder

    def _is_vs_team(self, game: Dict, team_id: int) -> bool:
        """Check if game was vs specific opponent"""
        # Implementation depends on data structure
        return False  # Placeholder

    def _get_opponent_defense_stats(self, team_id: int, prop_type: str) -> Dict:
        """Fetch opponent's defensive stats"""
        # Would query team stats or calculate from recent games
        return {
            "def_rating": 110,
            "pace": 100,
            "pts_allowed": 115
        }
```

**Feature Categories:**

1. **Player Baseline (10 features)**
   - Season averages for target stat
   - Games played, minutes
   - FG%, usage rate, true shooting%

2. **Recent Form (15 features)**
   - Last 5/10/20 game averages
   - Standard deviation (consistency)
   - Max/min values

3. **Trend Analysis (5 features)**
   - Improving/declining indicator
   - Linear trend slope
   - Acceleration (2nd derivative)

4. **Rest & Schedule (6 features)**
   - Days since last game
   - Back-to-back indicator
   - 3-in-4 nights indicator
   - Road trip game number

5. **Home/Away Splits (4 features)**
   - Home average vs away average
   - Current game location
   - Home court advantage estimate

6. **Matchup History (6 features)**
   - Avg vs this opponent (career)
   - Avg vs this opponent (this season)
   - Number of matchups
   - Last game vs opponent

7. **Opponent Defense (8 features)**
   - Defensive rating
   - Position-specific defense ranking
   - Pace
   - Points/Assists/Rebounds allowed per game

8. **Game Context (4 features)**
   - Day of week
   - Month (season progression)
   - Playoff implication
   - National TV game

9. **Minutes Trend (3 features)**
   - Recent average minutes
   - Minutes declining (injury concern)
   - Coach trust indicator

10. **Consistency (2 features)**
    - Coefficient of variation
    - Hit rate on similar lines

**Total:** ~50-60 features per prop

---

### Week 5-6: ML Model Training

#### 3.1 Training Data Preparation

**File:** `backend/ml/data_loaders/nba_props_data_loader.py`

```python
"""
Loads and prepares NBA props training data
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backend.database.connection import get_db_session
from backend.database.models import PlayerPropsLine, PlayerPropsResult
from backend.ml.feature_engineering.nba_props_features import NBAPropsFeatureEngineer

class NBAPropsDataLoader:
    """
    Prepares training data for NBA props ML models
    """

    def __init__(self, min_games: int = 100):
        self.min_games = min_games
        self.feature_engineer = NBAPropsFeatureEngineer()

    def load_training_data(self,
                          start_date: datetime,
                          end_date: datetime,
                          prop_type: str = "points") -> pd.DataFrame:
        """
        Load historical props data with features and outcomes

        Returns DataFrame with:
        - 50+ feature columns
        - Target columns: actual_value, hit (over/under), edge
        """
        db = get_db_session()

        # Join props lines with results
        query = db.query(
            PlayerPropsLine,
            PlayerPropsResult
        ).join(
            PlayerPropsResult,
            (PlayerPropsLine.date == PlayerPropsResult.date) &
            (PlayerPropsLine.player_id == PlayerPropsResult.player_id) &
            (PlayerPropsLine.prop_type == PlayerPropsResult.prop_type)
        ).filter(
            PlayerPropsLine.date.between(start_date, end_date),
            PlayerPropsLine.prop_type == prop_type
        )

        rows = []
        for line, result in query.all():
            # Extract features
            features = self.feature_engineer.extract_features(
                player_id=line.player_id,
                prop_type=prop_type,
                opponent_team_id=self._get_team_id(line.opponent),
                game_date=line.date,
                home_away=line.home_away
            )

            # Add target variables
            features["market_line"] = line.market_line
            features["actual_value"] = result.actual_value
            features["hit_over"] = 1 if result.actual_value > line.market_line else 0
            features["edge"] = result.actual_value - line.market_line
            features["player_id"] = line.player_id
            features["date"] = line.date

            rows.append(features)

        df = pd.DataFrame(rows)

        # Data quality filters
        df = df.dropna(subset=["season_avg_pts", "last_10_avg_pts"])
        df = df[df["season_games_played"] >= 10]  # Minimum games for reliability

        print(f"✓ Loaded {len(df)} training samples for {prop_type}")
        print(f"  Hit rate: {df['hit_over'].mean():.1%}")
        print(f"  Avg edge: {df['edge'].mean():.2f}")

        return df

    def _get_team_id(self, team_abbr: str) -> int:
        """Convert team abbreviation to ID"""
        # Would use a lookup table
        return 1  # Placeholder
```

**Training Data Requirements:**
- Minimum 1,000 props outcomes for reliable model
- Recommendation: Collect 2-3 months of data before training
- Update dataset daily as new results come in

---

#### 3.2 Model Training Scripts

**File:** `backend/ml/models/nba_props/train_xgboost_props.py`

```python
"""
Train XGBoost model for NBA player props
"""
import xgboost as xgb
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, accuracy_score
import joblib
from datetime import datetime, timedelta
from backend.ml.data_loaders.nba_props_data_loader import NBAPropsDataLoader

def train_nba_points_model():
    """
    Train XGBoost regression model to predict player points
    """
    # Load training data
    loader = NBAPropsDataLoader()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)  # 3 months of data

    df = loader.load_training_data(
        start_date=start_date,
        end_date=end_date,
        prop_type="points"
    )

    # Feature columns (exclude metadata and targets)
    feature_cols = [col for col in df.columns if col not in [
        "market_line", "actual_value", "hit_over", "edge",
        "player_id", "date"
    ]]

    X = df[feature_cols]
    y_regression = df["actual_value"]  # Predict exact points
    y_classification = df["hit_over"]  # Predict over/under

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_regression, test_size=0.2, random_state=42
    )

    # XGBoost parameters (tuned for props)
    params = {
        "objective": "reg:squarederror",
        "learning_rate": 0.05,
        "max_depth": 6,
        "min_child_weight": 3,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "n_estimators": 500,
        "early_stopping_rounds": 50,
        "random_state": 42
    }

    # Train regression model (predict exact value)
    model = xgb.XGBRegressor(**params)
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False
    )

    # Evaluate
    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)

    print(f"\n=== NBA Points XGBoost Model ===")
    print(f"RMSE: {rmse:.2f} points")
    print(f"MAE: {mae:.2f} points")

    # Classification accuracy (over/under)
    df_test = df.loc[X_test.index]
    predictions_vs_line = y_pred > df_test["market_line"]
    actual_vs_line = df_test["hit_over"]
    accuracy = accuracy_score(actual_vs_line, predictions_vs_line)
    print(f"Over/Under Accuracy: {accuracy:.1%}")

    # Feature importance
    importance = pd.DataFrame({
        "feature": feature_cols,
        "importance": model.feature_importances_
    }).sort_values("importance", ascending=False)

    print(f"\nTop 10 Most Important Features:")
    print(importance.head(10).to_string(index=False))

    # Save model
    model_path = f"backend/ml/models/nba_props/xgboost_points_{datetime.now().strftime('%Y%m%d')}.pkl"
    joblib.dump(model, model_path)
    print(f"\n✓ Model saved: {model_path}")

    return model

if __name__ == "__main__":
    train_nba_points_model()
```

**Model Types to Train:**

1. **XGBoost Regressor**
   - Predicts exact stat value
   - Best for capturing non-linear relationships
   - Target: RMSE < 3.0 points

2. **LightGBM Regressor**
   - Faster training and inference
   - Good for real-time predictions
   - Target: RMSE < 3.5 points

3. **Random Forest**
   - Provides uncertainty estimates
   - Less prone to overfitting
   - Target: RMSE < 4.0 points

4. **Ensemble Model**
   - Combines all 3 models
   - Weighted average based on recent performance
   - Target: RMSE < 2.8 points

**Performance Benchmarks:**
- **Excellent:** RMSE < 3.0 points, 55%+ over/under accuracy
- **Good:** RMSE 3.0-4.0 points, 52-55% accuracy
- **Baseline:** RMSE 4.0-5.0 points, 50-52% accuracy
- **Poor:** RMSE > 5.0 points, <50% accuracy

---

### Week 7-8: Production Integration

#### 4.1 Daily Prediction Pipeline

**File:** `backend/ml/prediction_pipelines/nba_props_daily_predictions.py`

```python
"""
Generate daily NBA props predictions using trained ML models
Runs at 9am CST
"""
import joblib
import pandas as pd
from datetime import datetime
from backend.player_props_client import PlayerPropsClient
from backend.ml.feature_engineering.nba_props_features import NBAPropsFeatureEngineer
from backend.database.models import PlayerPropsPrediction
from backend.database.connection import get_db_session

async def generate_daily_predictions(model_path: str = None):
    """
    Generate ML predictions for all NBA props today
    """
    # Load latest models
    if not model_path:
        model_path = "backend/ml/models/nba_props/xgboost_points_latest.pkl"

    model = joblib.load(model_path)
    feature_engineer = NBAPropsFeatureEngineer()
    props_client = PlayerPropsClient()
    db = get_db_session()

    # Fetch today's props
    nba_props = await props_client.fetch_all_player_props("basketball_nba")

    predictions = []
    for game_id, markets in nba_props.items():
        for market_key, props in markets.items():
            if market_key != "points":  # Start with points only
                continue

            for player_name, prop_data in props.items():
                # Extract features
                features = feature_engineer.extract_features(
                    player_id=prop_data["player_id"],
                    prop_type="points",
                    opponent_team_id=prop_data["opponent_team_id"],
                    game_date=datetime.now(),
                    home_away=prop_data["home_away"]
                )

                # Predict
                features_df = pd.DataFrame([features])
                predicted_value = model.predict(features_df)[0]
                market_line = prop_data["line"]

                # Calculate edge
                edge = predicted_value - market_line
                edge_pct = (edge / market_line) * 100

                # Confidence score (based on feature quality)
                confidence = calculate_confidence(features, model)

                # Recommendation
                if abs(edge_pct) < 5.0:
                    recommendation = "PASS"
                elif edge > 0:
                    recommendation = "OVER"
                else:
                    recommendation = "UNDER"

                # Store prediction
                prediction = PlayerPropsPrediction(
                    prediction_date=datetime.now().date(),
                    game_date=prop_data["game_date"],
                    player_id=prop_data["player_id"],
                    player_name=player_name,
                    team=prop_data["team"],
                    opponent=prop_data["opponent"],
                    prop_type="points",
                    market_line=market_line,
                    predicted_value=predicted_value,
                    confidence=confidence,
                    model_type="xgboost",
                    edge_pct=edge_pct,
                    recommendation=recommendation
                )

                db.add(prediction)
                predictions.append(prediction)

    db.commit()
    print(f"✓ Generated {len(predictions)} NBA points predictions")

    # Filter to high-edge plays
    high_edge = [p for p in predictions if abs(p.edge_pct) >= 5.0]
    print(f"  {len(high_edge)} with ≥5% edge")

    return predictions

def calculate_confidence(features: dict, model) -> float:
    """
    Calculate prediction confidence based on:
    - Feature completeness
    - Sample size (games played)
    - Consistency (low std dev)
    - Model certainty (tree agreement)
    """
    confidence = 70.0  # Base confidence

    # Increase confidence if player has many games
    games_played = features.get("season_games_played", 0)
    if games_played >= 40:
        confidence += 10
    elif games_played >= 20:
        confidence += 5

    # Increase confidence if player is consistent
    consistency = features.get("consistency_score", 1.0)
    if consistency < 0.2:  # Very consistent
        confidence += 10
    elif consistency < 0.4:
        confidence += 5

    # Decrease confidence if declining minutes (injury concern)
    if features.get("minutes_declining", 0) == 1:
        confidence -= 15

    # Decrease confidence if back-to-back
    if features.get("is_back_to_back", 0) == 1:
        confidence -= 5

    return min(max(confidence, 30), 95)  # Clamp between 30-95

if __name__ == "__main__":
    import asyncio
    asyncio.run(generate_daily_predictions())
```

**Schedule:**
- **9:00am CST:** Generate predictions for all props
- **10:00am CST:** Cache results in Redis for fast API access
- **Throughout day:** Monitor for line movements, regenerate if needed

---

#### 4.2 Update API Endpoints

**File:** `backend/routes/player_props.py` (UPDATE)

```python
"""
Add ML predictions endpoint
"""
from fastapi import APIRouter, Query
from datetime import datetime
from backend.database.models import PlayerPropsPrediction
from backend.database.connection import get_db_session

@app.get("/api/player-props/nba/ml-edges")
async def get_nba_ml_props_edges(
    min_edge_pct: float = Query(5.0, description="Minimum edge percentage"),
    min_confidence: float = Query(60.0, description="Minimum confidence score"),
    prop_types: str = Query("points,rebounds,assists", description="Comma-separated prop types")
):
    """
    Get NBA props with ML model predictions and edges
    Returns only props meeting edge and confidence thresholds
    """
    db = get_db_session()
    today = datetime.now().date()

    # Query pre-computed predictions
    predictions = db.query(PlayerPropsPrediction).filter(
        PlayerPropsPrediction.game_date == today,
        PlayerPropsPrediction.confidence >= min_confidence,
        PlayerPropsPrediction.edge_pct >= min_edge_pct,
        PlayerPropsPrediction.prop_type.in_(prop_types.split(","))
    ).order_by(
        PlayerPropsPrediction.edge_pct.desc()
    ).all()

    # Format response
    response = {
        "date": str(today),
        "total_edges": len(predictions),
        "props": []
    }

    for pred in predictions:
        prop_data = {
            "player_name": pred.player_name,
            "team": pred.team,
            "opponent": pred.opponent,
            "prop_type": pred.prop_type,
            "market_line": pred.market_line,
            "predicted_value": pred.predicted_value,
            "edge_pct": pred.edge_pct,
            "confidence": pred.confidence,
            "recommendation": pred.recommendation,
            "model_type": pred.model_type
        }
        response["props"].append(prop_data)

    return response
```

**New Endpoints:**
- `GET /api/player-props/nba/ml-edges` - ML predictions (new)
- `GET /api/player-props/nba/edges` - Keep old rule-based for comparison
- `GET /api/player-props/performance` - Model performance metrics

---

### Week 8: Testing & Validation

#### 5.1 Backtesting Framework

**File:** `backend/ml/evaluation/backtest_props_model.py`

```python
"""
Backtest NBA props ML model on historical data
"""
import pandas as pd
from datetime import datetime, timedelta
from backend.ml.data_loaders.nba_props_data_loader import NBAPropsDataLoader
import joblib

def backtest_model(model_path: str, days_back: int = 30):
    """
    Test model on most recent N days (walk-forward)
    """
    loader = NBAPropsDataLoader()
    model = joblib.load(model_path)

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    # Load data
    df = loader.load_training_data(start_date, end_date, prop_type="points")

    # Features
    feature_cols = [col for col in df.columns if col not in [
        "market_line", "actual_value", "hit_over", "edge",
        "player_id", "date"
    ]]

    X = df[feature_cols]
    predictions = model.predict(X)

    # Analyze by confidence level
    df["predicted_value"] = predictions
    df["predicted_over"] = predictions > df["market_line"]
    df["correct"] = df["predicted_over"] == df["hit_over"]

    # Overall metrics
    accuracy = df["correct"].mean()
    rmse = ((df["predicted_value"] - df["actual_value"]) ** 2).mean() ** 0.5

    # ROI calculation (assuming -110 odds)
    df["profit"] = df.apply(lambda row:
        0.91 if row["correct"] else -1.0, axis=1
    )
    roi = df["profit"].sum() / len(df) * 100

    print(f"\n=== Backtest Results ({days_back} days) ===")
    print(f"Total Predictions: {len(df)}")
    print(f"Accuracy: {accuracy:.1%}")
    print(f"RMSE: {rmse:.2f} points")
    print(f"ROI: {roi:+.2f}%")
    print(f"Total Profit: {df['profit'].sum():+.2f} units")

    # By edge size
    for min_edge in [3, 5, 7, 10]:
        subset = df[abs(df["predicted_value"] - df["market_line"]) >= min_edge]
        if len(subset) > 0:
            acc = subset["correct"].mean()
            roi_subset = subset["profit"].sum() / len(subset) * 100
            print(f"\n≥{min_edge}% Edge:")
            print(f"  Count: {len(subset)}")
            print(f"  Accuracy: {acc:.1%}")
            print(f"  ROI: {roi_subset:+.2f}%")

if __name__ == "__main__":
    backtest_model("backend/ml/models/nba_props/xgboost_points_latest.pkl")
```

**Success Criteria:**
- ✅ Accuracy > 53% on historical data
- ✅ ROI > +3% over 30 days
- ✅ Profitable at ≥5% edge threshold
- ✅ RMSE < 4.0 points

---

## DATA SOURCES & APIs

### Current Data Sources (Active)

#### 1. The Odds API (Props Lines)
**Status:** ✅ ACTIVE
**Cost:** $50-200/month depending on usage
**Coverage:** All 6 sports, all major books
**API Key:** Already configured in `backend/config.py`

**Endpoints:**
- `/sports/{sport}/odds` - Game odds
- `/sports/{sport}/events/{event_id}/odds` - Props odds

**Rate Limits:**
- 500 requests/month (free tier)
- Unlimited (paid tier: $50/mo)

**Props Markets:**
- NBA: Points, Rebounds, Assists, Threes, PRA, Blocks, Steals
- NFL: Pass Yards, Rush Yards, Receptions, TDs
- NHL: Points, Goals, Assists, Shots, Saves (goalies)
- MLB: Hits, Home Runs, RBIs, Strikeouts (pitchers)

---

### NEW Data Sources Needed

#### 2. BallDontLie API (NBA Player Stats)
**Status:** 🆕 NEEDS INTEGRATION
**Cost:** FREE or $10/mo (pro tier)
**Speed:** 30x faster than NBA.com API
**API Key:** `9ca7e6df-853f-4ac4-a964-2eafa7627b8d`

**Why:**
- Current NBA.com API is "extremely slow (10-30s)"
- BallDontLie: <500ms response time
- Already have API key, just need integration

**Endpoints:**
- `GET /players` - Search players
- `GET /stats` - Game logs
- `GET /season_averages` - Season stats
- `GET /games` - Game information

**Implementation Priority:** 🔥 HIGH (Week 1)

---

#### 3. NFL Player Stats API Options

**Option A: Sportradar NFL API** (RECOMMENDED)
- **Cost:** $500-2000/month
- **Coverage:** Real-time stats, injuries, depth charts
- **Quality:** Official NFL data partner
- **Delay:** Real-time to 5-minute delay
- **Trial:** 30-day free trial available

**Option B: ESPN API (Unofficial)**
- **Cost:** FREE
- **Coverage:** Basic stats, game logs
- **Quality:** Good but not real-time
- **Delay:** 15-30 minutes
- **Reliability:** Can break with ESPN updates

**Option C: Pro Football Reference (Scraping)**
- **Cost:** FREE
- **Coverage:** Historical data, season stats
- **Quality:** Excellent for historical
- **Delay:** Next-day data
- **Legal:** Check robots.txt

**Recommendation:**
- **Phase 1:** ESPN API (free, test viability)
- **Phase 2:** Sportradar (production quality)

---

#### 4. NHL Player Stats API Options

**Option A: NHL Official API** (RECOMMENDED)
- **Cost:** FREE
- **Coverage:** Real-time stats, all historical data
- **Quality:** Official, highly reliable
- **Delay:** Real-time
- **Docs:** https://gitlab.com/dword4/nhlapi

**Endpoints:**
- `/api/v1/people/{playerId}/stats` - Player stats
- `/api/v1/game/{gameId}/feed/live` - Live game data
- `/api/v1/schedule` - Schedule

**Implementation Priority:** 🔥 MEDIUM (Week 6-8)

---

#### 5. MLB Player Stats API Options

**Option A: MLB Stats API** (RECOMMENDED)
- **Cost:** FREE
- **Coverage:** Official MLB data
- **Quality:** Excellent
- **Delay:** Real-time
- **Docs:** https://github.com/toddrob99/MLB-StatsAPI

**Endpoints:**
- `/people/{playerId}` - Player info
- `/people/{playerId}/stats` - Stats
- `/game/{gamePk}/feed/live` - Live game

**Option B: Baseball Reference (Scraping)**
- **Cost:** FREE
- **Coverage:** Historical data
- **Quality:** Best for historical
- **Delay:** Next-day

**Implementation Priority:** 🔶 LOW (Phase 4)

---

#### 6. NCAAB Player Stats API Options

**Option A: ESPN College Basketball API**
- **Cost:** FREE (unofficial)
- **Coverage:** D1 player stats
- **Quality:** Good
- **Delay:** 15-30 minutes

**Option B: SportsReference Scraping**
- **Cost:** FREE
- **Coverage:** All divisions
- **Quality:** Excellent
- **Delay:** Next-day

**Option C: BallerTV / NCAA.com**
- **Cost:** Varies
- **Coverage:** Official but limited
- **Quality:** Good
- **Delay:** Real-time

**Recommendation:**
- Start with ESPN API
- Supplement with SportsReference scraping

**Implementation Priority:** 🔶 LOW (Phase 4)

---

### Data Source Summary Table

| Sport | Odds Source | Stats Source | Cost | Priority | Week |
|-------|------------|--------------|------|----------|------|
| NBA | The Odds API ✅ | BallDontLie 🆕 | $10/mo | 🔥 HIGH | 1-2 |
| NFL | The Odds API ✅ | ESPN → Sportradar | $0 → $500/mo | 🔥 HIGH | 8-10 |
| NHL | The Odds API ✅ | NHL Official API | FREE | 🔶 MEDIUM | 12-14 |
| MLB | The Odds API ✅ | MLB Stats API | FREE | 🔶 LOW | 16-18 |
| NCAAB | The Odds API ✅ | ESPN API | FREE | 🔶 LOW | 20-22 |

**Total Monthly Cost (All Sports):**
- Initial: $10/mo (BallDontLie)
- Production: $510/mo (+ Sportradar NFL)
- Maximum: $2010/mo (if using premium NFL data)

---

## WEEKLY SCHEDULE

### Phase 1: NBA Player Props ML (Weeks 1-8)

**Week 1: Database & Infrastructure**
- Day 1-2: Create database schema, set up PostgreSQL
- Day 3-4: Integrate BallDontLie API (replace NBA.com)
- Day 5: Build daily props lines scraper
- Day 6: Build results tracking scraper
- Day 7: Test data collection for 1 week

**Week 2: Data Collection**
- Days 1-7: Collect props lines and results
- Goal: Accumulate 500+ props outcomes
- Monitor data quality and API reliability

**Week 3: Feature Engineering**
- Day 1-3: Build NBAPropsFeatureEngineer class
- Day 4-5: Implement all 50+ feature calculations
- Day 6-7: Test feature extraction on historical data

**Week 4: Feature Engineering (cont.)**
- Day 1-3: Optimize feature calculations for speed
- Day 4-5: Build feature validation tests
- Day 6-7: Create feature importance analysis

**Week 5: Model Training (Points)**
- Day 1-2: Prepare training dataset
- Day 3-4: Train XGBoost model
- Day 5: Train LightGBM model
- Day 6: Train Random Forest model
- Day 7: Create ensemble model

**Week 6: Model Training (Other Props)**
- Day 1-2: Train rebounds models
- Day 3-4: Train assists models
- Day 5-6: Train threes/blocks/steals models
- Day 7: Model evaluation and comparison

**Week 7: Production Integration**
- Day 1-3: Build daily prediction pipeline
- Day 4-5: Update API endpoints
- Day 6-7: Frontend integration and testing

**Week 8: Testing & Launch**
- Day 1-3: Backtesting on historical data
- Day 4-5: Shadow mode (generate predictions, don't show users)
- Day 6-7: Public launch of NBA ML props

---

### Phase 2: NFL Player Props ML (Weeks 9-16)

**Week 9-10: NFL Data Infrastructure**
- Integrate ESPN NFL API
- Build NFL-specific feature engineering
- Collect 2-4 weeks of NFL props data

**Week 11-12: NFL Model Training**
- Train models for Pass Yards, Rush Yards, Receptions
- NFL-specific features (weather, home/away, matchup)

**Week 13-14: NFL Testing & Launch**
- Backtest on recent NFL weeks
- Launch NFL ML props

**Week 15-16: Optimization**
- Tune models based on first weeks of results
- Add live updates during games

---

### Phase 3: NHL Player Props ML (Weeks 17-24)

**Week 17-18: NHL Data Infrastructure**
- Integrate NHL Official API
- Build NHL-specific feature engineering
- Collect 3-4 weeks of NHL props data

**Week 19-20: NHL Model Training**
- Train models for Points, Goals, Assists, Shots
- Goalie-specific models (Saves)

**Week 21-22: NHL Testing & Launch**
- Backtest on historical data
- Launch NHL ML props

**Week 23-24: Optimization**
- Tune models
- Add line combinations and ice time features

---

### Phase 4: MLB & NCAAB (Weeks 25-32)

**MLB** (Weeks 25-28)
- Integrate MLB Stats API
- Train models for Hits, Home Runs, Strikeouts (pitchers)
- Launch

**NCAAB** (Weeks 29-32)
- Integrate ESPN College Basketball API
- Train models for Points, Rebounds, Assists
- Launch

---

## TECHNICAL ARCHITECTURE (FINAL)

### Complete ML System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA COLLECTION LAYER                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  [The Odds API] ──→ Props Lines Scraper (8am daily)          │
│  [BallDontLie]  ──→ Player Stats Scraper (7am daily)         │
│  [NFL API]      ──→ NFL Stats Scraper (7am daily)            │
│  [NHL API]      ──→ NHL Stats Scraper (7am daily)            │
│                                                               │
│  ↓                                                            │
│  [PostgreSQL Database]                                        │
│    - player_props_lines                                       │
│    - player_props_results                                     │
│    - player_props_predictions                                 │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                  FEATURE ENGINEERING LAYER                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  NBAPropsFeatureEngineer                                      │
│  NFLPropsFeatureEngineer                                      │
│  NHLPropsFeatureEngineer                                      │
│                                                               │
│  Extracts 50+ features per prop:                             │
│  - Recent form (5/10/20 games)                               │
│  - Matchup history                                            │
│  - Rest days, home/away                                       │
│  - Opponent defense                                           │
│  - Usage rates, consistency                                   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                      ML MODELS LAYER                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Per Sport × Per Prop Type × Per Model Type                  │
│                                                               │
│  NBA: Points, Rebounds, Assists, Threes, Blocks, Steals      │
│  NFL: Pass Yds, Rush Yds, Receptions, TDs                    │
│  NHL: Points, Goals, Assists, Shots, Saves                   │
│                                                               │
│  Models (per prop type):                                      │
│  1. XGBoost Regressor                                         │
│  2. LightGBM Regressor                                        │
│  3. Random Forest Regressor                                   │
│  4. Ensemble (weighted average)                               │
│                                                               │
│  Total Models: ~100-150                                       │
│  (6 prop types × 3 sports × 4 model types = 72 minimum)      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                   PREDICTION PIPELINE                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Daily Predictions (9am CST):                                 │
│  1. Fetch today's props lines                                 │
│  2. Load player stats (cached from 7am scrape)                │
│  3. Extract features for all props                            │
│  4. Run inference on all models                               │
│  5. Generate predictions + confidence + edge                  │
│  6. Store in database + Redis cache                           │
│  7. Send to frontend API                                      │
│                                                               │
│  Live Updates (every 30 min during games):                    │
│  1. Check for line movements                                  │
│  2. Re-run inference if line moved >0.5                       │
│  3. Alert users to new edges                                  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                  RETRAINING PIPELINE                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Weekly Retraining (Mondays 4-9am CST):                       │
│  1. Results Grading (2am):                                    │
│     - Fetch final game stats                                  │
│     - Match to props lines                                    │
│     - Store outcomes                                          │
│                                                               │
│  2. Model Retraining (4-7am):                                 │
│     - Load past 90 days of data                               │
│     - Retrain all models                                      │
│     - Evaluate on holdout set                                 │
│     - If better than current: deploy new models               │
│     - If worse: keep current models, log alert                │
│                                                               │
│  3. Model Deployment (7-9am):                                 │
│     - Save new models to production                           │
│     - Update model registry                                   │
│     - Clear prediction caches                                 │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                  PERFORMANCE TRACKING                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Real-time Metrics:                                           │
│  - Accuracy (over/under hit rate)                             │
│  - RMSE (prediction error)                                    │
│  - ROI (profit/loss)                                          │
│  - CLV (closing line value)                                   │
│                                                               │
│  By Dimension:                                                │
│  - Sport                                                      │
│  - Prop type                                                  │
│  - Confidence level                                           │
│  - Edge size                                                  │
│  - Model type                                                 │
│                                                               │
│  Displayed on:                                                │
│  - /model-performance page                                    │
│  - /ml-models-explained page                                  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND DISPLAY                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Props.tsx:                                                   │
│  - "ML Edges" tab (new)                                       │
│  - Shows player, prop type, line                              │
│  - ML prediction ± confidence                                 │
│  - Edge % and recommendation                                  │
│  - Best odds and bookmaker                                    │
│  - Projection breakdown                                       │
│                                                               │
│  Filters:                                                     │
│  - Sport                                                      │
│  - Prop type                                                  │
│  - Minimum edge %                                             │
│  - Minimum confidence                                         │
│  - Player search                                              │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## SUCCESS METRICS

### Model Performance Targets

| Metric | Baseline | Good | Excellent |
|--------|----------|------|-----------|
| **Accuracy (Over/Under)** | 50% | 53% | 56%+ |
| **RMSE (Points)** | 5.0 | 3.5 | <3.0 |
| **ROI (≥5% Edge)** | 0% | +3% | +8%+ |
| **CLV** | 0% | +2% | +5%+ |

### Business Metrics

- **User Engagement:** 50%+ of users check props daily
- **Retention:** Props users have 2x retention vs non-props users
- **Revenue:** Props drives 30%+ of subscription upgrades
- **Market Share:** #1 ranked for "player props ML predictions" SEO

---

## RISK MITIGATION

### Risk 1: Insufficient Historical Data
**Mitigation:**
- Start data collection immediately (Week 1)
- Consider purchasing historical props data ($500-2000)
- Use transfer learning from game totals models
- Accept lower accuracy initially, improve over time

### Risk 2: Slow API Responses
**Mitigation:**
- Use BallDontLie (30x faster than NBA.com)
- Cache player stats daily (don't fetch on-demand)
- Pre-compute predictions at 9am
- Use Redis for fast API responses

### Risk 3: Model Overfitting
**Mitigation:**
- Cross-validation on training
- Walk-forward backtesting
- Monitor live performance vs backtest
- Auto-rollback if performance degrades >5%

### Risk 4: Bookmaker Limits
**Mitigation:**
- Don't publish exact edge sizes publicly
- Require premium subscription for high-edge props
- Rotate bookmaker recommendations
- Focus on education, not guarantees

### Risk 5: Regulatory/Legal Issues
**Mitigation:**
- All disclaimers in place (done)
- "Educational purposes only" framing
- No guarantee of profits
- Check state-by-state gambling laws

---

## ESTIMATED COSTS

### Development Costs (4-6 months)

| Item | Cost |
|------|------|
| BallDontLie API | $10/mo × 6 = $60 |
| The Odds API | $50/mo × 6 = $300 |
| PostgreSQL (cloud) | $20/mo × 6 = $120 |
| Sportradar NFL (optional) | $500/mo × 4 = $2000 |
| Historical data purchase | $500 (one-time) |
| **Total (Basic)** | **$980** |
| **Total (with NFL premium)** | **$2980** |

### Ongoing Costs (Monthly)

| Item | Cost |
|------|------|
| BallDontLie API | $10 |
| The Odds API | $50 |
| PostgreSQL (cloud) | $20 |
| Sportradar NFL (optional) | $500 |
| **Total (Basic)** | **$80/mo** |
| **Total (with NFL premium)** | **$580/mo** |

### Return on Investment

**Current Users:** ~500 (estimate)
**Props Feature Value:** +$10/mo subscription upgrade
**Conversion Rate:** 30% try props → 20% convert to paid

**Monthly Revenue:**
- 500 users × 30% try props = 150 users try
- 150 × 20% convert = 30 new paid subs
- 30 × $10/mo = **$300/mo additional revenue**

**ROI:**
- Revenue: $300/mo
- Cost: $80-580/mo
- **Net Profit: $220/mo (basic) to -$280/mo (premium NFL)**

**Conclusion:** Profitable with basic APIs, may need higher pricing or more users to justify premium NFL data.

---

## NEXT STEPS

### Immediate Actions (This Week)

1. **Day 1:** Create database schema, set up PostgreSQL
2. **Day 2:** Integrate BallDontLie API, test player stats fetching
3. **Day 3:** Build daily props lines scraper
4. **Day 4:** Build results tracking scraper
5. **Day 5:** Deploy scrapers to VPS, start data collection
6. **Day 6-7:** Monitor data quality, fix any issues

### Week 2 Actions

1. Continue data collection (goal: 500+ props outcomes)
2. Begin feature engineering development
3. Research NFL and NHL APIs
4. Plan model training experiments

### Decision Points

**After 2 Weeks:**
- ✅ Do we have clean data collection working?
- ✅ Is BallDontLie API fast and reliable?
- ❌ If data quality issues, fix before proceeding

**After 4 Weeks:**
- ✅ Do we have 1000+ props outcomes?
- ✅ Are features extracting correctly?
- ❌ If insufficient data, wait 2 more weeks

**After 6 Weeks:**
- ✅ Are models beating baseline (53% accuracy)?
- ✅ Is RMSE < 4.0 points?
- ❌ If not, revise features or get more data

**After 8 Weeks:**
- ✅ Launch NBA ML props to production
- ✅ Begin NFL data collection
- ✅ Monitor NBA performance for 2 weeks before NFL

---

## CONCLUSION

**Current State:**
- Props UI: ✅ Complete
- Props odds: ✅ Working
- NBA projections: ⚠️ Rule-based only
- ML models: ❌ Not implemented

**What This Plan Delivers:**
- 🎯 NBA ML props in 8 weeks
- 🎯 NFL ML props in 16 weeks
- 🎯 NHL ML props in 24 weeks
- 🎯 100+ ML models across 3 sports
- 🎯 Daily predictions with confidence levels
- 🎯 Weekly automatic retraining
- 🎯 Real-time performance tracking

**Estimated Timeline:** 6 months full implementation
**Estimated Cost:** $980-2980 (one-time) + $80-580/mo (ongoing)
**Estimated ROI:** Profitable with basic APIs

**Critical Success Factor:** Start data collection immediately. Cannot train models without historical outcomes.

**First Step:** Approve this plan → Begin Week 1 tasks tomorrow.

---

**END OF IMPLEMENTATION PLAN**
