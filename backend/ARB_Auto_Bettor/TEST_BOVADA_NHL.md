# 🏒 Test Bovada NHL Auto-Fill - Live Game

## 🎯 What This Tests

**Kills TWO birds with one stone:**
1. ✅ **Goalie Pull Alert System** - Empty net goal opportunity detection
2. ✅ **Bovada Auto-Fill** - Automated bet slip filling on Bovada.lv

**Live Game:**
- **Boston Bruins @ Colorado Avalanche**
- **URL:** https://www.bovada.lv/sports/hockey/nhl/boston-bruins-colorado-avalanche-202510182111
- **Bet:** OVER 6.5 (goalie pull = empty net = more goals)
- **Stake:** $100

---

## 🚀 Quick Test (3 Steps)

### Step 1: Load Extension
```
1. Go to chrome://extensions/
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select: C:\Users\nashr\backend\ARB_Auto_Bettor\extension\
5. Check for errors - should load clean
```

### Step 2: Click Test Button
```
1. Click extension icon in toolbar
2. Popup opens
3. Scroll to bottom
4. Click "🏒 Test Bovada NHL (Goalie Pull)"
```

### Step 3: Watch the Auto-Fill
```
1. Bovada opens to exact game page
2. Watch console (F12) for logs
3. Content script will:
   ✅ Find game (Bruins vs Avalanche)
   ✅ Click OVER 6.5 bet
   ✅ Fill $100 stake
   ✅ Highlight confirm button
4. YOU manually review and place bet (if desired)
```

---

## 📊 What You Should See

### Extension Console Logs
```
[TEST] Testing Bovada auto-fill with NHL game...
[TEST] Using live NHL game: Bruins @ Avalanche
[TEST] Opening Bovada at: https://www.bovada.lv/sports/hockey/nhl/...
[TEST] Bovada tab opened, auto-fill triggered
```

### Background Service Worker
```
[ARB] 🧪 Testing auto-fill with opportunity
[ARB] 🏒 Using specific game URL: https://www.bovada.lv/...
[ARB] Opening BOVADA at: https://www.bovada.lv/...
[ARB] BOVADA tab created, ID: 123
[ARB] Sending fill_bet_slip message to BOVADA tab
[ARB] ✅ Test message sent to BOVADA content script
```

### Bovada Page Console
```
[BOVADA_FILLER] 🟢 Bovada Auto-Bettor initialized
[BOVADA_FILLER] ✅ Ready to receive bet opportunities
[BOVADA_FILLER] 📨 Message received: fill_bet_slip
[BOVADA_FILLER] 🎯 Attempting to fill bet slip for: {...}
[BET_FINDER:Bovada] Searching for game: Boston Bruins @ Colorado Avalanche
[BET_FINDER:Bovada] ✅ Found bet button
[BOVADA_FILLER] 🖱️ Clicking bet button
[BOVADA_FILLER] ⏳ Waiting for bet slip...
[BOVADA_FILLER] ✅ Bet slip appeared!
[BOVADA_FILLER] 💵 Stake filled: 100
[BOVADA_FILLER] ✅ Bet slip filled successfully!
```

### Visual Feedback on Bovada
1. **Blue highlight** - Game element found (Bruins @ Avalanche)
2. **Orange highlight** - OVER 6.5 bet button found and clicked
3. **Green highlight** - $100 stake filled in bet slip
4. **Pulsing green** - Confirm button highlighted (ready to place)
5. **Success notification** - Green popup top-right:
   ```
   ✅ Bet Slip Filled!
   Boston Bruins @ Colorado Avalanche
   Over 6.5
   Stake: $100
   ```

---

## 🧪 Test Opportunity Data

The button creates this test opportunity:
```json
{
  "sport": "icehockey_nhl",
  "home_team": "Colorado Avalanche",
  "away_team": "Boston Bruins",
  "market_type": "totals",
  "outcome": "Over",
  "point": 6.5,
  "odds": -110,
  "stake_amount": 100,
  "book1": "bovada",
  "bovada_url": "https://www.bovada.lv/sports/hockey/nhl/boston-bruins-colorado-avalanche-202510182111"
}
```

**Why OVER 6.5?**
- Goalie pull scenarios mean empty net goals
- Empty net = easier to score
- OVER bet has higher probability when goalie is pulled
- This simulates the "strong OVER potential" you mentioned

---

## 🎯 What the Auto-Fill Should Do

1. **Opens exact game URL** - Goes directly to Bruins @ Avalanche
2. **Finds totals market** - Looks for Over/Under section
3. **Clicks OVER 6.5** - Finds and clicks the Over button
4. **Bet slip opens** - Bovada's bet slip appears on right side
5. **Fills $100** - Enters stake amount in bet slip input
6. **Highlights confirm** - Pulsing green on "Place Bet" button

