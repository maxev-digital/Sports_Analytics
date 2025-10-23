# Auto-Betting Testing Guide

## BetUS.com Auto-Fill System

### 🎯 What We Built

The auto-betting system can:
1. **Find games** on sportsbook pages by team names
2. **Locate specific bets** (spread, total, moneyline)
3. **Fill bet slips** with calculated stake amounts
4. **Highlight confirm buttons** (without clicking for safety)

---

## 🧪 How to Test on BetUS.com

### Step 1: Load the Extension

1. Go to `chrome://extensions/`
2. Enable "Developer mode" (top right)
3. Click "Load unpacked"
4. Select: `C:\Users\nashr\backend\ARB_Auto_Bettor\extension\`
5. Extension should load successfully

### Step 2: Open BetUS.com

1. Navigate to: `https://www.betus.com.pa/sportsbook/`
2. **IMPORTANT**: You need to be logged in (even without money)
3. Go to NBA or any sport with games today
4. Open the browser console (`F12`) to see debug logs

### Step 3: Check Content Script Loaded

In the browser console, you should see:
```
[BETUS_FILLER] 🟢 BetUS Auto-Bettor initialized
[BETUS_FILLER] Settings loaded: {...}
[BETUS_FILLER] ✅ Ready to receive bet opportunities
```

If you see this, the content script is working! ✅

---

## 🔍 Manual Testing (Without Backend)

You can test the bet finder manually from the browser console on BetUS.com:

### Test 1: Find a Game

```javascript
// Create bet finder instance
const finder = new BetFinder('BetUS');

// Find a game (replace with actual teams on the page)
const gameElement = finder.findGameElement('Lakers', 'Warriors', 'body');

// Should highlight the game element
if (gameElement) {
  console.log('✅ Game found!', gameElement);
} else {
  console.log('❌ Game not found');
}
```

### Test 2: Find Market Tab

```javascript
// After finding game element
const totalTab = finder.findMarketTab('totals', gameElement);

if (totalTab) {
  console.log('✅ Total tab found!', totalTab);
  // Click it
  totalTab.click();
}
```

### Test 3: Find Bet Button

```javascript
// Find Over 225.5 button
const betButton = finder.findBetButton(gameElement, 'totals', 'Over', 225.5);

if (betButton) {
  console.log('✅ Bet button found!', betButton);
  // Highlight it
  finder.highlightElement(betButton, '#10b981', 5000);
}
```

### Test 4: Simulate Bet Fill

```javascript
// Send a test message to the content script
chrome.runtime.sendMessage({
  type: 'fill_bet_slip',
  opportunity: {
    home_team: 'Lakers',
    away_team: 'Warriors',
    market_type: 'totals',
    outcome: 'Over',
    point: 225.5,
    odds: -110,
    stake_amount: 100
  },
  autoBetMode: 'fill'
});
```

---

## 📋 What to Look For on BetUS

### DOM Structure to Inspect

When you're on BetUS.com, inspect the page and look for:

#### 1. Game Container
- Class names like: `.game-row`, `.event-container`, `.match-card`
- Text content with both team names
- Example:
  ```html
  <div class="event-row">
    <span>Lakers vs Warriors</span>
    <span>7:00 PM</span>
  </div>
  ```

#### 2. Market Tabs
- Buttons or links with text: "Total", "Spread", "Moneyline"
- Example:
  ```html
  <button class="market-tab">Total</button>
  <button class="market-tab">Spread</button>
  ```

#### 3. Bet Buttons
- Buttons with odds and outcomes
- Example:
  ```html
  <button class="bet-button">
    <span>Over 225.5</span>
    <span class="odds">-110</span>
  </button>
  ```

#### 4. Bet Slip Input
- Input field for stake amount
- Example:
  ```html
  <input type="number" name="stake" placeholder="Enter amount" />
  ```

#### 5. Confirm Button
- Button to place the bet
- Example:
  ```html
  <button class="place-bet-btn">Place Bet</button>
  ```

### Record Selectors

**Take notes on what you find!** For example:

```javascript
// BetUS DOM Selectors (update after inspection)
const BETUS_SELECTORS = {
  gameContainer: '.event-row',          // Container for each game
  gameTitle: '.event-title',            // Team names element
  marketTabs: '.market-tab',            // Market tab buttons
  betButtons: '.bet-button',            // Individual bet buttons
  betSlipInput: 'input[name="stake"]',  // Stake input field
  confirmButton: '.place-bet-btn'       // Confirm button
};
```

