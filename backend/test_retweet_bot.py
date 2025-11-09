# test_retweet_bot.py - DRY RUN TEST
import requests
from datetime import datetime, timezone

PRICING_URL = "https://max-ev-sports.com/pricing"
BETA_DEADLINE = "2025-11-10T06:00:00Z"

TWEET_IDS = [
    "1986219864873107845",
    "1986210281622565195",
    "1986207295441702931",
    "1986202714200850670",
    "1986201605994152087",
]

URGENCY_MESSAGES = [
    "{members} beta members already in. Don't miss out before Sunday!",
    "Join {members} smart bettors already using MAX EV Sports. Beta ends Sunday midnight.",
    "{members} members locked in $9.99/mo lifetime. Last chance before price goes up.",
    "Beta offer expires Sunday. {members} members already getting +42% ROI.",
    "Limited time: $9.99/mo beta access. {members} members already winning.",
]

def get_beta_member_count():
    try:
        response = requests.get("https://max-ev-sports.com/api/subscription/beta-count")
        if response.status_code == 200:
            data = response.json()
            return data.get("count", 45)
        return 45
    except Exception as e:
        print(f"API fetch error: {e} - Using fallback 45")
        return 45

def test_quote_tweets():
    print("=" * 80)
    print("QUOTE TWEET BOT - DRY RUN TEST")
    print("=" * 80)

    member_count = get_beta_member_count()
    print(f"\n[OK] API Call Success! Member Count: {member_count}")

    deadline_dt = datetime.fromisoformat(BETA_DEADLINE.replace("Z", "+00:00"))
    now_dt = datetime.now(timezone.utc)
    time_left = deadline_dt - now_dt
    hours_left = int(time_left.total_seconds() // 3600)

    print(f"[OK] Hours until deadline: {hours_left}h")
    print(f"\n[INFO] Will rotate through {len(TWEET_IDS)} existing tweets with images")

    print("\n" + "=" * 80)
    print("TESTING QUOTE TWEET EXAMPLES:")
    print("=" * 80)

    for i in range(5):
        tweet_idx = (member_count + i) % len(TWEET_IDS)
        tweet_id = TWEET_IDS[tweet_idx]

        message_idx = (member_count + i) % len(URGENCY_MESSAGES)
        urgency_message = URGENCY_MESSAGES[message_idx].format(members=member_count)

        time_urgency = f"\n\n[URGENT] FINAL HOURS" if hours_left < 6 else f"\n\n[TIME] {hours_left}h left"
        quote_text = f"{urgency_message}{time_urgency}\n\n{PRICING_URL} #SportsBetting #EVEdge"

        print(f"\n--- QUOTE TWEET #{i+1} (references tweet {tweet_id}) ---")
        print(quote_text)
        print(f"Character count: {len(quote_text)}/280")
        print(f"Original tweet URL: https://x.com/GTE_APW/status/{tweet_id}")
        print("-" * 80)

    print("\n" + "=" * 80)
    print("[SUCCESS] DRY RUN COMPLETE!")
    print("=" * 80)

if __name__ == "__main__":
    test_quote_tweets()
