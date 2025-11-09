# Monte Carlo Simulation API Documentation

**For C2 (Frontend) Integration**

---

## Endpoint

```
POST /api/simulation/monte-carlo
```

**Base URL**: `http://localhost:8000` (development) or your production URL

---

## Overview

This endpoint runs a **possession-by-possession Monte Carlo simulation** for live NBA games. It takes the current game state (quarter, time remaining, score) and simulates the remaining possessions to generate a probability distribution of final totals.

**Use Cases**:
- Real-time betting decision support during live games
- Visualizing probability distributions for users
- Identifying +EV opportunities with Kelly Criterion sizing
- Live game analytics and predictions

---

## Request Format

### Headers
```
Content-Type: application/json
```

### Request Body

```json
{
  "game_id": "nba_20251108_LAL_BOS",
  "current_state": {
    "quarter": 3,
    "time_remaining": "4:32",
    "home_score": 82,
    "away_score": 78
  },
  "home_stats": {
    "pace": 100.5,
    "off_rating": 118.2,
    "def_rating": 110.5
  },
  "away_stats": {
    "pace": 98.3,
    "off_rating": 115.8,
    "def_rating": 108.9
  },
  "market_total": 235.5,
  "n_simulations": 10000
}
```

### Request Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `game_id` | string | Yes | Unique game identifier |
| `current_state` | object | Yes | Current game state |
| `current_state.quarter` | integer (1-4) | Yes | Current quarter |
| `current_state.time_remaining` | string | Yes | Time remaining in quarter (MM:SS format) |
| `current_state.home_score` | integer | Yes | Current home team score |
| `current_state.away_score` | integer | Yes | Current away team score |
| `home_stats` | object | Yes | Home team statistics |
| `home_stats.pace` | float | Yes | Possessions per 48 minutes |
| `home_stats.off_rating` | float | Yes | Offensive rating (points per 100 possessions) |
| `home_stats.def_rating` | float | Yes | Defensive rating (points allowed per 100 possessions) |
| `away_stats` | object | Yes | Away team statistics |
| `away_stats.pace` | float | Yes | Possessions per 48 minutes |
| `away_stats.off_rating` | float | Yes | Offensive rating (points per 100 possessions) |
| `away_stats.def_rating` | float | Yes | Defensive rating (points allowed per 100 possessions) |
| `market_total` | float | Yes | Current betting market total line |
| `n_simulations` | integer | No | Number of simulations (default: 10000, min: 1000, max: 50000) |

---

## Response Format

### Success Response (200 OK)

```json
{
  "status": "success",
  "game_id": "nba_20251108_LAL_BOS",
  "over_probability": 0.0012,
  "under_probability": 0.9988,
  "push_probability": 0.0000,
  "over_ev": -0.9989,
  "under_ev": 0.9079,
  "recommended_bet": "UNDER",
  "edge": 0.9079,
  "kelly_pct": 5.00,
  "percentiles": {
    "5th": 192.9,
    "10th": 194.4,
    "25th": 196.9,
    "50th": 199.6,
    "75th": 202.3,
    "90th": 204.8,
    "95th": 206.2
  },
  "mean": 199.6,
  "median": 199.6,
  "std_dev": 4.04,
  "min": 187.2,
  "max": 212.8,
  "metadata": {
    "current_total": 160,
    "remaining_minutes": 16.53,
    "estimated_remaining_possessions": 34.2,
    "n_simulations": 10000
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | "success" or "error" |
| `game_id` | string | Echoed from request |
| `over_probability` | float | Probability the final total will be OVER the market line (0-1) |
| `under_probability` | float | Probability the final total will be UNDER the market line (0-1) |
| `push_probability` | float | Probability of a push (0-1, usually ~0) |
| `over_ev` | float | Expected value for betting OVER (-1 to +1 units) |
| `under_ev` | float | Expected value for betting UNDER (-1 to +1 units) |
| `recommended_bet` | string or null | "OVER", "UNDER", or null (no edge) |
| `edge` | float | Absolute edge in units (0 to 1+) |
| `kelly_pct` | float | Recommended bet size as % of bankroll (0-5%) |
| `percentiles` | object | Distribution percentiles (5th through 95th) |
| `mean` | float | Mean simulated final total |
| `median` | float | Median simulated final total |
| `std_dev` | float | Standard deviation of simulations |
| `min` | float | Minimum simulated total |
| `max` | float | Maximum simulated total |
| `metadata` | object | Additional context information |
| `metadata.current_total` | integer | Current combined score |
| `metadata.remaining_minutes` | float | Minutes remaining in regulation |
| `metadata.estimated_remaining_possessions` | float | Estimated possessions remaining |
| `metadata.n_simulations` | integer | Number of simulations run |

---

## Error Responses

### 400 Bad Request
Invalid input parameters (e.g., quarter not 1-4, negative scores, etc.)

```json
{
  "detail": "Invalid input: quarter must be between 1 and 4"
}
```

### 500 Internal Server Error
Simulation error (rare, usually indicates a bug)

```json
{
  "detail": "Simulation error: <error message>"
}
```

---

## Example Usage

### JavaScript / TypeScript (React)

```typescript
interface MonteCarloRequest {
  game_id: string;
  current_state: {
    quarter: number;
    time_remaining: string;
    home_score: number;
    away_score: number;
  };
  home_stats: {
    pace: number;
    off_rating: number;
    def_rating: number;
  };
  away_stats: {
    pace: number;
    off_rating: number;
    def_rating: number;
  };
  market_total: number;
  n_simulations?: number;
}

