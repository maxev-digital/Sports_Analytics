# NHL Goalie Pull Alert Timing Update
**Updated:** 2025-11-14
**Status:** LIVE on VPS

## Feed Delay Issue
Our NHL data feed has a **30-second delay** from real-time game action. This means when we see "2:00 remaining", the actual game is at "1:30 remaining".

## Solution: Adjusted Alert Timing

### OLD System (Removed):
- **EARLY WARNING:** 5:00 remaining - prepare betting books
- **IMMINENT:** 30-90 seconds before expected pull

**Problem:** By the time we calculated the goalie would pull in 60 seconds, it had already happened in the real game.

### NEW System (Active):

#### Alert Triggers (in our delayed feed):

| Score Deficit | Alert Trigger (Our Feed) | Real Game Time | Window (seconds) |
|---------------|-------------------------|----------------|------------------|
| **-1 goal**   | 2:00 (120 sec)          | ~1:30 (90 sec) | 115-125 sec      |
| **-2 goals**  | 3:00 (180 sec)          | ~2:30 (150 sec)| 175-185 sec      |
| **-3+ goals** | 3:00 (180 sec)          | ~2:30 (150 sec)| 175-185 sec      |

#### Alert Windows:
- **±5 second window** around trigger point to catch the exact moment
- Example: Down 1 goal triggers when we see 1:55 to 2:05 remaining

## Logic Changes

### Code Location: `backend/nhl_goalie_pull_predictor.py`

```python
# OLD:
is_early_warning = current_time_remaining >= 300 and score_diff in [-1, -2]
is_imminent = 30 <= time_until_pull <= 90

# NEW:
if score_diff <= -2:
    # Down 2+ goals: Alert at 3:00 mark (real game ~2:30)
    if current_time_remaining >= 175 and current_time_remaining <= 185:
        is_imminent = True
        alert_type = 'IMMINENT'
elif score_diff == -1:
    # Down 1 goal: Alert at 2:00 mark (real game ~1:30)
    if current_time_remaining >= 115 and current_time_remaining <= 125:
        is_imminent = True
        alert_type = 'IMMINENT'
```

## Alert Behavior

### Single Alert Type:
- **IMMINENT only** (removed EARLY_WARNING)
- Alert fires once at optimal betting moment
- No multiple alerts per game situation

### Priority Levels:
- **HIGH:** Confidence ≥70% for down 1, ≥65% for down 2+
- **MEDIUM:** Lower confidence situations

### EV Requirement:
- **Minimum 5% Expected Value** to trigger alert
- Only show positive EV betting opportunities

## User Experience

### Alert Message:
```
🚨 GOALIE PULL ALERT - HIGH PRIORITY

Tampa Bay Lightning @ Florida Panthers
Score: 2-3
Time: 2:00 remaining (Period 3)

📊 SITUATION:
Tampa Bay Lightning trailing by 1 goal(s)
Goalie pull expected within 30-90 seconds (real game time)
Coach: Jon Cooper (Analytics: 8.2/10)
Confidence: 75%

💰 BET NOW - OVER 5.5 @ +135

📈 BETTING EDGE:
Edge: +15.8%
Expected Value: +36.2%
Win Probability: 58.4%

⏰ PLACE BET IMMEDIATELY!
Feed is 30 seconds delayed - goalie pull happening soon in real time.
Odds will shift to -110 or worse after pull is visible on broadcast.
```

### Key Messaging:
- Clear explanation of feed delay
- "Real game time" context
- Urgency to bet before odds shift
- Single, actionable alert

## Testing Scenarios

### Down 1 Goal:
- ✓ 2:05 (125s) → ALERT (real: 1:35)
- ✓ 2:00 (120s) → ALERT (real: 1:30)
- ✓ 1:55 (115s) → ALERT (real: 1:25)
- ✗ 2:10 (130s) → No alert (too early)
- ✗ 1:50 (110s) → No alert (too late)

### Down 2+ Goals:
- ✓ 3:05 (185s) → ALERT (real: 2:35)
- ✓ 3:00 (180s) → ALERT (real: 2:30)
- ✓ 2:55 (175s) → ALERT (real: 2:25)
- ✗ 3:10 (190s) → No alert (too early)
- ✗ 2:50 (170s) → No alert (too late)

## Deployment

### Local System:
✅ Updated: `C:\Users\nashr\backend\nhl_goalie_pull_predictor.py`

### VPS Production:
✅ Updated: `/root/sporttrader/backend/nhl_goalie_pull_predictor.py`
✅ Service restarted: 00:57:22 UTC (Nov 15, 2025)
✅ Status: Active and monitoring

## Next Steps

1. ✅ Timing adjustment complete
2. 🔄 **IN PROGRESS:** Review edge calculation based on team EN stats
3. ⏳ **PENDING:** Live testing during tonight's games
4. ⏳ **PENDING:** Monitor alert accuracy vs actual pull times

## Notes

- Alert window is intentionally narrow (±5 sec) to avoid duplicate alerts
- System polls every 10 seconds, so some variance expected
- Real-world testing will validate 30-second delay assumption
- May need fine-tuning based on actual game observations
