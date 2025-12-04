# MoreHockeyStats.com API Integration Plan
**Created:** 2025-11-11
**Status:** Pending API Access Approval
**Priority:** HIGH (Unique Data Source)

---

## OVERVIEW

Integration of MoreHockeyStats.com event-level NHL data into our autonomous ML system.

**Expected Impact:** +2-5% accuracy improvement on NHL predictions (especially late-game)

**Unique Value:** Only source with granular empty net goal data going back to 1999

---

## PHASE 1: API CLIENT IMPLEMENTATION (Day 1-2)

### File: `backend/scrapers/morehockeystats_client.py`

```python
"""
MoreHockeyStats.com API Client
MongoDB-style REST API for NHL event data

Documentation: https://morehockeystats.com/data/api
Pricing: $0.01/record or free with attribution
"""

import requests
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class MoreHockeyStatsClient:
    """
    Client for MoreHockeyStats.com MongoDB-style API

    Collections used:
    - GOAL: Goal events (empty net detection)
    - FAC: Faceoff events (possession proxy)
    - PENL: Penalty events (special teams situations)
    - games: Game metadata
    - schedule: Schedule data
    """

    API_URL = "https://morehockeystats.com/api"
    COST_PER_RECORD = 0.01  # $0.01 per record for most collections

    def __init__(self, username: str, password: str, cache_dir: str = None):
        """
        Initialize API client

        Args:
            username: API username from MoreHockeyStats
            password: API password
            cache_dir: Optional directory to cache responses
        """
        self.username = username
        self.password = password
        self.cache_dir = Path(cache_dir) if cache_dir else Path(__file__).parent.parent / "data" / "cache" / "morehockeystats"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.total_cost = 0.0  # Track API usage costs

    def _build_request(self, query: Dict) -> Dict:
        """Build API request with credentials"""
        return {
            "user": self.username,
            "pass": self.password,
            "query": query
        }

    def _execute_query(self, query: Dict, cache_key: str = None) -> Dict:
        """
        Execute API query with optional caching

        Args:
            query: MongoDB-style query dict
            cache_key: Optional cache filename

        Returns:
            API response dict with 'data', 'count', 'cost', 'status'
        """
        # Check cache first
        if cache_key:
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                logger.info(f"Using cached data: {cache_key}")
                with open(cache_file, 'r') as f:
                    return json.load(f)

        # Execute API request
        payload = self._build_request(query)

        try:
            response = requests.post(self.API_URL, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()

            # Track costs
            cost = result.get('cost', 0)
            self.total_cost += cost
            logger.info(f"Query cost: ${cost:.4f} | Total session cost: ${self.total_cost:.4f}")

            # Check status
            status = result.get('status', 0)
            if status != 201:
                logger.error(f"API error: {result.get('error', 'Unknown error')}")
                raise Exception(f"API returned status {status}")

            # Cache response
            if cache_key:
                with open(cache_file, 'w') as f:
                    json.dump(result, f, indent=2)

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise

    def estimate_cost(self, query: Dict) -> float:
        """
        Estimate query cost before execution

        Args:
            query: The query to estimate

        Returns:
            Estimated cost in dollars
        """
        count_query = query.copy()
        count_query['type'] = 'count'

        result = self._execute_query(count_query)
        record_count = result.get('count', 0)

        estimated_cost = record_count * self.COST_PER_RECORD
        logger.info(f"Estimated query cost: ${estimated_cost:.2f} ({record_count} records)")

        return estimated_cost

    # ========== EMPTY NET DATA ==========

    def get_empty_net_goals(
        self,
        season: int,
        team: Optional[str] = None,
        include_playoffs: bool = False
    ) -> List[Dict]:
        """
        Get empty net goal events

        Args:
            season: NHL season (e.g., 20232024 for 2023-24)
            team: Optional team filter (e.g., "TOR")
            include_playoffs: Include playoff games

        Returns:
            List of goal event dictionaries
        """
        filter_query = {
            "season": season,
            "emptyNet": True
        }

        if team:
            # Get goals scored BY team AND goals allowed by team
            filter_query["$or"] = [
                {"team": team},
                {"opponent": team}
            ]

        if not include_playoffs:
            filter_query["stage"] = {"$ne": "playoffs"}

        query = {
            "type": "find",
            "collection": "GOAL",
            "filter": filter_query,
            "fields": {
                "team": 1,
                "opponent": 1,
                "period": 1,
                "periodTime": 1,
                "scorer": 1,
                "score": 1,
                "situation": 1,
                "game": 1,
                "date": 1
            }
        }

        cache_key = f"empty_net_{season}_{team or 'all'}_playoffs_{include_playoffs}"
        result = self._execute_query(query, cache_key=cache_key)

        return result.get('data', [])

    def get_team_empty_net_stats(self, season: int) -> Dict[str, Dict]:
        """
        Get empty net statistics for all teams

        Args:
            season: NHL season

        Returns:
            Dict mapping team abbr to {goals_for, goals_against, net_rating}
        """
        all_en_goals = self.get_empty_net_goals(season)

        team_stats = {}

        for goal in all_en_goals:
            scoring_team = goal.get('team')
            opponent_team = goal.get('opponent')

            # Initialize team stats
            if scoring_team not in team_stats:
                team_stats[scoring_team] = {'goals_for': 0, 'goals_against': 0}
            if opponent_team not in team_stats:
                team_stats[opponent_team] = {'goals_for': 0, 'goals_against': 0}

            # Record goal
            team_stats[scoring_team]['goals_for'] += 1
            team_stats[opponent_team]['goals_against'] += 1

        # Calculate net ratings
        for team, stats in team_stats.items():
            stats['net_rating'] = stats['goals_for'] - stats['goals_against']
            stats['efficiency'] = stats['goals_for'] / max(stats['goals_for'] + stats['goals_against'], 1)

        return team_stats

    # ========== FACEOFF DATA ==========

    def get_faceoff_stats(
        self,
        season: int,
        team: Optional[str] = None,
        zone: Optional[str] = None
    ) -> List[Dict]:
        """
        Get faceoff events

        Args:
            season: NHL season
            team: Optional team filter
            zone: Optional zone filter ("Off", "Def", "Neu")

        Returns:
            List of faceoff event dictionaries
        """
        filter_query = {"season": season}

        if team:
            filter_query["$or"] = [
                {"winner": team},
                {"loser": team}
            ]

        if zone:
            filter_query["zone"] = zone

        query = {
            "type": "find",
            "collection": "FAC",
            "filter": filter_query,
            "fields": {
                "winner": 1,
                "loser": 1,
                "zone": 1,
                "period": 1,
                "game": 1
            }
        }

        cache_key = f"faceoffs_{season}_{team or 'all'}_{zone or 'all'}"
        result = self._execute_query(query, cache_key=cache_key)

        return result.get('data', [])

    def get_team_faceoff_percentages(self, season: int) -> Dict[str, float]:
        """
        Calculate faceoff win % for all teams

        Args:
            season: NHL season

        Returns:
            Dict mapping team abbr to faceoff win percentage
        """
        all_faceoffs = self.get_faceoff_stats(season)

        team_wins = {}
        team_total = {}

        for faceoff in all_faceoffs:
            winner = faceoff.get('winner')
            loser = faceoff.get('loser')

            # Track wins
            team_wins[winner] = team_wins.get(winner, 0) + 1

            # Track total faceoffs
            team_total[winner] = team_total.get(winner, 0) + 1
            team_total[loser] = team_total.get(loser, 0) + 1

        # Calculate percentages
        faceoff_pct = {}
        for team in team_total:
            wins = team_wins.get(team, 0)
            total = team_total[team]
            faceoff_pct[team] = wins / total if total > 0 else 0.5

        return faceoff_pct

    # ========== PENALTY DATA ==========

    def get_penalty_stats(
        self,
        season: int,
        team: Optional[str] = None,
        period: Optional[int] = None
    ) -> List[Dict]:
        """
        Get penalty events

        Args:
            season: NHL season
            team: Optional team that committed penalty
            period: Optional period filter (1, 2, 3, 4=OT)

        Returns:
            List of penalty event dictionaries
        """
        filter_query = {"season": season}

        if team:
            filter_query["team"] = team

        if period:
            filter_query["period"] = period

        query = {
            "type": "find",
            "collection": "PENL",
            "filter": filter_query,
            "fields": {
                "team": 1,
                "player": 1,
                "penalty": 1,
                "period": 1,
                "periodTime": 1,
                "duration": 1,
                "game": 1
            }
        }

        cache_key = f"penalties_{season}_{team or 'all'}_p{period or 'all'}"
        result = self._execute_query(query, cache_key=cache_key)

        return result.get('data', [])

    # ========== REFERENCE DATA ==========

    def get_team_list(self) -> List[Dict]:
        """Get list of all NHL teams"""
        query = {
            "type": "find",
            "collection": "teams",
            "filter": {},
            "fields": {
                "abbreviation": 1,
                "name": 1,
                "conference": 1,
                "division": 1
            }
        }

        result = self._execute_query(query, cache_key="teams_all")
        return result.get('data', [])

    def get_schedule(self, season: int, team: Optional[str] = None) -> List[Dict]:
        """
        Get game schedule

        Args:
            season: NHL season
            team: Optional team filter

        Returns:
            List of scheduled games
        """
        filter_query = {"season": season}

        if team:
            filter_query["$or"] = [
                {"homeTeam": team},
                {"awayTeam": team}
            ]

        query = {
            "type": "find",
            "collection": "schedule",
            "filter": filter_query,
            "fields": {
                "date": 1,
                "homeTeam": 1,
                "awayTeam": 1,
                "gameId": 1,
                "stage": 1
            }
        }

        cache_key = f"schedule_{season}_{team or 'all'}"
        result = self._execute_query(query, cache_key=cache_key)

        return result.get('data', [])


# ========== CLI USAGE EXAMPLE ==========

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Get credentials from environment
    username = os.getenv('MOREHOCKEYSTATS_USERNAME')
    password = os.getenv('MOREHOCKEYSTATS_PASSWORD')

    if not username or not password:
        print("ERROR: Set MOREHOCKEYSTATS_USERNAME and MOREHOCKEYSTATS_PASSWORD in .env")
        exit(1)

    # Initialize client
    client = MoreHockeyStatsClient(username, password)

    # Example: Get Toronto Maple Leafs empty net stats for 2023-24
    print("\\n=== Toronto Maple Leafs Empty Net Goals (2023-24) ===")
    en_goals = client.get_empty_net_goals(season=20232024, team="TOR")
    print(f"Total empty net goals involving TOR: {len(en_goals)}")

    # Example: Get all teams' empty net stats
    print("\\n=== All Teams Empty Net Stats (2023-24) ===")
    all_teams_en = client.get_team_empty_net_stats(season=20232024)
    for team, stats in sorted(all_teams_en.items(), key=lambda x: x[1]['net_rating'], reverse=True)[:10]:
        print(f"{team}: +{stats['goals_for']}/-{stats['goals_against']} (Net: {stats['net_rating']:+d})")

    # Example: Get faceoff win percentages
    print("\\n=== Faceoff Win % (2023-24) - Top 10 ===")
    faceoff_pct = client.get_team_faceoff_percentages(season=20232024)
    for team, pct in sorted(faceoff_pct.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"{team}: {pct*100:.1f}%")

    # Show total API cost
    print(f"\\n=== Total API Cost This Session: ${client.total_cost:.2f} ===")
```

