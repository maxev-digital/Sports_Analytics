#!/usr/bin/env python3
"""
Daily NBA Predictions Workflow
Predicts games in the NEXT 7 DAYS using current team stats
Run this daily for fresh predictions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta, timezone
import pandas as pd

# Import our modules
from scrapers.nba.nba_api_stats import NBAScraper
from scrapers.odds.odds_api_scraper import OddsAPIScraper
from models.nba.totals_predictor import NBATotalsPredictor

def run_daily_predictions():
    """Complete daily workflow - predicts next 7 days of games"""
    print("\n" + "="*70)
    print("NBA DAILY PREDICTIONS WORKFLOW")
    print("="*70)
    print(f"Run Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # === STEP 1: SCRAPE NBA TEAM STATS ===
    print("\n[1/3] Scraping NBA team stats...")
    print("-"*70)
    
    nba_scraper = NBAScraper()
    team_stats = nba_scraper.run_full_scrape()
    
    if team_stats is None:
        print("❌ Failed to get team stats")
        return
    
    # === STEP 2: GET BETTING ODDS ===
    print("\n[2/3] Fetching betting odds...")
    print("-"*70)
    
    odds_scraper = OddsAPIScraper()
    odds_df = odds_scraper.get_nba_odds()
    
    if odds_df.empty:
        print("⚠️  No games found in API")
        return
    
    # === FILTER TO NEXT 7 DAYS ===
    # Convert commence_time to datetime (already in UTC from API)
    odds_df['commence_time'] = pd.to_datetime(odds_df['commence_time'], utc=True)
    
    # Get current time in UTC for comparison
    current_time_utc = datetime.now(timezone.utc)
    seven_days_from_now = current_time_utc + timedelta(days=14)
    
    # Filter to next 7 days
    upcoming_odds = odds_df[
        (odds_df['commence_time'] >= current_time_utc) & 
        (odds_df['commence_time'] <= seven_days_from_now)
    ].copy()
    
    if upcoming_odds.empty:
        print("⚠️  No games in the next 7 days")
        return
    
    # Convert to local time for display
    upcoming_odds['game_datetime_local'] = upcoming_odds['commence_time'].dt.tz_convert('US/Eastern')
    upcoming_odds['game_date'] = upcoming_odds['game_datetime_local'].dt.date
    upcoming_odds['game_time'] = upcoming_odds['game_datetime_local'].dt.strftime('%I:%M %p')
    upcoming_odds['day_of_week'] = upcoming_odds['game_datetime_local'].dt.strftime('%A')
    
    unique_games_count = upcoming_odds['game_id'].nunique()
    date_range = f"{upcoming_odds['game_date'].min()} to {upcoming_odds['game_date'].max()}"
    
    print(f"\n✓ Found {unique_games_count} games in next 7 days")
    print(f"📅 Date range: {date_range}")
    
    # === STEP 3: GENERATE PREDICTIONS ===
    print("\n[3/3] Generating predictions...")
    print("-"*70)
    
    predictor = NBATotalsPredictor(team_stats)
    
    predictions = []
    skipped = []
    
    # Get unique games
    unique_games = upcoming_odds[['game_id', 'home_team', 'away_team', 'game_date', 'game_time', 'day_of_week']].drop_duplicates()
    
    for _, game in unique_games.iterrows():
        game_id = game['game_id']
        home_team = game['home_team']
        away_team = game['away_team']
        game_date = game['game_date']
        game_time = game['game_time']
        day_of_week = game['day_of_week']
        
        # Get consensus market total
        market_total = odds_scraper.get_consensus_total(game_id, upcoming_odds)
        
        if market_total is None:
            skipped.append(f"{away_team} @ {home_team}")
            continue
        
        # Generate prediction
        result = predictor.predict_game_total(home_team, away_team)
        
        if 'error' in result:
            print(f"  ⚠️  Skipping {away_team} @ {home_team}: {result['error']}")
            skipped.append(f"{away_team} @ {home_team} - {result['error']}")
            continue
        
        # Calculate edge
        edge = predictor.calculate_edge(result['predicted_total'], market_total)
        
        # Calculate days until game
        days_until = (game_date - datetime.now().date()).days
        
        predictions.append({
            'game_date': str(game_date),
            'day_of_week': day_of_week,
            'game_time': game_time,
            'days_until': days_until,
            'game_id': game_id,
            'away_team': away_team,
            'home_team': home_team,
            'away_pace': result['breakdown']['away_pace'],
            'home_pace': result['breakdown']['home_pace'],
            'expected_pace': result['expected_pace'],
            'away_off_rating': result['breakdown']['away_off_rating'],
            'home_off_rating': result['breakdown']['home_off_rating'],
            'away_def_rating': result['breakdown']['away_def_rating'],
            'home_def_rating': result['breakdown']['home_def_rating'],
            'away_expected_pts': result['away_expected_points'],
            'home_expected_pts': result['home_expected_points'],
            'predicted_total': result['predicted_total'],
            'market_total': market_total,
            'edge': edge['edge'],
            'recommendation': edge['side'],
            'confidence': edge['confidence'],
            'bet': 'YES' if edge['bet'] else 'NO'
        })
    
    if not predictions:
        print("\n⚠️  No valid predictions generated")
        if skipped:
            print("\nSkipped games:")
            for skip in skipped:
                print(f"  - {skip}")
        return
    
    predictions_df = pd.DataFrame(predictions)
    
    # Sort by date, then by edge (highest first)
    predictions_df = predictions_df.sort_values(['game_date', 'edge'], ascending=[True, False])
    
    # === DISPLAY BY DATE ===
    print("\n" + "="*70)
    print("PREDICTIONS BY DATE")
    print("="*70)
    
    for game_date in sorted(predictions_df['game_date'].unique()):
        date_games = predictions_df[predictions_df['game_date'] == game_date]
        day_name = date_games.iloc[0]['day_of_week']
        days_until = date_games.iloc[0]['days_until']
        
        if days_until == 0:
            day_label = "TODAY"
        elif days_until == 1:
            day_label = "TOMORROW"
        else:
            day_label = f"in {days_until} days"
        
        print(f"\n📅 {game_date} ({day_name}) - {day_label}")
        print(f"   {len(date_games)} games")
        print("-"*70)
        
        for _, pred in date_games.iterrows():
            print(f"\n  {pred['game_time']} - {pred['away_team']} @ {pred['home_team']}")
            print(f"    Model: {pred['predicted_total']} | Market: {pred['market_total']} | Edge: {pred['edge']}")
            
            bet_icon = "✅ BET" if pred['bet'] == 'YES' else "❌ PASS"
            print(f"    Recommendation: {pred['recommendation']} ({pred['confidence']}) - {bet_icon}")
    
    # === SAVE RESULTS ===
    output_dir = 'backend/data/predictions'
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{output_dir}/nba_predictions_{timestamp}.csv'
    predictions_df.to_csv(filename, index=False)
    
    latest_file = f'{output_dir}/nba_predictions_latest.csv'
    predictions_df.to_csv(latest_file, index=False)
    
    # === SUMMARY ===
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"✓ Total games analyzed: {len(predictions_df)}")
    print(f"✓ Games by confidence level:")
    print(f"   HIGH: {len(predictions_df[predictions_df['confidence']=='HIGH'])}")
    print(f"   MEDIUM: {len(predictions_df[predictions_df['confidence']=='MEDIUM'])}")
    print(f"   LOW: {len(predictions_df[predictions_df['confidence']=='LOW'])}")
    print(f"   NONE: {len(predictions_df[predictions_df['confidence']=='NONE'])}")
    print(f"✓ Recommended bets: {len(predictions_df[predictions_df['bet']=='YES'])}")
    
    print(f"\n📁 Saved to: {filename}")
    print(f"📁 Latest: {latest_file}")
    
    # === TOP BETS (NEXT 3 DAYS) ===
    next_3_days = datetime.now().date() + timedelta(days=3)
    soon_bets = predictions_df[
        (predictions_df['bet'] == 'YES') & 
        (pd.to_datetime(predictions_df['game_date']).dt.date <= next_3_days)
    ]
    
    if len(soon_bets) > 0:
        print("\n🎯 TOP BETS (NEXT 3 DAYS):")
        print("-"*70)
        top_bets = soon_bets.nlargest(5, 'edge')
        for _, bet in top_bets.iterrows():
            print(f"  {bet['game_date']} ({bet['day_of_week']}) - {bet['game_time']}")
            print(f"  {bet['away_team']} @ {bet['home_team']}")
            print(f"    {bet['recommendation']} {bet['market_total']} (Edge: {bet['edge']}) - {bet['confidence']}")
            print()
    else:
        print("\n⚠️  No recommended bets in the next 3 days")
    
    # === GAMES TODAY ===
    today = datetime.now().date()
    today_games = predictions_df[pd.to_datetime(predictions_df['game_date']).dt.date == today]
    
    if len(today_games) > 0:
        print("\n🏀 GAMES TODAY:")
        print("-"*70)
        for _, game in today_games.iterrows():
            print(f"  {game['game_time']} - {game['away_team']} @ {game['home_team']}")
            print(f"    {game['recommendation']} {game['market_total']} (Edge: {game['edge']}) - {game['confidence']}")
    else:
        next_game = predictions_df.iloc[0]
        print(f"\n📅 No games today. Next game: {next_game['game_date']} ({next_game['day_of_week']})")
    
    print("\n" + "="*70)
    print("✅ DAILY PREDICTIONS COMPLETE")
    print("="*70)
    
    return predictions_df


if __name__ == "__main__":
    run_daily_predictions()