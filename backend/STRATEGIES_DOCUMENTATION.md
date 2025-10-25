# Betting Strategies Documentation

## Overview
Complete documentation of all betting strategies implemented in the system, how they work, and which sports they apply to.

---

## Strategy Categories (12 Total)

### 1. **Pace-Based Analysis**
**Strategy Name**: `pace_based`
**Category**: `pace_based`
**Sports Applied**: NBA, NCAAB

**How It Works**:
- Analyzes team pace ratings (possessions per game)
- Calculates expected possessions using geometric mean of both teams' pace
- Factors in offensive and defensive efficiency ratings
- Adjusts for rest days and back-to-back games
- Predicts game totals based on pace × efficiency

**Key Metrics**:
- Team pace ratings
- Offensive rating (points per 100 possessions)
- Defensive rating (points allowed per 100 possessions)
- Home court advantage (+2.5 points for NBA)
- Rest day adjustments

**Confidence Levels**:
- HIGH: 5.0+ point edge
- MEDIUM: 3.0-4.9 point edge
- LOW: 2.0-2.9 point edge

**Implementation**: `backend/models/nba/totals_predictor.py`

---

### 2. **Fatigue Model**
**Strategy Name**: `fatigue`
**Category**: `fatigue`
**Sports Applied**: NBA, NHL, NFL

**How It Works**:
- Tracks rest days between games
- Identifies back-to-back situations
- Analyzes travel distance and time zones crossed
- Measures games played in last 7 days
- Predicts performance degradation due to fatigue

**Key Factors**:
- **Back-to-back games**: -2.0 pace adjustment (NBA)
- **Both teams rested (2+ days)**: +1.0 pace boost
- **One team fresh (3+ days)**: +1.5 pace advantage
- **Miles traveled**: Impacts away team performance
- **Time zones**: West coast teams traveling east

**Edge Detection**:
- Significant rest advantage (3+ day differential)
- Back-to-back vs rested opponent
- Cross-country travel with time zone changes

**Implementation**: Integrated into ensemble model

---

### 3. **Regression Analysis**
**Strategy Name**: `regression`
**Category**: `regression`
**Sports Applied**: NBA, MLB, NFL

**How It Works**:
- Compares recent performance (last 5 games) to season averages
- Identifies teams performing above/below their mean
- Predicts reversion to the mean
- Targets overvalued/undervalued lines based on recent variance

**Statistical Approach**:
- Calculate variance from season average for:
  - Points per game (PPG)
  - Points allowed per game (PAPG)
  - Field goal percentage
  - Three-point percentage
- Weight recent games vs season baseline
- Project return to normal performance levels

**Best Opportunities**:
- Team on hot streak with inflated totals
- Team in cold streak with deflated totals
- Market overreacting to small sample sizes

**Implementation**: `backend/models/ensemble/betting_ensemble.py`

---

### 4. **Multi-Sport Ensemble**
**Strategy Name**: `multi_sport_ensemble`
**Category**: `multi_sport_ensemble`
**Sports Applied**: NBA, NHL, NFL, MLB

**How It Works**:
- Combines pace, fatigue, and regression strategies
- Weighted ensemble approach (default: 40% pace, 30% fatigue, 30% regression)
- Each strategy generates independent prediction
- Weighted average produces final recommendation
- Confidence based on strategy agreement

**Ensemble Weighting**:
```python
predicted_total = (
    pace_prediction * 0.40 +
    fatigue_prediction * 0.30 +
    regression_prediction * 0.30
)
```

**Confidence Calculation**:
- HIGH: All 3 strategies agree (within 2 points)
- MEDIUM: 2 of 3 strategies agree
- LOW: Strategies disagree significantly

**Expected Value (EV)**:
- Calculates true probability vs market odds
- Factors in confidence level
- Recommends Kelly Criterion bet sizing

**Implementation**: `backend/models/ensemble/betting_ensemble.py`

---

### 5. **Moneyline Value**
**Strategy Name**: `moneyline`
**Category**: `moneyline`
**Sports Applied**: NBA, NHL, NFL, MLB