---

## PHASE 2: FEATURE ENGINEERING (Day 3)

### File: `backend/ml/feature_engineering/nhl_morehockeystats_features.py`

```python
"""
NHL Feature Engineering using MoreHockeyStats.com Data

Adds advanced features not available elsewhere:
- Empty net goal rates (team offense/defense)
- Faceoff dominance by zone
- Late-game penalty frequency
"""

import pandas as pd
import numpy as np
from typing import Dict
import logging

from backend.scrapers.morehockeystats_client import MoreHockeyStatsClient

logger = logging.getLogger(__name__)


class NHLMoreHockeyStatsFeatures:
    """Enhanced NHL features from MoreHockeyStats.com"""

    def __init__(self, api_client: MoreHockeyStatsClient):
        self.client = api_client
        self._en_cache = {}  # Cache empty net stats
        self._faceoff_cache = {}  # Cache faceoff stats

    def add_empty_net_features(self, df: pd.DataFrame, season: int) -> pd.DataFrame:
        """
        Add empty net performance features

        Features added:
        - home_en_goals_for_rate: Home team's empty net goals scored per game
        - home_en_goals_against_rate: Home team's empty net goals allowed per game
        - away_en_goals_for_rate: Away team's empty net goals scored per game
        - away_en_goals_against_rate: Away team's empty net goals allowed per game
        - home_en_net_rating: Net empty net goal differential
        - away_en_net_rating: Net empty net goal differential

        Args:
            df: DataFrame with 'home_team' and 'away_team' columns
            season: NHL season (e.g., 20232024)

        Returns:
            DataFrame with new empty net features
        """
        logger.info(f"Adding empty net features for season {season}")

        # Get empty net stats (cached)
        if season not in self._en_cache:
            self._en_cache[season] = self.client.get_team_empty_net_stats(season)

        en_stats = self._en_cache[season]

        # Add features for home team
        df['home_en_goals_for'] = df['home_team'].map(lambda t: en_stats.get(t, {}).get('goals_for', 0))
        df['home_en_goals_against'] = df['home_team'].map(lambda t: en_stats.get(t, {}).get('goals_against', 0))
        df['home_en_net_rating'] = df['home_team'].map(lambda t: en_stats.get(t, {}).get('net_rating', 0))

        # Add features for away team
        df['away_en_goals_for'] = df['away_team'].map(lambda t: en_stats.get(t, {}).get('goals_for', 0))
        df['away_en_goals_against'] = df['away_team'].map(lambda t: en_stats.get(t, {}).get('goals_against', 0))
        df['away_en_net_rating'] = df['away_team'].map(lambda t: en_stats.get(t, {}).get('net_rating', 0))

        # Calculate per-game rates (assuming 82-game season)
        for col in ['home_en_goals_for', 'home_en_goals_against', 'away_en_goals_for', 'away_en_goals_against']:
            df[f'{col}_rate'] = df[col] / 82.0

        logger.info(f"Added {len([c for c in df.columns if 'en_' in c])} empty net features")

        return df

    def add_faceoff_features(self, df: pd.DataFrame, season: int) -> pd.DataFrame:
        """
        Add faceoff dominance features

        Features added:
        - home_faceoff_win_pct: Home team's overall faceoff win %
        - away_faceoff_win_pct: Away team's overall faceoff win %
        - faceoff_advantage: Difference in faceoff %

        Args:
            df: DataFrame with team columns
            season: NHL season

        Returns:
            DataFrame with faceoff features
        """
        logger.info(f"Adding faceoff features for season {season}")

        # Get faceoff stats (cached)
        if season not in self._faceoff_cache:
            self._faceoff_cache[season] = self.client.get_team_faceoff_percentages(season)

        faceoff_pct = self._faceoff_cache[season]

        # Add features
        df['home_faceoff_win_pct'] = df['home_team'].map(lambda t: faceoff_pct.get(t, 0.5))
        df['away_faceoff_win_pct'] = df['away_team'].map(lambda t: faceoff_pct.get(t, 0.5))
        df['faceoff_advantage'] = df['home_faceoff_win_pct'] - df['away_faceoff_win_pct']

        logger.info(f"Added faceoff features")

        return df

    def add_all_features(self, df: pd.DataFrame, season: int) -> pd.DataFrame:
        """
        Add all MoreHockeyStats features

        Args:
            df: Input DataFrame
            season: NHL season

        Returns:
            DataFrame with all features added
        """
        df = self.add_empty_net_features(df, season)
        df = self.add_faceoff_features(df, season)

        return df
```

