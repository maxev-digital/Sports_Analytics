# Max EV Boost API Documentation

## Overview

The Max EV Boost API provides endpoints for analyzing NBA and NCAAB games using XGBoost-powered regression-to-mean detection. The system identifies when live betting lines deviate significantly from predicted values, creating +EV betting opportunities.

---

## 📊 System Performance

### NBA Max EV Boost
- **Win Rate**: 66.3%
- **ROI**: +26.5%
- **Backtest Data**: 163 alerts across 3,690 games
- **Model**: 49 features, XGBoost quantile regression

### NCAAB Max EV Boost
- **Win Rate**: 60.0%
- **ROI**: +14.5%
- **Backtest Data**: 30 alerts across 675 games
- **Model**: 8 KenPom features, XGBoost quantile regression

---

## 🚀 API Endpoints

### Base URL
```
http://localhost:8000/api/max-ev-boost
```

---

### 1. NBA Game Analysis

**Endpoint**: `POST /api/max-ev-boost/nba/analyze`

**Description**: Analyze a single NBA game for regression opportunities

**Request Body**:
```json
{
  "game_id": "nba_20250108_LAL_BOS",
  "home_team": "Los Angeles Lakers",
  "away_team": "Boston Celtics",
  "home_stats": {
    "games_played": 35,
    "wins": 22,
    "win_pct": 0.629,
    "ppg": 118.5,
    "opp_ppg": 112.3,
    "point_diff": 6.2,
    "fg_pct": 0.478,
    "fg3_pct": 0.371,
    "ft_pct": 0.812,
    "rebounds": 45.2,
    "assists": 26.8,
    "turnovers": 13.5,
    "steals": 8.2,
    "blocks": 5.1,
    "plus_minus": 6.2,
    "last_5_ppg": 121.2,
    "last_10_ppg": 119.8,
    "last_5_wins": 4,
    "last_10_wins": 7
  },
  "away_stats": {
    "games_played": 36,
    "wins": 25,
    "win_pct": 0.694,
    "ppg": 122.1,
    "opp_ppg": 110.5,
    "point_diff": 11.6,
    "fg_pct": 0.492,
    "fg3_pct": 0.385,
    "ft_pct": 0.825,
    "rebounds": 47.3,
    "assists": 28.2,
    "turnovers": 12.8,
    "steals": 7.9,
    "blocks": 6.3,
    "plus_minus": 11.6,
    "last_5_ppg": 125.4,
    "last_10_ppg": 123.2,
    "last_5_wins": 5,
    "last_10_wins": 8
  },
  "live_total": 235.5
}
```

**Response**:
```json
{
  "status": "success",
  "game_id": "nba_20250108_LAL_BOS",
  "home_team": "Los Angeles Lakers",
  "away_team": "Boston Celtics",
  "predicted_mean": 238.5,
  "predicted_lower": 213.5,
  "predicted_upper": 249.9,
  "std_dev": 14.23,
  "live_total": 235.5,
  "z_score": -0.21,
  "is_alert": false,
  "alert_type": null,
  "confidence": "LOW",
  "recommended_bet": null,
  "kelly_pct": 0.0
}
```

---

### 2. NCAAB Game Analysis

**Endpoint**: `POST /api/max-ev-boost/ncaab/analyze`

**Description**: Analyze a single NCAAB game for regression opportunities

**Request Body**:
```json
{
  "game_id": "ncaab_20250108_DUKE_UNC",
  "home_team": "Duke",
  "away_team": "North Carolina",
  "home_stats": {
    "adj_em": 28.5,
    "off_eff": 118.2,
    "def_eff": 89.7,
    "tempo": 70.5
  },
  "away_stats": {
    "adj_em": 25.3,
    "off_eff": 115.8,
    "def_eff": 90.5,
    "tempo": 68.2
  },
  "live_total": 160.5
}
```