interface MonteCarloResponse {
  status: string;
  game_id: string;
  over_probability: number;
  under_probability: number;
  push_probability: number;
  over_ev: number;
  under_ev: number;
  recommended_bet: string | null;
  edge: number;
  kelly_pct: number;
  percentiles: {
    "5th": number;
    "10th": number;
    "25th": number;
    "50th": number;
    "75th": number;
    "90th": number;
    "95th": number;
  };
  mean: number;
  median: number;
  std_dev: number;
  min: number;
  max: number;
  metadata: {
    current_total: number;
    remaining_minutes: number;
    estimated_remaining_possessions: number;
    n_simulations: number;
  };
}

async function runMonteCarloSimulation(
  request: MonteCarloRequest
): Promise<MonteCarloResponse> {
  const response = await fetch('http://localhost:8000/api/simulation/monte-carlo', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Simulation failed');
  }

  return response.json();
}

// Example usage
const result = await runMonteCarloSimulation({
  game_id: 'nba_20251108_LAL_BOS',
  current_state: {
    quarter: 3,
    time_remaining: '4:32',
    home_score: 82,
    away_score: 78,
  },
  home_stats: {
    pace: 100.5,
    off_rating: 118.2,
    def_rating: 110.5,
  },
  away_stats: {
    pace: 98.3,
    off_rating: 115.8,
    def_rating: 108.9,
  },
  market_total: 235.5,
  n_simulations: 10000,
});

console.log('Recommended bet:', result.recommended_bet);
console.log('Edge:', result.edge);
console.log('Kelly %:', result.kelly_pct);
```

### cURL (for testing)

```bash
curl -X POST "http://localhost:8000/api/simulation/monte-carlo" \
  -H "Content-Type: application/json" \
  -d '{
    "game_id": "nba_20251108_LAL_BOS",
    "current_state": {
      "quarter": 3,
      "time_remaining": "4:32",
      "home_score": 82,
      "away_score": 78
    },
    "home_stats": {
      "pace": 100.5,
      "off_rating": 118.2,
      "def_rating": 110.5
    },
    "away_stats": {
      "pace": 98.3,
      "off_rating": 115.8,
      "def_rating": 108.9
    },
    "market_total": 235.5,
    "n_simulations": 10000
  }'
```

---

## Integration Notes for C2

### Data Sources

You'll need to provide the following data to the simulation endpoint:

1. **Current Game State**: Get from live scoreboard API
   - Quarter, time remaining, current scores

2. **Team Stats (Pace & Efficiency)**: You have several options:
   - **Option A**: Use existing `/api/games` endpoint - it already includes pace and ratings for live games
   - **Option B**: Fetch from a dedicated team stats endpoint if available
   - **Option C**: Pre-compute season averages and store in frontend state

3. **Market Total**: Get from odds feed (already available in your odds data)

### Recommended Frontend Flow

```
1. User clicks "Simulate Game" button on a live game card
2. Frontend gathers:
   - Game state from live scoreboard
   - Team stats from games endpoint or cached data
   - Market total from odds feed
3. POST to /api/simulation/monte-carlo
4. Display results:
   - Probability chart/graph
   - Recommended bet with confidence
   - Kelly sizing suggestion
   - Expected value
```

### Performance Considerations

- **Simulation Time**: ~500-1000ms for 10,000 simulations
- **Caching**: Consider caching results for 30-60 seconds to avoid excessive API calls
- **UI/UX**: Show loading spinner while simulation runs
- **Debouncing**: If user can adjust parameters, debounce API calls

### Visual Components to Build

1. **Probability Distribution Chart**:
   - Use percentiles to draw bell curve
   - Highlight market line on chart
   - Show Over/Under probabilities

2. **Betting Recommendation Card**:
   - Show recommended bet (OVER/UNDER)
   - Display edge and expected value
   - Show Kelly % sizing suggestion

3. **Metadata Display**:
   - Current total
   - Remaining time/possessions
   - Simulated range (min/max)

---

## Health Check Endpoint

For monitoring/debugging:

```
GET /api/simulation/health
```

Response:
```json
{
  "status": "healthy",
  "service": "Monte Carlo Simulation",
  "version": "1.0.0"
}
```

---

## Technical Details

### How It Works

1. **Possession Calculation**: Estimates remaining possessions based on:
   - Time remaining in current quarter
   - Quarters remaining
   - Team pace averages

2. **Possession Simulation**: For each simulation:
   - Randomly determines number of possessions (with variance)
   - Simulates each possession individually
   - Alternates between home and away teams
   - Applies offensive/defensive ratings with variance

3. **Probability Analysis**: After simulations:
   - Calculates win probabilities for Over/Under
   - Computes expected value assuming -110 odds
   - Determines optimal bet and Kelly sizing

### Variance Parameters

- **Pace Variance**: ±10% (captures game flow randomness)
- **Efficiency Variance**: ±8% per possession (shot-to-shot variance)

These are calibrated from historical NBA data to produce realistic distributions.

---

## Support

For issues or questions about this API:
- Check FastAPI auto-generated docs: `http://localhost:8000/docs`
- Review simulation logic: `backend/simulation/monte_carlo_totals.py`
- Contact: Backend team (C1)

---

**Last Updated**: November 8, 2025
**Version**: 1.0.0
**Status**: Production Ready
