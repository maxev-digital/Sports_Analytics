# Bovada Test Mode - Quick Start Guide

## 🎯 Goal
Test the ARB Auto Bettor extension with Bovada.lv using a low $5 stake (no arbitrage needed).

---

## 📋 Prerequisites

1. **Chrome Extension Loaded**
   - Extension files are at: `C:\Users\nashr\backend\ARB_Auto_Bettor\extension`
   - Must load in Chrome as unpacked extension

2. **Bovada Account** (optional but recommended)
   - You can test without logging in, but bet slip won't be placeable
   - With login: You can place actual $5 test bets

---

## 🚀 Installation Steps

### Step 1: Load Extension in Chrome

1. Open Chrome and go to: `chrome://extensions/`
2. Enable **"Developer mode"** (toggle in top-right)
3. Click **"Load unpacked"**
4. Navigate to: `C:\Users\nashr\backend\ARB_Auto_Bettor\extension`
5. Click **"Select Folder"**

✅ **Success**: You should see "ARB Auto Bettor™" in your extensions list

### Step 2: Verify Extension Loaded

1. Look for the extension icon in Chrome toolbar (should be a dollar sign or icon)
2. Click the icon to open popup
3. Should see:
   - Header: "SportTrader.io ARB Auto Bettor"
   - Status: "Connecting..." or "Connected"
   - Stats showing arbitrage opportunities
   - **Orange "Test Bovada Auto-Fill ($5)" button** at the bottom

---

## 🧪 Testing the Extension

### Method 1: Using Test Button (Easiest)

1. **Click the extension icon** to open popup
2. Scroll down to see **"🧪 Test Mode"** section (orange box)
3. Click **"Test Bovada Auto-Fill ($5)"**
4. Bovada.lv will open automatically
5. **IMPORTANT**: Click any bet on Bovada (any game, any market)
6. Watch as the extension:
   - Detects bet slip opening
   - Fills in $5 stake automatically
   - Highlights "Place Bet" button (green pulsing glow)
7. **YOU manually click "Place Bet"** if you want to place the bet

### Method 2: Manual Testing (More Control)

1. Open Bovada.lv manually in a new tab
2. Navigate to any sport (Basketball, Football, etc.)
3. Click a bet to open the bet slip
4. Open Chrome DevTools (F12)
5. Go to **Console** tab
6. Look for:
   ```
   [ARB] Bovada content script loaded
   [ARB BOVADA] Ready for auto-fill. Waiting for bet slip...
   ```
7. If bet slip is already open, you should see:
   ```
   [ARB BOVADA] Bet slip detected opening
   [ARB BOVADA] Found stake input with selector: input[type="number"]
   [ARB BOVADA] ✅ Stake filled: 5.00
   ```

---

## 🔍 What to Look For

### ✅ **Success Indicators:**

1. **Green notification overlay** appears saying "✅ Bet Slip Filled!"
2. **Stake input** shows "$5.00"
3. **"Place Bet" button** has green pulsing glow and border
4. Console shows successful log messages

### ⚠️ **Manual Mode (If Auto-Fill Doesn't Work):**

1. **Orange notification** appears with manual instructions
2. Says "Please click a bet to open the bet slip"
3. You manually enter $5 and click "Place Bet"

### ❌ **Troubleshooting:**

**Issue**: No notification appears
- Check DevTools Console for errors
- Make sure bet slip is visible on page
- Try clicking a different bet

**Issue**: Stake input not filled
- Bovada's HTML may have changed
- Check console for selector errors
- Extension will show manual instructions as fallback

**Issue**: "Place Bet" button not highlighted
- Extension couldn't find the button
- Button will still work - just not glowing
- Look for console message about button not found

---

## 🎬 Step-by-Step Test Scenario

**Scenario: Test with NBA game (no account needed)**

