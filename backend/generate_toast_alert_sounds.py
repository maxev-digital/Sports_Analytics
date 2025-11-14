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
    "draftkings_alert.mp3": "DraftKings opportunity detected!",
    "fanduel_alert.mp3": "FanDuel opportunity detected!",
    "betmgm_alert.mp3": "BetMGM opportunity detected!",
    "betrivers_alert.mp3": "BetRivers opportunity detected!",
    "williamhill_alert.mp3": "William Hill opportunity detected!",
    "fanatics_alert.mp3": "Fanatics opportunity detected!",
    "espnbet_alert.mp3": "ESPN BET opportunity detected!",
    "caesars_alert.mp3": "Caesars opportunity detected!",
    "pointsbet_alert.mp3": "PointsBet opportunity detected!",
    "ballybet_alert.mp3": "Bally Bet opportunity detected!",
    "betonline_alert.mp3": "BetOnline opportunity detected!",
    "bovada_alert.mp3": "Bovada opportunity detected!",
    "mybookie_alert.mp3": "MyBookie opportunity detected!",
    "lowvig_alert.mp3": "LowVig opportunity detected!",
    "betway_alert.mp3": "Betway opportunity detected!",
    "betus_alert.mp3": "BetUS opportunity detected!",
    "superbook_alert.mp3": "SuperBook opportunity detected!",
    "wynnbet_alert.mp3": "WynnBet opportunity detected!",
    "unibet_alert.mp3": "Unibet opportunity detected!",
    "twinspires_alert.mp3": "TwinSpires opportunity detected!",
    "sugarhouse_alert.mp3": "SugarHouse opportunity detected!",
    "betfred_alert.mp3": "Betfred opportunity detected!",
    "hardrock_alert.mp3": "Hard Rock opportunity detected!",
    "sisportsbook_alert.mp3": "S I Sportsbook opportunity detected!",
    "barstool_alert.mp3": "Barstool opportunity detected!",

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
    print("🎙️  TOAST ALERT SOUND GENERATOR - ElevenLabs API")
    print("="*80)
    print(f"\n📊 Total alerts to generate: {len(TOAST_ALERTS)}")
    print(f"   - Core alerts: 20")
    print(f"   - Sportsbook alerts: 25")
    print(f"   - Strategy alerts: 45")
    print(f"📁 Output directory: frontend/public/alerts/")
    print(f"🎤 Voice: Brian (Authoritative, Professional)")
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