**How It Works**:
- Converts spread predictions to win probability
- Compares to implied probability from moneyline odds
- Identifies mispriced moneylines
- Targets underdogs with value

**Probability Calculation**:
- Use pace/efficiency to predict point differential
- Convert point spread to win probability
- Compare to market ML odds implied probability

**Edge Detection**:
- Our probability > market probability by 5%+
- Underdog situations with inflated favorite lines
- Home underdogs with rest advantage

**Best Spots**:
- Close games with overpriced favorites
- Home underdogs off a loss
- Teams undervalued due to recent performance

---

### 6. **Live Betting**
**Strategy Name**: `live_betting`
**Category**: `live_betting`
**Sports Applied**: NBA, NFL

**How It Works**:
- Tracks in-game momentum shifts
- Monitors live odds movement
- Identifies middle opportunities
- Capitalizes on overreactions to game flow

**Real-Time Factors**:
- Current score vs expected score
- Pace of play (faster/slower than predicted)
- Momentum indicators (runs, scoring droughts)
- Live line vs pregame line differential

**Opportunity Types**:
- **Middles**: Bet opposite side when line moves significantly
- **Hedges**: Lock in profit on pregame bets
- **Value**: Market overreacting to temporary game state

**Implementation**: `backend/scrapers/nba/backend/live_analytics_engine.py`

---

### 7. **Arbitrage**
**Strategy Name**: `arbitrage`
**Category**: `arbitrage`
**Sports Applied**: All sports (NBA, NHL, NFL, MLB, NCAAB, NCAAF)

**How It Works**:
- Scans multiple bookmakers simultaneously
- Identifies price discrepancies
- Calculates risk-free profit opportunities
- Monitors line movements across books

**Arbitrage Detection**:
```python
# Example: Total arbitrage
prob_over = american_to_prob(best_over_odds)
prob_under = american_to_prob(best_under_odds)

if (prob_over + prob_under) < 1.0:
    # Arbitrage exists!
    profit = 1.0 - (prob_over + prob_under)
```

**Minimum Thresholds**:
- Profit: 0.5%+ (after accounting for transaction costs)
- Window: Must be executable within 30 seconds
- Books: Requires accounts at 4+ sportsbooks

**Alert Triggers**:
- New arbitrage opportunities (real-time)
- Expiring arbitrage (line about to move)
- Book limits/restrictions

**Implementation**: `backend/scrapers/nba/backend/alert_monitor.py`

---

### 8. **Steam Moves**
**Strategy Name**: `steam_move`
**Category**: `steam_move`
**Sports Applied**: All sports

**How It Works**:
- Detects sudden, significant line movements
- Identifies sharp money (professional bettors)
- Tracks consensus across multiple bookmakers
- Follows the "smart money"

**Detection Criteria**:
- Line moves 1.5+ points (totals) or 1.0+ points (spreads) within 10 minutes
- Movement in same direction across 3+ major books
- No obvious news to explain movement
- Occurs close to game time

**Confidence Indicators**:
- **Strong Steam**: 5+ books move within 5 minutes
- **Medium Steam**: 3-4 books move within 10 minutes
- **Weak Steam**: 2 books move, others following

**Follow Strategy**:
- Bet the side sharp money is hitting
- Enter at best available price quickly
- Target 2-3% edge before line settles

**Implementation**: `backend/scrapers/nba/backend/alert_monitor.py`

---

### 9. **Line Movement**
**Strategy Name**: `line_movement`
**Category**: `line_movement`
**Sports Applied**: All sports

**How It Works**:
- Tracks line history from opening to current
- Identifies reverse line movement (RLM)
- Detects professional vs public betting patterns
- Monitors line freezes and rapid shifts

**Movement Types**:
1. **Standard Movement**: Line moves with public betting percentage
2. **Reverse Line Movement (RLM)**: Line moves opposite to public betting
   - Indicates sharp action
   - 70% public on one side, line moves other way
3. **Steam Move**: Rapid coordinated movement (see above)
4. **Line Freeze**: Line stops moving despite heavy action on one side

