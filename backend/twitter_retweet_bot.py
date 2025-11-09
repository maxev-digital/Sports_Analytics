# twitter_retweet_bot.py - Retweet existing image posts with quote tweets
import tweepy
import requests
import time
from datetime import datetime, timezone

# === CONFIG ===
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAHw85QEAAAAAyykrT8mOAF5XDzSvW5fbQESpsnU%3DdFM8ecC6loeuqF5j1hWpABBfZFM44XPpwFkGEIAjCcF0zXZhH1"
CONSUMER_KEY = "xJDysjZKhx6Hz0WYBxZKIkQyq"
CONSUMER_SECRET = "gEg7V95ZiHNNTjHHYfAGPKIgyTL3YeRioFQM8qHxRhT2eoc2Wd"
ACCESS_TOKEN = "1853837572327227392-bcnHZP9X4vTvvtaoYjFIraLhgjJ4nO"
ACCESS_TOKEN_SECRET = "IB7cbDy3yuvxRbbA9Clbcuc6CKWW0zGA956ohE4EngE6h"

PRICING_URL = "https://max-ev-sports.com/pricing"
BETA_DEADLINE = "2025-11-10T06:00:00Z"

# Your existing tweet IDs with images
TWEET_IDS = [
    "1986219864873107845",  # 1st tweet
    "1986210281622565195",  # 2nd tweet
    "1986207295441702931",  # 3rd tweet
    "1986202714200850670",  # 4th tweet
    "1986201605994152087",  # 5th tweet
]

# Urgency messages to add when quote tweeting
URGENCY_MESSAGES = [
    "{members} beta members already in. Don't miss out before Sunday!",
    "Join {members} smart bettors already using MAX EV Sports. Beta ends Sunday midnight.",
    "{members} members locked in $9.99/mo lifetime. Last chance before price goes up.",
    "Beta offer expires Sunday. {members} members already getting +42% ROI.",
    "Limited time: $9.99/mo beta access. {members} members already winning.",
]

# Init client
client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=CONSUMER_KEY,
    consumer_secret=CONSUMER_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET,
    wait_on_rate_limit=True
)

# === FETCH BETA MEMBER COUNT ===
def get_beta_member_count():
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

# === QUOTE TWEET WITH URGENCY ===
def quote_tweet_existing():
    print("[DEBUG] Starting quote tweet function...", flush=True)
    member_count = get_beta_member_count()
    print(f"[DEBUG] Got member count: {member_count}", flush=True)

    deadline_dt = datetime.fromisoformat(BETA_DEADLINE.replace("Z", "+00:00"))
    now_dt = datetime.now(timezone.utc)
    time_left = deadline_dt - now_dt
    hours_left = int(time_left.total_seconds() // 3600)
    print(f"[DEBUG] Hours left: {hours_left}h", flush=True)

    if time_left.total_seconds() <= 0:
        print("Deadline passed - bot stopping.")
        return False

    # Rotate through your image tweets
    tweet_idx = member_count % len(TWEET_IDS)
    tweet_id = TWEET_IDS[tweet_idx]
    print(f"[DEBUG] Will quote tweet ID: {tweet_id}", flush=True)

    # Rotate through urgency messages
    message_idx = member_count % len(URGENCY_MESSAGES)
    urgency_message = URGENCY_MESSAGES[message_idx].format(members=member_count)

    # Add time urgency
    time_urgency = f"\n\n[URGENT] FINAL HOURS" if hours_left < 6 else f"\n\n[TIME] {hours_left}h left"

    # Full quote tweet text
    quote_text = f"{urgency_message}{time_urgency}\n\n{PRICING_URL} #SportsBetting #EVEdge"
    print(f"[DEBUG] Tweet text ready ({len(quote_text)} chars)", flush=True)

    try:
        print("[DEBUG] Attempting to post to Twitter...", flush=True)
        # Quote tweet (reference your original tweet with image)
        response = client.create_tweet(
            text=quote_text,
            quote_tweet_id=tweet_id
        )
        print(f"[SUCCESS] Quote tweet posted! ID: {response.data['id']} | Members: {member_count} | Hours: {hours_left}h", flush=True)
        return True
    except Exception as e:
        print(f"[ERROR] Tweet error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return False

# === MAIN LOOP: Run Every 6 Hours ===
if __name__ == "__main__":
    import sys
    print("=" * 60, flush=True)
    print("MAX EV RETWEET BOT STARTING...", flush=True)
    print("=" * 60, flush=True)
    print(f"Deadline: {BETA_DEADLINE}", flush=True)
    print(f"Will quote tweet from {len(TWEET_IDS)} existing image tweets", flush=True)
    sys.stdout.flush()

    while True:
        now_dt = datetime.now(timezone.utc)
        deadline_dt = datetime.fromisoformat(BETA_DEADLINE.replace("Z", "+00:00"))

        if now_dt >= deadline_dt:
            member_count = get_beta_member_count()
            final_tweet = f"BETA OFFICIALLY CLOSED! {member_count} members joined - thanks for the rush. MAX EV Sports waitlist now open: {PRICING_URL} #EVBetting"
            client.create_tweet(text=final_tweet)
            print(f"Final tweet posted with {member_count} members - bot shutting down.")
            break

        success = quote_tweet_existing()
        if not success:
            print("Tweet failed, will retry in 6 hours")

        print("Sleeping 6 hours...")
        time.sleep(6 * 3600)  # 6 hours
