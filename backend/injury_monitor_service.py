"""
Standalone Injury Monitor Service (Nitter RSS + Team Feeds)

This service runs SEPARATELY from main.py to prevent Twitter API issues
from crashing the main site.

Features:
- Polls Nitter RSS feeds for top reporters (Woj, Shams, Schefter, etc.)
- Monitors team RSS feeds for official updates
- Uses SQLite for deduplication
- Writes alerts to shared JSON file that main.py can read
- If this crashes, main.py stays up!

Usage:
    python injury_monitor_service.py

Requirements:
    pip install feedparser pyyaml requests
"""

import time
import sqlite3
import requests
import feedparser
import yaml
import hashlib
import re
import json
import logging
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "injury_sources.yaml"
DB_FILE = BASE_DIR / "data" / "injury_alerts.db"
ALERTS_FILE = BASE_DIR / "data" / "injury_alerts.json"

# Ensure data directory exists
(BASE_DIR / "data").mkdir(exist_ok=True)

# Load configuration
try:
    with open(CONFIG_FILE, 'r') as f:
        CONFIG = yaml.safe_load(f)
    logger.info(f"✅ Loaded config from {CONFIG_FILE}")
except Exception as e:
    logger.error(f"❌ Failed to load config: {e}")
    raise

# Initialize SQLite database for deduplication
DB = sqlite3.connect(DB_FILE, check_same_thread=False)
DB.execute("""CREATE TABLE IF NOT EXISTS seen (
  src TEXT,
  item_id TEXT,
  ts_seen TEXT,
  PRIMARY KEY (src, item_id)
)""")
DB.commit()
logger.info(f"✅ Database initialized at {DB_FILE}")

# Request headers
HEADERS = {"User-Agent": "MaxEV-InjuryBot/2.0"}


def already_seen(src: str, item_id: str) -> bool:
    """Check if we've already processed this item"""
    cur = DB.execute("SELECT 1 FROM seen WHERE src=? AND item_id=?", (src, item_id))
    return cur.fetchone() is not None


def mark_seen(src: str, item_id: str):
    """Mark an item as seen"""
    DB.execute(
        "INSERT OR IGNORE INTO seen (src, item_id, ts_seen) VALUES (?, ?, ?)",
        (src, item_id, datetime.utcnow().isoformat())
    )
    DB.commit()


def to_item_id(entry: Dict) -> str:
    """Generate unique ID for RSS entry"""
    if "id" in entry:
        return entry.id
    # Fallback: hash title + link
    raw = (entry.get("title", "") + entry.get("link", "")).encode("utf-8")
    return hashlib.sha1(raw).hexdigest()


def fetch_rss(url: str, etag: Optional[str] = None, last_modified: Optional[str] = None):
    """
    Fetch RSS feed with conditional GET to avoid unnecessary downloads
    Returns: (content, etag, last_modified)
    """
    headers = HEADERS.copy()
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified

    try:
        r = requests.get(url, headers=headers, timeout=10)

        # 304 = Not Modified
        if r.status_code == 304:
            return None, etag, last_modified

        r.raise_for_status()

        etag = r.headers.get("ETag", etag)
        last_modified = r.headers.get("Last-Modified", last_modified)

        return r.text, etag, last_modified

    except Exception as e:
        logger.warning(f"⚠️  Error fetching {url}: {e}")
        return None, etag, last_modified


def keyword_hit(text: str, keywords: List[str]) -> bool:
    """Check if text contains any injury keywords"""
    t = text.lower()
    return any(k.lower() in t for k in keywords)


def extract_player_team(text: str) -> List[str]:
    """
    Extract potential player/team names (capitalized sequences)
    Simple heuristic - ideally match against known player/team database
    """
    # Find sequences like "LeBron James" or "Boston Celtics"
    candidates = re.findall(r"[A-Z][a-z]+(?:\s[A-Z][a-z]+)+", text)
    return candidates[:5]  # Return top 5 candidates


def calculate_confidence(text: str, reporter_tier: int) -> float:
    """Calculate alert confidence based on keywords and reporter tier"""
    t = text.lower()

    # Base confidence from reporter tier
    tier_confidence = {1: 0.95, 2: 0.85, 3: 0.75}
    base = tier_confidence.get(reporter_tier, 0.60)

    # Boost for clear status keywords
    if "ruled out" in t or "out for" in t:
        return min(base * 1.05, 1.0)
    elif "doubtful" in t:
        return base * 0.95
    elif "questionable" in t:
        return base * 0.85

    return base


def save_alert(alert: Dict):
    """
    Save alert to shared JSON file that main.py can read
    Keeps only last 100 alerts to prevent file bloat
    """
    try:
        # Load existing alerts
        if ALERTS_FILE.exists():
            with open(ALERTS_FILE, 'r') as f:
                alerts = json.load(f)
        else:
            alerts = []

        # Add new alert
        alerts.insert(0, alert)

        # Keep only last 100 alerts
        alerts = alerts[:100]

        # Save back
        with open(ALERTS_FILE, 'w') as f:
            json.dump(alerts, f, indent=2)

        logger.info(f"💾 Saved alert to {ALERTS_FILE}")

    except Exception as e:
        logger.error(f"❌ Error saving alert: {e}")


def push_alert(payload: Dict):
    """
    Process and store an injury alert
    This is where you could also send to Discord, Slack, etc.
    """
    logger.info(f"🚨 INJURY ALERT: {payload['source']}")
    logger.info(f"   📰 {payload['title']}")
    logger.info(f"   👤 Entities: {', '.join(payload['entities_guess'])}")
    logger.info(f"   🔗 {payload['link']}")
    logger.info(f"   ⏰ {payload['published']}")
    logger.info(f"   📊 Confidence: {payload['confidence']:.0%}")

    # Save to shared storage
    save_alert(payload)


