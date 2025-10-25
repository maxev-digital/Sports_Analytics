"""
Generate professional voice alerts for ARB Auto Bettor using Eleven Labs API
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
# Use text-to-speech endpoint (same as what worked for sound effects)
ELEVEN_LABS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"

# Use a professional voice ID (Adam - deep, confident voice)
VOICE_ID = "pNInz6obpgDQGcFmaJgB"  # Adam - default professional voice

# Voice alerts to generate
VOICE_ALERTS = {
    "high_priority.mp3": "High priority arbitrage opportunity!",
    "arbitrage_found.mp3": "Arbitrage opportunity",
    "low_priority.mp3": "Arbitrage found",
    "steam_move.mp3": "Steam move detected",
    "goalie_pull.mp3": "Goalie pulled! Betting opportunity!",
    "line_movement.mp3": "Significant line movement detected",
}

def generate_voice_alert(filename: str, text: str):
    """Generate a voice alert using Eleven Labs API"""
    script_dir = Path(__file__).parent
    output_dir = script_dir / "extension" / "sounds"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename

    if output_path.exists():
        print(f"[SKIP] {filename} already exists")
        return

    print(f"[GENERATING] {filename}: '{text}'")

    url = f"{ELEVEN_LABS_API_URL}/{VOICE_ID}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVEN_LABS_API_KEY
    }

    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.5,
            "use_speaker_boost": True
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"[OK] Generated {filename} ({len(response.content)} bytes)")
        else:
            print(f"[ERROR] {filename}: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"[ERROR] {filename}: {str(e)}")

def main():
    if not ELEVEN_LABS_API_KEY:
        print("[ERROR] ELEVEN_LABS_API_KEY not found in .env file")
        return

    print(f"\n[INFO] Generating {len(VOICE_ALERTS)} voice alerts using Eleven Labs API...\n")

    for filename, text in VOICE_ALERTS.items():
        generate_voice_alert(filename, text)

    print(f"\n[INFO] Voice alert generation complete!")
    print(f"[INFO] Files saved to: extension/sounds/")

if __name__ == "__main__":
    main()
