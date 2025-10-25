#!/usr/bin/env python3
"""
Test Live NCAAF Odds - TIMEZONE FIXED VERSION
Properly handles UTC to CST conversion
"""

import requests
from datetime import datetime, timezone
import pytz
import time

API_KEY = "3b91452fcbaa6deffecb2e5843655099"
SPORT = "americanfootball_ncaaf"

# Set YOUR timezone
LOCAL_TZ = pytz.timezone('America/Chicago')  # CST/CDT

def get_local_time():
    """Get current time in CST"""
    return datetime.now(LOCAL_TZ)

def convert_to_local(utc_timestamp):
    """Convert UTC timestamp to local time"""
    utc_time = datetime.fromisoformat(utc_timestamp.replace('Z', '+00:00'))
    local_time = utc_time.astimezone(LOCAL_TZ)
    return local_time

def fetch_live_odds():
    """Fetch current odds from API"""
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds/"
    
    params = {
        'apiKey': API_KEY,
        'regions': 'us',
        'markets': 'totals',
        'oddsFormat': 'american'
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        # Check API usage
        requests_used = response.headers.get('x-requests-used', 'unknown')
        requests_remaining = response.headers.get('x-requests-remaining', 'unknown')
        
        print(f"\n📊 API Usage:")
        print(f"   Requests used: {requests_used}")
        print(f"   Requests remaining: {requests_remaining}")
        
        return response.json()
        
    except Exception as e:
        print(f"❌ Error fetching odds: {str(e)}")
        return []

def analyze_game_status(game, now_local):
    """Determine if game is live, upcoming, or finished"""
    game_time_local = convert_to_local(game['commence_time'])
    time_diff = (game_time_local - now_local).total_seconds() / 60  # minutes
    
    # Game status logic
    if time_diff > 30:
        status = 'upcoming'
    elif -180 <= time_diff <= 30:  # Game started up to 3 hours ago
        status = 'live'
    else:
        status = 'finished'
    
    return status, game_time_local, time_diff

def check_odds():
    """Check current odds and categorize games"""
    now_local = get_local_time()
    
    print("\n" + "="*70)
    print(f"CHECK AT: {now_local.strftime('%Y-%m-%d %I:%M:%S %p %Z')}")
    print("="*70)
    
    games = fetch_live_odds()
    
    if not games:
        print("❌ No games found")
        return
    
    # Categorize games
    live_games = []
    upcoming_games = []
    finished_games = []
    
    for game in games:
        status, game_time, time_diff = analyze_game_status(game, now_local)
        
        game_info = {
            'game': game,
            'game_time': game_time,
            'time_diff': time_diff,
            'status': status
        }
        
        if status == 'live':
            live_games.append(game_info)
        elif status == 'upcoming':
            upcoming_games.append(game_info)
        else:
            finished_games.append(game_info)
    
    # Display summary
    print(f"\n🏈 Found {len(games)} games total")
    print(f"   🔴 Live/In Progress: {len(live_games)}")
    print(f"   ✅ Recently Finished: {len(finished_games)}")
    print(f"   📅 Upcoming: {len(upcoming_games)}")
    
    # Show LIVE games first
    if live_games:
        print("\n" + "="*70)
        print("🔴 LIVE GAMES (In Progress):")
        print("="*70)
        
        for info in live_games[:10]:  # Show first 10 live games
            game = info['game']
            game_time = info['game_time']
            time_diff = info['time_diff']
            
            print(f"\n🏈 {game['away_team']} @ {game['home_team']}")
            print(f"   Kickoff: {game_time.strftime('%I:%M %p %Z')}")
            print(f"   Started: {abs(time_diff):.0f} minutes ago")
            
            # Check if odds are available
            if game.get('bookmakers'):
                print(f"   ✅ LIVE ODDS AVAILABLE ({len(game['bookmakers'])} bookmakers)")
                
                for bookmaker in game['bookmakers'][:3]:  # Show first 3 books
                    for market in bookmaker['markets']:
                        if market['key'] == 'totals':
                            total = market['outcomes'][0]['point']
                            print(f"   📊 {bookmaker['title']:<20} Total: {total}")
                
                # Check last updated
                if 'last_update' in game:
                    last_update = convert_to_local(game['last_update'])
                    minutes_ago = (now_local - last_update).total_seconds() / 60
                    print(f"   🕐 Last Updated: {minutes_ago:.1f} minutes ago")
            else:
                print(f"   ❌ NO LIVE ODDS AVAILABLE")
    
    # Show upcoming games
    if upcoming_games and len(upcoming_games) <= 5:
        print("\n" + "="*70)
        print("📅 UPCOMING GAMES:")
        print("="*70)
        
        for info in upcoming_games[:5]:
            game = info['game']
            game_time = info['game_time']
            time_diff = info['time_diff']
            
            print(f"\n🏈 {game['away_team']} @ {game['home_team']}")
            print(f"   Starts: {game_time.strftime('%I:%M %p %Z')}")
            print(f"   In: {time_diff:.1f} minutes")
            
            if game.get('bookmakers'):
                for bookmaker in game['bookmakers'][:2]:
                    for market in bookmaker['markets']:
                        if market['key'] == 'totals':
                            total = market['outcomes'][0]['point']
                            print(f"   📊 {bookmaker['title']:<20} Total: {total}")

def main():
    print("="*70)
    print("TESTING LIVE IN-GAME ODDS - NCAAF (TIMEZONE FIXED)")
    print("="*70)
    
    now = get_local_time()
    print(f"\n📅 Today: {now.strftime('%A, %B %d, %Y')}")
    print(f"⏰ Time: {now.strftime('%I:%M %p %Z')}")
    
    print("\n🎯 What we're checking:")
    print("  1. Are there games LIVE right now?")
    print("  2. Do bookmakers offer live odds during games?")
    print("  3. How recent are the odds updates?")
    
    print("\n📋 Running 3 checks, 2 minutes apart...")
    
    for i in range(3):
        print("\n" + "#"*70)
        print(f"CHECK {i+1} of 3")
        print("#"*70)
        
        check_odds()
        
        if i < 2:
            print(f"\n⏳ Waiting 2 minutes before next check...")
            time.sleep(120)
    
    print("\n" + "="*70)
    print("✅ TEST COMPLETE")
    print("="*70)

if __name__ == "__main__":
    main()