1. Load extension in Chrome ✅
2. Click extension icon ✅
3. Click "Test Bovada Auto-Fill ($5)" button ✅
4. Wait for Bovada.lv to load (3-5 seconds) ✅
5. See NBA games listed ✅
6. Click any moneyline bet (e.g., "Lakers -150") ✅
7. Bet slip opens on right side ✅
8. **Watch**: Stake field fills with "5.00" automatically! ✅
9. **Watch**: "Place Bet" button starts pulsing green! ✅
10. **See**: Green notification overlay appears ✅
11. **YOU**: Click "Place Bet" if you want to place bet ✅

**Expected Time**: 30 seconds total

---

## 📝 Console Output (What You Should See)

### In Extension Service Worker:
```
[ARB] ARB Auto Bettor™ background service worker starting...
[ARB] Starting REST API polling (WebSocket disabled)...
```

### In Bovada Page Console:
```
[ARB] Bovada content script loaded
[ARB BOVADA] Ready for auto-fill. Waiting for bet slip...
[ARB BOVADA] Bet slip detected opening
[ARB BOVADA] TEST MODE - Looking for bet slip with stake: 5
[ARB BOVADA] Found stake input with selector: input[type="number"]
[ARB BOVADA] ✅ Stake filled: 5.00
[ARB BOVADA] ✅ "Place Bet" button highlighted - CLICK IT MANUALLY
```

---

## 🔒 ToS Compliance Reminder

**What the Extension Does:**
- ✅ Opens Bovada.lv
- ✅ Detects bet slip opening
- ✅ Fills in stake amount ($5)
- ✅ Highlights "Place Bet" button

**What the Extension NEVER Does:**
- ❌ Clicks "Place Bet" button automatically
- ❌ Places bets without your manual click
- ❌ Stores login credentials
- ❌ Bypasses any security

**YOU MUST:**
- 👆 Manually click "Place Bet" every time
- 👀 Review odds and stake before placing
- ✅ Comply with Bovada's terms of service

---

## 🎯 Next Steps After Testing

### If Test Succeeds:
1. ✅ Extension works with Bovada!
2. Test with other bookmakers (DraftKings, FanDuel, etc.)
3. Connect to live arbitrage backend
4. Start placing real arbitrage bets

### If Test Fails:
1. Check DevTools Console for errors
2. Verify extension loaded correctly
3. Try different Bovada markets (NBA vs NFL vs NHL)
4. Review `bovada.js` content script for selector updates
5. Post console errors for debugging

---

## 🛠️ Updating Selectors (If Auto-Fill Breaks)

Bovada updates their website frequently. If auto-fill stops working:

1. Open Bovada and click a bet
2. Right-click the stake input field → **Inspect**
3. Note the selector (e.g., `input[data-test="stake-input"]`)
4. Open: `C:\Users\nashr\backend\ARB_Auto_Bettor\extension\content_scripts\bovada.js`
5. Find the `findStakeInput()` function (line ~60)
6. Add your new selector to the `selectors` array:
   ```javascript
   const selectors = [
     'input[data-test="stake-input"]', // Add this
     'input[name="stake"]',
     // ... existing selectors
   ];
   ```
7. Reload extension: `chrome://extensions/` → Reload button
8. Test again

---

## 📊 Testing Checklist

- [ ] Extension loaded in Chrome
- [ ] Extension icon visible in toolbar
- [ ] Popup opens when clicked
- [ ] Test button visible (orange, at bottom)
- [ ] Bovada opens when test button clicked
- [ ] Content script loaded (check console)
- [ ] Bet slip opens when bet clicked
- [ ] Stake auto-fills with $5.00
- [ ] "Place Bet" button highlighted (green glow)
- [ ] Green notification overlay appears
- [ ] Manual click on "Place Bet" works

---

## 💬 Support

**Check Logs:**
- Extension service worker: `chrome://extensions/` → Service worker
- Bovada page console: F12 → Console tab
- Look for `[ARB]` and `[ARB BOVADA]` prefixed messages

**Common Issues:**
1. "Content script not loading" → Check manifest.json includes Bovada
2. "Stake input not found" → Bovada HTML changed, update selectors
3. "Button not highlighting" → Button selector changed, update code

---

**Version**: 1.0.0
**Test Stake**: $5.00
**Status**: ✅ Ready to Test
**Time Required**: 1-2 minutes

**Let's test it!** 🚀
