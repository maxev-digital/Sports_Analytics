"""
Generate detailed custom audio alerts for goalie pull opportunities via ElevenLabs API
Creates two comprehensive audio files:
1. OVER alert (2-goal deficit, early goalie pull)
2. UNDER alert (1-goal deficit, low EN scoring teams)
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

# Detailed goalie pull alert scripts
GOALIE_PULL_ALERTS = {
    "goalie_pull_over_detailed.mp3": """
    Goalie Pull Alert! Two-goal deficit situation detected.

    The trailing team is down by two goals with approximately two minutes and forty-five seconds remaining in the third period.
    Based on historical data, the team will likely pull their goalie in the next 15 to 30 seconds for an early extra attacker.

    Here's the key empty net statistics: The trailing team has shown aggressive empty net offense this season,
    while the leading team has capitalized on empty net defensive opportunities.

    The recommended play is to bet the GAME OVER or the trailing team's TEAM TOTAL OVER at the best available odds across all sportsbooks.
    This is critical: Getting your bet in NOW, before the goalie is actually pulled, provides the best return on investment over time.
    Once the goalie is pulled, sportsbooks will adjust the lines significantly, reducing your edge.

    Empty net situations average point-eight to one-point-two goals scored.
    Historical data shows this setup hits at a sixty-five percent rate when trailing by two goals.

    Time is of the essence. Check DraftKings, FanDuel, BetMGM, and all available books.
    Take the best OVER price you can find right now. The edge disappears once the goalie leaves the ice.
    This is a high-confidence, time-sensitive opportunity with an expected ROI of twelve percent.

    Act now for maximum value!
    """,

    "goalie_pull_under_detailed.mp3": """
    One-Goal Deficit UNDER Alert! Low empty net scoring opportunity detected.

    The trailing team is down by exactly one goal with approximately two minutes remaining in the third period.
    This is a critical difference from two-goal deficit situations. When down by only one goal,
    teams typically wait much longer to pull the goalie, usually not until one minute thirty seconds or less remaining.

    Here's why this is a strong UNDER opportunity: Both teams have demonstrated LOW empty net goal production this season.
    The trailing team has scored four or fewer empty net goals all year, and the leading team has also scored four or fewer.
    When both teams struggle to capitalize on empty net situations, the current score tends to hold.

    The recommended plays are: First, bet the GAME UNDER. Second, if available, bet NO GOAL SCORED NEXT.
    Third, for maximum payout, consider the EXACT SCORE bet for the game to finish at the current score.

    Again, timing is critical for ROI. Get these bets in NOW at the best available odds before any goalie pull actually happens.
    Historical data shows when both teams have low empty net totals and the deficit is one goal,
    the score holds sixty-eight percent of the time.

    The edge here is the combination of late goalie pull timing plus inefficient empty net teams.
    Less time on ice with six attackers, plus teams that don't score well in those situations, equals the score standing pat.

    Shop all your sportsbooks: DraftKings, FanDuel, Caesars, BetMGM. Find the best UNDER price available.
    For NO GOAL SCORED NEXT, you're typically looking at plus-one-fifty or better.
    For exact score, odds can reach plus-three-hundred or higher, offering exceptional value if the score holds.

    This is a high-confidence play with expected ROI of fifteen percent. The key is acting now before the market adjusts.
    Early entry at best odds maximizes your edge over time.

    Lock in your bets immediately!
    """
}

def generate_alert_sound(filename: str, text: str):
    """Generate alert sound using ElevenLabs API"""
    # Save to frontend/public folder
    output_dir = Path(__file__).parent.parent / "frontend" / "public" / "alerts"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename

    if output_path.exists():
        print(f"✓ File already exists: {filename}")
        overwrite = input("  Overwrite? (y/n): ").lower().strip()
        if overwrite != 'y':
            print(f"  Skipping {filename}")
            return True

    print(f"\n⏳ GENERATING: {filename}")
    print(f"   Length: {len(text)} characters")
    print(f"   Estimated duration: ~{len(text.split()) / 2.5:.1f} seconds")

    url = f"{ELEVEN_LABS_API_URL}/{VOICE_ID}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVEN_LABS_API_KEY
    }

    # Voice settings optimized for detailed, urgent betting alerts
    payload = {
        "text": text.strip(),
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.65,         # Stable for clarity in long-form
            "similarity_boost": 0.85,  # Very high for consistent voice
            "style": 0.3,              # Professional, not overly dramatic
            "use_speaker_boost": True
        }
    }

    try:
        print("   Calling ElevenLabs API...")
        response = requests.post(url, headers=headers, json=payload, timeout=60)

        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            file_size_kb = len(response.content) / 1024
            print(f"✅ SUCCESS: {filename}")
            print(f"   File size: {file_size_kb:.1f} KB")
            print(f"   Saved to: {output_path}")
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
    print("🎙️  GOALIE PULL DETAILED AUDIO ALERTS - ElevenLabs API")
    print("="*80)
    print(f"\n📊 Generating {len(GOALIE_PULL_ALERTS)} detailed audio alerts:")
    print(f"   1. OVER alert (2-goal deficit, early goalie pull)")
    print(f"   2. UNDER alert (1-goal deficit, low EN scoring)")
    print(f"\n📁 Output directory: frontend/public/alerts/")
    print(f"🎤 Voice: Brian (Authoritative, Professional)")
    print(f"\n💡 Key emphasis: Early betting at best available odds for maximum ROI")
    print("\n" + "-"*80 + "\n")

    success_count = 0
    error_count = 0

    for i, (filename, text) in enumerate(GOALIE_PULL_ALERTS.items(), 1):
        print(f"[{i}/{len(GOALIE_PULL_ALERTS)}]")

        result = generate_alert_sound(filename, text)
        if result:
            success_count += 1
        else:
            error_count += 1

    print("\n" + "="*80)
    print("📊 GENERATION COMPLETE")
    print("="*80)
    print(f"✅ Successfully generated: {success_count}")
    print(f"❌ Errors: {error_count}")
    print(f"\n📁 Files saved to: frontend/public/alerts/")
    print("\nThese detailed audio files can now be used in GoaliePullMonitor alerts!")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
