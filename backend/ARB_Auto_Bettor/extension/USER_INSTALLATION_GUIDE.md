# MAX-EV Sports Chrome Extension - Installation Guide

Welcome to MAX-EV Sports! This guide will help you install and use your Chrome extension for automated betting alerts.

---

## What You'll Get

The MAX-EV Sports Chrome Extension provides:

- **Real-Time Arbitrage Alerts** - Get notified when risk-free profits are available
- **Middle Opportunities** - Find betting gaps where both sides can win
- **Steam Move Detection** - Catch sharp money movements before odds shift
- **Goalie Pull Alerts** - NHL empty net betting opportunities
- **Voice Notifications** - Professional audio alerts for high-priority opportunities
- **Auto-Detection** - Works automatically when you visit sportsbook websites

**Supported Sportsbooks:**
- DraftKings
- FanDuel
- BetMGM
- Caesars
- BetRivers
- Bovada
- BetUS
- BetOnline
- LowVig.ag
- MyBookie

---

## Installation Instructions

### Step 1: Extract the Extension Files

1. Locate the **ARB_Auto_Bettor_Extension.zip** file attached to your email
2. Right-click the zip file and select **"Extract All..."**
3. Choose a location (e.g., Desktop or Documents)
4. Click **"Extract"**

### Step 2: Open Chrome Extensions Page

1. Open Google Chrome browser
2. Click the **three dots** menu (⋮) in the top-right corner
3. Go to **More Tools** → **Extensions**
4. Or simply type in the address bar: `chrome://extensions/`

### Step 3: Enable Developer Mode

1. In the top-right corner of the Extensions page, toggle **"Developer mode"** to ON
2. Three new buttons will appear: "Load unpacked", "Pack extension", "Update"

### Step 4: Load the Extension

1. Click **"Load unpacked"** button
2. Navigate to the folder where you extracted the files (from Step 1)
3. Select the **"extension"** folder
4. Click **"Select Folder"**

### Step 5: Verify Installation

You should see:
- **ARB Auto Bettor™** appears in your extensions list
- A new icon appears in your Chrome toolbar (may need to click the puzzle piece icon to pin it)
- Status shows: "Service worker (Inactive)" or "Service worker (Active)"

---

## How to Use

### Opening the Extension

1. Click the **ARB Auto Bettor™ icon** in your Chrome toolbar
2. The popup will show:
   - Current arbitrage opportunities
   - Middle opportunities
   - Steam moves
   - Goalie pull alerts

### Understanding Alerts

**Arbitrage Opportunities (Green)**
- Risk-free profit by betting both sides
- Shows: Books, odds, stake amounts, guaranteed profit
- Example: "Bet $100 on FanDuel Lakers +150 and $86 on DraftKings Warriors -140 = $14 profit"

**Middle Opportunities (Blue)**
- Potential to win both bets if result lands in the gap
- Shows: Gap size, books, bet sides
- Example: "Over 5.5 @ +120 vs Under 6.5 @ -110, Gap: 1.0"

**Steam Moves (Orange)**
- Sharp money detected - odds moving quickly
- Shows: Original line → New line, movement size
- Example: "Lakers -3.5 → -5.5, Move: 2.0 points"

**Goalie Pull Alerts (Red - NHL only)**
- Team about to pull goalie - bet OVER before odds shift
- Shows: Expected pull time, current odds, edge percentage
- Example: "Lightning pulling goalie in ~90s, OVER 5.5 @ +135, Edge: +8.5%"

### Audio Notifications

The extension plays audio alerts for:
- 🔴 **High Priority** - Arbitrage found (immediate action required)
- 🟠 **Medium Priority** - Strong middle or steam move
- 🟢 **Low Priority** - Standard opportunity

**To adjust volume:**
- Use your computer's system volume
- Or disable notifications in Settings (gear icon in popup)

### Automatic Sportsbook Detection

When you visit a supported sportsbook:
1. The extension automatically detects bets on the page
2. Compares them to current opportunities
3. Highlights matching bets if found
4. No manual searching required!

---

## Settings & Configuration

Click the **gear icon (⚙️)** in the extension popup to access:

### API Connection
- **Auto-detected** - Uses max-ev-sports.com by default
- Test connection with "Test Connection" button
- Should show: "Connected ✓"

### Alert Preferences
- **Arbitrage Alerts**: ON/OFF
- **Middle Opportunities**: ON/OFF
- **Steam Moves**: ON/OFF
- **Goalie Pull Alerts**: ON/OFF

### Sound Settings
- **Enable Sounds**: Toggle audio notifications
- **Volume**: Adjust notification volume (0-100%)

### Display Options
- **Show expired alerts**: Keep old alerts visible
- **Auto-refresh interval**: How often to check for new opportunities (default: 10 seconds)

---

## Troubleshooting

### Extension Not Showing Any Opportunities

**Check:**
1. Is the extension icon showing a green dot? (Active)
2. Click "Test Connection" in settings - should show "Connected ✓"
3. Check the main website: https://www.max-ev-sports.com/odds
4. Verify your subscription is active

**Fix:**
- Refresh the extension popup
- Click the refresh icon (↻) in the popup
- Close and reopen the popup

### "Connection Failed" Error

**Check:**
1. Your internet connection
2. Visit https://www.max-ev-sports.com/ - does it load?
3. Check if your firewall is blocking the connection