---

## PHASE 3: INTEGRATION INTO ML PIPELINE (Day 4-5)

### Update: `backend/ml/data_loaders/nhl_data_loader.py`

Add MoreHockeyStats features to the data loading pipeline:

```python
def load_nhl_training_data(seasons: List[str] = None) -> pd.DataFrame:
    """Load NHL training data with all features"""

    # ... existing code to load base data ...

    # Add MoreHockeyStats features (if API access available)
    if has_morehockeystats_access():
        from backend.scrapers.morehockeystats_client import MoreHockeyStatsClient
        from backend.ml.feature_engineering.nhl_morehockeystats_features import NHLMoreHockeyStatsFeatures

        client = MoreHockeyStatsClient(
            username=os.getenv('MOREHOCKEYSTATS_USERNAME'),
            password=os.getenv('MOREHOCKEYSTATS_PASSWORD')
        )

        feature_eng = NHLMoreHockeyStatsFeatures(client)

        for season in seasons:
            season_int = int(season.replace('-', ''))  # "2023-24" -> 20232024
            df = feature_eng.add_all_features(df, season_int)

        logger.info("Added MoreHockeyStats features")

    return df
```

### Update: `backend/ml/feature_engineering/nhl_features.py`

Register new features:

```python
class NHLFeatureEngineer:
    def get_feature_names(self, market_type: str) -> List[str]:
        """Get feature names for a market type"""

        base_features = [
            # ... existing features ...
        ]

        # Add MoreHockeyStats features
        morehockeystats_features = [
            'home_en_goals_for_rate',
            'home_en_goals_against_rate',
            'home_en_net_rating',
            'away_en_goals_for_rate',
            'away_en_goals_against_rate',
            'away_en_net_rating',
            'home_faceoff_win_pct',
            'away_faceoff_win_pct',
            'faceoff_advantage'
        ]

        return base_features + morehockeystats_features
```

