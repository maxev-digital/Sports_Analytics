# twitter_auto_poster.py - Auto-post fresh tweets with rotating images
import tweepy
import requests
import time
import os
import glob
from datetime import datetime, timezone

# === CONFIG ===
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAHw85QEAAAAAyykrT8mOAF5XDzSvW5fbQESpsnU%3DdFM8ecC6loeuqF5j1hWpABBfZFM44XPpwFkGEIAjCcF0zXZhH1"
CONSUMER_KEY = "xJDysjZKhx6Hz0WYBxZKIkQyq"
CONSUMER_SECRET = "gEg7V95ZiHNNTjHHYfAGPKIgyTL3YeRioFQM8qHxRhT2eoc2Wd"
ACCESS_TOKEN = "1853837572327227392-bcnHZP9X4vTvvtaoYjFIraLhgjJ4nO"
ACCESS_TOKEN_SECRET = "IB7cbDy3yuvxRbbA9Clbcuc6CKWW0zGA956ohE4EngE6h"

PRICING_URL = "https://max-ev-sports.com/pricing"
BETA_DEADLINE = "2025-11-10T06:00:00Z"

# Path to images folder (add/update images here)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_FOLDER = os.path.join(SCRIPT_DIR, "twitter_images")

# Tweet templates - HONEST, NO FAKE MEMBER COUNTS
TWEET_TEMPLATES = [
    {
        "text": "🚀 BETA LAUNCH: Lock in $9.99/mo lifetime pricing.\n\nMAX EV Sports auto-detects +EV opportunities across NHL, NBA, NFL & NCAA.\n\nLimited time offer ends Sunday.\n\n{pricing_url}\n#SportsBetting #EVEdge",
        "tags": ["sports", "analytics", "general"]
    },
    {
        "text": "⚡ Built the tool OddsJam wishes they had.\n\nLive odds tracking • Strategy alerts • Auto-bet integration\n\nBeta special: $9.99/mo expires Sunday.\n\n{pricing_url}\n#BettingTools #EV",
        "tags": ["features", "analytics", "general"]
    },
    {
        "text": "📊 Goalie Pull strategy showing +42% ROI in backtests.\n\nReal-time alerts. Live odds from 60+ books. Proven strategies.\n\nBeta launch: $9.99/mo ends Sunday.\n\n{pricing_url}\n#NHL #SportsBetting",
        "tags": ["strategies", "analytics", "sports"]
    },
    {
        "text": "🎯 Lock in lifetime pricing before Sunday.\n\nGet instant alerts for:\n• Quarter Reversal patterns\n• Arbitrage opportunities\n• Sharp money movement\n\n$9.99/mo beta offer.\n\n{pricing_url}\n#BettingEdge #EV",
        "tags": ["strategies", "features", "general"]
    },
    {
        "text": "🔥 Price goes up after Sunday. Lock in $9.99/mo now.\n\nMAX EV Sports tracks:\n✅ Live games (NHL, NBA, NFL, NCAA)\n✅ +EV strategy alerts\n✅ Auto-betting integration\n\n{pricing_url}\n#SportsBetting",
        "tags": ["sports", "features", "general"]
    },
    {
        "text": "⏰ LIMITED TIME: Beta launch pricing ends Sunday.\n\nInstant alerts when:\n• NHL goalies get pulled (+42% ROI)\n• NBA quarters reverse (+12% ROI)\n• Arbitrage appears\n\n$9.99/mo.\n\n{pricing_url}",
        "tags": ["strategies", "sports", "general"]
    },
    {
        "text": "💰 Early adopter special: $9.99/mo lifetime.\n\nMAX EV Sports includes:\n• NHL Goalie Pull alerts\n• NBA Quarter Reversal detection\n• Real-time middle finder\n• 60+ sportsbooks\n\nEnds Sunday.\n\n{pricing_url}",
        "tags": ["strategies", "features", "general"]
    },
    {
        "text": "📈 Desktop app + Chrome extension + Mobile ready.\n\nLive +EV alerts across all major sports.\n\nBeta pricing ($9.99/mo) expires Sunday midnight.\n\nBe an early adopter.\n\n{pricing_url}\n#SportsBetting",
        "tags": ["features", "general"]
    },
    {
        "text": "🏒 NHL Goalie Pull strategy: +42% ROI (backtested)\n🏀 NBA Quarter Reversal: +12% ROI\n🎲 Arbitrage detector: Real-time\n\nAll for $9.99/mo.\n\nBeta ends Sunday.\n\n{pricing_url}\n#EV #BettingEdge",
        "tags": ["strategies", "sports", "general"]
    },
    {
        "text": "What OddsJam doesn't tell you:\n\nTheir tool costs $129/mo.\nMine costs $9.99/mo (beta).\n\nSame data. Better alerts. Desktop + extension.\n\nLaunching Sunday.\n\n{pricing_url}\n#SportsBetting",
        "tags": ["competitive", "pricing", "general"]
    }
]

