Got you. You can stay fast without the official X/Twitter API by leaning on self-hosted Nitter + league/team RSS/press feeds, then running a polite poller with de-dupe + backoff. This avoids brittle page scraping, cuts rate-limit risk, and keeps you within safer ToS territory than hammering twitter.com directly.

Below is a complete, practical setup: architecture, config, and drop-in Python you can run today.

⚠️ Quick legal/tech note

Scraping twitter.com/m.twitter.com directly is brittle and may violate X’s ToS.

Safer approach: self-host Nitter (an alternative front-end that exposes per-account RSS), and pair it with official team/league RSS or status pages.

You still get seconds-to-minutes latency, especially for insiders (Schefter/Woj/Shams) and official team accounts.

🏗️ Architecture (simple & robust)

Sources

Insiders via Nitter RSS (self-host): https://your-nitter/AdamSchefter/rss, …/wojespn/rss, etc.

Official team feeds: team site RSS (press releases / game notes) and league injury pages where available.

Poller

Python worker every 15–30s (insiders) and 60–120s (teams), using conditional GET (If-Modified-Since).

Filter & De-dupe

SQLite table stores seen item IDs + timestamps.

Keyword/entity match (player/team dictionaries).

Alert Router

Your webhook (FastAPI), Discord, Slack, or internal queue → your “injury-cascade” strategy.

⚙️ Step 1 — Self-host Nitter (so you don’t ping twitter.com)

docker-compose.yml

version: "3.8"
services:
  redis:
    image: redis:7
    restart: unless-stopped
  nitter:
    image: zedeus/nitter:latest
    restart: unless-stopped
    ports: ["127.0.0.1:8080:8080"]
    environment:
      - NITTER_REDIS_HOST=redis
      - NITTER_ENABLE_RSS=true


Point your poller at http://127.0.0.1:8080/<handle>/rss.

Tip: Put Nginx/Cloudflare in front with a small cache (30–60s) to reduce even your own poll load.

🗂️ Step 2 — Maintain a small config of targets

sources.yaml

insiders:
  - handle: AdamSchefter
  - handle: RapSheet
  - handle: wojespn
  - handle: ShamsCharania
  - handle: ShamsUpdates
  - handle: JeffPassan
  - handle: Ken_Rosenthal
teams:
  nba:
    - name: Boston Celtics
      rss: https://www.nba.com/celtics/rss.xml
    - name: Denver Nuggets
      rss: https://www.nba.com/nuggets/rss.xml
  nfl:
    - name: Kansas City Chiefs
      rss: https://www.chiefs.com/rss/rss-team-news.xml
keywords:
  high_impact: ["inactive", "out", "questionable", "probable", "game-time decision", "lineup", "starting", "scratch"]


You can add more team feeds as you go. For leagues missing good RSS, you can poll their game notes PDFs (use Last-Modified and hash diffs).

🐍 Step 3 — Python poller (Nitter + RSS + de-dupe + alerts)

Requires: pip install feedparser pyyaml requests (and httpx if you prefer)

import time, sqlite3, requests, feedparser, yaml, hashlib, re
from datetime import datetime
from email.utils import parsedate_to_datetime

CONFIG = yaml.safe_load(open("sources.yaml", "r"))
DB = sqlite3.connect("seen.db")
DB.execute("""CREATE TABLE IF NOT EXISTS seen (
  src TEXT, item_id TEXT, ts_seen TEXT, PRIMARY KEY (src, item_id)
)""")
DB.commit()

HEADERS = {"User-Agent": "MaxEV-InjuryBot/1.0"}

def already_seen(src, item_id):
    cur = DB.execute("SELECT 1 FROM seen WHERE src=? AND item_id=?", (src, item_id))
    return cur.fetchone() is not None

def mark_seen(src, item_id):
    DB.execute("INSERT OR IGNORE INTO seen (src, item_id, ts_seen) VALUES (?, ?, ?)",
               (src, item_id, datetime.utcnow().isoformat()))
    DB.commit()

def to_item_id(entry):
    # Prefer GUID; fallback to link hash
    if "id" in entry: return entry.id
    raw = (entry.get("title","") + entry.get("link","")).encode("utf-8")
    return hashlib.sha1(raw).hexdigest()