**Fix:**
- Disable VPN if you're using one
- Try a different network
- Contact support: support@max-ev-sports.com

### Audio Alerts Not Playing

**Check:**
1. Is "Enable Sounds" turned ON in settings?
2. Is your computer volume up?
3. Are other Chrome sounds working?

**Fix:**
- Open Chrome settings → Privacy and security → Site settings → Sound
- Make sure "Sites can play sound" is enabled
- Restart Chrome

### Sportsbook Detection Not Working

**Check:**
1. Are you on a supported sportsbook website?
2. Is the page fully loaded?
3. Check Chrome console for errors (F12 key)

**Fix:**
- Refresh the sportsbook page
- Make sure you're logged into the sportsbook
- Clear browser cache and reload

### Extension Shows "Service Worker (Inactive)"

This is **normal**! The service worker activates automatically when:
- A new opportunity is detected
- You open the popup
- You visit a sportsbook website

---

## Best Practices

### For Arbitrage Betting

1. **Act Quickly** - Arb opportunities disappear fast (30-60 seconds)
2. **Have Multiple Books Open** - Keep tabs ready for both sportsbooks
3. **Check Limits** - Ensure you can place the required stake at both books
4. **Use Round Numbers** - Bet slightly less than calculated to avoid odd amounts

### For Middle Opportunities

1. **Understand the Risk** - Both bets can lose if result falls outside the gap
2. **Target Large Gaps** - 1.5+ points for spreads, 1.0+ for totals
3. **Compare to CLV** - Check if you're getting better odds than closing line
4. **Use Kelly Criterion** - Size bets based on edge and bankroll

### For Steam Moves

1. **Verify the Movement** - Check multiple sources to confirm
2. **Act Before Line Moves** - Steam moves quickly across books
3. **Know Why** - Injury news? Weather? Sharp bettor action?
4. **Track Your Results** - Keep records to learn which moves are profitable

### For Goalie Pull Alerts

1. **Bet Immediately** - Pull happens within 30-90 seconds of alert
2. **Use Live Betting** - Pre-game totals won't include empty net scenarios
3. **Watch the Game** - Confirm the team is actually trailing as expected
4. **Know the Coach** - Some coaches pull early (high analytics score)

---

## Security & Privacy

### What Data Does the Extension Access?

- **Betting opportunities** from MAX-EV Sports API
- **Page content** on supported sportsbook websites (read-only)
- **Your settings** (stored locally in Chrome)

### What Data is NOT Accessed?

- ❌ Your sportsbook login credentials
- ❌ Your betting history
- ❌ Your personal information
- ❌ Your payment details

### Is It Safe?

- ✅ **100% ToS Compliant** - No automation of bet placement
- ✅ **Read-Only** - Extension only highlights opportunities, never places bets
- ✅ **No Data Sent** - Your browsing data stays on your computer
- ✅ **Open Source** - Code is available for review upon request

---

## Support & Contact

### Need Help?

- **Email**: support@max-ev-sports.com
- **Website**: https://www.max-ev-sports.com/
- **Response Time**: Within 24 hours

### Found a Bug?

Please report:
1. What you were doing when it happened
2. Which sportsbook website (if applicable)
3. Screenshot of the error (if possible)
4. Your Chrome version (chrome://version/)

### Feature Requests

We love feedback! Email us with:
- What feature you'd like
- Why it would be useful
- How you envision it working

---

## Frequently Asked Questions

**Q: Is this legal?**
A: Yes! The extension is a information tool only. You manually place all bets. It's like having a calculator - completely legal.

**Q: Will I get banned from sportsbooks?**
A: No. The extension is read-only and doesn't interact with sportsbook websites. It simply highlights opportunities.

**Q: How much can I make?**
A: Depends on your bankroll and time commitment. Arbitrage offers 2-5% risk-free returns. Middles and steam moves have higher variance but higher upside.

**Q: Do I need accounts at all sportsbooks?**
A: No, but having 3-5 accounts gives you more opportunities. Start with DraftKings, FanDuel, and BetMGM.

**Q: What's the catch?**
A: No catch! This is a subscription service. Your success is our success.

**Q: Can I use this on my phone?**
A: Currently Chrome desktop only. Mobile version coming soon!

**Q: Does it work in my state?**
A: Works in all legal US sports betting states. Check your state laws.

**Q: How often are opportunities found?**
A: Varies by day. NBA/NFL game days: 10-30 per day. Off-season: fewer opportunities.

---

## Updates & Changelog

The extension auto-updates through the MAX-EV Sports API. No reinstallation needed!

**Current Version**: 1.0.0

**Recent Updates**:
- Added middle opportunity detection
- Improved audio alert system with professional voice
- Enhanced sportsbook detection for Bovada and BetUS
- Added goalie pull prediction for NHL games

---

## Getting Started Checklist

- [ ] Extension installed and showing in Chrome toolbar
- [ ] Clicked "Test Connection" - shows "Connected ✓"
- [ ] Opened popup - seeing live opportunities (or "No opportunities")
- [ ] Audio alerts enabled in settings
- [ ] Pinned extension icon to toolbar for quick access
- [ ] Opened 2-3 sportsbook tabs in Chrome
- [ ] Bookmarked https://www.max-ev-sports.com/ for quick access

---

**Welcome to MAX-EV Sports! Let's start finding profitable betting opportunities together.**

Questions? Email us: support@max-ev-sports.com
