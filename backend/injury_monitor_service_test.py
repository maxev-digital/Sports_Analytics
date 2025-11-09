"""
Test Version of Injury Monitor Service (No Docker/Nitter Required)

This generates mock injury alerts for testing the system
Use this while Docker is starting up or for development

Usage:
    python injury_monitor_service_test.py
"""

import time
import json
import logging
from datetime import datetime
from pathlib import Path
from random import choice, random

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent
ALERTS_FILE = BASE_DIR / "data" / "injury_alerts.json"

# Ensure data directory exists
(BASE_DIR / "data").mkdir(exist_ok=True)

# Mock data for testing
MOCK_REPORTERS = [
    {"handle": "wojespn", "name": "Adrian Wojnarowski", "sport": "NBA"},
    {"handle": "ShamsCharania", "name": "Shams Charania", "sport": "NBA"},
    {"handle": "AdamSchefter", "name": "Adam Schefter", "sport": "NFL"},
    {"handle": "RapSheet", "name": "Ian Rapoport", "sport": "NFL"},
]

MOCK_PLAYERS = {
    "NBA": [
        ("LeBron James", "Los Angeles Lakers"),
        ("Stephen Curry", "Golden State Warriors"),
        ("Kevin Durant", "Phoenix Suns"),
        ("Giannis Antetokounmpo", "Milwaukee Bucks"),
        ("Luka Doncic", "Dallas Mavericks"),
    ],
    "NFL": [
        ("Patrick Mahomes", "Kansas City Chiefs"),
        ("Josh Allen", "Buffalo Bills"),
        ("Jalen Hurts", "Philadelphia Eagles"),
        ("Joe Burrow", "Cincinnati Bengals"),
        ("Lamar Jackson", "Baltimore Ravens"),
    ]
}

MOCK_INJURIES = [
    ("ruled out", "ankle sprain", 0.95),
    ("questionable", "knee soreness", 0.75),
    ("doubtful", "hamstring strain", 0.85),
    ("out", "shoulder injury", 0.95),
    ("game-time decision", "back tightness", 0.70),
]


def generate_mock_alert():
    """Generate a mock injury alert"""
    reporter = choice(MOCK_REPORTERS)
    sport = reporter["sport"]
    player_name, team = choice(MOCK_PLAYERS[sport])
    status, injury, confidence = choice(MOCK_INJURIES)

    opponent = choice([t for p, t in MOCK_PLAYERS[sport] if t != team])

    title = f"{player_name} {status} tonight vs {opponent} with {injury}"

    alert = {
        "source": f"nitter:{reporter['handle']}",
        "title": title,
        "link": f"http://127.0.0.1:8080/{reporter['handle']}/status/{int(time.time())}",
        "published": datetime.utcnow().isoformat() + "Z",
        "entities_guess": [player_name, team, opponent],
        "text": title,
        "confidence": confidence,
        "test_mode": True
    }

    return alert


def save_alerts(alerts):
    """Save alerts to JSON file"""
    try:
        with open(ALERTS_FILE, 'w') as f:
            json.dump(alerts, f, indent=2)
        logger.info(f"💾 Saved {len(alerts)} alerts to {ALERTS_FILE}")
    except Exception as e:
        logger.error(f"❌ Error saving alerts: {e}")


def run_test_mode():
    """Run in test mode - generate mock alerts periodically"""
    logger.info("=" * 80)
    logger.info("INJURY MONITOR TEST MODE (No Docker/Nitter Required)")
    logger.info("Generates mock injury alerts for testing")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"💾 Alerts file: {ALERTS_FILE}")
    logger.info(f"🔗 Test API: http://localhost:8000/api/injuries/alerts")
    logger.info("")
    logger.info("Press Ctrl+C to stop")
    logger.info("")

    alerts = []

    # Generate initial batch of alerts
    logger.info("🔄 Generating initial test alerts...")
    for _ in range(5):
        alert = generate_mock_alert()
        alerts.insert(0, alert)
        logger.info(f"   🚨 {alert['title']}")

    save_alerts(alerts)
    logger.info("")
    logger.info(f"✅ Generated {len(alerts)} test alerts")
    logger.info("🔄 Will generate new alert every 30 seconds...")
    logger.info("")

    cycle = 0
    while True:
        try:
            time.sleep(30)

            cycle += 1
            logger.info(f"[Cycle {cycle}] Generating new mock alert...")

            # Generate new alert
            alert = generate_mock_alert()
            alerts.insert(0, alert)

            # Keep only last 100 alerts
            alerts = alerts[:100]

            # Save
            save_alerts(alerts)

            logger.info(f"   🚨 {alert['title']}")
            logger.info(f"   📊 Total alerts: {len(alerts)}")
            logger.info("")

        except KeyboardInterrupt:
            logger.info("")
            logger.info("⏹️  Shutting down test mode...")
            break
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            time.sleep(10)


if __name__ == "__main__":
    run_test_mode()
