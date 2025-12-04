# Test Injury Alerts in Extension

## ✅ Setup Complete!

### What We Built:

1. **Standalone Injury Monitor** (`injury_monitor_service_test.py`)
   - Runs independently from main.py
   - Generates mock injury alerts every 30 seconds
   - Writes to `backend/data/injury_alerts.json`

2. **Chrome Extension Integration**
   - Modified `background.js` to fetch injury alerts
   - Modified `popup.js` to display alerts
   - Modified `popup.html` to show alert count

3. **API Endpoint** (in main.py)
   - `GET /api/injuries/alerts` - Returns injury alerts

## 🧪 Testing Steps

### Step 1: Verify Injury Monitor is Running

The injury monitor service is currently running in the background and generating test alerts.

Check the output:
```bash
# See latest alerts
type backend\data\injury_alerts.json
```

You should see alerts like:
- "Stephen Curry out tonight vs Dallas Mavericks"
- "Patrick Mahomes questionable vs Baltimore Ravens"
- etc.

### Step 2: Load Extension in Chrome

1. Open Chrome
2. Go to `chrome://extensions/`
3. Enable "Developer mode" (top right)
4. Click "Load unpacked"
5. Select folder: `C:\Users\nashr\backend\ARB_Auto_Bettor\extension`

### Step 3: Check Extension Console

1. Click extension icon in Chrome toolbar
2. Right-click → "Inspect popup"
3. Go to Console tab
4. Look for:
   ```
   [INJURY] ✅ Received 11 injury alerts from monitor service
   ```

### Step 4: View Alerts in Extension Popup

1. Click the extension icon
2. You should see:
   - **🚨 Injury Alerts** stat card showing count
   - Individual injury alert cards in the feed with:
     - Player name and injury status
     - Reporter (e.g., @AdamSchefter)
     - Confidence percentage
     - "🧪 TEST MODE" badge

### Step 5: Test Notifications

High-confidence alerts (95%+) should trigger:
- 🔊 Sound alert (if enabled)
- 🗣️ Voice announcement (if enabled)
- Chrome notification

## 🎯 Expected Results

### In Extension Popup:
- Stat card: "🚨 Injury Alerts: 11" (or current count)
- Alert cards sorted by confidence
- High confidence (95%): Red border, "🚨 HIGH CONFIDENCE"
- Medium confidence (85-94%): Orange border, "⚠️ CONFIRMED"
- Lower confidence (<85%): Blue border, "📰 REPORTED"

### In Extension Console:
```
[INJURY] ✅ Received 11 injury alerts from monitor service
[POPUP] Injury alerts count: 11
[POPUP] Total alerts in feed: 11
```

### In Background Console:
```
[INJURY] 🚨 Real-time injury alerts: 11 active
[INJURY] 🆕 NEW HIGH-CONFIDENCE ALERT: Kevin Durant out tonight...
```

## 🐛 Troubleshooting

### No alerts showing?

**Check if monitor is running:**
```bash
tasklist | findstr python
```

**Check alerts file exists:**
```bash
dir backend\data\injury_alerts.json
```

**Check file contents:**
```bash
type backend\data\injury_alerts.json
```

### Extension not fetching alerts?

The backend needs to be restarted to enable the new `/api/injuries/alerts` endpoint.

**Temporary workaround:** Extension will work once backend restarts. The injury monitor runs independently, so alerts are still being collected!

### Extension console shows "endpoint not available"?

This is expected! The endpoint requires backend restart. But the injury monitor is still collecting alerts in the JSON file.

## 🚀 Next Steps

1. **Restart backend** to enable API endpoint:
   ```bash
   # Stop current backend (Ctrl+C)
   # Restart:
   cd backend
   python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Switch to real Nitter** (when ready):
   ```bash
   # Start Nitter with Docker
   docker-compose -f docker-compose.nitter.yml up -d

   # Stop test monitor
   taskkill /F /IM python.exe /FI "WINDOWTITLE eq injury_monitor*"

   # Start real monitor
   python injury_monitor_service.py
   ```

3. **Deploy to production**:
   - Run injury monitor as a service (pm2 or systemd)
   - Deploy Nitter to server
   - Update extension to point to production

## 📊 Current Status

✅ Injury Monitor: **RUNNING** (test mode)
✅ Extension Code: **INTEGRATED**
✅ Alerts File: **UPDATING** (every 30s)
⏸️ API Endpoint: **NEEDS BACKEND RESTART**
⏸️ Nitter: **NOT STARTED** (using test mode)

## 🎉 Success Criteria

- [ ] Extension loads without errors
- [ ] Injury alerts count appears in popup
- [ ] Alert cards display in feed
- [ ] Test mode badge shows on alerts
- [ ] Console logs show "Received X injury alerts"
- [ ] Clicking alert opens source link

Once these work, you're good to go! 🚀
