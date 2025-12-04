# Alert Tracking Integration Guide

## Overview

The alert tracking system now supports **Empty Net (Goalie Pull)** and **Volatility Arbitrage** alerts. All alerts are tracked in:
- `/backend/data/alerts/tracked_alerts.json` - Active alerts
- `/backend/data/tracking/alerts_log.csv` - Complete historical log
- `/backend/data/tracking/alerts_results_log.csv` - Results and outcomes

## New Alert Endpoints

### 1. Empty Net / Goalie Pull Alerts
**Endpoint:** `GET /api/alerts/empty-net`

Returns NHL goalie pull betting opportunities currently active.

**Response Format:**
```json
{
  "count": 5,
  "alert_type": "empty_net",
  "alerts": [
    {
      "id": "uuid",
      "game_id": "game_id",
      "sport": "icehockey_nhl",
      "home_team": "Team Name",
      "away_team": "Team Name",
      "commence_time": "2025-11-16T20:00:00Z",
      "market_type": "totals",
      "recommended_side": "NNG @ +180",
      "recommended_odds": 180,
      "recommended_bookmaker": "fanduel",
      "confidence": "HIGH",
      "edge_percent": 8.5,
      "profit_potential": 25.3,
      "generated_at": "2025-11-16T19:45:00Z",
      "status": "pending",
      "strategy_details": {
        "time_remaining": "2:15",
        "score_diff": -1,
        "pull_probability": 0.87,
        "en_goal_probability": 0.42
      }
    }
  ]
}
```

### 2. Volatility Arbitrage Alerts
**Endpoint:** `GET /api/alerts/volatility-arb`

Returns volatility arbitrage hedge opportunities currently active.

**Response Format:**
```json
{
  "count": 3,
  "alert_type": "volatility_arb",
  "alerts": [
    {
      "id": "uuid",
      "game_id": "game_id",
      "sport": "basketball_nba",
      "home_team": "Team Name",
      "away_team": "Team Name",
      "commence_time": "2025-11-16T20:00:00Z",
      "market_type": "moneyline",
      "recommended_side": "Team Name @ -150",
      "recommended_odds": -150,
      "recommended_bookmaker": "draftkings",
      "confidence": "MEDIUM",
      "edge_percent": 12.3,
      "profit_potential": 45.0,
      "generated_at": "2025-11-16T19:30:00Z",
      "status": "pending",
      "strategy_details": {
        "entry_team": "Original Team",
        "entry_odds": 250,
        "hedge_trigger_met": true,
        "guaranteed_profit": 45.0,
        "position_id": "position_uuid"
      }
    }
  ]
}
```

## Integration Points

### For Goalie Pull / Empty Net Alerts

**Location:** `backend/routes/goalie_pull.py` or `backend/ml/goalie_pull/live_monitor_service.py`

**When to log:**
- When goalie pull opportunity is detected (NNG bet becomes +EV)
- When probability of goalie pull exceeds threshold

**How to log:**
```python
from storage.alert_storage import alert_storage
from utils.alert_logger import log_alert

# When goalie pull opportunity detected
alert = alert_storage.create_alert(
    alert_type='empty_net',
    game_id=game_id,
    sport='icehockey_nhl',
    home_team=home_team,
    away_team=away_team,
    commence_time=game_commence_time,
    market_type='totals',  # or 'nng' for No Next Goal
    recommended_side=f"NNG @ +{odds}",
    recommended_odds=odds,
    recommended_bookmaker=best_book,
    confidence='HIGH',  # or 'MEDIUM', 'LOW' based on probability
    edge_percent=ev_percent,
    profit_potential=expected_profit,
    strategy_details={
        'time_remaining': time_remaining_str,
        'score_diff': score_differential,
        'pull_probability': pull_prob,
        'en_goal_probability': en_goal_prob,
        'trailing_team': trailing_team
    }
)

# Also log to CSV for historical tracking
log_alert({
    'id': alert.id,
    'alert_type': 'empty_net',
    'game_id': game_id,
    'sport': 'icehockey_nhl',
    'away_team': away_team,
    'home_team': home_team,
    'market_type': 'totals',
    'recommended_side': f"NNG @ +{odds}",
    'recommended_odds': odds,
    'recommended_bookmaker': best_book,
    'confidence': 'HIGH',
    'edge_percent': ev_percent,
    'profit_potential': expected_profit,
    'generated_at': datetime.now().isoformat(),
    'timestamp': datetime.now().isoformat(),
    'status': 'pending',
    'strategy_details': {...}
})
```