**Response**:
```json
{
  "status": "success",
  "game_id": "ncaab_20250108_DUKE_UNC",
  "home_team": "Duke",
  "away_team": "North Carolina",
  "predicted_mean": 160.7,
  "predicted_lower": 150.8,
  "predicted_upper": 164.8,
  "std_dev": 5.49,
  "live_total": 160.5,
  "z_score": -0.03,
  "is_alert": false,
  "alert_type": null,
  "confidence": "LOW",
  "recommended_bet": null,
  "kelly_pct": 0.0
}
```

---

### 3. Batch Analysis (NBA)

**Endpoint**: `POST /api/max-ev-boost/nba/analyze-batch`

**Description**: Analyze multiple NBA games simultaneously

**Request Body**: Array of NBA game requests (same format as single analysis)

**Response**: Array of analysis results

---

### 4. Batch Analysis (NCAAB)

**Endpoint**: `POST /api/max-ev-boost/ncaab/analyze-batch`

**Description**: Analyze multiple NCAAB games simultaneously

**Request Body**: Array of NCAAB game requests (same format as single analysis)

**Response**: Array of analysis results

---

### 5. System Status

**Endpoint**: `GET /api/max-ev-boost/status`

**Description**: Check health and performance of Max EV Boost systems

**Response**:
```json
{
  "nba": {
    "status": "operational",
    "models_loaded": true,
    "performance": {
      "win_rate": 66.3,
      "roi": 26.5,
      "backtest_alerts": 163,
      "backtest_games": 3690
    }
  },
  "ncaab": {
    "status": "operational",
    "models_loaded": true,
    "performance": {
      "win_rate": 60.0,
      "roi": 14.5,
      "backtest_alerts": 30,
      "backtest_games": 675
    }
  }
}
```

---

## 🎯 Response Fields Explained

### Predictions
- `predicted_mean`: Expected total points (50th percentile)
- `predicted_lower`: Lower bound (10th percentile)
- `predicted_upper`: Upper bound (90th percentile)
- `std_dev`: Standard deviation of prediction

### Alert Information
- `z_score`: Standard deviations from prediction (positive = line too high, negative = line too low)
- `is_alert`: True if |z_score| >= 2.0 (bet recommended)
- `alert_type`: "OVER" or "UNDER" (only if alert triggered)
- `confidence`:
  - "EXTREME": |z_score| >= 2.5 (highest edge)
  - "STRONG": 2.0 <= |z_score| < 2.5
  - "MODERATE": 1.5 <= |z_score| < 2.0
  - "LOW": |z_score| < 1.5 (no bet)

### Betting Recommendation
- `recommended_bet`: "OVER" or "UNDER" (only if alert)
- `kelly_pct`: Recommended bet size as % of bankroll (3-5% for alerts)

---

## 📈 Alert Trigger Logic

### When Does an Alert Fire?

**Condition**: `|z_score| >= 2.0`

**What It Means**:
- Live betting line has drifted **2+ standard deviations** from our prediction
- Statistical anomaly - line is likely mispriced
- Regression to mean is expected

**Example**:
```
Predicted Mean: 220 points
Std Dev: 10 points
Live Total: 242 points

Z-Score = (242 - 220) / 10 = +2.2 SD
Alert: UNDER (live line too high, bet under)
Confidence: STRONG
Kelly %: 4.2%
```

---

## 💰 Kelly Criterion Bet Sizing

The API automatically calculates optimal bet size using Quarter Kelly:

### Win Probabilities (Historical)
- **EXTREME** (2.5+ SD): 68% win rate → 4-5% Kelly
- **STRONG** (2.0-2.49 SD): 62% win rate → 3-4% Kelly
- **MODERATE** (1.5-1.99 SD): 55% win rate → 2-3% Kelly

### Example
```json
{
  "confidence": "STRONG",
  "kelly_pct": 3.8,
  "recommended_bet": "UNDER"
}
```

**Interpretation**: Bet 3.8% of your bankroll on UNDER

**Bankroll Example**:
- $10,000 bankroll → Bet $380
- $5,000 bankroll → Bet $190
- $1,000 bankroll → Bet $38

---