**RLM Strategy**:
- Public: 65%+ on one side
- Line: Moves toward other side
- Action: Bet with the line movement (sharps)

**Thresholds**:
- Significant: 1.0+ point movement
- Major: 2.0+ point movement
- Extreme: 3.0+ point movement

**Implementation**: `backend/scrapers/nba/backend/alert_monitor.py`

---

### 10. **Sharp Action**
**Strategy Name**: `sharp_action`
**Category**: `sharp_action`
**Sports Applied**: All sports

**How It Works**:
- Identifies betting patterns of professional bettors
- Tracks accounts known to be sharp players
- Monitors respected bookmakers (Pinnacle, Circa)
- Detects limit increases and book responses

**Sharp Indicators**:
- Line originates from sharp books (Pinnacle, Circa)
- Other books follow within minutes
- Large bets at opening lines
- Books lower limits on specific sides

**Detection Methods**:
- **Pinnacle Tracking**: Monitor Pinnacle for line origination
- **Limit Tracking**: Books reducing max bet amounts
- **Timing**: Bets placed immediately at opening
- **Correlation**: Multiple sharp indicators align

**Follow Criteria**:
- Pinnacle line moves first
- 3+ books follow within 5 minutes
- Movement of 1+ point
- No public news to explain

---

### 11. **Public Fade**
**Strategy Name**: `public_fade`
**Category**: `public_fade`
**Sports Applied**: NFL, NBA, MLB

**How It Works**:
- Tracks public betting percentages
- Identifies heavily bet sides (70%+ public)
- Bets against the public in specific situations
- Targets overvalued public favorites

**Fade Situations**:
1. **Heavy Public Favorite** (75%+ public, line not moving)
2. **Primetime Games** (more casual bettor action)
3. **Popular Teams** (Lakers, Cowboys, Yankees)
4. **Playoff Games** (public emotional betting)

**Optimal Conditions**:
- 70%+ public on one side
- Line moving TOWARD the public side (reverse of sharp money)
- Large spread/total (public loves favorites and overs)
- National TV game

