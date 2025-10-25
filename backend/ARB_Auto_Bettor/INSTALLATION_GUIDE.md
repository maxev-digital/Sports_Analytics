1# ARB Auto Bettor™ Chrome Extension - Installation Guide

## Overview

ARB Auto Bettor™ is a Chrome extension that assists with automated arbitrage betting across multiple sportsbooks. This guide will walk you through installing the extension in Chrome.

**Important:** This is an unpacked extension (not published on the Chrome Web Store), so you'll need to load it manually in Developer Mode.

---

## Prerequisites

- Google Chrome browser (version 88 or later)
- The extension files located at: `backend/ARB_Auto_Bettor/extension/`

---

## Installation Steps

### Step 1: Enable Developer Mode in Chrome

1. Open Google Chrome
2. Click the three-dot menu (⋮) in the top-right corner
3. Navigate to: **Extensions** > **Manage Extensions**
   - Or type `chrome://extensions` in the address bar and press Enter
4. Toggle the **Developer mode** switch in the top-right corner to **ON**

![Developer Mode Toggle](https://i.imgur.com/developer-mode-example.png)

---

### Step 2: Load the Extension

1. Click the **Load unpacked** button (appears after enabling Developer Mode)
2. Navigate to your project directory
3. Select the folder: `backend/ARB_Auto_Bettor/extension/`
4. Click **Select Folder**

---

### Step 3: Verify Installation

You should now see:
- **ARB Auto Bettor™** listed in your extensions
- The extension icon in your Chrome toolbar
- Status: "On" with a blue toggle switch

![Extension Installed](https://i.imgur.com/extension-installed-example.png)

---

### Step 4: Pin the Extension (Optional but Recommended)

1. Click the puzzle piece icon (Extensions) in the Chrome toolbar
2. Find **ARB Auto Bettor™** in the list
3. Click the pin icon to keep it visible in your toolbar

---

## Configuration

### Initial Setup

1. Click the **ARB Auto Bettor™** icon in your toolbar
2. The popup will open - click **Settings** (gear icon)
3. Configure your preferences:
   - Enable/disable specific sportsbooks
   - Set notification preferences
   - Configure automated betting parameters

### Backend Connection

The extension connects to your local backend API at `http://localhost:8000`.

**Before using the extension, ensure your backend is running:**

```bash
# From the project root directory
cd backend
python -m uvicorn main:app --reload
```

Verify the backend is running by visiting: `http://localhost:8000/docs`

---

## Supported Sportsbooks

The extension works with the following betting sites:

- DraftKings
- FanDuel
- BetMGM
- Caesars
- BetRivers
- BetUS
- BetOnline
- Bovada
- MyBookie
- Fanatics

---

## How to Use

1. **Start the backend server** (see Configuration section above)
2. **Open a supported sportsbook** in your browser
3. **Navigate to the betting page** for your sport
4. The extension will:
   - Automatically detect betting opportunities
   - Display notifications for arbitrage opportunities
   - Highlight profitable bets on the page
5. Click the extension icon to view current opportunities and statistics

---

## Troubleshooting

### Extension Not Loading

**Problem:** "Cannot load extension" error

**Solution:**
- Ensure you selected the `extension/` folder (not a parent folder)
- Check that `manifest.json` is in the root of the selected folder
- Verify all required files are present

### Extension Not Working on Sportsbooks

**Problem:** No detection or highlighting on betting sites

**Solutions:**
1. **Check backend connection:**
   - Ensure `http://localhost:8000` is running
   - Check browser console for connection errors (F12 > Console)

2. **Refresh the extension:**
   - Go to `chrome://extensions`
   - Click the refresh icon (🔄) on the ARB Auto Bettor card

3. **Reload the sportsbook page:**
   - Hard refresh with Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)

### Permission Errors

**Problem:** Extension requests additional permissions

**Solution:**
- This is normal for the host permissions listed in the manifest
- Click "Allow" to enable the extension to work with sportsbooks

### Backend Connection Errors

**Problem:** Extension shows "Backend Offline" or similar message

**Solutions:**
1. Verify the backend is running: `curl http://localhost:8000/api/games`
2. Check your firewall isn't blocking localhost connections
3. Ensure no other service is using port 8000

---

## Updating the Extension

When you make changes to the extension code:

1. Go to `chrome://extensions`
2. Find **ARB Auto Bettor™**
3. Click the refresh icon (🔄)
4. Reload any open sportsbook tabs

---

## Uninstalling

To remove the extension:

1. Go to `chrome://extensions`
2. Find **ARB Auto Bettor™**
3. Click **Remove**
4. Confirm removal

---

## Important Notes

### Terms of Service Compliance

This extension is designed to be **95% automated, 100% ToS compliant**:
- It assists with finding opportunities but requires user confirmation
- It respects rate limits and doesn't spam betting APIs
- All bets require final user approval

### Security & Privacy

- The extension only communicates with your local backend (localhost)
- No data is sent to external servers
- All betting credentials remain with the sportsbook sites
- The extension cannot access data from other websites

### Best Practices

1. **Always verify bets** before confirming (never blindly trust automation)
2. **Monitor your bankroll** and set appropriate limits
3. **Keep the backend updated** with latest odds data
4. **Don't leave the extension running unattended** for extended periods
5. **Test with small bets** before scaling up

---

## Support

If you encounter issues:

1. Check the browser console for errors (F12 > Console tab)
2. Review the backend logs for API errors
3. Verify all sportsbook sites are accessible
4. Ensure you're using the latest version of Chrome

---

## Development Mode Notes

Since this is loaded as an unpacked extension:

- You'll see a warning banner: "Disable Developer Mode Extensions"
  - This is normal - you can dismiss it
- The extension will be disabled if you close Chrome in some configurations
  - Just re-enable it from `chrome://extensions` if needed
- Chrome may periodically remind you about Developer Mode
  - This is a security feature - it's safe to keep Developer Mode on for your own extensions

---

## Version Information

- **Extension Version:** 1.0.0
- **Manifest Version:** 3 (latest Chrome extension format)
- **Minimum Chrome Version:** 88+

---

## Next Steps

After installation:

1. Read the [Usage Guide](./USAGE_GUIDE.md) (if available)
2. Configure your settings in the extension popup
3. Start the backend server
4. Visit a supported sportsbook and test the functionality
5. Monitor performance and adjust settings as needed

---

**Remember:** Sports betting involves risk. This tool is for informational and analytical purposes. Always bet responsibly and within your means.