### For Volatility Arbitrage Alerts

**Location:** `backend/strategies/volatility_arbitrage/detector.py` or `backend/routes/volatility_arb.py`

**When to log:**
- When hedge opportunity is detected (odds movement creates profitable hedge)
- When trigger price is reached on existing position

**How to log:**
```python
from storage.alert_storage import alert_storage
from utils.alert_logger import log_alert

# When volatility arb hedge opportunity detected
alert = alert_storage.create_alert(
    alert_type='volatility_arb',
    game_id=position.game_id,
    sport=position.sport,
    home_team=position.home_team,
    away_team=position.away_team,
    commence_time=position.game_commence_time,
    market_type='moneyline',  # or 'spreads'
    recommended_side=f"{hedge_team} @ {hedge_odds}",
    recommended_odds=hedge_odds,
    recommended_bookmaker=best_hedge_book,
    confidence='MEDIUM',
    edge_percent=None,  # Not applicable for hedge
    profit_potential=guaranteed_profit,
    strategy_details={
        'entry_team': position.entry_team,
        'entry_odds': position.entry_odds,
        'entry_stake': position.entry_stake,
        'hedge_stake': hedge_stake,
        'hedge_trigger_met': True,
        'guaranteed_profit': guaranteed_profit,
        'position_id': position.id
    }
)

# Also log to CSV
log_alert({
    'id': alert.id,
    'alert_type': 'volatility_arb',
    'game_id': position.game_id,
    'sport': position.sport,
    'away_team': position.away_team,
    'home_team': position.home_team,
    'market_type': 'moneyline',
    'recommended_side': f"{hedge_team} @ {hedge_odds}",
    'recommended_odds': hedge_odds,
    'recommended_bookmaker': best_hedge_book,
    'confidence': 'MEDIUM',
    'profit_potential': guaranteed_profit,
    'generated_at': datetime.now().isoformat(),
    'timestamp': datetime.now().isoformat(),
    'status': 'pending',
    'strategy_details': {...}
})
```

## Grading Alerts

### Empty Net Alerts
After game completes, grade using:
```python
from utils.alert_logger import log_alert_result, grade_alert

# Determine outcome
actual_result = {
    'en_goal_scored': True/False,  # Did empty net goal occur?
    'goalie_pulled': True/False,   # Was goalie actually pulled?
    'away_score': final_away_score,
    'home_score': final_home_score
}

outcome, profit, notes = grade_alert(
    alert_type='empty_net',
    recommended_side='NNG @ +180',
    recommended_odds=180,
    actual_result=actual_result,
    market_type='totals'
)

# Log result
log_alert_result(
    alert_id=alert.id,
    alert_type='empty_net',
    game_id=game_id,
    outcome=outcome,  # 'won', 'lost', or 'push'
    actual_result=actual_result,
    recommended_side='NNG @ +180',
    profit_loss=profit,
    grading_method='auto',
    notes=notes
)
```

### Volatility Arb Alerts
Grade when position is closed:
```python
# Volatility arbs always result in guaranteed profit if hedged correctly
outcome, profit, notes = ('won', guaranteed_profit, 'Volatility arb hedge executed')

log_alert_result(
    alert_id=alert.id,
    alert_type='volatility_arb',
    game_id=game_id,
    outcome='won',
    actual_result={'profit': guaranteed_profit},
    recommended_side=f"{hedge_team} @ {hedge_odds}",
    profit_loss=guaranteed_profit,
    grading_method='auto',
    notes='Hedge executed successfully'
)
```

## Next Steps

1. **Integrate goalie pull monitoring service** to call `alert_storage.create_alert()` when opportunities detected
2. **Integrate volatility arb detector** to call `alert_storage.create_alert()` when hedge triggers fire
3. **Implement automated grading** for both alert types after games complete
4. **Test endpoints** with curl or frontend to verify alerts are being tracked

## Testing

Test the new endpoints:
```bash
# Test empty net alerts
curl https://max-ev-sports.com/api/alerts/empty-net

# Test volatility arb alerts
curl https://max-ev-sports.com/api/alerts/volatility-arb

# Check all alert performance
curl https://max-ev-sports.com/api/alerts/performance
```
