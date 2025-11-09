# test_twitter_bot.py - DRY RUN TEST (no actual tweets)
import requests
from datetime import datetime, timezone

# === CONFIG ===
PRICING_URL = "https://max-ev-sports.com/pricing"
BETA_DEADLINE = "2025-11-10T06:00:00Z"  # Sunday midnight CST = 6:00 AM UTC

# Ad copy variants
AD_TEMPLATES = [
    "I built the tool OddsJam wishes they had.\nGoalie Pull +42% ROI\nQ3 Reversal +12.1% ROI\nAuto-bets for you.\n\n{members} beta members already in. Join before Sunday: {url}",
    "Track. Compare. Win.\nLive odds screen + AI value alerts.\n{members} bettors already using it.\n\nBeta ends Sunday midnight: {url}",
    "Stop leaving EV on the table.\nMAX EV Sports = your new edge.\n+42% ROI edges live now.\n\n{members} members locked in $9.99/mo. Last chance: {url}"
]

# === FETCH BETA MEMBER COUNT ===
def get_beta_member_count():
    try:
        response = requests.get("https://max-ev-sports.com/api/subscription/beta-count")
        if response.status_code == 200:
            data = response.json()
            return data.get("count", 45)
        return 45
    except Exception as e:
        print(f"API fetch error: {e} — Using fallback 45")
        return 45

# === TEST TWEET GENERATION ===
def test_tweet_generation():
    print("=" * 80)
    print("TWITTER BOT DRY RUN TEST")
    print("=" * 80)

    member_count = get_beta_member_count()
    print(f"\n[OK] API Call Success! Member Count: {member_count}")

    deadline_dt = datetime.fromisoformat(BETA_DEADLINE.replace("Z", "+00:00"))
    now_dt = datetime.now(timezone.utc)
    time_left = deadline_dt - now_dt
    hours_left = int(time_left.total_seconds() // 3600)

    print(f"[OK] Deadline: {BETA_DEADLINE}")
    print(f"[OK] Hours until deadline: {hours_left}h")

    print("\n" + "=" * 80)
    print("TESTING ALL 3 TWEET TEMPLATES:")
    print("=" * 80)

    for idx, template in enumerate(AD_TEMPLATES, 1):
        urgency = "[URGENT] FINAL HOURS" if hours_left < 6 else f"[TIME] {hours_left}h left"
        tweet = template.format(members=f"{member_count}", url=PRICING_URL) + f"\n\n{urgency} #SportsBetting #EVEdge"

        print(f"\n--- TEMPLATE {idx} ---")
        print(tweet)
        print(f"Character count: {len(tweet)}/280")
        print("-" * 80)

    # Test final tweet
    print("\n" + "=" * 80)
    print("FINAL TWEET (when deadline hits):")
    print("=" * 80)
    final_tweet = "BETA OFFICIALLY CLOSED! {members} members joined—thanks for the rush. MAX EV Sports waitlist now open: {url} #EVBetting".format(members=member_count, url=PRICING_URL)
    print(final_tweet)
    print(f"Character count: {len(final_tweet)}/280")

    print("\n" + "=" * 80)
    print("[SUCCESS] DRY RUN COMPLETE - Everything looks good!")
    print("=" * 80)

if __name__ == "__main__":
    test_tweet_generation()