**Caution**:
- Public sometimes right (don't blindly fade)
- Combine with other signals (RLM, sharp action)
- Best in specific contexts (primetime, playoffs)

---

### 12. **Weather Impact**
**Strategy Name**: `weather_impact`
**Category**: `weather_impact`
**Sports Applied**: NFL, MLB (outdoor games only)

**How It Works**:
- Analyzes weather forecasts for outdoor games
- Adjusts totals for wind, precipitation, temperature
- Identifies games where weather significantly impacts scoring
- Targets markets that haven't adjusted for conditions

**Key Weather Factors**:

**NFL**:
- **Wind**: >15 MPH = -3 to -7 points on total
- **Rain**: Heavy rain = -5 to -10 points (passing game impact)
- **Snow**: Heavy snow = -7 to -14 points
- **Cold**: <20°F = -3 to -5 points
- **Dome advantage**: Increases for weather-impacted outdoor teams

**MLB**:
- **Wind direction**: In from CF = under, Out to CF = over
- **Temperature**: >80°F = ball carries further (over)
- **Humidity**: High humidity = ball doesn't carry (under)
- **Rain delays**: Impacts starting pitchers, bullpen usage

**Edge Calculation**:
- Compare predicted weather impact to market adjustment
- Books often slow to adjust totals for late weather changes
- Best value 2-3 hours before game when forecast updates

---

## Strategy Application by Sport

### NBA
**Primary Strategies**:
1. Pace-Based (40% weight)
2. Fatigue (30% weight)
3. Regression (30% weight)
4. Multi-Sport Ensemble (combines above)
5. Moneyline Value
6. Live Betting

**Secondary Strategies**:
- Arbitrage (opportunistic)
- Steam Moves (follow sharp action)
- Line Movement (track RLM)
- Sharp Action (Pinnacle tracking)
- Public Fade (primetime games, popular teams)

---

### NHL
**Primary Strategies**:
1. Regression (recent goalie performance)
2. Fatigue (back-to-backs very impactful)
3. Multi-Sport Ensemble
4. Moneyline Value

**Secondary Strategies**:
- Arbitrage
- Steam Moves
- Line Movement
- Sharp Action

**NHL-Specific Factors**:
- Goalie matchups (starting goalie critical)
- Home ice advantage
- Division games (lower totals)
- Rest advantage (back-to-backs common)

---

### NFL
**Primary Strategies**:
1. Weather Impact (outdoor games)
2. Fatigue (short weeks, TNF, MNF)
3. Regression
4. Multi-Sport Ensemble
5. Live Betting

**Secondary Strategies**:
- Public Fade (most effective in NFL)
- Sharp Action
- Line Movement (very significant in NFL)
- Moneyline Value

**NFL-Specific Factors**:
- Weather (most impactful sport)
- Key numbers (3, 7, 10, 14)
- Division games (lower scoring)
- Playoff experience

---

### MLB
**Primary Strategies**:
1. Regression (pitcher performance, recent batting)
2. Weather Impact (wind, temperature)
3. Moneyline Value (F5 innings)
4. Multi-Sport Ensemble

**Secondary Strategies**:
- Arbitrage
- Steam Moves
- Sharp Action
- Line Movement

**MLB-Specific Factors**:
- Starting pitcher matchup
- Bullpen quality and usage
- Park factors (Coors Field vs pitcher parks)
- Day vs night games
- Series position (game 1 vs 3)

---

### NCAAB (College Basketball)
**Primary Strategies**:
1. Pace-Based (college pace varies widely)
2. Regression
3. Multi-Sport Ensemble

**Secondary Strategies**:
- Arbitrage
- Line Movement
- Public Fade (tournament games)

**NCAAB-Specific Factors**:
- Conference strength
- Home court advantage (louder crowds)
- Tournament experience
- KenPom efficiency ratings

---

### NCAAF (College Football)
**Primary Strategies**:
1. Weather Impact
2. Public Fade (popular teams heavily bet)
3. Regression

**Secondary Strategies**:
- Arbitrage
- Line Movement
- Sharp Action

**NCAAF-Specific Factors**:
- Talent disparities (larger than NFL)
- Motivation (bowl games, rivalry games)
- Conference championships
- Public bias toward top 25 teams

---

## Implementation Checklist

### To Start Logging Plays Automatically:

**1. In your NBA prediction script** (`run_daily_predictions.py`):
```python
from backend.scrapers.nba.backend.auto_play_logger import log_nba_prediction

# After generating predictions
for prediction in predictions:
    if prediction['confidence'] in ['HIGH', 'MEDIUM']:
        play_id = log_nba_prediction(prediction, bookmaker_data)
        if play_id:
            print(f"Logged play: {play_id}")
```

**2. For recording results** (after games complete):
```python
from backend.scrapers.nba.backend.auto_play_logger import record_nba_result

# After fetching game scores
for game in completed_games:
    if game['play_id']:
        success = record_nba_result(game['play_id'], game_result_data)
```

**3. Bookmaker line tracking**:
- The `auto_play_logger` automatically finds the best line across all books
- Records: bookmaker name, exact odds, line value at time of bet
- Stores alternate books for comparison
- Tracks line movement from recommendation to close

---

## Database Schema

Every logged play captures:
- **Game Info**: sport, teams, game time, game ID
- **Strategy**: strategy name, category, confidence level
- **Recommendation**: play type, side, line, price
- **Bookmaker**: best book, price at recommendation, alternates
- **Edge Calculation**: our probability, market probability, edge %, EV
- **Context**: momentum indicator, trend data, notes
- **Timestamp**: exact time of recommendation

Every result captures:
- **Outcome**: won/lost/push
- **Final Score**: home score, away score, total
- **Line Tracking**: opening line, closing line, line movement
- **Profitability**: profit/loss in units, ROI percentage
- **Verification**: verified status, timestamp

---

## Next Steps

1. **Integration**: Add auto-logging to your existing prediction scripts
2. **Testing**: Run a few predictions to verify logging works
3. **Monitoring**: Check Multi-Sport page to see performance data populate
4. **Refinement**: Adjust strategy weights based on historical performance

All data persists across server restarts in SQLite database!
