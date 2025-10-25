# Testing BetUS Auto-Fill - Quick Start Guide

## 🎯 What We Built

A complete testing system that:
1. **Creates a test opportunity** with a random NBA game
2. **Opens BetUS.com** automatically
3. **Finds the game** on the page
4. **Clicks the bet button**
5. **Fills the bet slip** with $100 stake
6. **Highlights the confirm button** (you click manually)

---

## 🚀 Quick Test (3 Steps)

### Step 1: Load Extension

```bash
1. Open Chrome
2. Go to chrome://extensions/
3. Enable "Developer mode" (top right)
4. Click "Load unpacked"
5. Select folder: C:\Users\nashr\backend\ARB_Auto_Bettor\extension\
6. Extension should load with no errors
```

### Step 2: Click Test Button

```bash
1. Click the extension icon in Chrome toolbar
2. Popup opens
3. Scroll down to bottom
4. Click "🧪 Test BetUS Auto-Fill" button
```

### Step 3: Watch the Magic

```bash
1. BetUS.com opens in new tab automatically
2. Watch console (F12) for logs
3. Content script will:
   ✅ Find the game (blue highlight)
   ✅ Click bet button (orange highlight)
   ✅ Fill stake amount (green highlight)
   ✅ Highlight confirm button (pulsing green)
4. YOU manually review and click confirm
```

---

## 📊 What to Watch For

### Console Logs (F12)

**Background Script Console** (`chrome://extensions/` → Click "service worker"):
```
[ARB] 🧪 Testing BetUS auto-fill with opportunity: {...}
[ARB] BetUS tab created, ID: 123
[ARB] Sending fill_bet_slip message to BetUS tab
[ARB] ✅ Test message sent to BetUS content script
```

**BetUS Page Console** (on BetUS.com page, press F12):
```
[BETUS_FILLER] 🟢 BetUS Auto-Bettor initialized
[BETUS_FILLER] ✅ Ready to receive bet opportunities
[BETUS_FILLER] 📨 Message received: fill_bet_slip
[BETUS_FILLER] 🎯 Attempting to fill bet slip for: {...}
[BET_FINDER:BetUS] Searching for game: Warriors @ Lakers
[BET_FINDER:BetUS] ✅ Found 1 potential matches
[BET_FINDER:BetUS] Looking for market type: totals
[BET_FINDER:BetUS] ✅ Found market tab: Total
[BET_FINDER:BetUS] Looking for bet: Over 225.5
[BET_FINDER:BetUS] ✅ Found bet button: Over 225.5 (-110)
[BETUS_FILLER] 🖱️ Clicking bet button
[BETUS_FILLER] ⏳ Waiting for bet slip...
[BETUS_FILLER] ✅ Bet slip appeared!
[BETUS_FILLER] 💵 Stake filled: 100
[BETUS_FILLER] ✅ Bet slip filled successfully!
```

### Visual Feedback

You should see on the BetUS page:
1. **Blue glow** around game element (2 seconds)
2. **Orange glow** around bet button (1.5 seconds)
3. **Bet button clicks** automatically
4. **Green glow** around stake input (3 seconds)
5. **Pulsing green glow** around confirm button (5 seconds)
6. **Green notification** top-right:
   ```
   ✅ Bet Slip Filled!
   Warriors @ Lakers
   Over 225.5
   Stake: $100
   ```

---

## 🎲 Test Opportunities Generated

The test button creates random opportunities with:
- **Random NBA teams** (Lakers, Celtics, Heat, Bucks, etc.)
- **Random totals** (215.5, 220.5, 225.5, 228.5, 232.5)
- **Always "Over" on BetUS**
- **$100 stake amount**
- **Always uses real team names** for matching

Example test opportunity:
```json
{
  "home_team": "Los Angeles Lakers",
  "away_team": "Golden State Warriors",
  "market_type": "totals",
  "outcome": "Over",
  "point": 225.5,
  "odds": -110,
  "stake_amount": 100,
  "book1": "betus"
}
```

---

## 🐛 Troubleshooting

### "Game not found"

**Possible reasons:**
- BetUS doesn't have NBA games right now
- Team names don't match exactly
- Page is still loading

