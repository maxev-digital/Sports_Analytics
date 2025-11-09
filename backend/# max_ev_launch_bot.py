# max_ev_launch_bot.py
import tweepy
import requests
import time
from datetime import datetime, timezone

# === CONFIG ===
# Paste your existing creds here
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAHw85QEAAAAAyykrT8mOAF5XDzSvW5fbQESpsnU%3DdFM8ecC6loeuqF5j1hWpABBfZFM44XPpwFkGEIAjCcF0zXZhH1"  # For app-only if needed
CONSUMER_KEY = "xJDysjZKhx6Hz0WYBxZKIkQyq"
CONSUMER_SECRET = "gEg7V95ZiHNNTjHHYfAGPKIgyTL3YeRioFQM8qHxRhT2eoc2Wd"
ACCESS_TOKEN = "1853837572327227392-a8mf6PscUHjSV3NH7XvUk29BPGIZlu"
ACCESS_TOKEN_SECRET = "Nr2YD00ENyuvv2diSrpyrSMhLZDbrz9FdoVELJQqPUzFh"

PRICING_URL = "https://max-ev-sports.com/pricing"
BETA_DEADLINE = "2025-11-10T06:00:00Z"  # Sunday midnight CST = 6:00 AM UTC

# Ad copy variants (rotate for freshness) - emphasize momentum/growth
AD_TEMPLATES = [
    "I built the tool OddsJam wishes they had.\nGoalie Pull +42% ROI\nQ3 Reversal +12.1% ROI\nAuto-bets for you.\n\n{members} beta members already in. Join before Sunday: {url}",
    "Track. Compare. Win.\nLive odds screen + AI value alerts.\n{members} bettors already using it.\n\nBeta ends Sunday midnight: {url}",
    "Stop leaving EV on the table.\nMAX EV Sports = your new edge.\n+42% ROI edges live now.\n\n{members} members locked in $9.99/mo. Last chance: {url}"
]

# Init client with user context for posting (free tier OK)
client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=CONSUMER_KEY,
    consumer_secret=CONSUMER_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET,
    wait_on_rate_limit=True
)

# === FETCH BETA MEMBER COUNT (Your Real API Endpoint) ===
def get_beta_member_count():
    try:
        response = requests.get("https://max-ev-sports.com/api/subscription/beta-count")
        if response.status_code == 200:
            data = response.json()
            return data.get("count", 45)  # Fallback to 45 if no count
        return 45
    except Exception as e:
        print(f"API fetch error: {e} — Using fallback 45")
        return 45

# === POST COUNTDOWN TWEET ===
def post_countdown_tweet():
    member_count = get_beta_member_count()
    deadline_dt = datetime.fromisoformat(BETA_DEADLINE.replace("Z", "+00:00"))
    now_dt = datetime.now(timezone.utc)
    time_left = deadline_dt - now_dt

    if time_left.total_seconds() <= 0:
        tweet = "BETA CLOSED! {members} members joined - full launch incoming. Join waitlist: {url} #EVBetting".format(members=member_count, url=PRICING_URL)
        hours_left = 0
    else:
        hours_left = int(time_left.total_seconds() // 3600)
        urgency = "[URGENT] FINAL HOURS" if hours_left < 6 else f"[TIME] {hours_left}h left"
        template_idx = member_count % len(AD_TEMPLATES)  # Rotate based on member count
        tweet = AD_TEMPLATES[template_idx].format(members=f"{member_count}", url=PRICING_URL) + f"\n\n{urgency} #SportsBetting #EVEdge"

    try:
        response = client.create_tweet(text=tweet)
        print(f"[{datetime.now()}] Tweet posted! ID: {response.data['id']} | Members: {member_count} | Hours left: {hours_left}")
    except Exception as e:
        print(f"Tweet error: {e} — Check creds/limits")

# === MAIN LOOP: Run Every 6 Hours Till Deadline ===
if __name__ == "__main__":
    print("MAX EV Bot starting... Deadline: " + BETA_DEADLINE)
    while True:
        now_dt = datetime.now(timezone.utc)
        deadline_dt = datetime.fromisoformat(BETA_DEADLINE.replace("Z", "+00:00"))
        if now_dt >= deadline_dt:
            member_count = get_beta_member_count()
            final_tweet = "BETA OFFICIALLY CLOSED! {members} members joined - thanks for the rush. MAX EV Sports waitlist now open: {url} #EVBetting".format(members=member_count, url=PRICING_URL)
            client.create_tweet(text=final_tweet)
            print(f"Final tweet posted with {member_count} members—bot shutting down.")
            break
        post_countdown_tweet()
        print("Sleeping 6 hours...")
        time.sleep(6 * 3600)  # 21600 seconds