def fetch_rss(url, etag=None, last_modified=None):
    # Conditional GET to avoid rate limits
    headers = HEADERS.copy()
    if etag: headers["If-None-Match"] = etag
    if last_modified: headers["If-Modified-Since"] = last_modified
    r = requests.get(url, headers=headers, timeout=10)
    if r.status_code == 304:
        return None, etag, last_modified
    r.raise_for_status()
    etag = r.headers.get("ETag", etag)
    last_modified = r.headers.get("Last-Modified", last_modified)
    return r.text, etag, last_modified

def keyword_hit(text, keywords):
    t = text.lower()
    return any(k.lower() in t for k in keywords)

def extract_player_team(text):
    # naive: return capitalized words sequences (you likely have a players/teams dictionary to match)
    cand = re.findall(r"[A-Z][a-z]+(?:\s[A-Z][a-z]+)+", text)
    return cand[:5]

def push_alert(payload):
    # Replace with your internal webhook; for now just print
    print("[ALERT]", payload)

def process_feed(src, url, keywords):
    # In-memory conditional caching (you can persist these if you want)
    if not hasattr(process_feed, "meta"): process_feed.meta = {}
    etag, lm = None, None
    if url in process_feed.meta:
        etag, lm = process_feed.meta[url]

    try:
        xml, etag, lm = fetch_rss(url, etag, lm)
        process_feed.meta[url] = (etag, lm)
        if xml is None:
            return 0
        feed = feedparser.parse(xml)
    except Exception as e:
        print(f"[WARN] {src} fetch error: {e}")
        return 0

    count = 0
    for entry in feed.entries:
        iid = to_item_id(entry)
        if already_seen(src, iid):
            continue
        title = entry.get("title","")
        summary = entry.get("summary","")
        combined = f"{title} :: {summary}"
        if keyword_hit(combined, keywords):
            # Build alert
            pub = entry.get("published")
            ts = None
            try:
                ts = parsedate_to_datetime(pub).isoformat() if pub else datetime.utcnow().isoformat()
            except:
                ts = datetime.utcnow().isoformat()
            payload = {
                "source": src,
                "title": title,
                "link": entry.get("link",""),
                "published": ts,
                "entities_guess": extract_player_team(combined),
                "text": combined[:500]
            }
            push_alert(payload)
            count += 1
        mark_seen(src, iid)
    return count

def loop():
    insiders = CONFIG.get("insiders", [])
    teams = CONFIG.get("teams", {})
    kw = CONFIG.get("keywords", {}).get("high_impact", [])
    insider_urls = [f"http://127.0.0.1:8080/{h['handle']}/rss" for h in insiders]
    team_urls = []
    for league, arr in teams.items():
        team_urls += [t["rss"] for t in arr if t.get("rss")]

    # Staggered polling: insiders faster, teams slower
    t0, t1 = 0, 0
    while True:
        now = time.time()
        if now - t0 > 20:  # insiders ~20s cadence
            for u in insider_urls:
                process_feed(f"nitter:{u.split('/')[-2]}", u, kw)
            t0 = now
        if now - t1 > 60:  # teams ~60s cadence
            for u in team_urls:
                process_feed(f"team:{u}", u, kw)
            t1 = now
        time.sleep(3)

if __name__ == "__main__":
    loop()


What this does

Polls insiders every ~20s, teams every ~60s

Uses ETag/Last-Modified to avoid redownloading unchanged feeds

Filters by high-impact keywords

De-dupes via SQLite

Emits a clean alert payload you can pipe into your alert engine

Plug push_alert() into your alert router (FastAPI endpoint, Kafka topic, or Discord webhook) and you’re live.

🧪 Step 4 — Reduce noise with a player/team dictionary

Create a simple CSV of player_name, team, league and match in extract_player_team() to tag/weight alerts. You can store it in Postgres and load it into memory at startup.

📈 Step 5 — Reliability & rate-limit hygiene

Keep insider list short (Schefter/Woj/Shams + a few beat writers per team).

Cache 30–60s at your Nginx/Cloudflare layer.

Use exponential backoff on 429/5xx; the above code already avoids re-fetching when the feed hasn’t changed.

Add a cooldown in your own alert engine so you don’t spam users when an item is edited.

Variants / Upgrades

Multi-instance Nitter (or multiple IPs) if you scale the insider list.

Team game-notes PDFs: add a tiny PDF fetcher that saves the hash of the latest PDF; when hash changes, parse text (e.g., pdfminer.six) and scan for keywords.

League official injury endpoints (where available) as a truth source to confirm high-impact alerts before pushing to users.