---

## 🐛 Troubleshooting

### "Game not found"
**Solutions:**
- Game might not be live yet
- Team names might not match Bovada's format
- Check Bovada page manually to see team names
- Look at console for exact team name matching

### "Bet button not found"
**Possible causes:**
- Over/Under not available for this game
- Different total (might be 6.0 or 7.0, not 6.5)
- Bet is suspended/unavailable

**Solutions:**
- Manually check what totals are available
- Update test opportunity with correct total
- Look at Bovada DOM structure

### "Bet slip input not found"
**Fix:**
- Log in to Bovada first
- Manually click a bet to see bet slip
- Inspect the stake input field
- Update selectors in `bovada.js`

---

## 📋 What to Document

After testing, record:

### 1. Game Element Selector
```javascript
// How is the game displayed on Bovada?
// Example:
<div class="coupon-container">
  <div class="game-header">Bruins @ Avalanche</div>
</div>

// Record selector:
gameContainer: '.coupon-container'
```

### 2. Bet Button Selector
```javascript
// How are Over/Under buttons structured?
// Example:
<button class="outcome-btn">
  <span>Over 6.5</span>
  <span>-110</span>
</button>

// Record selector:
betButton: '.outcome-btn' or 'sp-outcome'
```

### 3. Bet Slip Input Selector
```javascript
// Where's the stake input in bet slip?
// Example:
<input type="tel" class="stake-input" />

// Record selector:
stakeInput: 'input[type="tel"]' or 'input[class*="stake"]'
```

### 4. Confirm Button
```javascript
// What's the "Place Bet" button?
// Example:
<button class="place-wager">Place Wager</button>

// Record selector:
confirmButton: '.place-wager' or 'button[class*="place"]'
```

---

## ✅ Success Criteria

Test is successful if:
1. ✅ Bovada opens to exact game page
2. ✅ Content script initializes (console log)
3. ✅ Bruins @ Avalanche game is found
4. ✅ OVER 6.5 bet button is clicked
5. ✅ Bet slip opens on right side
6. ✅ $100 stake is filled
7. ✅ Confirm button is highlighted
8. ✅ Success notification appears

**You don't need to actually place the bet!** Just verify auto-fill works.

---

## 🔍 Bovada-Specific Notes

**Bovada is different from other sportsbooks:**
- Uses `<sp-outcome>` custom elements (might need special handling)
- Bet slip appears as sidebar on right
- Often uses `type="tel"` for stake input (not `type="number"`)
- May require clicking expand button to see all markets
- Team names might be formatted differently (check exact spelling)

**Expected Bovada DOM:**
- Game container: `.coupon-container` or `[class*="event"]`
- Bet buttons: `sp-outcome` or `.outcome`
- Bet slip: `.betslip-container` or `[class*="betslip"]`
- Stake input: `input[type="tel"]` or `input[class*="stake"]`
- Confirm: `button[class*="place"]` or similar

---

## 🎬 Next Steps After Test

### If it works perfectly:
1. ✅ Document exact Bovada selectors you found
2. 📋 Update `bovada.js` with Bovada-specific selectors
3. 🚀 Test with other NHL games
4. 🏀 Test with other sports (NBA, NFL, MLB)
5. 🎯 Integrate with real goalie pull alerts

### If it partially works:
1. Note which step failed (game finding, bet clicking, slip filling)
2. Inspect Bovada DOM at failure point
3. Update selectors in `bovada.js`
4. Try again

### If it doesn't work at all:
1. Check console for errors
2. Make sure extension is loaded
3. Verify Bovada URL is correct
4. Try manual click to see bet slip structure
5. Report specific error messages

---

## 📞 Report Back

After testing, tell me:

✅ **What worked:**
- Did Bovada open to correct game?
- Did it find the game element?
- Did it click the OVER bet?
- Did bet slip open?
- Did it fill $100?

❌ **What didn't work:**
- Which step failed?
- Error messages?
- Screenshots of Bovada structure?

📋 **Bovada DOM info:**
- Actual selectors for game, bet button, bet slip, confirm
- Any Bovada-specific quirks you noticed

---

## 🎯 Why This Test is Perfect

1. **Real live game** - Bruins @ Avalanche is happening now
2. **Specific URL** - We know exactly where to go
3. **Goalie pull context** - OVER bet makes sense for empty net scenario
4. **Two features tested** - Auto-fill + goalie pull opportunity detection
5. **Safe testing** - Can test without placing actual bet

---

**Ready?** Just click the button and watch it work! 🏒🚀

Report back with what you see!
