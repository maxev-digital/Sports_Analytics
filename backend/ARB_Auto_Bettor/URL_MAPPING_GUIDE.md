# URL Mapping System - Complete Guide

## 🎯 Problem Solved

The extension needs to open the correct bookmaker page for each game. Instead of static URLs, we now have a **dynamic URL builder** that constructs URLs based on:
- **Bookmaker** (DraftKings, FanDuel, Bovada, etc.)
- **Sport** (NBA, NFL, NHL, MLB, NCAAF, Soccer)
- **Game** (Lakers vs Warriors, Cowboys vs Eagles, etc.)

---

## 📁 Files

### `extension/url_builder.js`
The core URL building system with patterns for all 11 bookmakers.

---

## 🔧 How It Works

### Input Data (from your backend API):
```javascript
{
  sport_key: "basketball_nba",
  home_team: "Los Angeles Lakers",
  away_team: "Golden State Warriors",
  commence_time: "2025-10-18T19:00:00Z"
}
```

### Output URL:
```
Bovada: https://www.bovada.lv/sports/basketball/nba
DraftKings: https://sportsbook.draftkings.com/leagues/basketball/nba
FanDuel: https://sportsbook.fanduel.com/navigation/nba
```

---

## 📊 Current Coverage

### ✅ **Sport-Level URLs** (Working Now)
Opens the correct sport page where user can find their game.

| Bookmaker | NBA URL Pattern |
|-----------|----------------|
| DraftKings | `/leagues/basketball/nba` |
| FanDuel | `/navigation/nba` |
| BetMGM | `/en/sports/basketball-7/betting/usa-9/nba` |
| Caesars | `/basketball/nba` |
| BetRivers | `/?page=sportsbook#basketball` |
| Bovada | `/sports/basketball/nba` |
| BetOnline | `/sportsbook/basketball/nba` |
| MyBookie | `/sportsbook/nba/` |
| BetUS | `/sportsbook/basketball/` |
| LowVig | `/sports/basketball` |
| William Hill | `/bet/en/betting/t/basketball/nba` |

### 🔄 **Game-Level URLs** (Future Enhancement)
Deep links to specific games - requires research for each bookmaker.

---

## 🚀 Usage

### In Extension Code:

```javascript
// Import the URL builder
importScripts('url_builder.js'); // In background.js

// Or in HTML:
<script src="../url_builder.js"></script> // In popup.html

// Build a URL
const gameData = {
  sport_key: 'basketball_nba',
  home_team: 'Los Angeles Lakers',
  away_team: 'Golden State Warriors',
  commence_time: new Date().toISOString()
};

const url = buildBookmakerURL('bovada', gameData);
// Returns: https://www.bovada.lv/sports/basketball/nba

// Open the URL
chrome.tabs.create({ url: url });
```

### For Different Sports:

```javascript
// NFL
const nflGame = {
  sport_key: 'americanfootball_nfl',
  home_team: 'Dallas Cowboys',
  away_team: 'Philadelphia Eagles'
};
buildBookmakerURL('draftkings', nflGame);
// Returns: https://sportsbook.draftkings.com/leagues/football/nfl

// NHL
const nhlGame = {
  sport_key: 'icehockey_nhl',
  home_team: 'Boston Bruins',
  away_team: 'Toronto Maple Leafs'
};
buildBookmakerURL('fanduel', nhlGame);
// Returns: https://sportsbook.fanduel.com/navigation/nhl
```

---

## 🛠️ How to Add Game-Specific URLs

If you discover a bookmaker has predictable game URLs, you can add them:

### Step 1: Research the URL Pattern

Visit the bookmaker and find a game. Look at the URL:

**Example - Hypothetical DraftKings URL:**
```
https://sportsbook.draftkings.com/leagues/basketball/nba/lakers-at-warriors-20251018
```

### Step 2: Update `url_builder.js`

Find the bookmaker in the `urlPatterns` object:

```javascript
'draftkings': {
  base: 'https://sportsbook.draftkings.com',
  sport: {
    'basketball': `/leagues/basketball/${league}`,
    // ... other sports
  },
  // ADD THIS:
  game: (homeSlug, awaySlug, league) => {
    const date = new Date().toISOString().split('T')[0].replace(/-/g, '');
    return `/leagues/basketball/${league}/${awaySlug}-at-${homeSlug}-${date}`;
  }
},
```

### Step 3: Test It

```javascript
const testGame = {
  sport_key: 'basketball_nba',
  home_team: 'Los Angeles Lakers',
  away_team: 'Golden State Warriors'
};

const url = buildBookmakerURL('draftkings', testGame);
console.log(url);
// Should output the game-specific URL
```

### Step 4: Verify in Browser

- Open the generated URL
- Confirm it goes directly to the game
- If not, adjust the pattern and try again

---

## 📝 URL Pattern Examples

### Bookmakers WITH Predictable Game URLs:

**None yet** - Most bookmakers use dynamic IDs or session-based URLs

### Bookmakers WITHOUT Predictable Game URLs:

**All current bookmakers** - They use:
- Database IDs that change (e.g., `/game/12345678`)
- Session tokens (e.g., `/sportsbook?id=abc123xyz`)
- JavaScript-rendered content (no URL changes)

**Workaround**: Open sport-level page, let user find game (current behavior)

---

## 🔍 Troubleshooting

### Issue: URL Opens Wrong Sport

**Check**: Is `sport_key` correctly formatted in your backend data?

```javascript
// Correct format:
"basketball_nba"       // NBA
"americanfootball_nfl" // NFL
"icehockey_nhl"        // NHL
"baseball_mlb"         // MLB

// Not:
"nba"                  // Too short
"Basketball_NBA"       // Wrong case
```

### Issue: URL Opens But Shows Loading Screen

**Cause**: Bookmaker requires login or has geo-restrictions

**Solutions**:
1. User must be logged into bookmaker
2. Use VPN if geo-blocked
3. Check if bookmaker domain is correct (`.com` vs `.lv` vs `.ag`)

### Issue: Want Team-Specific Search

**Enhancement**: Add search parameter to URL

```javascript
// Example for bookmakers with search:
const url = `${baseUrl}/search?q=${encodeURIComponent(game.home_team)}`;
```

---

## 🎯 Testing Checklist

For each bookmaker:

- [ ] NBA URL works
- [ ] NFL URL works
- [ ] NHL URL works
- [ ] MLB URL works
- [ ] NCAAF URL works
- [ ] User can find the game on the page
- [ ] Content script detects bet slip
- [ ] Auto-fill works with $5 test stake

---

## 💡 Future Enhancements

### 1. **Bookmaker Search APIs**

Some bookmakers have search APIs that could return game-specific URLs:

```javascript
async function searchBookmakerForGame(bookmaker, game) {
  const response = await fetch(`https://${bookmaker}.com/api/search`, {
    method: 'POST',
    body: JSON.stringify({
      query: `${game.home_team} vs ${game.away_team}`
    })
  });
  const data = await response.json();
  return data.game_url;
}
```

### 2. **Smart Navigation**

After opening sport page, inject JavaScript to:
1. Search page for team names
2. Auto-click the matching game
3. Wait for bet slip to appear

```javascript
// In content script:
function findGameOnPage(homeTeam, awayTeam) {
  const gameLinks = document.querySelectorAll('a[href*="game"]');
  for (const link of gameLinks) {
    if (link.textContent.includes(homeTeam) && link.textContent.includes(awayTeam)) {
      return link;
    }
  }
  return null;
}
```

### 3. **URL Database**

Build a database of game URLs over time:

```json
{
  "game_id": "abc123",
  "bookmaker": "draftkings",
  "url": "https://sportsbook.draftkings.com/...",
  "expires": "2025-10-18T19:00:00Z"
}
```

Cache these for the duration of the game.

---

## 📚 API Integration

Your backend API provides this data:

```json
{
  "arbitrage": {
    "alerts": [
      {
        "game_id": "bbde7751a144b98ed150d7a5f7dc8f87",
        "sport": "basketball_nba",
        "home_team": "Oklahoma City Thunder",
        "away_team": "Houston Rockets",
        "book_a": "williamhill_us",
        "book_b": "fanatics",
        "commence_time": "2025-10-18T16:27:09.000628"
      }
    ]
  }
}
```

The URL builder uses:
- ✅ `sport` → Determines sport-level URL
- ✅ `home_team` → For future game-specific URLs
- ✅ `away_team` → For future game-specific URLs
- ✅ `book_a` / `book_b` → Selects bookmaker pattern
- ⏳ `commence_time` → Could be used for date-based URLs

---

## 🔒 Security Notes

**URL Validation**:
```javascript
function isValidBookmakerURL(url) {
  const allowedDomains = [
    'draftkings.com',
    'fanduel.com',
    'bovada.lv',
    'betmgm.com',
    // ... etc
  ];

  try {
    const urlObj = new URL(url);
    return allowedDomains.some(domain => urlObj.hostname.includes(domain));
  } catch {
    return false;
  }
}
```

**Never Trust User Input**: All URLs are built from predefined patterns, not user input.

---

## 📊 Performance

**Current System:**
- ✅ **Instant URL generation** (no API calls)
- ✅ **Works offline** (static patterns)
- ✅ **No rate limits** (no external dependencies)

**Future Game-Specific URLs:**
- ⚠️ May require API calls to bookmaker search
- ⚠️ Could be rate-limited
- ⚠️ May need caching layer

---

## 🎬 Quick Reference

| Need | Use | Example |
|------|-----|---------|
| Build URL | `buildBookmakerURL(bookmaker, game)` | `buildBookmakerURL('bovada', gameData)` |
| Get bookmaker info | `getBookmakerInfo(key)` | `getBookmakerInfo('draftkings')` |
| Team to slug | `slugify(team)` | `slugify('Los Angeles Lakers')` → `'los-angeles-lakers'` |

---

**Version**: 1.0.0
**Last Updated**: October 18, 2025
**Status**: ✅ Production Ready (Sport-Level URLs)
**Next**: Add game-specific URLs as patterns are discovered
