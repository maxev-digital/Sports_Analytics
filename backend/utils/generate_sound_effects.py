"""
Eleven Labs Sound Effect Generator
Generates all sound effects needed for Max EV Sports website using Eleven Labs API
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
ELEVEN_LABS_API_URL = "https://api.elevenlabs.io/v1/sound-generation"

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent.parent / "frontend" / "public"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Sound effects to generate with their descriptions
SOUND_EFFECTS = {
    # Dashboard/Home
    "cash-register.mp3": "Cash register cha-ching sound, short and crisp, coins dropping",
    "coins.mp3": "Coins clinking together, small handful, metallic",
    "whoosh.mp3": "Quick whoosh sound, air swoosh, modern UI transition",

    # Alerts
    "alert-bell.mp3": "Notification bell, clear single ding, pleasant tone",
    "notification.mp3": "Subtle notification chime, modern app alert sound",
    "siren.mp3": "Brief alert siren, urgent but not annoying, 1 second",
    "whistle.mp3": "Quick referee whistle, sharp and clear",

    # Props
    "swish.mp3": "Basketball swish through net, clean swoosh",
    "swoosh.mp3": "Quick air swoosh, transition sound, smooth",
    "success.mp3": "Success chime, positive uplifting tone",

    # Analytics
    "data-ping.mp3": "Digital ping sound, data processing beep",
    "calculate.mp3": "Quick calculation sound, digital processing",
    "scan.mp3": "Scanning sound effect, electronic sweep",

    # Odds
    "tick.mp3": "Clock tick, single tick sound, mechanical",
    "click.mp3": "Mouse click sound, button press, crisp",
    "line-move.mp3": "Line movement indicator, rising pitch tone",
    "lock.mp3": "Locking sound, mechanical click, secure",

    # Tools
    "power-up.mp3": "Power up sound, energizing, game-like",
    "success-chime.mp3": "Success chime, completion sound, positive",
    "tool-select.mp3": "Tool selection sound, interface click",

    # Pricing
    "upgrade.mp3": "Level up sound, achievement unlock, ascending tones",
    "level-up.mp3": "Video game level up sound, triumphant",
    "checkout.mp3": "Checkout confirmation sound, purchase complete",
    "unlock.mp3": "Unlock sound effect, achievement unlocked",

    # Strategy Settings
    "toggle-on.mp3": "Toggle switch on, mechanical click upward",
    "toggle-off.mp3": "Toggle switch off, mechanical click downward",
    "save.mp3": "Save confirmation sound, quick positive beep",

    # Multi-Sport
    "sport-switch.mp3": "Sport switching sound, interface transition",
    "buzzer.mp3": "Basketball buzzer, game horn, loud and clear",
    "horn.mp3": "Hockey horn, goal horn, celebratory",
    "whistle-nfl.mp3": "Football referee whistle, sharp blast",

    # Navigation
    "tab-switch.mp3": "Subtle tab switch sound, soft click",
    "dropdown.mp3": "Dropdown menu open, subtle swoosh down",
    "logout.mp3": "Logout sound, closing interface, gentle",

    # Bet Tracking
    "bet-placed.mp3": "Bet placed confirmation, positive beep",
    "win.mp3": "Winning sound, celebration, coins and chimes",
    "victory.mp3": "Victory fanfare, triumphant short melody",
    "loss.mp3": "Loss sound, gentle descending tone, sympathetic",
    "push.mp3": "Push sound, neutral beep, neither positive nor negative",

    # Live Games
    "game-start.mp3": "Game start horn, beginning whistle",
    "buzzer-quarter.mp3": "Quarter end buzzer, period transition",
    "goal.mp3": "Goal celebration horn, brief and exciting",
    "final-whistle.mp3": "Final game whistle, ending sound",

    # Learn/Education
    "page-turn.mp3": "Page turning sound, paper flip",
    "lightbulb.mp3": "Light bulb moment, idea sound, bright ding",
    "graduate.mp3": "Graduation sound, achievement complete, ascending scale",
}


def generate_sound_effect(filename: str, prompt: str, duration: float = 1.0):
    """
    Generate a sound effect using Eleven Labs API

    Args:
        filename: Output filename (e.g., "cash-register.mp3")
        prompt: Description of the sound effect
        duration: Duration in seconds (default 1.0)
    """
    if not ELEVEN_LABS_API_KEY:
        print("[ERROR] ELEVEN_LABS_API_KEY not found in .env file")
        return False

    output_path = OUTPUT_DIR / filename

    # Check if file already exists
    if output_path.exists():
        print(f"[SKIP] {filename} (already exists)")
        return True

    print(f"[GEN] Generating {filename}...")
    print(f"      {prompt}")

    headers = {
        "xi-api-key": ELEVEN_LABS_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "text": prompt,
        "duration_seconds": duration,
        "prompt_influence": 0.5  # Balance between prompt and quality
    }

    try:
        response = requests.post(
            ELEVEN_LABS_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            # Save the audio file
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"[OK] Generated: {filename}\n")
            return True
        else:
            print(f"[ERROR] Status {response.status_code}")
            print(f"        {response.text}\n")
            return False

    except Exception as e:
        print(f"[ERROR] {str(e)}\n")
        return False


def generate_all_sounds():
    """Generate all sound effects defined in SOUND_EFFECTS"""
    print("=" * 60)
    print("MAX EV SPORTS - Sound Effect Generator")
    print("Using Eleven Labs API")
    print("=" * 60)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print(f"Total sounds to generate: {len(SOUND_EFFECTS)}\n")

    if not ELEVEN_LABS_API_KEY:
        print("[ERROR] ELEVEN_LABS_API_KEY not set in .env file")
        print("\nPlease add your API key to backend/.env:")
        print("ELEVEN_LABS_API_KEY=your_api_key_here\n")
        return

    successful = 0
    failed = 0
    skipped = 0

    for filename, prompt in SOUND_EFFECTS.items():
        output_path = OUTPUT_DIR / filename
        if output_path.exists():
            skipped += 1

        result = generate_sound_effect(filename, prompt)
        if result:
            successful += 1
        else:
            failed += 1

    print("=" * 60)
    print("GENERATION COMPLETE")
    print("=" * 60)
    print(f"[OK] Successful: {successful}")
    print(f"[SKIP] Skipped: {skipped}")
    print(f"[FAIL] Failed: {failed}")
    print(f"[DIR] Output location: {OUTPUT_DIR}")
    print("\nAll sound files are ready to use in your React app!")


if __name__ == "__main__":
    generate_all_sounds()
