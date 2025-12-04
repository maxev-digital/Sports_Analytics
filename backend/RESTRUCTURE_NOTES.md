# Data Fetching Restructure - ESPN as Primary Source

## Problem
Platform only shows games when The Odds API has them. Need to show all upcoming/live games from ESPN regardless of odds availability.

## Solution
**ESPN as primary source → Odds as overlay**

### Changes Made

1. **Added Schedule Fetching to ESPN Clients**
   - `espn_nfl_client.py`: Added `fetch_schedule()` method
   - `nba_live_client.py`: Added `fetch_schedule()` method
   
2. **Restructured game_tracker.py Flow**
   - STEP 1: Fetch ESPN schedules (NBA + NFL) - PRIMARY SOURCE
   - STEP 2: Fetch odds data - SECONDARY SOURCE (overlay)
   - STEP 3: Fetch live scoreboards for real-time data
   - STEP 4: Create odds lookup by team names
   - STEP 5: Process ESPN games and merge with odds when available

### New Data Flow

```
ESPN API (Primary)          The Odds API (Secondary)
      ↓                              ↓
  All Games              →       Odds Lookup
  (Schedule)                    (by team names)
      ↓                              ↓
  ├─ Match Found? ────────────→ Merge Odds
  │      Yes                      (full data)
  │      
  └─ Match Not Found? ──────→ Display Without Odds
         No                    (game still shows)
```

### Benefits

1. **Always Show Games**: Users see all scheduled games, not just ones with odds
2. **Better UX**: Can prepare for upcoming games even before odds are posted
3. **More Data**: ESPN provides schedule, scores, and live stats regardless of betting markets
4. **Fail-Safe**: If Odds API is down, games still display (without betting lines)

### Implementation Status

- [x] Add schedule methods to ESPN clients
- [ ] Complete game merging logic in game_tracker.py
- [ ] Handle games without odds (display with "No odds available" message)
- [ ] Test with live data
- [ ] Deploy to production

### Next Steps

1. Complete the ESPN game processing loop
2. Add proper handling for games without odds
3. Update frontend to handle games that may not have odds
4. Test thoroughly with different scenarios:
   - Games with full odds
   - Games without odds
   - Mixed scenarios
