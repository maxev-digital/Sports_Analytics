# ESPN-First Data Fetching Implementation Guide

## CRITICAL ISSUE
The current system only shows games when The Odds API has betting lines. This means:
- No odds available = No games shown
- Users can't see upcoming games to prepare
- System appears "broken" when odds aren't posted yet

## SOLUTION OVERVIEW
Change data fetching priority: **ESPN API (Primary) → Odds API (Secondary/Overlay)**

## KEY CHANGES REQUIRED

### 1. ESPN Clients - Add Schedule Methods ✅ DONE
- `espn_nfl_client.py`: Added `fetch_schedule()` method
- `nba_live_client.py`: Added `fetch_schedule()` method + List import

### 2. Game Tracker - Restructure update_games() ⚠️ IN PROGRESS

The file game_tracker.py got partially corrupted during editing. Here's what the new flow should be:

```python
async def update_games(self):
    # STEP 1: Fetch ESPN schedules (PRIMARY SOURCE)
    espn_games = []
    espn_games.extend(self.nba_live_client.fetch_schedule())
    espn_games.extend(self.espn_nfl_client.fetch_schedule())
    
    # STEP 2: Fetch odds (SECONDARY - for overlay)
    odds_data = await self.odds_client.get_live_games()
    scores_data = await self.odds_client.get_game_scores()
    
    # STEP 3: Create odds lookup by team matchup
    odds_lookup = {}
    for game in odds_data:
        key = f"{game['away_team']}@{game['home_team']}".lower()
        odds_lookup[key] = game
    
    # STEP 4: Process EACH ESPN game
    for espn_game in espn_games:
        home_team = espn_game['home_team']
        away_team = espn_game['away_team']
        
        # Try to find matching odds
        lookup_key = f"{away_team}@{home_team}".lower()
        odds_game = odds_lookup.get(lookup_key)
        
        if odds_game:
            # Has odds: Create full game with betting lines
            # (existing game creation logic)
            pass
        else:
            # No odds: Create basic game without betting lines
            game_id = f"espn_{sport_key}_{home_team}_{away_team}"
            game_state = GameState(
                id=game_id,
                sport_key=espn_game['sport_key'],
                home_team=Team(name=home_team, score=None),
                away_team=Team(name=away_team, score=None),
                commence_time=espn_game['commence_time'],
                status=espn_game['status']
            )
            new_games[game_id] = LiveGame(
                state=game_state,
                odds=[],  # Empty odds list
                projection=None
            )
```

## BENEFITS OF THIS APPROACH

1. **Always Show Games**: Platform shows all scheduled games
2. **Graceful Degradation**: If Odds API is down, games still display
3. **Better UX**: Users can see upcoming matchups before odds are posted
4. **Flexible**: Can mark games as "Odds not yet available"

## IMPLEMENTATION STATUS

- [x] Add schedule methods to ESPN clients
- [ ] Complete game_tracker.py restructure (file needs fixing)
- [ ] Handle empty odds list in frontend
- [ ] Add "No odds available" UI indicator
- [ ] Test with various scenarios
- [ ] Deploy to production

## QUICK FIX TO RESUME

The game_tracker.py file has a corrupted section around line 480-500. To fix:

1. Backup current game_tracker.py
2. Remove the duplicate "for game_data in filtered_odds:" loop
3. Keep only the "for espn_game in espn_games:" loop
4. Implement the logic shown above for handling games with/without odds

## TESTING SCENARIOS

After implementing:
1. Test with games that have full odds ✓
2. Test with games that have NO odds ✓
3. Test with mixed scenarios ✓
4. Test when Odds API is completely unavailable ✓
5. Verify frontend handles empty odds gracefully ✓

## DEPLOYMENT

Once tested locally:
```bash
# On production server 148.230.87.135
cd /path/to/backend
git pull
systemctl restart sports-betting-backend
```

## FALLBACK PLAN

If issues arise, the old odds-first approach can be restored by reverting game_tracker.py to use the filtered_odds loop instead of espn_games loop.