# Init Tweepy clients (need both v2 Client and v1 API for media upload)
client_v2 = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=CONSUMER_KEY,
    consumer_secret=CONSUMER_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET,
    wait_on_rate_limit=True
)

# V1 API needed for media upload
auth = tweepy.OAuth1UserHandler(
    consumer_key=CONSUMER_KEY,
    consumer_secret=CONSUMER_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET
)
api_v1 = tweepy.API(auth)


def get_beta_member_count():
    """Fetch current beta member count from API"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get("https://max-ev-sports.com/api/subscription/beta-count", headers=headers, timeout=5)
        print(f"[DEBUG] API Response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            count = data.get("count", 45)
            print(f"[DEBUG] Member count from API: {count}")
            return count
        print(f"[DEBUG] API returned {response.status_code}, using fallback")
        return 45
    except Exception as e:
        print(f"[DEBUG] API fetch error: {e} - Using fallback 45")
        return 45


def get_available_images():
    """Get all images from twitter_images folder"""
    if not os.path.exists(IMAGES_FOLDER):
        print(f"[WARNING] Images folder not found: {IMAGES_FOLDER}")
        return []

    # Get all jpg, jpeg, png files
    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']:
        image_files.extend(glob.glob(os.path.join(IMAGES_FOLDER, ext)))

    image_files.sort()  # Keep consistent order
    print(f"[DEBUG] Found {len(image_files)} images in {IMAGES_FOLDER}")
    return image_files


def post_tweet_with_image():
    """Post a fresh tweet with an image"""
    print("[DEBUG] Starting tweet post function...", flush=True)

    # Calculate time left
    deadline_dt = datetime.fromisoformat(BETA_DEADLINE.replace("Z", "+00:00"))
    now_dt = datetime.now(timezone.utc)
    time_left = deadline_dt - now_dt
    hours_left = int(time_left.total_seconds() // 3600)
    print(f"[DEBUG] Hours left: {hours_left}h", flush=True)

    if time_left.total_seconds() <= 0:
        print("Deadline passed - bot stopping.")
        return False

    # Select tweet template (rotate based on time)
    import random
    random.seed(int(now_dt.timestamp() // 3600))  # Changes every hour
    template_idx = random.randint(0, len(TWEET_TEMPLATES) - 1)
    template = TWEET_TEMPLATES[template_idx]

    # Format tweet text
    tweet_text = template["text"].format(
        pricing_url=PRICING_URL
    )

    # Add urgency if < 24 hours left
    if hours_left < 24:
        tweet_text += f"\n\n⚠️ FINAL {hours_left} HOURS"

    print(f"[DEBUG] Tweet text ready ({len(tweet_text)} chars)", flush=True)

    # Get available images
    images = get_available_images()

    if not images:
        print("[WARNING] No images found - posting text-only tweet")
        media_ids = None
    else:
        # Select image (rotate independently based on timestamp)
        # This ensures different image even if template is same
        image_idx = int(now_dt.timestamp() // (6 * 3600)) % len(images)  # Changes every 6 hours
        image_path = images[image_idx]
        print(f"[DEBUG] Selected image: {os.path.basename(image_path)}", flush=True)

        try:
            # Upload media using v1 API
            print("[DEBUG] Uploading image...", flush=True)
            media = api_v1.media_upload(filename=image_path)
            media_ids = [media.media_id]
            print(f"[DEBUG] Image uploaded! Media ID: {media.media_id}", flush=True)
        except Exception as e:
            print(f"[ERROR] Image upload failed: {e}", flush=True)
            media_ids = None

    # Post tweet
    try:
        print("[DEBUG] Attempting to post tweet...", flush=True)
        response = client_v2.create_tweet(
            text=tweet_text,
            media_ids=media_ids
        )
        tweet_id = response.data['id']
        tweet_url = f"https://x.com/GTE_APW/status/{tweet_id}"
        print(f"[SUCCESS] Tweet posted!", flush=True)
        print(f"  Tweet ID: {tweet_id}", flush=True)
        print(f"  URL: {tweet_url}", flush=True)
        print(f"  Hours left: {hours_left}h", flush=True)
        if media_ids:
            print(f"  Image: {os.path.basename(images[image_idx])}", flush=True)
        return True
    except Exception as e:
        print(f"[ERROR] Tweet posting failed: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return False


def post_final_tweet():
    """Post final 'beta closed' tweet"""
    final_text = f"🎉 BETA LAUNCH COMPLETE!\n\nEarly adopter pricing ($9.99/mo) has ended.\n\nWaitlist now open for next pricing tier.\n\nThanks to everyone who joined the beta!\n\n{PRICING_URL}\n\n#SportsBetting #BetaLaunch"

    try:
        response = client_v2.create_tweet(text=final_text)
        print(f"[SUCCESS] Final tweet posted!")
        return True
    except Exception as e:
        print(f"[ERROR] Final tweet failed: {e}")
        return False


# === MAIN LOOP ===
if __name__ == "__main__":
    import sys
    print("=" * 60, flush=True)
    print("MAX EV SPORTS - TWITTER AUTO POSTER", flush=True)
    print("=" * 60, flush=True)
    print(f"Deadline: {BETA_DEADLINE}", flush=True)
    print(f"Images folder: {IMAGES_FOLDER}", flush=True)
    print(f"Tweet templates: {len(TWEET_TEMPLATES)}", flush=True)

    # Check images
    images = get_available_images()
    if images:
        print(f"Available images: {len(images)}", flush=True)
        for img in images:
            print(f"  - {os.path.basename(img)}", flush=True)
    else:
        print("[WARNING] No images found - will post text-only tweets", flush=True)

    print("=" * 60, flush=True)
    sys.stdout.flush()

    # Main loop
    while True:
        now_dt = datetime.now(timezone.utc)
        deadline_dt = datetime.fromisoformat(BETA_DEADLINE.replace("Z", "+00:00"))

        # Check if deadline passed
        if now_dt >= deadline_dt:
            print("\n[INFO] Deadline reached - posting final tweet...", flush=True)
            post_final_tweet()
            print("[INFO] Bot shutting down. Beta campaign complete!", flush=True)
            break

        # Post tweet
        success = post_tweet_with_image()
        if not success:
            print("[WARNING] Tweet failed, will retry in 6 hours", flush=True)

        # Sleep for 6 hours
        from datetime import timedelta
        print(f"\n[INFO] Sleeping 6 hours until next post...", flush=True)
        print(f"[INFO] Next post at: {datetime.now(timezone.utc) + timedelta(hours=6)}", flush=True)
        print("-" * 60, flush=True)
        time.sleep(6 * 3600)
