# ARB Auto Bettor - Development Log

## Project Overview

**ARB Auto Bettor** is a Chrome Extension (Manifest V3) that monitors 11 sportsbooks for arbitrage betting opportunities, steam moves, line movements, and NHL goalie pull situations. The extension connects to a Python FastAPI backend that scrapes odds and analyzes betting markets in real-time.

**Technology Stack:**
- Chrome Extension (Manifest V3)
- Service Worker for background processing
- REST API polling (5-second intervals)
- Web Speech API for voice announcements
- Web Audio API for sound alerts
- Chrome Storage Sync API for settings persistence

---

## Feature Implementation History

### Phase 1: Core Arbitrage Detection
**Status:** ✅ Complete

**Features:**
- Real-time arbitrage opportunity detection across 11 sportsbooks
- Multi-sport support (NBA, NFL, NHL, MLB, NCAAF, Soccer)
- Profit percentage calculations
- Sound alerts with 3 priority levels (High: 5%+, Medium: 3-5%, Low: 1-3%)
- Voice announcements with opportunity details
- Chrome notifications with "Open Bets" action button
- Auto-open sportsbook tabs feature

**Key Files:**
- `extension/background.js` - Service worker, alert logic
- `extension/popup/popup.html` - Main UI structure
- `extension/popup/popup.js` - UI rendering and interaction
- `extension/popup/popup.css` - Styling and animations

---

### Phase 2: Steam Moves & Line Movements
**Status:** ✅ Complete

