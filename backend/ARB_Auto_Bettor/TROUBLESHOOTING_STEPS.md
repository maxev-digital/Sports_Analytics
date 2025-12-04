# ARB Auto Bettor™ Extension Troubleshooting

## After Chrome Restart - Check These In Order:

### 1. ✅ Backend Status (Already Verified)
- Backend is running on port 8000 ✅
- 16 active arbitrage opportunities ✅
- WebSocket endpoint available at ws://localhost:8000/ws ✅

### 2. 🔍 Check Extension Loaded
1. Open `chrome://extensions/`
2. Find **ARB Auto Bettor™**
3. Should show:
   - ✅ Extension enabled (toggle is ON)
   - ✅ No errors shown
   - ✅ Version 1.0.0

### 3. 🔍 Check Service Worker
1. On `chrome://extensions/` page
2. Find **ARB Auto Bettor™**
3. Look for **"service worker"** link (blue text)
4. Click it to open DevTools console
5. **Expected output:**
   ```
   [ARB] ARB Auto Bettor™ background service worker starting...
   [ARB] Connecting to WebSocket: ws://localhost:8000/ws
   [ARB] ✅ WebSocket connected
   [ARB] Message received: {type: "connection_established", ...}
   [ARB] Message received: {type: "opportunities_update", opportunities: Array(16)}
   [ARB] 📋 Opportunities update: 16 active
   ```

6. **If you see errors instead:**
   - Screenshot the error
   - Look for: "WebSocket error", "CORS", "Connection refused"
   - Copy the full error message

### 4. 🔍 Check Extension Popup
1. Click the extension icon in toolbar (green $ icon)
2. **Should show:**
   - Green dot + "Connected" (top right)
   - "16" in Active Opportunities
   - "Lakers vs Warriors", "Thunder vs Rockets", etc.

3. **If shows "Disconnected":**
   - Right-click the extension icon
   - Select "Inspect Popup"
   - Check Console tab for errors

### 5. 🔍 Check Extension Badge
Look at the extension icon in toolbar:
- **"ON"** in green = Connected, no opportunities above threshold
- **Number (1-16)** in orange = Connected, X opportunities available
- **"OFF"** in gray = Disconnected
- **"ERR"** in red = Error connecting

## Common Issues & Fixes

### Issue: "WebSocket connection refused"
**Fix:** Backend might not be running
```bash
# Check if backend is running:
curl http://localhost:8000/api/alerts/all

# If nothing, start backend:
cd C:\Users\nashr\backend\scrapers\nba\backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Issue: "CORS error" or "Origin not allowed"
**Fix:** WebSocket should allow all origins, but check main.py CORS settings

### Issue: Service Worker shows "Inactive" or "Stopped"
**Fix:**
1. Click "Reload" on chrome://extensions/
2. OR Click the service worker link to wake it up

### Issue: "Extension context invalidated"
**Fix:**
1. Reload extension on chrome://extensions/
2. Close all extension popups
3. Click extension icon again

### Issue: Popup shows empty list but says "Connected"
**Fix:**
1. Click Refresh button in popup
2. Check if minProfit threshold is too high (default 1.0%)
3. Check service worker console for opportunity filtering

## Manual WebSocket Test

If extension still won't connect, test WebSocket directly:

1. Open: `C:\Users\nashr\backend\ARB_Auto_Bettor\test_websocket.html`
2. Should see: "✅ Connected to WebSocket"
3. Should see: Opportunities update with 16 items
4. If this fails, backend WebSocket isn't working

## Backend Logs

Check backend terminal for:
```
INFO: WebSocket client connected. Total connections: 1
```

If you don't see this, the extension isn't reaching the backend.

## Next Steps Based on What You See

**Scenario A: Service worker says "WebSocket connected" but popup shows "Disconnected"**
- Issue with popup.js getting status from background.js
- Check popup DevTools console

**Scenario B: Service worker shows errors connecting to WebSocket**
- Backend issue or firewall blocking
- Test with test_websocket.html

**Scenario C: Service worker is "Inactive" and won't start**
- Extension manifest issue
- Try removing and re-adding extension

**Scenario D: Everything connects but no opportunities show**
- Opportunities are being filtered out
- Check settings or minProfit threshold

---

## Report Back With:

1. **Extension badge** - What does it say? (ON/OFF/ERR/number)
2. **Service worker console** - Copy first 10 lines
3. **Popup status** - Connected or Disconnected?
4. **Any error messages** - From service worker or popup console

Then I can pinpoint the exact issue!