---

## PHASE 4: TESTING & VALIDATION (Day 6-7)

### Backtest Script: `backend/ml/backtest_morehockeystats.py`

```python
"""
Backtest NHL models with and without MoreHockeyStats features
Compare MAE, RMSE, accuracy improvements
"""

import pandas as pd
from backend.ml.training.train_nhl_models import NHLModelTrainer
from backend.ml.data_loaders.nhl_data_loader import load_nhl_training_data

# Load data WITHOUT MoreHockeyStats features
df_baseline = load_nhl_training_data(seasons=['2022-23', '2023-24'], use_morehockeystats=False)

# Load data WITH MoreHockeyStats features
df_enhanced = load_nhl_training_data(seasons=['2022-23', '2023-24'], use_morehockeystats=True)

# Train models on both datasets
trainer = NHLModelTrainer()

print("=== BASELINE (without MoreHockeyStats) ===")
baseline_meta = trainer.train_totals_models(df_baseline)

print("=== ENHANCED (with MoreHockeyStats) ===")
enhanced_meta = trainer.train_totals_models(df_enhanced)

# Compare performance
print("\\n=== PERFORMANCE COMPARISON ===")
print(f"Baseline MAE: {baseline_meta['training_stats']['xgboost']['mae']:.3f}")
print(f"Enhanced MAE: {enhanced_meta['training_stats']['xgboost']['mae']:.3f}")
print(f"Improvement: {((baseline_meta['training_stats']['xgboost']['mae'] - enhanced_meta['training_stats']['xgboost']['mae']) / baseline_meta['training_stats']['xgboost']['mae'] * 100):.2f}%")
```

