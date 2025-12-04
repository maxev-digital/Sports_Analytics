# Injury Monitor Service - Setup Guide

## Overview

The **Injury Monitor Service** runs **separately from main.py** to prevent Twitter/X API issues from crashing your main site.

### Architecture

```
┌─────────────────────────────────────┐
│  main.py (FastAPI)                  │
│  - Port 8000                        │
│  - ONLY READS alerts                │
│  - Never crashes from Twitter       │
└─────────────────────────────────────┘
            ↑ reads
            │
┌───────────────────────────────────┐
│  injury_alerts.json (shared)      │
└───────────────────────────────────┘
            ↑ writes
            │
┌─────────────────────────────────────┐
│  injury_monitor_service.py          │
│  - Separate process                 │
│  - Polls Nitter RSS                 │
│  - If crashes, main.py stays up!    │
└─────────────────────────────────────┘
            ↑ polls
            │
┌───────────────────────────────────┐
│  Nitter (Docker)                  │
│  - http://localhost:8080          │
│  - RSS feeds for Twitter/X        │
└───────────────────────────────────┘
```

## Key Benefits

✅ **No Twitter API needed** - Uses self-hosted Nitter RSS feeds
✅ **Site stays up** - If injury monitor crashes, main.py keeps running
✅ **No rate limits** - RSS is much lighter than Twitter API
✅ **Legal & safe** - Doesn't violate Twitter ToS
✅ **Fast alerts** - Still get alerts in 20-60 seconds

## Setup Instructions

### Step 1: Install Docker (if not installed)

**Windows:** Download from https://www.docker.com/products/docker-desktop/

**Linux/Mac:**
```bash
# Docker already installed on most Linux servers
docker --version
```

### Step 2: Start Nitter (Self-Hosted Twitter RSS)

```bash
cd backend
docker-compose -f docker-compose.nitter.yml up -d
```

Verify Nitter is running:
```bash
curl http://127.0.0.1:8080
```

### Step 3: Install Python Dependencies

```bash
pip install feedparser pyyaml requests
```

### Step 4: Configure Sources (Optional)

Edit `backend/injury_sources.yaml` to customize:
- Which reporters to monitor (Woj, Shams, Schefter, etc.)
- Polling intervals
- Injury keywords

Default config monitors:
- NBA: Woj, Shams
- NFL: Schefter, Rapoport
- NHL: Seravalli, LeBrun
- MLB: Passan, Rosenthal (season only)

### Step 5: Start Injury Monitor Service

**Windows:**
```bash
cd backend
start_injury_monitor.bat
```

**Linux/Mac:**
```bash
cd backend
python injury_monitor_service.py
```

**Run in background (Linux/Mac):**
```bash
nohup python injury_monitor_service.py > injury_monitor.log 2>&1 &
```

**Run in background (Windows with pm2):**
```bash
pm2 start injury_monitor_service.py --name injury-monitor --interpreter python
```

### Step 6: Verify It's Working

Check logs:
```bash
# Windows
type backend\injury_monitor.log

# Linux/Mac
tail -f backend/injury_monitor.log
```

Check alerts file:
```bash
# Windows
type backend\data\injury_alerts.json

# Linux/Mac
cat backend/data/injury_alerts.json
```

Test API endpoint:
```bash
curl http://localhost:8000/api/injuries/alerts
```

## Usage

### API Endpoint

**GET /api/injuries/alerts**

Returns latest injury alerts:

```json
{
  "count": 3,
  "status": "ok",
  "alerts": [
    {
      "source": "nitter:wojespn",
      "title": "LeBron James ruled out tonight vs Celtics with ankle injury",
      "link": "http://127.0.0.1:8080/wojespn/status/123456789",
      "published": "2025-11-06T18:30:00Z",
      "entities_guess": ["LeBron James", "Boston Celtics"],
      "text": "LeBron James ruled out tonight vs Celtics with ankle injury...",
      "confidence": 0.95
    }
  ]
}
```

### Frontend Integration

```typescript
// Fetch injury alerts from API
async function getInjuryAlerts() {
  const response = await fetch('http://localhost:8000/api/injuries/alerts');
  const data = await response.json();

  if (data.status === 'ok') {
    console.log(`Found ${data.count} injury alerts`);
    data.alerts.forEach(alert => {
      console.log(`🚨 ${alert.title} (${alert.confidence * 100}% confidence)`);
    });
  }
}
```

## Troubleshooting

### Nitter not running

```bash
# Check if Nitter container is running
docker ps | grep nitter

# Start Nitter
docker-compose -f docker-compose.nitter.yml up -d

# Check Nitter logs
docker logs nitter
```