**Solutions:**
- Log in to BetUS first
- Navigate to NBA section manually
- Try again (different random teams)
- Check console for exact team names BetUS uses

### "Bet slip input not found"

**Possible reasons:**
- Bet slip didn't open
- Different selector on BetUS
- Need to be logged in

**Solutions:**
- Log in to BetUS account
- Manually click a bet first to see bet slip
- Inspect bet slip input field
- Update selector in `betus.js`

### "Content script not loaded"

**Check:**
```
1. Extension is loaded at chrome://extensions/
2. BetUS URL matches manifest: https://www.betus.com.pa/*
3. Reload extension
4. Reload BetUS page
5. Check for errors in extension console
```

### No console logs on BetUS page

**Fix:**
```
1. Reload extension at chrome://extensions/
2. Hard refresh BetUS page (Ctrl+Shift+R)
3. Check if URL is correct: https://www.betus.com.pa/
4. Look for content script injection errors
```

---

## 📸 What to Document

When testing, take notes on:

### 1. Game Container
```javascript
// What element wraps each game?
// Example:
<div class="event-row">
  <span class="teams">Lakers vs Warriors</span>
</div>

// Record the selector:
gameContainer: '.event-row'
```

### 2. Market Tabs
```javascript
// How are tabs structured?
// Example:
<button class="market-button">Total</button>

// Record the selector:
marketTab: '.market-button'
```

### 3. Bet Buttons
```javascript
// What do bet buttons look like?
// Example:
<button class="odd-btn">
  <span>Over 225.5</span>
  <span>-110</span>
</button>

// Record the selector:
betButton: '.odd-btn'
```

### 4. Bet Slip Input
```javascript
// Where's the stake input?
// Example:
<input type="number" name="wager" />

// Record the selector:
stakeInput: 'input[name="wager"]'
```

### 5. Confirm Button
```javascript
// What's the confirm button?
// Example:
<button class="place-wager-btn">Place Wager</button>

// Record the selector:
confirmButton: '.place-wager-btn'
```

---

## 📝 Report Back

After testing, report:

✅ **What worked:**
- Did it find the game?
- Did it click the bet?
- Did it fill the stake?
- Did it highlight confirm button?

❌ **What didn't work:**
- Which step failed?
- Error messages in console?
- Screenshots of BetUS DOM structure?

📋 **BetUS DOM selectors:**
- Record actual selectors you found
- We'll update `betus.js` with correct ones

---

## 🎯 Success Criteria

The test is successful if:
1. ✅ BetUS page opens
2. ✅ Content script initializes (see console log)
3. ✅ Game is found and highlighted
4. ✅ Bet button is clicked
5. ✅ Bet slip opens
6. ✅ Stake amount is filled ($100)
7. ✅ Confirm button is highlighted (pulsing green)
8. ✅ Green notification appears

**You don't need to actually place the bet!** Just verify the auto-fill worked correctly.

---

## 🔧 If You Need to Adjust Selectors

After testing, if selectors don't work, update:

**File:** `extension/content/sportsbooks/betus.js`

**Lines to update:**
```javascript
// Around line 90-100, add BetUS-specific selectors:
async findGame(opportunity) {
  const containerSelectors = [
    '.YOUR-ACTUAL-SELECTOR-HERE',  // <-- Add real BetUS selector
    '.events-list',
    '.games-list',
    'body'
  ];
  // ... rest of function
}
```

---

## 🎬 Next Steps After Successful Test

Once BetUS works:
1. Document the selectors you found
2. Update `betus.js` with BetUS-specific selectors
3. Test with different sports (NFL, NHL, MLB)
4. Test with different market types (spreads, moneylines)
5. Expand to other sportsbooks (DraftKings, FanDuel, etc.)

---

## 📞 Need Help?

Check these resources:
- `content/TESTING_GUIDE.md` - Detailed testing guide
- `content/base/bet_finder.js` - Core matching logic
- `content/sportsbooks/betus.js` - BetUS implementation
- Browser console logs - All actions are logged

**Ready to test?** Click the button and watch the magic happen! 🚀
