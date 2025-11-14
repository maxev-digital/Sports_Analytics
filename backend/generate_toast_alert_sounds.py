"""
Generate all toast alert sound effects using ElevenLabs API
Run once to create all audio files, then use them without API calls
"""
import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

ELEVEN_LABS_API_KEY = os.getenv('ELEVEN_LABS_API_KEY')
ELEVEN_LABS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"

# Use Brian voice (authoritative, clear, professional)
VOICE_ID = "nPczCjzI2devNBz1zQrb"

# All toast alert audio files to generate
TOAST_ALERTS = {
    # Arbitrage alerts (CRITICAL - Red windows)
    "arbitrage_critical.mp3": "Critical arbitrage opportunity! Risk-free profit available!",
    "arbitrage_high.mp3": "High-priority arbitrage detected!",
    "arbitrage_found.mp3": "Arbitrage opportunity found",

    # Steam move alerts (Blue windows)
    "steam_critical.mp3": "Major steam move detected! Sharp money flooding in!",
    "steam_high.mp3": "Significant steam move! Line moving fast!",
    "steam_medium.mp3": "Steam move detected",

    # Middle opportunity alerts (Green windows)
    "middle_critical.mp3": "Excellent middle opportunity! Potential double win!",
    "middle_high.mp3": "Middle opportunity available",
    "middle_medium.mp3": "Middling chance detected",

    # Goalie pull alerts (NHL specific)
    "goalie_pull_critical.mp3": "Goalie pulled! Empty net opportunity!",
    "goalie_pull_warning.mp3": "Goalie pull expected soon! Prepare to bet!",

    # General betting alerts (Orange windows)
    "alert_high.mp3": "High-confidence betting opportunity!",
    "alert_medium.mp3": "Betting opportunity detected",
    "alert_low.mp3": "New betting alert",

    # Confidence levels
    "high_confidence.mp3": "High confidence",
    "medium_confidence.mp3": "Medium confidence",
    "critical_urgency.mp3": "Critical urgency!",

    # Generic notification sounds
    "new_alert.mp3": "New alert",
    "opportunity.mp3": "Opportunity",
    "bet_now.mp3": "Place bet now!",

    # ========== SPORTSBOOK ALERTS (25 books) ==========
    "draftkings_alert.mp3": "Best available line at DraftKings",
    "fanduel_alert.mp3": "Best available line at FanDuel",
    "betmgm_alert.mp3": "Best available line at BetMGM",
    "betrivers_alert.mp3": "Best available line at BetRivers",
    "williamhill_alert.mp3": "Best available line at William Hill",
    "fanatics_alert.mp3": "Best available line at Fanatics",
    "espnbet_alert.mp3": "Best available line at ESPN BET",
    "caesars_alert.mp3": "Best available line at Caesars",
    "pointsbet_alert.mp3": "Best available line at PointsBet",
    "ballybet_alert.mp3": "Best available line at Bally Bet",
    "betonline_alert.mp3": "Best available line at BetOnline",
    "bovada_alert.mp3": "Best available line at Bovada",
    "mybookie_alert.mp3": "Best available line at MyBookie",
    "lowvig_alert.mp3": "Best available line at LowVig",
    "betway_alert.mp3": "Best available line at Betway",
    "betus_alert.mp3": "Best available line at BetUS",
    "superbook_alert.mp3": "Best available line at SuperBook",
    "wynnbet_alert.mp3": "Best available line at WynnBet",
    "unibet_alert.mp3": "Best available line at Unibet",
    "twinspires_alert.mp3": "Best available line at TwinSpires",
    "sugarhouse_alert.mp3": "Best available line at SugarHouse",
    "betfred_alert.mp3": "Best available line at Betfred",
    "hardrock_alert.mp3": "Best available line at Hard Rock",
    "sisportsbook_alert.mp3": "Best available line at S I Sportsbook",
    "barstool_alert.mp3": "Best available line at Barstool",

    # ========== BETTING STRATEGY ALERTS (40+ strategies) ==========
    "b2b_rested_alert.mp3": "Back-to-back versus rested team opportunity!",
    "clv_tracker_alert.mp3": "Closing line value detected!",
    "divisional_rivalry_alert.mp3": "Divisional rivalry edge found!",
    "fatigue_detector_alert.mp3": "Team fatigue opportunity detected!",
    "fatigue_strategy_alert.mp3": "Fatigue-based betting edge!",
    "favorite_comeback_alert.mp3": "Favorite comeback opportunity!",
    "goalie_pull_alert.mp3": "Goalie pull predictor alert!",
    "halftime_tracker_alert.mp3": "Halftime adjustment opportunity!",
    "home_away_split_alert.mp3": "Home away split edge detected!",
    "injury_cascade_alert.mp3": "Injury cascade opportunity!",
    "kelly_sizing_alert.mp3": "Kelly criterion sizing recommendation!",
    "key_numbers_alert.mp3": "Key number edge detected!",
    "live_betting_alert.mp3": "Live betting opportunity!",
    "low_hold_alert.mp3": "Low hold opportunity found!",
    "matchup_history_alert.mp3": "Historical matchup edge!",
    "momentum_detector_alert.mp3": "Momentum shift detected!",
    "moneyline_alert.mp3": "Moneyline value found!",
    "multi_sport_ensemble_alert.mp3": "Multi-sport ensemble prediction!",
    "nba_quarter_reversal_alert.mp3": "N B A quarter reversal opportunity!",
    "pace_based_alert.mp3": "Pace-based edge detected!",
    "player_props_alert.mp3": "Player prop opportunity!",
    "regression_alert.mp3": "Regression to mean opportunity!",
    "schedule_fatigue_alert.mp3": "Schedule fatigue edge detected!",
    "sharp_money_alert.mp3": "Sharp money movement detected!",
    "sharp_money_tracker_alert.mp3": "Sharp money tracking alert!",
    "weather_integration_alert.mp3": "Weather impact opportunity!",
    "weather_strategy_alert.mp3": "Weather-based edge detected!",
    "line_movement_alert.mp3": "Significant line movement!",
    "reverse_line_movement_alert.mp3": "Reverse line movement detected!",
    "public_fade_alert.mp3": "Public fade opportunity!",
    "contrarian_alert.mp3": "Contrarian betting edge!",
    "steam_chase_alert.mp3": "Steam chase opportunity!",
    "opening_line_alert.mp3": "Opening line value detected!",
    "closing_line_alert.mp3": "Closing line opportunity!",
    "correlated_parlay_alert.mp3": "Correlated parlay edge!",
    "live_hedging_alert.mp3": "Live hedging opportunity!",
    "arbitrage_detector_alert.mp3": "Arbitrage detected!",
    "middle_finder_alert.mp3": "Middle opportunity found!",
    "betting_against_public_alert.mp3": "Betting against public edge!",
    "home_underdog_alert.mp3": "Home underdog value!",
    "road_favorite_alert.mp3": "Road favorite edge detected!",
    "divisional_underdog_alert.mp3": "Divisional underdog opportunity!",
    "conference_matchup_alert.mp3": "Conference matchup edge!",
    "playoff_intensity_alert.mp3": "Playoff intensity factor detected!",
    "revenge_game_alert.mp3": "Revenge game opportunity!",
    "lookahead_spot_alert.mp3": "Lookahead spot edge detected!",

    # ========== BET ACTION PHRASES (Reusable for any bet) ==========
    "bet_the_over.mp3": "Bet the over",
    "bet_the_under.mp3": "Bet the under",
    "bet_home_spread.mp3": "Bet the home spread",
    "bet_away_spread.mp3": "Bet the away spread",
    "bet_home_moneyline.mp3": "Bet the home moneyline",
    "bet_away_moneyline.mp3": "Bet the away moneyline",
    "bet_both_sides.mp3": "Bet both sides",
    "take_the_over.mp3": "Take the over",
    "take_the_under.mp3": "Take the under",
    "take_home_team.mp3": "Take the home team",
    "take_away_team.mp3": "Take the away team",

    # ========== CONNECTOR WORDS (For chaining alerts) ==========
    "versus.mp3": "versus",
    "at.mp3": "at",
    "and.mp3": "and",
    "or.mp3": "or",
    "also.mp3": "also",

    # ========== PRO TEAM NAMES (NBA: 25, NHL: 27, NFL: 32) ==========
    # NBA Teams
    "team_atlanta_hawks.mp3": "Atlanta Hawks",
    "team_brooklyn_nets.mp3": "Brooklyn Nets",
    "team_charlotte_hornets.mp3": "Charlotte Hornets",
    "team_cleveland_cavaliers.mp3": "Cleveland Cavaliers",
    "team_dallas_mavericks.mp3": "Dallas Mavericks",
    "team_denver_nuggets.mp3": "Denver Nuggets",
    "team_detroit_pistons.mp3": "Detroit Pistons",
    "team_golden_state_warriors.mp3": "Golden State Warriors",
    "team_houston_rockets.mp3": "Houston Rockets",
    "team_indiana_pacers.mp3": "Indiana Pacers",
    "team_los_angeles_clippers.mp3": "Los Angeles Clippers",
    "team_los_angeles_lakers.mp3": "Los Angeles Lakers",
    "team_miami_heat.mp3": "Miami Heat",
    "team_milwaukee_bucks.mp3": "Milwaukee Bucks",
    "team_minnesota_timberwolves.mp3": "Minnesota Timberwolves",
    "team_new_orleans_pelicans.mp3": "New Orleans Pelicans",
    "team_new_york_knicks.mp3": "New York Knicks",
    "team_orlando_magic.mp3": "Orlando Magic",
    "team_philadelphia_76ers.mp3": "Philadelphia 76ers",
    "team_phoenix_suns.mp3": "Phoenix Suns",
    "team_portland_trail_blazers.mp3": "Portland Trail Blazers",
    "team_sacramento_kings.mp3": "Sacramento Kings",
    "team_san_antonio_spurs.mp3": "San Antonio Spurs",
    "team_toronto_raptors.mp3": "Toronto Raptors",
    "team_utah_jazz.mp3": "Utah Jazz",

    # NHL Teams
    "team_anaheim_ducks.mp3": "Anaheim Ducks",
    "team_boston_bruins.mp3": "Boston Bruins",
    "team_buffalo_sabres.mp3": "Buffalo Sabres",
    "team_calgary_flames.mp3": "Calgary Flames",
    "team_carolina_hurricanes.mp3": "Carolina Hurricanes",
    "team_colorado_avalanche.mp3": "Colorado Avalanche",
    "team_columbus_blue_jackets.mp3": "Columbus Blue Jackets",
    "team_dallas_stars.mp3": "Dallas Stars",
    "team_detroit_red_wings.mp3": "Detroit Red Wings",
    "team_edmonton_oilers.mp3": "Edmonton Oilers",
    "team_florida_panthers.mp3": "Florida Panthers",
    "team_los_angeles_kings.mp3": "Los Angeles Kings",
    "team_montreal_canadiens.mp3": "Montreal Canadiens",
    "team_nashville_predators.mp3": "Nashville Predators",
    "team_new_york_islanders.mp3": "New York Islanders",
    "team_ottawa_senators.mp3": "Ottawa Senators",
    "team_philadelphia_flyers.mp3": "Philadelphia Flyers",
    "team_pittsburgh_penguins.mp3": "Pittsburgh Penguins",
    "team_san_jose_sharks.mp3": "San Jose Sharks",
    "team_seattle_kraken.mp3": "Seattle Kraken",
    "team_st_louis_blues.mp3": "St Louis Blues",
    "team_toronto_maple_leafs.mp3": "Toronto Maple Leafs",
    "team_utah_mammoth.mp3": "Utah Mammoth",
    "team_vancouver_canucks.mp3": "Vancouver Canucks",
    "team_vegas_golden_knights.mp3": "Vegas Golden Knights",
    "team_washington_capitals.mp3": "Washington Capitals",
    "team_winnipeg_jets.mp3": "Winnipeg Jets",

    # NFL Teams
    "team_arizona_cardinals.mp3": "Arizona Cardinals",
    "team_atlanta_falcons.mp3": "Atlanta Falcons",
    "team_baltimore_ravens.mp3": "Baltimore Ravens",
    "team_buffalo_bills.mp3": "Buffalo Bills",
    "team_carolina_panthers.mp3": "Carolina Panthers",
    "team_chicago_bears.mp3": "Chicago Bears",
    "team_cincinnati_bengals.mp3": "Cincinnati Bengals",
    "team_cleveland_browns.mp3": "Cleveland Browns",
    "team_dallas_cowboys.mp3": "Dallas Cowboys",
    "team_denver_broncos.mp3": "Denver Broncos",
    "team_detroit_lions.mp3": "Detroit Lions",
    "team_green_bay_packers.mp3": "Green Bay Packers",
    "team_houston_texans.mp3": "Houston Texans",
    "team_indianapolis_colts.mp3": "Indianapolis Colts",
    "team_jacksonville_jaguars.mp3": "Jacksonville Jaguars",
    "team_kansas_city_chiefs.mp3": "Kansas City Chiefs",
    "team_las_vegas_raiders.mp3": "Las Vegas Raiders",
    "team_los_angeles_chargers.mp3": "Los Angeles Chargers",
    "team_los_angeles_rams.mp3": "Los Angeles Rams",
    "team_miami_dolphins.mp3": "Miami Dolphins",
    "team_minnesota_vikings.mp3": "Minnesota Vikings",
    "team_new_england_patriots.mp3": "New England Patriots",
    "team_new_orleans_saints.mp3": "New Orleans Saints",
    "team_new_york_giants.mp3": "New York Giants",
    "team_new_york_jets.mp3": "New York Jets",
    "team_philadelphia_eagles.mp3": "Philadelphia Eagles",
    "team_pittsburgh_steelers.mp3": "Pittsburgh Steelers",
    "team_san_francisco_49ers.mp3": "San Francisco 49ers",
    "team_seattle_seahawks.mp3": "Seattle Seahawks",
    "team_tampa_bay_buccaneers.mp3": "Tampa Bay Buccaneers",
    "team_tennessee_titans.mp3": "Tennessee Titans",
    "team_washington_commanders.mp3": "Washington Commanders",
}