### No alerts appearing

1. Check if injury monitor service is running:
   ```bash
   # Windows
   tasklist | findstr python

   # Linux/Mac
   ps aux | grep injury_monitor
   ```

2. Check logs for errors:
   ```bash
   # Service logs
   type backend\injury_monitor.log  # Windows
   tail -f backend/injury_monitor.log  # Linux/Mac
   ```

3. Verify Nitter RSS feeds:
   ```bash
   curl http://127.0.0.1:8080/wojespn/rss
   ```

### Service keeps crashing

The whole point of this architecture is that crashes DON'T affect main.py!

But to debug:
1. Check Python dependencies: `pip install feedparser pyyaml requests`
2. Check Nitter is accessible: `curl http://127.0.0.1:8080`
3. Check file permissions for `backend/data/` directory
4. Review logs for specific errors

## Advanced Configuration

### Add More Reporters

Edit `backend/injury_sources.yaml`:

```yaml
insiders:
  - handle: YourNewReporter
    name: Reporter Name
    sport: NBA
    tier: 1  # 1=highest, 3=lowest
```

### Change Polling Intervals

Edit `backend/injury_sources.yaml`:

```yaml
polling:
  insiders: 20  # seconds (faster = more API load)
  teams: 60     # seconds
  sleep: 3      # sleep between cycles
```

### Add Custom Keywords

Edit `backend/injury_sources.yaml`:

```yaml
keywords:
  high_impact:
    - "your custom keyword"
    - "another keyword"
```

### Production Deployment

For production servers, use a process manager:

**PM2 (recommended):**
```bash
pm2 start injury_monitor_service.py --name injury-monitor --interpreter python
pm2 save
pm2 startup  # Auto-start on server reboot
```

**systemd (Linux):**
Create `/etc/systemd/system/injury-monitor.service`:
```ini
[Unit]
Description=Injury Monitor Service
After=network.target docker.service

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/backend
ExecStart=/usr/bin/python3 injury_monitor_service.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable injury-monitor
sudo systemctl start injury-monitor
sudo systemctl status injury-monitor
```

## Monitoring & Maintenance

### Check Service Health

```bash
# Check if service is running
ps aux | grep injury_monitor

# Check recent alerts
curl http://localhost:8000/api/injuries/alerts | jq '.count'

# Check Nitter health
curl http://127.0.0.1:8080/health
```

### Clean Up Old Alerts

The service automatically keeps only the last 100 alerts in `injury_alerts.json`.

To manually clear:
```bash
rm backend/data/injury_alerts.json
rm backend/data/injury_alerts.db
```

### Update Nitter

```bash
docker-compose -f docker-compose.nitter.yml pull
docker-compose -f docker-compose.nitter.yml up -d
```

## Extension Integration (Optional)

To integrate with your Chrome extension:

1. **Extension calls API endpoint:**
   ```javascript
   // In extension background.js
   async function checkInjuryAlerts() {
     const response = await fetch('http://localhost:8000/api/injuries/alerts');
     const data = await response.json();

     // Show notifications for high-confidence alerts
     data.alerts
       .filter(alert => alert.confidence > 0.90)
       .forEach(alert => {
         chrome.notifications.create({
           type: 'basic',
           title: '🚨 Injury Alert',
           message: alert.title
         });
       });
   }

   // Poll every 30 seconds
   setInterval(checkInjuryAlerts, 30000);
   ```

2. **Or run monitor in extension directly:**
   - Copy `injury_monitor_service.py` logic to extension
   - Use extension's background service worker
   - Store alerts in chrome.storage.local

## Summary

🎯 **Main Benefits:**
- ✅ Site never crashes from Twitter issues
- ✅ No Twitter API needed (uses Nitter RSS)
- ✅ Fast alerts (20-60 seconds)
- ✅ Runs independently
- ✅ Easy to monitor and maintain

🚀 **Quick Start:**
```bash
# 1. Start Nitter
docker-compose -f docker-compose.nitter.yml up -d

# 2. Install deps
pip install feedparser pyyaml requests

# 3. Start monitor
python injury_monitor_service.py

# 4. Test
curl http://localhost:8000/api/injuries/alerts
```

📚 **Files Created:**
- `docker-compose.nitter.yml` - Nitter Docker config
- `injury_sources.yaml` - Reporter/team configuration
- `injury_monitor_service.py` - Standalone monitoring service
- `start_injury_monitor.bat` - Windows startup script
- `data/injury_alerts.json` - Shared alerts storage
- `data/injury_alerts.db` - Deduplication database

Need help? Check logs first, then review troubleshooting section above.
