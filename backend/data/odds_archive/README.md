# Odds Archive System

## Overview

Automated system to collect and archive historical odds data from The Odds API for 5 major sports leagues.

## Features

✅ **Game Odds Collection** (Spreads, Totals, Moneyline)
- NBA (basketball_nba)
- NCAAB (basketball_ncaab)
- NHL (icehockey_nhl)
- NFL (americanfootball_nfl)
- NCAAF (americanfootball_ncaaf)

✅ **Player Props Collection** (WORKING!)
- **NBA**: points, rebounds, assists, threes, blocks, steals
- **NHL**: goals, assists, points, shots_on_goal
- **NFL**: pass_yds, pass_tds, rush_yds, receptions
- **NCAAF**: pass_yds, pass_tds, rush_yds, receptions
- **NCAAB**: points, rebounds, assists, threes

✅ **Automated Collection**
- Runs every 30 minutes via systemd timer
- Smart rate limiting based on API remaining requests
- Logs all collection activity
- Fetches props per event (one API call per game)

✅ **Data Storage**
- Single unified SQLite database: `odds_history.db`
- 6 tables: game_odds_pregame, game_odds_live, prop_odds_pregame, prop_odds_live, prop_results, game_results
- Proper indexing for performance
- Snapshot types: opening (>48hrs), morning (2-48hrs), closing (0-2hrs)

## Current Status (Nov 18, 2025)

**Database Statistics:**
- **Game odds**: 12,723 pregame records
- **Player props**: 9,865 prop records (587 unique players)
- **Database size**: 7.2 MB
- **Date range**: Nov 18 - Dec 7, 2025
- **API requests remaining**: 12.22M (paid tier)

**Props by Sport:**
- NBA: 5,572 props
- NHL: 3,396 props
- NCAAF: 302 props
- NCAAB: 310 props
- NFL: 285 props

**Collection Performance:**
- ~4,000-5,000 game odds per cycle
- ~10,000 player props per cycle
- ~50-70 API requests per cycle (including props)
- Database grows ~2-3 MB per cycle (with line changes)

## Files

### Core Files
- `odds_archive_db.py` - Database schema and management
- `odds_collector_service.py` - Collection service with rate limiting

### Systemd Service
- `/etc/systemd/system/odds-collector.service` - Systemd service definition
- `/etc/systemd/system/odds-collector.timer` - Timer (every 30 minutes)

### Logs
- `/var/log/odds-collector.log` - Standard output (currently unused)
- `/var/log/odds-collector-error.log` - All logging output (INFO + ERROR)

## Management Commands

### Check Timer Status
```bash
systemctl status odds-collector.timer
systemctl list-timers odds-collector.timer
```

### Manual Collection Run
```bash
systemctl start odds-collector.service
```

### View Logs
```bash
tail -f /var/log/odds-collector-error.log
```

### Database Statistics
```bash
cd /root/sporttrader/backend/data/odds_archive
python3 odds_archive_db.py
```

### Stop/Disable Collection
```bash
systemctl stop odds-collector.timer
systemctl disable odds-collector.timer
```

### Restart Collection
```bash
systemctl restart odds-collector.timer
```

## Storage Estimates

**Per Collection (30 minutes):**
- ~4,000-5,000 game odds records
- ~10,000 player prop records
- ~2-3 MB database growth (with line changes)

**Daily Estimates:**
- 48 collections per day
- ~200,000 game odds records per day
- ~480,000 player prop records per day
- ~100-150 MB per day

**Monthly Estimates:**
- ~6M game odds records
- ~14M player prop records
- ~3-4.5 GB per month

**Data Retention:**
- Auto-archive data older than 365 days
- Keep prop results forever (valuable for analysis)
- Estimated annual storage: ~40-50 GB

## API Usage

**Rate Limits:**
- Paid tier: 12+ million requests remaining
- Usage: ~50-70 requests per collection cycle (5 sports + props per game)
- Daily usage: ~2,400-3,400 requests (48 collections/day)
- Monthly usage: ~72,000-102,000 requests
- **Well within limits** (less than 1% of available requests)

## Database Schema

### game_odds_pregame
Pregame odds for spreads, totals, and moneylines with snapshot types (opening/morning/closing)

### game_odds_live
Live in-game odds with current score and time remaining

### prop_odds_pregame
Pregame player prop odds (not currently collecting)

### prop_odds_live
Live player prop odds (not currently collecting)

### prop_results
Graded player prop results with WIN/LOSS/PUSH outcomes

### game_results
Final game scores for reference

## Future Enhancements

1. **Prop Grading Integration** (HIGH PRIORITY)
   - Connect to NBA API, NHL API, etc. for player stats
   - Automatically grade props after games complete
   - Calculate prop betting performance metrics
   - Track sharp vs public prop lines

2. **Live Odds Collection**
   - Enable in-game odds collection
   - Store current score and time remaining
   - Track live line movements
   - Detect live betting opportunities

3. **Performance Dashboard**
   - Web UI to view collection status
   - Database size and growth charts
   - API usage monitoring
   - Prop performance tracking

4. **Advanced Analytics**
   - Line movement detection (opening to closing)
   - Sharp money indicators
   - Prop line value analysis
   - Player prop hit rate by book

5. **Optimization**
   - Only fetch props for games within 48 hours
   - Skip sports with no games today
   - Intelligent caching to reduce redundant API calls

## Maintenance

The system is fully automated and requires minimal maintenance:
- Systemd timer handles scheduling
- Auto-restarts on failure
- Logs all activity
- Smart rate limiting prevents API overuse

Monitor occasionally:
- Check logs for errors
- Verify database size growth
- Confirm API requests remaining
