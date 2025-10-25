# ARB Auto Bettor - Production Workflow

## Overview

The extension is now configured for **production use** with real backend alerts. All test buttons and mock data have been removed.

---

## How It Works

### 1. Backend Detection
- **Background script** polls backend every 5 seconds
- **Endpoint:** `http://localhost:8000/api/alerts/all`
- Fetches: Arbitrage, Steam Moves, Line Movements, Goalie Pulls

### 2. Alert Detection
When backend returns new opportunities:
- **Arbitrage**: Compares to `seenOpportunityIds` Set
- **Steam Moves**: Compares to `seenSteamMoveIds` Set
- **Line Movements**: Compares to `seenLineMovementIds` Set
- **Goalie Pulls**: Compares to `seenGoaliePullIds` Set

### 3. Alert Notification
If **NEW** opportunity detected:
- ✅ Plays sound alert (if enabled)
- ✅ Plays voice announcement (if enabled)
- ✅ Shows Chrome notification
- ✅ Updates badge count/color
- ✅ Stores in current opportunities

### 4. User Interaction

#### Option A: Click Opportunity Card
1. User opens popup (clicks extension icon)
2. User clicks on opportunity card
3. `openOpportunity()` sends message to background
4. Background calls `openSportsbookTabs()`

#### Option B: Click Notification
1. Chrome notification appears
2. User clicks "Open Bets" button
3. Background retrieves opportunity
4. Background calls `openSportsbookTabs()`

### 5. Auto-Fill Process

**openSportsbookTabs() function:**
```javascript
1. Builds URLs for both sportsbooks using buildBookmakerURL()
2. Opens tab for Book 1 (inactive)
3. Opens tab for Book 2 (active - user sees this)
4. Waits 3 seconds for pages to load
5. Sends fill_bet_slip message to each tab's content script
```

**Content Scripts (betus.js, bovada.js):**
```javascript
1. Receive fill_bet_slip message
2. findGame() - Locate game on page (fuzzy team matching)
3. findAndClickMarket() - Click market tab (Total, Spread, ML)
4. findAndClickBet() - Find and click bet button
5. waitForBetSlip() - Wait for bet slip to appear
6. fillStakeAmount() - Fill stake input with amount
7. highlightConfirmButton() - Highlight confirm (pulsing green)
8. showNotification() - Show success notification
```

**User Action Required:**
- User **manually reviews** bet details
- User **manually clicks** confirm button to place bet

---

## Settings Configuration

### Alert Types (Settings Page)
- ✅ Arbitrage Alerts
- ✅ Steam Move Alerts
- ✅ Line Movement Alerts
- ✅ Goalie Pull Alerts

Each can be toggled individually.

### Auto-Bet Mode (Settings Page)
- **fill**: Auto-fill bet slips (recommended)
- **manual**: Just open tabs, no auto-fill

### Enabled Sportsbooks (Settings Page)
Only enabled sportsbooks will have tabs opened.

---

## Data Flow Diagram

```
Backend API (localhost:8000)
    ↓ (polling every 5s)
Background Script
    ↓ (detects new opportunity)
Check if new? → No → Ignore
    ↓ Yes
Play Alerts (sound + voice + notification)
    ↓
Store in currentOpportunities
    ↓
User clicks opportunity/notification
    ↓
openSportsbookTabs(opportunity)
    ↓
Open Book1 + Book2 tabs
    ↓ (after 3s)
Send fill_bet_slip to content scripts
    ↓
Content scripts auto-fill bet slips
    ↓
User manually confirms bet
```

---

## Key Functions Reference

### Background Script (background.js)

| Function | Purpose |
|----------|---------|
| `fetchOpportunities()` | Poll backend API every 5s |
| `handleOpportunitiesUpdate()` | Process arbitrage alerts |
| `handleSteamMovesUpdate()` | Process steam move alerts |
| `handleLineMovementsUpdate()` | Process line movement alerts |
| `handleGoaliePullsUpdate()` | Process goalie pull alerts |
| `openSportsbookTabs()` | Open sportsbook tabs + trigger auto-fill |
| `buildBookmakerURL()` | Generate sportsbook URLs |
| `playHighPriority()` | Play high priority sound |
| `playMediumPriority()` | Play medium priority sound |
| `playLowPriority()` | Play low priority sound |

### Popup Script (popup.js)