### Target Metrics:
- **MAE improvement:** 2-5%
- **Late 3rd period accuracy:** 5-10% (most impact)
- **Empty net situations:** 15-20% (direct application)

---

## PHASE 5: DEPLOYMENT (Day 8)

### Environment Variables

Add to `backend/.env`:
```bash
# MoreHockeyStats.com API
MOREHOCKEYSTATS_USERNAME=your_username_here
MOREHOCKEYSTATS_PASSWORD=your_password_here
MOREHOCKEYSTATS_ENABLED=true
```

### Update Autonomous Learning

Add to `backend/ml/autonomous_learning_system.py`:

```python
# Check if MoreHockeyStats is enabled
if os.getenv('MOREHOCKEYSTATS_ENABLED', 'false').lower() == 'true':
    logger.info("MoreHockeyStats features ENABLED")
    use_morehockeystats = True
else:
    logger.info("MoreHockeyStats features DISABLED")
    use_morehockeystats = False
```

### Add to Weekly Cron

Already handled by existing autonomous learning schedule (Mondays 4am CST for NHL).

---

## COST MONITORING

### Track API Usage

Create: `backend/ml/morehockeystats_usage_tracker.py`

```python
"""Track MoreHockeyStats API usage and costs"""

import json
from pathlib import Path
from datetime import datetime

class UsageTracker:
    def __init__(self):
        self.log_file = Path(__file__).parent.parent / "logs" / "morehockeystats_usage.json"
        self.log_file.parent.mkdir(exist_ok=True)

    def log_query(self, collection: str, record_count: int, cost: float):
        """Log API query"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "collection": collection,
            "records": record_count,
            "cost": cost
        }

        # Append to log
        logs = []
        if self.log_file.exists():
            with open(self.log_file, 'r') as f:
                logs = json.load(f)

        logs.append(log_entry)

        with open(self.log_file, 'w') as f:
            json.dump(logs, f, indent=2)

    def get_monthly_cost(self) -> float:
        """Calculate current month's API costs"""
        if not self.log_file.exists():
            return 0.0

        with open(self.log_file, 'r') as f:
            logs = json.load(f)

        current_month = datetime.now().strftime('%Y-%m')
        monthly_cost = sum(
            log['cost']
            for log in logs
            if log['timestamp'].startswith(current_month)
        )

        return monthly_cost
```

