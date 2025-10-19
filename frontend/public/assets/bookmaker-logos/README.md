# Bookmaker Logos Directory

This directory contains logo files for all supported bookmakers.

## Setup Instructions

### Quick Start - Download Logos Automatically

```bash
# From frontend directory
node scripts/download-logos.js
```

This will download the top 20 most popular bookmaker logos (about 600KB total).

### Manual Setup

1. Download official logos from bookmaker media/press pages
2. Save as PNG format (128x128px or 256x256px recommended)
3. Name files to match bookmaker key (e.g., `draftkings.png`)
4. Place in this directory

### File Naming

Files must be named **exactly** as the bookmaker key from `src/data/bookmakers.ts`:

✅ Correct:
- `draftkings.png`
- `fanduel.png`
- `betmgm.png`
- `williamhill_us.png` (note the underscore)

❌ Incorrect:
- `DraftKings.png` (uppercase)
- `draft-kings.png` (hyphen instead of no space)
- `draftkings.jpg` (must be .png)

### Priority List (Download These First)

**US Major Books:**
1. draftkings.png
2. fanduel.png
3. betmgm.png
4. caesars.png
5. betrivers.png
6. pointsbet.png
7. williamhill_us.png
8. fanatics.png
9. espnbet.png

**Offshore/Global:**
10. betonlineag.png
11. bovada.png
12. mybookieag.png
13. pinnacle.png
14. bet365.png

**International:**
15. williamhill.png
16. ladbrokes.png
17. sportsbet.png
18. tab.png
19. bwin.png
20. betway.png

### Fallback Behavior

If a logo file is missing, the app will automatically fall back to Google's favicon service. You don't need all 62 logos - just the ones you want optimized performance for.

### File Specifications

- **Format:** PNG (preferred) or SVG
- **Size:** 128x128px to 256x256px
- **Background:** Transparent preferred, white acceptable
- **File Size:** < 50KB per logo (use compression)

### Testing

After adding logos, test locally:

```bash
npm run dev
# Check that logos appear in the UI
# Check browser console for any 404 errors
```

## Current Status

- [ ] Priority logos downloaded (run `node scripts/download-logos.js`)
- [ ] Default placeholder created
- [ ] Production build tested
- [ ] Deployed to VPS

For more details, see `/BOOKMAKER_LOGOS_SETUP.md` in the project root.