def generate_alert_sound(filename: str, text: str):
    """Generate alert sound using ElevenLabs API"""
    # Save to frontend/public folder
    output_dir = Path(__file__).parent.parent / "frontend" / "public" / "alerts"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename

    if output_path.exists():
        print(f"✓ SKIP: {filename} already exists")
        return True

    print(f"⏳ GENERATING: {filename}")
    print(f"   Text: '{text}'")

    url = f"{ELEVEN_LABS_API_URL}/{VOICE_ID}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVEN_LABS_API_KEY
    }

    # Voice settings for alert sounds - clear, urgent, professional
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.6,          # Slightly more stable for clarity
            "similarity_boost": 0.8,   # Higher for consistent voice
            "style": 0.4,              # Less dramatic, more professional
            "use_speaker_boost": True
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            file_size_kb = len(response.content) / 1024
            print(f"✅ SUCCESS: {filename} ({file_size_kb:.1f} KB)")
            return True
        else:
            print(f"❌ ERROR: {filename}")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ EXCEPTION: {filename}")
        print(f"   Error: {str(e)}")
        return False

def main():
    if not ELEVEN_LABS_API_KEY:
        print("❌ ERROR: ELEVEN_LABS_API_KEY not found in .env file")
        print("Please add your ElevenLabs API key to backend/.env")
        return

    print("\n" + "="*80)
    print("🎙️  COMPREHENSIVE VOICE ALERT SYSTEM - ElevenLabs API")
    print("="*80)
    print(f"\n📊 Total alerts to generate: {len(TOAST_ALERTS)}")
    print(f"   - Core alerts: 20")
    print(f"   - Sportsbook alerts: 25")
    print(f"   - Strategy alerts: 45")
    print(f"   - Bet action phrases: 11")
    print(f"   - Connector words: 5")
    print(f"   - Pro team names: 84 (NBA: 25, NHL: 27, NFL: 32)")
    print(f"📁 Output directory: frontend/public/alerts/")
    print(f"🎤 Voice: Brian (Authoritative, Professional)")
    print(f"\n💡 These alerts can be chained together for flowing announcements!")
    print("\n" + "-"*80 + "\n")

    success_count = 0
    skip_count = 0
    error_count = 0

    for i, (filename, text) in enumerate(TOAST_ALERTS.items(), 1):
        print(f"[{i}/{len(TOAST_ALERTS)}] ", end="")

        if Path(f"../frontend/public/alerts/{filename}").exists():
            print(f"✓ SKIP: {filename} (already exists)")
            skip_count += 1
            continue

        result = generate_alert_sound(filename, text)
        if result:
            success_count += 1
        else:
            error_count += 1
        print()  # Blank line between files

    print("\n" + "="*80)
    print("📊 GENERATION COMPLETE")
    print("="*80)
    print(f"✅ Successfully generated: {success_count}")
    print(f"⏭️  Skipped (already exist): {skip_count}")
    print(f"❌ Errors: {error_count}")
    print(f"📁 Files saved to: frontend/public/alerts/")
    print("\nYou can now use these audio files in your toast alerts without API calls!")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