---

## 🐛 Debugging Tips

### Console Logs to Watch

The content script logs everything it's doing:

```
[BET_FINDER:BetUS] Searching for game: Warriors @ Lakers
[BET_FINDER:BetUS] ✅ Found 3 potential matches
[BET_FINDER:BetUS] Best match: Warriors @ Lakers - 7:00 PM
[BET_FINDER:BetUS] Looking for market type: totals
[BET_FINDER:BetUS] ✅ Found market tab: Total
[BET_FINDER:BetUS] Looking for bet: Over 225.5
[BET_FINDER:BetUS] ✅ Found bet button: Over 225.5 (-110)
[BETUS_FILLER] 🎯 Attempting to fill bet slip for: {...}
[BETUS_FILLER] 🖱️ Clicking bet button
[BETUS_FILLER] ⏳ Waiting for bet slip...
[BETUS_FILLER] ✅ Bet slip appeared!
[BETUS_FILLER] 💵 Stake filled: 100
[BETUS_FILLER] ✅ Bet slip filled successfully!
```

### Common Issues

**"Game not found"**
- Check team names match exactly
- Try searching for one team at a time
- BetUS might use abbreviations (LAL instead of Lakers)

**"Market tab not found"**
- BetUS might auto-select totals, no tab needed
- Look for tabs with different text ("O/U" instead of "Total")

**"Bet button not found"**
- Line might have moved (225.5 → 226.0)
- Bet might be disabled/suspended
- Point value might be formatted differently ("225½" vs "225.5")

**"Bet slip input not found"**
- Bet slip might not be open yet
- Need to wait longer for it to appear
- Input might have different selector

---

## 🎨 Visual Indicators

When the auto-fill works, you should see:

1. **Blue highlight** on game element (2 seconds)
2. **Orange highlight** on bet button (1.5 seconds)
3. **Bet button clicks** automatically
4. **Green highlight** on stake input (3 seconds)
5. **Green pulsing glow** on confirm button (5 seconds)
6. **Green notification** at top-right of page:
   ```
   ✅ Bet Slip Filled!
   Warriors @ Lakers
   Over 225.5
   Stake: $100
   ```

---

## 📝 Next Steps After Testing

### If it works:
1. Document the exact BetUS DOM selectors you found
2. Test with different sports (NFL, NHL, MLB)
3. Test with different market types (spreads, moneylines)
4. Update `betus.js` with BetUS-specific selectors if needed

### If it doesn't work:
1. Check console logs for errors
2. Inspect BetUS DOM structure manually
3. Update selectors in `bet_finder.js` or `betus.js`
4. Report specific issues (which step failed)

### Improvements to Make:
1. Add BetUS-specific selector overrides
2. Handle dynamic content loading (SPAs)
3. Add retry logic for slow-loading pages
4. Handle edge cases (suspended bets, unavailable markets)

---

## 🚀 Testing with Real Backend

Once you have the backend running with live opportunities:

1. Start backend: `uvicorn main:app --reload`
2. Backend should detect arbitrage opportunities
3. Extension will auto-open BetUS tab (if BetUS is one of the books)
4. Content script will auto-fill bet slip
5. You review and confirm manually

**NEVER** click the confirm button automatically - always manual final review!

---

## 📊 Success Metrics

The system is working well if:
- ✅ Finds games 90%+ of the time
- ✅ Fills correct stake amount 100% of the time
- ✅ Highlights correct bet button 90%+ of the time
- ✅ Takes less than 3 seconds total
- ✅ Shows clear visual feedback
- ✅ Doesn't crash or error out

---

## 🔒 Safety Features Built-In

1. **Never auto-clicks confirm** - Always requires manual confirmation
2. **Visual highlighting** - Shows exactly what it's doing
3. **Detailed logging** - Full transparency in console
4. **Graceful failures** - Shows error messages instead of breaking
5. **Settings respect** - Only works if autoBetMode is enabled

---

## 📞 Support

If you encounter issues:
1. Check console for error messages
2. Take screenshots of BetUS DOM structure
3. Note which step fails (game finding, market selection, etc.)
4. Update this guide with BetUS-specific quirks you discover

**Remember**: This is a testing/development tool. Always verify bets manually before confirming!