**Features:**
- Steam move detection (70%+ books moving same direction)
- Line movement tracking (1.5+ point movements)
- Stale line identification (books that haven't moved yet)
- Distinctive alert sounds for each alert type
- Voice announcements with stale line information

**Implementation Details:**
- Steam moves: Higher-pitched triangle wave sound
- Voice announces: Game, direction, books moved, and best stale price
- Separate tracking with `seenSteamMoveIds` Set

**Key Functions:**
- `handleSteamMovesUpdate()` - Process steam move alerts
- `playSteamMoveAlert()` - Play distinctive steam alert
- `renderSteamMoves()` - Display steam move cards

---

### Phase 3: 4-Tab UI & Sport-Specific Styling
**Status:** ✅ Complete

**Features:**
- 4 tabs: Arbitrage, Steam Moves, Line Movements, Goalie Pull
- Sport-specific card colors matching playing surfaces:
  - NBA: Blue gradient (court)
  - NFL/NCAAF/Soccer: Green gradient (field/pitch)
  - NHL: Light blue-white gradient (ice)
  - MLB: Brown-tan gradient (dirt infield)
- Microsoft Fluent Emoji CDN for consistent emoji rendering
- Clickable stat boxes to switch tabs
- Empty state messages for each tab

**CSS Classes:**
```css
.opportunity-card[data-sport="NBA"] - Blue gradient
.opportunity-card[data-sport="NFL"] - Green gradient
.opportunity-card[data-sport="NHL"] - Ice gradient
.opportunity-card[data-sport="MLB"] - Dirt gradient
```

---

### Phase 4: NHL Goalie Pull Alerts
**Status:** ✅ Complete

**Trigger Conditions:**
- 3rd period
- 5 minutes or less remaining
- 2-goal difference
- Trailing team likely to pull goalie

**Features:**
- Red pulsing card with animation
- "2-GOAL GAME" badge
- Clickable Bovada button
- Urgent square-wave alert sound
- Voice announcement: "Goalie pull alert! [Game]. Score: [Score]. Time: [Time] remaining. Two goal game. Prepare Bovada now!"

**Implementation:**
- Separate REST API endpoint: `/api/goalie-pull-opportunities`
- Polling every 5 seconds
- Duplicate prevention via `seenGoaliePullIds`

**Key Files:**
- `popup.html:133` - 4th stat box for goalie pull count
- `popup.html:154` - Goalie pull tab button
- `popup.css:406-499` - Goalie card styling with pulse animation
- `popup.js:413-476` - `renderGoaliePulls()` function
- `background.js:645-680` - Goalie pull update handler
- `background.js:752-775` - `playGoaliePullAlert()` function

---

### Phase 5: Individual Alert Type Settings
**Status:** ✅ Complete

**Features:**
- Individual toggle switches for each alert type:
  - Arbitrage Alerts
  - Steam Move Alerts
  - Line Movement Alerts
  - Goalie Pull Alerts
- Settings persist across sessions via Chrome Storage Sync
- Background script checks settings before playing alerts
- Settings page with visual icons for each alert type

**Settings Structure:**
```javascript
{
  enableArbitrageAlerts: true,
  enableSteamAlerts: true,
  enableLineAlerts: true,
  enableGoalieAlerts: true
}
```

**Conditional Alert Logic:**
- `background.js:544-563` - Arbitrage alert check
- `background.js:587-603` - Steam move alert check
- `background.js:625-641` - Line movement alert check
- `background.js:663-678` - Goalie pull alert check

**Key Files:**
- `settings/settings.html:197-287` - Alert toggles UI
- `settings/settings.js:86-90` - Load alert settings
- `settings/settings.js:140-144` - Save alert settings
- `background.js:147-157` - `loadSettings()` function

---

### Phase 6: Duplicate Alert Prevention
**Status:** ✅ Complete

**Implementation:**
Each alert type maintains a JavaScript Set to track seen alerts:

```javascript
let seenOpportunityIds = new Set();    // Arbitrage
let seenSteamMoveIds = new Set();      // Steam moves
let seenLineMovementIds = new Set();   // Line movements
let seenGoaliePullIds = new Set();     // Goalie pulls
```

**ID Generation Patterns:**
- Arbitrage: `${game_id}_${book_a}_${book_b}_${market_type}`
- Steam moves: `${game_id}_${bookmaker}_${market_type}_${timestamp}`
- Line movements: `${game_id}_${market_type}_${timestamp}`
- Goalie pulls: `${game_id}_${timestamp}`

**Cleanup Logic:**
Old IDs are removed when opportunities expire to prevent memory leaks (lines 537-542, 580-585, 618-623, 655-660 in background.js).

---

### Phase 7: Timestamp System
**Status:** ✅ Complete
**Date Implemented:** Recent session (continuation)

**Features:**
- Alert detection time (blue) - Shows when alert was created
- Game start time (green) - Shows when game begins
- Smart relative time formatting ("2 mins ago", "1 hour ago")
- Smart absolute time formatting ("Today 7:30 PM", "Tomorrow 3:00 PM", "Dec 25 8:00 PM")

**Helper Functions:**
- `formatTimeAgo(timestamp)` - Converts timestamp to relative time
  - < 1 min: "Just now"
  - 1-59 mins: "X mins ago"
  - 1-23 hours: "X hours ago"
  - 1+ days: "X days ago"

- `formatGameTime(commence_time)` - Converts game time to readable format
  - Same day: "Today 7:30 PM"
  - Tomorrow: "Tomorrow 3:00 PM"
  - Future: "Dec 25 8:00 PM"

**Timestamp Display:**
All 4 card types now show timestamps at the bottom:
```html
<div class="alert-timestamps">
  <span class="timestamp-alert">⏰ Alert: ${alertTime}</span>
  <span class="timestamp-game">🎮 Game: ${gameTime}</span>
</div>
```

**Key Files:**
- `popup.js:32-74` - Timestamp helper functions
- `popup.js:244-247` - Arbitrage card timestamps
- `popup.js:348-351` - Steam move card timestamps
- `popup.js:404-407` - Line movement card timestamps
- `popup.js:457-460` - Goalie pull card timestamps
- `popup.css:294-321` - Timestamp styling

---

### Phase 8: Auto-Betting System (BetUS)
**Status:** 🚧 Testing Phase
**Date Implemented:** 2025-10-18

**Overview:**
Automated bet slip filling system that locates bets on sportsbook pages and auto-fills stake amounts. Starting with BetUS.com for initial testing.

**Features:**
- **Smart Game Matching** - Fuzzy team name matching with abbreviations support
- **Market Detection** - Finds and clicks market tabs (Spread, Total, Moneyline)
- **Bet Locating** - Identifies specific bet buttons by outcome and line value
- **Auto-Fill** - Fills stake amount in bet slip
- **Visual Highlighting** - Color-coded highlights show system actions:
  - Blue: Game found
  - Orange: Bet button found
  - Green: Stake filled, confirm button ready
- **Safety Features** - Never auto-clicks confirm button (manual review required)
- **On-Page Notifications** - Floating success/error messages

**Architecture:**

```
Base Framework:
- bet_finder.js (360 lines)
  - Team name normalization
  - Fuzzy matching algorithm
  - Market tab detection
  - Bet button location
  - Visual highlighting

Sportsbook-Specific:
- betus.js (450 lines)
  - BetUS DOM navigation
  - Bet slip handling
  - Message listener
  - Auto-fill orchestration
```

**Matching Algorithm:**

1. **Team Normalization** - Remove prefixes (LA, New York), special characters
2. **Fuzzy Matching** - Handle abbreviations (Lakers ↔ LAL, Warriors ↔ GSW)
3. **Proximity Scoring** - Prefer elements with both teams close together
4. **Market Filtering** - Click tabs to access correct market type
5. **Line Verification** - Match point values (225.5, -3.5, etc.)
6. **Odds Check** - Verify odds match within 10-15 points tolerance

**Message Flow:**

```
Background Script
    ↓ (alert detected)
openSportsbookTabs()
    ↓ (creates tab)
chrome.tabs.sendMessage()
    ↓ (type: 'fill_bet_slip')
BetUSBetFiller.fillBetSlip()
    ↓
1. findGame() → highlight blue
2. findAndClickMarket() → click tab
3. findAndClickBet() → highlight orange, click
4. waitForBetSlip() → wait for DOM
5. fillStakeAmount() → highlight green
6. Highlight confirm button → pulsing green
    ↓
User manually reviews and confirms
```

**Team Abbreviation Map:**
- 30+ NBA team abbreviations supported
- Handles variations: "LA Lakers", "Los Angeles", "LAL", "Lakers"
- Handles variations: "Golden State", "Warriors", "GSW"
- Extensible for NFL, NHL, MLB teams

**DOM Selectors (Generic):**
```javascript
// Bet slip input
'input[name*="stake"]'
'input[placeholder*="amount"]'
'input[type="number"]'

// Confirm button
'button[class*="place-bet"]'
'button:contains("Place Bet")'
'.bet-slip button[type="submit"]'
```

**Safety Mechanisms:**
- `isProcessing` flag prevents concurrent bet fills
- Never auto-clicks confirm button (manual review required)
- Graceful error handling with user notifications
- Detailed console logging for debugging
- Visual feedback at every step

**Key Files:**
- `content/base/bet_finder.js` - Core matching logic
- `content/sportsbooks/betus.js` - BetUS implementation
- `content/TESTING_GUIDE.md` - Testing instructions
- `manifest.json:44-50` - Content script injection
- `background.js:798-864` - Message passing to content scripts

**Key Functions:**

| Function | Purpose | Location |
|----------|---------|----------|
| `BetFinder.findGameElement()` | Locate game by team names | bet_finder.js:97 |
| `BetFinder.teamsMatch()` | Fuzzy team name matching | bet_finder.js:37 |
| `BetFinder.normalizeTeamName()` | Clean team names for matching | bet_finder.js:19 |
| `BetFinder.findBetButton()` | Find specific bet button | bet_finder.js:183 |
| `BetFinder.highlightElement()` | Visual highlight with color | bet_finder.js:251 |
| `BetUSBetFiller.fillBetSlip()` | Main auto-fill orchestration | betus.js:81 |
| `BetUSBetFiller.fillStakeAmount()` | Fill stake in bet slip | betus.js:203 |
| `BetUSBetFiller.showNotification()` | On-page notifications | betus.js:271 |

**Testing Instructions:**

See `content/TESTING_GUIDE.md` for detailed testing procedures.

Quick test from console:
```javascript
// Test team matching
const finder = new BetFinder('BetUS');
const game = finder.findGameElement('Lakers', 'Warriors', 'body');
finder.highlightElement(game, '#10b981', 5000);
```

**Next Steps:**
1. ✅ Test on live BetUS.com (user has account)
2. 📋 Document actual BetUS DOM selectors after inspection
3. 🔧 Adjust selectors based on real site structure
4. 🚀 Expand to other sportsbooks (DraftKings, FanDuel, etc.)
5. ⚡ Add retry logic for slow-loading pages
6. 🎯 Handle edge cases (suspended bets, unavailable markets)

**Known Limitations:**
- Requires specific DOM structure (common across most sportsbooks)
- May need sportsbook-specific selector overrides
- Assumes single bet slip (no parlays yet)
- Timing-sensitive (3-second wait for page load)

---

## File Structure

```
ARB_Auto_Bettor/
├── extension/
│   ├── manifest.json              # Chrome extension manifest (V3)
│   ├── background.js              # Service worker (1102 lines)
│   ├── offscreen.html             # Offscreen document for audio
│   ├── offscreen.js               # Audio playback handler
│   │
│   ├── popup/
│   │   ├── popup.html             # Main popup UI (4 tabs)
│   │   ├── popup.js               # UI logic and rendering (642 lines)
│   │   └── popup.css              # Styling with sport-specific colors (583 lines)
│   │
│   ├── settings/
│   │   ├── settings.html          # Settings page UI (301 lines)
│   │   ├── settings.js            # Settings logic (281 lines)
│   │   └── settings.css           # Settings styling
│   │
│   ├── content/
│   │   └── content.js             # Content script for bet slip auto-fill
│   │
│   └── icons/
│       └── icon.svg               # Extension icon
│
└── DEVELOPMENT_LOG.md             # This file
```

---

## Architecture & Data Flow

### 1. Backend → Extension Communication

**Polling System:**
- REST API polling every 5 seconds (WebSocket disabled)
- Endpoint: `http://localhost:8000/api/alerts/all`
- Separate endpoint for goalie pulls: `/api/goalie-pull-opportunities`

**Data Flow:**
```
Backend API
    ↓
background.js (fetchOpportunities)
    ↓
handleOpportunitiesUpdate() / handleSteamMovesUpdate() / etc.
    ↓
Check if NEW opportunity (via Sets)
    ↓
Play alert (if enabled in settings)
    ↓
Store in currentOpportunities / currentSteamMoves / etc.
    ↓
popup.js requests data via chrome.runtime.sendMessage
    ↓
Render cards in UI
```

### 2. Alert System Architecture

**Sound Alerts:**
- High Priority (5%+): Square wave, 4 beeps, urgent
- Medium Priority (3-5%): Sine wave, 2 beeps, moderate
- Low Priority (1-3%): Sine wave, 1 beep, gentle
- Steam Moves: Triangle wave, 3 fast beeps
- Goalie Pull: Square wave, 4 pulsing beeps (urgent)

**Voice Alerts:**
- Web Speech API via offscreen document
- Configurable rate, pitch, and volume
- Different announcements based on alert type
- Stale line information for steam moves

**Offscreen Document:**
Required for Manifest V3 service workers to play audio:
- `offscreen.html` - Minimal HTML document
- `offscreen.js` - Handles audio playback and TTS
- Created on-demand via `ensureOffscreenDocument()`
- Reasons: `['AUDIO_PLAYBACK']`

### 3. Settings Management

**Storage:**
- Chrome Storage Sync API (syncs across devices)
- Settings object stored at key: `'settings'`
- Loaded on extension startup
- Updated via settings page

**Default Settings:**
```javascript
{
  totalBankroll: 10000,
  maxBetPercentage: 2.0,
  minProfitThreshold: 2.0,
  betSizingMethod: 'flat_percentage',
  fixedBetAmount: 100,

  sportsbooks: {
    draftkings: { enabled: true, balance: 0 },
    fanduel: { enabled: true, balance: 0 },
    betmgm: { enabled: false, balance: 0 },
    caesars: { enabled: false, balance: 0 },
    betrivers: { enabled: false, balance: 0 }
  },

  autoBetMode: 'fill',
  skipInsufficientFunds: true,
  alertOnSkipped: false,

  enableArbitrageAlerts: true,
  enableSteamAlerts: true,
  enableLineAlerts: true,
  enableGoalieAlerts: true,

  soundEnabled: true,
  voiceEnabled: true,
  soundVolume: 0.5
}
```

---

## Key Functions Reference

### Background Script (background.js)

| Function | Purpose | Line |
|----------|---------|------|
| `loadSettings()` | Load settings from Chrome storage | 147-157 |
| `fetchOpportunities()` | Poll REST API for alerts | 1000-1058 |
| `handleOpportunitiesUpdate()` | Process arbitrage alerts | 511-567 |
| `handleSteamMovesUpdate()` | Process steam move alerts | 570-605 |
| `handleLineMovementsUpdate()` | Process line movement alerts | 608-642 |
| `handleGoaliePullsUpdate()` | Process goalie pull alerts | 645-680 |
| `updateBadge()` | Update extension badge count/color | 683-707 |
| `playGoaliePullAlert()` | Play goalie pull sound/voice | 752-775 |
| `playSteamMoveAlert()` | Play steam move sound/voice | 710-749 |
| `soundAlerts.playAndAnnounce()` | Play sound + voice for arb | 308-316 |
| `ensureOffscreenDocument()` | Create offscreen doc for audio | 322-340 |
| `buildBookmakerURL()` | Generate sportsbook URLs | 45-70 |

### Popup Script (popup.js)

| Function | Purpose | Line |
|----------|---------|------|
| `loadOpportunities()` | Request data from background | 135-174 |
| `renderOpportunities()` | Render arbitrage cards | 176-264 |
| `renderSteamMoves()` | Render steam move cards | 286-366 |
| `renderLineMovements()` | Render line movement cards | 368-411 |
| `renderGoaliePulls()` | Render goalie pull cards | 413-476 |
| `formatTimeAgo()` | Format relative timestamps | 32-49 |
| `formatGameTime()` | Format game start times | 51-74 |
| `getSportEmoji()` | Get sport emoji URL | 7-17 |
| `detectSport()` | Detect sport from game data | 19-29 |
| `getBookmaker()` | Get bookmaker name/logo | 77-101 |
| `switchTab()` | Switch between tabs | 273-284 |
| `updateStats()` | Update stat box counts | 266-271 |

### Settings Script (settings.js)

| Function | Purpose | Line |
|----------|---------|------|
| `loadSettings()` | Load settings from storage | 55-104 |
| `saveSettings()` | Save settings to storage | 107-179 |
| `resetSettings()` | Reset to defaults | 182-195 |
| `toggleFixedAmountInput()` | Show/hide fixed amount field | 233-240 |
| `showNotification()` | Display save notification | 243-255 |
| `calculateTotalBalance()` | Sum enabled book balances | 266-280 |

---

## Bookmaker URL Builder

**Supported Bookmakers (11):**
1. DraftKings
2. FanDuel
3. BetMGM
4. Caesars
5. BetRivers
6. Bovada
7. BetOnline
8. MyBookie
9. BetUS
10. LowVig
11. William Hill

**URL Pattern:**
```javascript
{
  base: 'https://sportsbook.draftkings.com',
  path: `/leagues/${sport}/${league}`
}
```

**Sport Keys:**
- `basketball` → NBA
- `americanfootball` → NFL, NCAAF
- `baseball` → MLB
- `icehockey` → NHL
- `soccer` → MLS, EPL

---

## Implementation Decisions & Reasoning

### 1. Why REST API Polling Instead of WebSocket?
**Decision:** Use REST polling (5-second interval) instead of WebSocket
**Reasoning:**
- More reliable for local development
- Easier to debug and monitor
- Less complex error handling
- WebSocket reconnection issues in Manifest V3
- 5-second polling is fast enough for betting opportunities

**Location:** `background.js:9-10`

### 2. Why Offscreen Document for Audio?
**Decision:** Use offscreen document instead of background script audio
**Reasoning:**
- Manifest V3 service workers can't play audio directly
- Offscreen documents have full DOM access
- Required for Web Speech API (TTS)
- Chrome's recommended approach

**Location:** `background.js:322-340`, `offscreen.html`, `offscreen.js`

### 3. Why JavaScript Sets for Duplicate Prevention?
**Decision:** Use Sets instead of arrays for tracking seen alerts
**Reasoning:**
- O(1) lookup time vs O(n) for arrays
- Built-in `.has()` and `.add()` methods
- Automatic deduplication
- Memory efficient with cleanup logic

**Location:** `background.js:110-120`

### 4. Why Sport-Specific Card Colors?
**Decision:** Color cards based on playing surface (court/field/ice)
**Reasoning:**
- Visual differentiation at a glance
- Intuitive sport recognition
- Enhances user experience
- Matches real-world associations

**Location:** `popup.css:150-228`

### 5. Why Simplified Goalie Pull Logic?
**Decision:** Simple triggers (5 min, 3rd period, 2-goal diff) instead of complex EV
**Reasoning:**
- User requested simplification for testing
- Complex EV calculations can be added later
- Simpler = more reliable alerts
- Easier to debug and verify

**Location:** Backend logic (not in extension)

---

## Known Issues & Technical Debt

### 1. Missing Goalie Pull Timestamp
**Issue:** Goalie pull cards show "🏒 Live Game" instead of actual game time
**Reason:** API might not provide `commence_time` for live games
**Solution:** Add game time to backend response or use live game time
**Priority:** Low

### 2. Bookmaker URL Accuracy
**Issue:** Some bookmaker URLs might not link directly to specific games
**Reason:** Sportsbook URL structures vary and change frequently
**Solution:** Regular URL pattern updates, possibly scrape actual game URLs
**Priority:** Medium

### 3. No Auto-Refresh in Popup
**Issue:** Popup refreshes every 10 seconds while open, but doesn't show "loading" state
**Reason:** User experience consideration - silent background updates
**Solution:** Add loading spinner or "Last updated" timestamp
**Priority:** Low

### 4. No Bet Slip Auto-Fill (Yet)
**Issue:** Extension doesn't automatically fill bet slips on sportsbook pages
**Reason:** Content scripts not fully implemented for all books
**Solution:** Implement content script selectors for each sportsbook
**Priority:** High (future enhancement)

### 5. Hardcoded Backend URL
**Issue:** Backend URL is hardcoded to `http://localhost:8000`
**Reason:** Development environment assumption
**Solution:** Make backend URL configurable in settings
**Priority:** Medium

**Location:** `background.js:7`

---

## Future Enhancements

### Planned Features
1. **Bet Slip Auto-Fill** - Automatically fill bet amounts on sportsbook sites
2. **Performance Tracking** - Track ROI, win rate, profit/loss over time
3. **Custom Alert Sounds** - Upload custom audio files for alerts
4. **Discord/Telegram Integration** - Send alerts to messaging apps
5. **Configurable Backend URL** - Connect to remote backend servers
6. **Historical Alert Log** - View past opportunities in popup
7. **Bankroll Management** - Track remaining balance across sportsbooks
8. **Advanced Filters** - Filter by sport, bookmaker, profit threshold
9. **Dark/Light Theme** - User-selectable color schemes
10. **Export Data** - Download opportunity history as CSV

### Experimental Ideas
- **Machine Learning ROI Prediction** - Predict opportunity success rate
- **Live Game Tracking** - Real-time score updates for goalie pull
- **Arbitrage Calculator** - Manual bet calculator in popup
- **Multi-Account Support** - Track multiple user bankrolls
- **Browser Notifications Permission** - Optional browser notifications

---

## Testing Checklist

### Before Each Release
- [ ] Test all 4 tabs render correctly
- [ ] Test sound alerts for each priority level
- [ ] Test voice announcements for each alert type
- [ ] Test settings persist after browser restart
- [ ] Test duplicate alert prevention works
- [ ] Test timestamp formatting (past, present, future)
- [ ] Test empty states for all tabs
- [ ] Test bookmaker URLs open correctly
- [ ] Test sport detection and emoji rendering
- [ ] Test badge count and color updates
- [ ] Test goalie pull alert triggers correctly
- [ ] Test settings page save/reset buttons
- [ ] Test individual alert type toggles
- [ ] Test volume slider updates correctly

### Manual Testing Commands
```javascript
// In popup.js console:
formatTimeAgo(new Date(Date.now() - 120000)); // "2 mins ago"
formatGameTime(new Date(Date.now() + 86400000)); // "Tomorrow X:XX PM"

// In background.js console:
soundAlerts.playHighPriority();
soundAlerts.speak("Testing voice announcement");
```

---

## Quick Reference Commands

### Reload Extension
1. Go to `chrome://extensions/`
2. Find "ARB Auto Bettor"
3. Click refresh icon

### View Background Script Console
1. Go to `chrome://extensions/`
2. Find "ARB Auto Bettor"
3. Click "service worker" link

### Clear Settings
```javascript
chrome.storage.sync.clear();
```

### View Current Opportunities
```javascript
chrome.runtime.sendMessage({type: 'get_opportunities'}, console.log);
```

### Force Fetch Opportunities
```javascript
fetchOpportunities();
```

---

## Version History

### v1.0.0 (Initial Development)
- Core arbitrage detection
- Basic sound alerts
- WebSocket connection

### v1.1.0 (Steam & Lines)
- Steam move detection
- Line movement tracking
- 3-tab UI

### v1.2.0 (Goalie Pull)
- NHL goalie pull alerts
- 4-tab UI
- Sport-specific styling

### v1.3.0 (Settings Overhaul)
- Individual alert type toggles
- Improved settings page
- Duplicate alert prevention

### v1.4.0 (Timestamps) - CURRENT
- Alert detection timestamps
- Game start time display
- Smart time formatting
- Development log created

---

## Contact & Support

**Developer:** Claude Code (Anthropic)
**User:** nashr
**Project Location:** `C:\Users\nashr\backend\ARB_Auto_Bettor\`

**Related Projects:**
- NBA/NCAAB Sports Betting Analytics System (parent project)
- Google Sheets integration for tracking
- KenPom scraping system

---

## Notes for Future Developers

1. **Always test alerts with settings disabled** - Ensure conditional checks work
2. **Clean up Sets regularly** - Prevent memory leaks from old opportunity IDs
3. **Update bookmaker URLs** - Sportsbooks change their URL structures
4. **Maintain backwards compatibility** - Old settings objects should still work
5. **Document breaking changes** - Update this log when making structural changes
6. **Test across Chrome versions** - Manifest V3 behavior varies by version
7. **Monitor API rate limits** - 5-second polling = 720 requests/hour
8. **Keep popup lightweight** - Popup closes when focus lost, minimize state

---

---

## Testing Progress & Notes

### Bovada Auto-Fill Testing (2025-10-18)

**Status:** ⚠️ Partially Working - Needs More Testing

**What Works:**
- ✅ Content script loads successfully on Bovada
- ✅ Script initializes and is ready to receive messages
- ✅ Goalie pull alert sound plays correctly
- ✅ Opens to correct game page
- ✅ Bet slip appears (sometimes)

**What Needs Debugging:**
- ❌ Bet slip input not filling with $100
- ❌ Inconsistent bet button clicking
- ⚠️ Need to identify correct Bovada bet slip input selector

**Issues Encountered:**
1. **Line Movement** - Initial test used 6.5, but line moved to 5.5 during testing
2. **Solution Applied** - Changed to search for ANY "Over" bet (removed specific point requirement)
3. **Account Safety** - User correctly identified risk of triggering fraud detection with too many test attempts

**Bovada-Specific Observations:**
- Bet slip detected via mutation observer (working)
- Content script logs show proper initialization
- Need actual DOM selectors from manual inspection when safe to test

**Next Steps (When Safe to Test):**
1. Use demo/test account if available
2. Manually inspect bet slip input field (right-click → inspect)
3. Get exact selector: type, name, id, class attributes
4. Consider testing on less sensitive sportsbook first (BetUS, etc.)
5. Limit testing frequency to avoid account flags

**Testing Safety Notes:**
- ⚠️ Avoid rapid repeated tests on same sportsbook
- ⚠️ Bovada may have fraud detection - be cautious
- ✅ Always test with small amounts first
- ✅ Consider using VPN or different browser profile for testing
- ✅ Space out test attempts by several minutes

---

### BetUS Auto-Fill Testing (2025-10-18)

**Status:** 🚧 In Progress - Initial Test Failed

**Test Configuration:**
- ✅ Changed from Bovada to BetUS (empty account = safer)
- ✅ Using NHL games instead of NBA (hockey is live)
- ✅ Looking for ANY "Over" bet (no specific total)
- ✅ Opening live-betting page: https://www.betus.com.pa/live-betting/
- ✅ $100 stake amount
- ✅ Sound alert working

**Test Results:**
- ✅ Extension reloaded successfully
- ✅ Test button clicked
- ✅ Live-betting page opened correctly
- ❌ **Bet slip did not open**

**What Happened:**
1. User clicked "🧪 Test BetUS Auto-Fill" button
2. Initially opened NBA page (wrong URL)
3. Fixed: Changed URL from `/sportsbook/basketball/nba/` to `/live-betting/`
4. Second test: Live-betting page loaded
5. No bet slip appeared - script likely couldn't find the game or bet button

**Changes Made:**
- `background.js:1044` - Changed BetUS URL to live-betting page
- `popup.js:720-775` - Using NHL games in mock opportunity generator
- Test uses random NHL teams: Bruins, Avalanche, Maple Leafs, Lightning, etc.

**Next Steps (For Next Session):**
1. Check console logs in BetUS page (F12 → Console)
2. Look for `[BETUS_FILLER]` messages
3. Identify why game wasn't found or bet button wasn't clicked
4. May need to manually inspect BetUS live-betting DOM structure
5. Verify NHL game names match between test and BetUS page
6. Consider using specific game URL like we did for Bovada

**Possible Issues to Debug:**
- Game name mismatch (our test vs BetUS display)
- Bet button selector not matching BetUS structure
- Page load timing (may need longer wait)
- Live-betting page has different DOM than static pages

**User Feedback:**
> "No it didnt pull up a bet slip save this chat for the files and we will try again later. I'm tired for the day."

**Session Status:** Paused - will resume debugging next session

---

**Last Updated:** 2025-10-18
**Log Created By:** Claude Code (Anthropic)