### Budget Alerts

Set monthly budget: $50 (if paid), $0 (if free)

Alert if approaching limit.

---

## SUCCESS METRICS

Track in `ML_AUTONOMOUS_SYSTEM_REFERENCE.md`:

```markdown
## MoreHockeyStats Integration Results

**Integrated:** [DATE]
**Status:** Active / Trial / Disabled

### Model Performance Impact:
- Baseline NHL MAE: X.XXX
- Enhanced NHL MAE: X.XXX
- Improvement: +X.X%

### Late-Game Accuracy:
- 3rd Period predictions: +X.X% accuracy
- Empty net situations: +XX% accuracy

### API Usage:
- Monthly queries: ~X,XXX records
- Monthly cost: $XX.XX
- Collections used: GOAL, FAC, PENL

### ROI Analysis:
- Cost: $XX/month
- Accuracy gain: X%
- User value: Higher win rate on late-game bets
- ROI: Positive/Negative
```

---

## ROLLBACK PLAN

If MoreHockeyStats doesn't improve models or is too expensive:

1. Set `MOREHOCKEYSTATS_ENABLED=false` in .env
2. Models will train without these features
3. No code changes needed (graceful degradation)
4. Keep client code for future use

---

## ATTRIBUTION IMPLEMENTATION

### NHL Page Badge

Add to `frontend/src/pages/LiveGames.tsx` (NHL section):

```tsx
{sport === 'icehockey_nhl' && (
  <div className="flex items-center gap-2 text-xs text-white/60 mt-2">
    <span>Empty net data powered by</span>
    <a
      href="https://morehockeystats.com"
      target="_blank"
      rel="noopener noreferrer"
      className="text-blue-400 hover:text-blue-300 underline"
    >
      MoreHockeyStats.com
    </a>
  </div>
)}
```

### Data Sources Page

Add to `frontend/src/pages/About.tsx` or create new page:

```tsx
<div className="data-source-card">
  <h3>MoreHockeyStats.com</h3>
  <p>
    Provides unique event-level NHL data including empty net statistics,
    faceoff analysis, and penalty timing data dating back to 1999.
  </p>
  <a href="https://morehockeystats.com">Visit MoreHockeyStats.com →</a>
</div>
```

---

## TIMELINE SUMMARY

| Phase | Duration | Status |
|-------|----------|--------|
| **Email Request** | Day 0 | ⏳ Pending |
| **API Access Granted** | Day 1-7 | ⏳ Waiting |
| **Client Implementation** | Day 1-2 | 🔜 Ready to start |
| **Feature Engineering** | Day 3 | 🔜 Code templates ready |
| **ML Integration** | Day 4-5 | 🔜 Integration points identified |
| **Testing & Validation** | Day 6-7 | 🔜 Backtest scripts ready |
| **Deployment** | Day 8 | 🔜 Deployment plan complete |
| **Monitoring** | Ongoing | 🔜 Tracking systems ready |

**Total:** 8 days from API access to production deployment

---

## NEXT STEPS

1. ✅ Email template created (MOREHOCKEYSTATS_API_REQUEST.md)
2. ✅ Implementation plan documented (this file)
3. ⏳ **SEND EMAIL to contact@morehockeystats.com**
4. ⏳ Wait for API access approval
5. ⏳ Implement client (use code templates above)
6. ⏳ Test with sample queries
7. ⏳ Integrate into ML pipeline
8. ⏳ Deploy to production

---

**STATUS:** Implementation plan complete, waiting for API access approval

**CONTACT:** contact@morehockeystats.com