def process_feed(src: str, url: str, keywords: List[str], reporter_tier: int = 1):
    """
    Process an RSS feed and extract injury alerts

    Args:
        src: Source identifier (e.g., "nitter:wojespn")
        url: RSS feed URL
        keywords: List of injury keywords to filter
        reporter_tier: Tier of reporter (1=highest, 3=lowest)

    Returns:
        Number of new alerts found
    """
    # In-memory cache for conditional GET (ETag/Last-Modified)
    if not hasattr(process_feed, "meta"):
        process_feed.meta = {}

    etag, lm = None, None
    if url in process_feed.meta:
        etag, lm = process_feed.meta[url]

    # Fetch RSS
    xml, etag, lm = fetch_rss(url, etag, lm)
    process_feed.meta[url] = (etag, lm)

    if xml is None:
        return 0  # Not modified

    # Parse feed
    try:
        feed = feedparser.parse(xml)
    except Exception as e:
        logger.warning(f"⚠️  Error parsing feed {src}: {e}")
        return 0

    count = 0
    for entry in feed.entries:
        iid = to_item_id(entry)

        # Skip if already processed
        if already_seen(src, iid):
            continue

        # Extract text
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        combined = f"{title} :: {summary}"

        # Check for injury keywords
        if keyword_hit(combined, keywords):
            # Extract timestamp
            pub = entry.get("published")
            try:
                ts = parsedate_to_datetime(pub).isoformat() if pub else datetime.utcnow().isoformat()
            except:
                ts = datetime.utcnow().isoformat()

            # Calculate confidence
            confidence = calculate_confidence(combined, reporter_tier)

            # Build alert payload
            payload = {
                "source": src,
                "title": title,
                "link": entry.get("link", ""),
                "published": ts,
                "entities_guess": extract_player_team(combined),
                "text": combined[:500],
                "confidence": confidence
            }

            # Push alert
            push_alert(payload)
            count += 1

        # Mark as seen (even if not an injury alert)
        mark_seen(src, iid)

    return count


def get_nitter_url(handle: str) -> str:
    """Get Nitter RSS URL for a Twitter handle (using public instance)"""
    # Using nitter.net - main public instance
    return f"https://nitter.net/{handle}/rss"


def run_monitoring_loop():
    """
    Main monitoring loop
    Runs continuously, polling insiders and team feeds at different intervals
    """
    logger.info("🚀 Starting Injury Monitor Service...")
    logger.info(f"📡 Nitter endpoint: https://nitter.net (public instance)")
    logger.info(f"💾 Alerts file: {ALERTS_FILE}")
    logger.info(f"🗃️  Database: {DB_FILE}")

    # Load config
    insiders = CONFIG.get("insiders", [])
    teams = CONFIG.get("teams", {})
    keywords = CONFIG.get("keywords", {}).get("high_impact", [])
    polling_config = CONFIG.get("polling", {})

    insider_interval = polling_config.get("insiders", 20)
    team_interval = polling_config.get("teams", 60)
    sleep_time = polling_config.get("sleep", 3)

    # Build feed URLs
    insider_feeds = []
    for insider in insiders:
        handle = insider["handle"]
        tier = insider.get("tier", 1)
        sport = insider.get("sport", "Unknown")
        url = get_nitter_url(handle)
        insider_feeds.append((f"nitter:{handle}", url, tier, sport))

    team_feeds = []
    for league, team_list in teams.items():
        for team in team_list:
            if team.get("rss"):
                team_feeds.append((f"team:{team['name']}", team["rss"], 2))

    logger.info(f"📊 Monitoring {len(insider_feeds)} insiders, {len(team_feeds)} teams")
    logger.info(f"⏱️  Insiders: {insider_interval}s | Teams: {team_interval}s")

    # Timestamps for staggered polling
    last_insider_poll = 0
    last_team_poll = 0

    # Main loop
    while True:
        try:
            now = time.time()

            # Poll insiders (faster cadence)
            if now - last_insider_poll > insider_interval:
                logger.info(f"🔍 Polling {len(insider_feeds)} insiders...")
                for src, url, tier, sport in insider_feeds:
                    count = process_feed(src, url, keywords, tier)
                    if count > 0:
                        logger.info(f"   ✅ {src} ({sport}): {count} new alerts")
                last_insider_poll = now

            # Poll teams (slower cadence)
            if now - last_team_poll > team_interval:
                logger.info(f"🔍 Polling {len(team_feeds)} team feeds...")
                for src, url, tier in team_feeds:
                    count = process_feed(src, url, keywords, tier)
                    if count > 0:
                        logger.info(f"   ✅ {src}: {count} new alerts")
                last_team_poll = now

            # Sleep
            time.sleep(sleep_time)

        except KeyboardInterrupt:
            logger.info("⏹️  Shutting down...")
            break

        except Exception as e:
            logger.error(f"❌ Error in monitoring loop: {e}")
            time.sleep(10)  # Back off on error


if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("INJURY MONITOR SERVICE (Standalone)")
    logger.info("Runs independently from main.py - won't crash the site!")
    logger.info("=" * 80)

    # Check if public Nitter instance is accessible
    try:
        r = requests.get("https://nitter.net", timeout=5)
        logger.info("✅ Public Nitter instance is accessible")
    except:
        logger.warning("⚠️  Public Nitter instance not responding")
        logger.warning("   This may be temporary - will retry connections...")
        logger.warning("   Alternative: Use a different public instance in code")

    # Start monitoring
    run_monitoring_loop()