| Function | Purpose |
|----------|---------|
| `loadOpportunities()` | Request data from background |
| `renderOpportunities()` | Render arbitrage cards |
| `renderSteamMoves()` | Render steam move cards |
| `renderLineMovements()` | Render line movement cards |
| `renderGoaliePulls()` | Render goalie pull cards |
| `openOpportunity()` | Send open_opportunity message |
| `switchTab()` | Switch between tabs |

### Content Scripts (betus.js, bovada.js)

| Function | Purpose |
|----------|---------|
| `fillBetSlip()` | Main auto-fill orchestration |
| `findGame()` | Locate game element by teams |
| `findAndClickMarket()` | Click market tab |
| `findAndClickBet()` | Find and click bet button |
| `waitForBetSlip()` | Wait for bet slip DOM |
| `fillStakeAmount()` | Fill stake input |
| `highlightConfirmButton()` | Highlight confirm button |
| `showNotification()` | Show success notification |

---

## Safety Features

1. ✅ **Never auto-clicks confirm** - Always requires manual review
2. ✅ **Visual highlighting** - Shows what it's doing (blue → orange → green)
3. ✅ **Detailed logging** - All actions logged to console
4. ✅ **Graceful errors** - Shows error messages instead of crashing
5. ✅ **Settings respect** - Only works if autoBetMode enabled
6. ✅ **Duplicate prevention** - Won't alert twice for same opportunity

---

## Startup Checklist

### 1. Start Backend
```bash
cd C:\Users\nashr\backend\ARB_Auto_Bettor\backend
uvicorn main:app --reload
```

### 2. Load Extension
```
1. Go to chrome://extensions/
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select: C:\Users\nashr\backend\ARB_Auto_Bettor\extension\
5. Verify no errors in console
```

### 3. Verify Connection
```
1. Click extension icon
2. Status should show "Connected" (green dot)
3. Stat boxes should show counts
4. If disconnected, check backend is running
```

### 4. Configure Settings
```
1. Click "⚙️ Settings" in popup
2. Enable desired alert types
3. Set auto-bet mode to "fill"
4. Enable sportsbooks you have accounts with
5. Enter bankroll and stakes
6. Click "Save Settings"
```

---

## Monitoring

### Extension Console
```
1. Go to chrome://extensions/
2. Find "ARB Auto Bettor"
3. Click "service worker" link
4. View background script logs
```

### Sportsbook Page Console
```
1. On BetUS/Bovada page
2. Press F12
3. Look for [BETUS_FILLER] or [BOVADA_FILLER] logs
4. Verify auto-fill actions
```

---

## Troubleshooting

### "Disconnected" Status
- ✅ Check backend is running at localhost:8000
- ✅ Verify firewall isn't blocking connection
- ✅ Check backend console for errors

### No Opportunities Showing
- ✅ Backend might not have any opportunities right now
- ✅ Check backend logs to see if it's detecting opportunities
- ✅ Try refreshing the popup

### Auto-Fill Not Working
- ✅ Check autoBetMode is set to "fill" in settings
- ✅ Verify content script loaded (check page console)
- ✅ Sportsbook DOM structure may have changed
- ✅ Team names might not match exactly

### Bet Slip Not Filling
- ✅ Check stake input selector in content script
- ✅ Sportsbook might require login first
- ✅ Bet might be suspended/unavailable
- ✅ Wait 3+ seconds for page to fully load

---

## Production Best Practices

1. ✅ **Test with small stakes first** - Verify auto-fill accuracy
2. ✅ **Always review before confirming** - Never blindly confirm bets
3. ✅ **Monitor performance** - Track ROI in Google Sheets
4. ✅ **Keep bankroll updated** - Update settings as balance changes
5. ✅ **Disable alerts when not betting** - Avoid distractions
6. ✅ **Check sportsbook limits** - Some books have max bets
7. ✅ **Space out bets** - Don't hammer books with rapid bets

---

## Next Steps

1. Start backend server
2. Load extension
3. Verify connection
4. Configure settings
5. Wait for real opportunities
6. Click opportunity → auto-fill → manual confirm
7. Track results in Google Sheets
8. Adjust settings based on performance

---

**Extension Status:** Production Ready ✅
**Test Code Removed:** ✅
**Normal Flow Verified:** ✅
**Last Updated:** 2025-10-19