## 🔧 Integration Examples

### Python

```python
import requests

# Analyze NBA game
response = requests.post('http://localhost:8000/api/max-ev-boost/nba/analyze', json={
    "game_id": "nba_001",
    "home_team": "Lakers",
    "away_team": "Celtics",
    "home_stats": {...},
    "away_stats": {...},
    "live_total": 235.5
})

result = response.json()

if result['is_alert']:
    print(f"ALERT: Bet {result['recommended_bet']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Kelly Size: {result['kelly_pct']}%")
    print(f"Z-Score: {result['z_score']}")
```

### JavaScript/TypeScript

```typescript
const analyzeGame = async (gameData) => {
  const response = await fetch('http://localhost:8000/api/max-ev-boost/nba/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(gameData)
  });

  const result = await response.json();

  if (result.is_alert) {
    console.log(`ALERT: Bet ${result.recommended_bet}`);
    console.log(`Confidence: ${result.confidence}`);
    console.log(`Kelly: ${result.kelly_pct}%`);
  }
};
```

### cURL

```bash
curl -X POST http://localhost:8000/api/max-ev-boost/nba/analyze \
  -H "Content-Type: application/json" \
  -d @nba_game_data.json
```

---

## ⚡ Performance Optimization

### Model Loading
- Models are lazy-loaded on first request
- Singleton pattern ensures models loaded only once
- Subsequent requests reuse loaded models (fast)

### Batch Processing
- Use `/analyze-batch` endpoints for scanning multiple games
- More efficient than individual requests
- Shared model loading overhead

---

## 🚨 Error Handling

### Common Errors

**Model Not Found**:
```json
{
  "status": "error",
  "detail": "NBA analysis failed: 'lower'"
}
```
**Solution**: Ensure model files exist in `backend/ml/models/`

**Missing Required Fields**:
```json
{
  "detail": [
    {
      "loc": ["body", "home_stats", "ppg"],
      "msg": "field required"
    }
  ]
}
```
**Solution**: Check request body matches required schema

---

## 📁 File Locations

### API Routes
- `backend/routes/max_ev_boost.py` - FastAPI endpoints

### Analyzers
- `backend/ml/nba_regression_analyzer.py` - NBA analyzer
- `backend/ml/ncaab_regression_analyzer.py` - NCAAB analyzer

### Models
- `backend/ml/models/nba_quantile_lower_latest.json`
- `backend/ml/models/nba_quantile_mean_latest.json`
- `backend/ml/models/nba_quantile_upper_latest.json`
- `backend/ml/models/ncaab_quantile_lower_latest.json`
- `backend/ml/models/ncaab_quantile_mean_latest.json`
- `backend/ml/models/ncaab_quantile_upper_latest.json`

### Tests
- `backend/test_max_ev_boost_api.py` - Automated test suite

---

## 🎓 How It Works

### 1. Data Collection
- Collect NBA/NCAAB team statistics
- Fetch current live betting total

### 2. Prediction
- XGBoost models predict game total using team stats
- Generate 10th, 50th, 90th percentile predictions
- Calculate standard deviation

### 3. Z-Score Calculation
```
z_score = (live_total - predicted_mean) / std_dev
```

### 4. Alert Decision
- If `|z_score| >= 2.0`: **ALERT**
- Recommend bet direction opposite of deviation
  - Positive z-score (line too high) → Bet UNDER
  - Negative z-score (line too low) → Bet OVER

### 5. Kelly Sizing
- Use historical win rates at each confidence level
- Apply Quarter Kelly for safety
- Cap at 5% maximum

---

## 🔐 Security Notes

- API runs locally (localhost:8000)
- No authentication required for local development
- Add auth middleware before deploying to production

---

## 📞 Support

- **Issues**: Report bugs in test suite output
- **Models**: Retrain models using training scripts in `backend/ml/`
- **Performance**: Monitor backtest results in `backend/data/backtesting/`

---

**Last Updated**: 2025-11-08
**API Version**: 1.0
**Status**: Production Ready ✅
