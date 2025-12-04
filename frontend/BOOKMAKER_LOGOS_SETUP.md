# Bookmaker Logos - Production Setup Guide

## Overview

This guide explains how to set up bookmaker logos for production deployment on Hostinger VPS.

## File Locations

- **Bookmaker Data:** `src/data/bookmakers.ts` (all 62 bookmakers)
- **Logo Storage:** `public/assets/bookmaker-logos/` (create this folder)

## Development vs Production

### Development (Current)
- Uses Google Favicon Service
- No logo files needed
- Works automatically
- URL: `https://www.google.com/s2/favicons?domain=draftkings.com&sz=64`

### Production (Recommended)
- Self-hosted logo files in `/public/assets/bookmaker-logos/`
- Falls back to Google favicon if logo missing
- Better performance, quality, and reliability

## Production Setup Steps

### Step 1: Create Logo Directory

```bash
# In your frontend project
mkdir -p public/assets/bookmaker-logos
```

### Step 2: Download Bookmaker Logos

**Option A: Manual Collection (Recommended for Quality)**

1. Visit each bookmaker's press/media page:
   - DraftKings: https://www.draftkings.com/about/media-center
   - FanDuel: https://press.fanduel.com/
   - BetMGM: https://www.betmgm.com/en/about-us/media-kit
   - Caesars: https://www.caesars.com/corporate/media-center
   - etc.

2. Download official logos (PNG format, transparent background preferred)

3. Rename files to match bookmaker keys:
   - `draftkings.png`
   - `fanduel.png`
   - `betmgm.png`
   - etc.

4. Recommended size: 128x128px or 256x256px (will scale down)

**Option B: Automated Scraping (Faster but Lower Quality)**

Use this script to download favicons at scale:

```bash
# Create a download script
# Will download from Google favicon service to local files
```

**Option C: Logo Collection Services**

- Clearbit Logo API: `https://logo.clearbit.com/draftkings.com`
- Brandfetch: https://brandfetch.com/
- Companies Logos: Various free logo databases

### Step 3: Organize Logos by Priority

Focus on the **top 20 most popular** bookmakers first:

**Priority 1 - Major US Books:**
- draftkings.png
- fanduel.png
- betmgm.png
- caesars.png
- betrivers.png
- pointsbet.png
- williamhill_us.png
- fanatics.png
- espnbet.png

**Priority 2 - Offshore/Global:**
- betonlineag.png
- bovada.png
- mybookieag.png
- pinnacle.png
- bet365.png

**Priority 3 - UK/EU/AU:**
- williamhill.png
- ladbrokes.png
- sportsbet.png
- tab.png
- bwin.png

The rest will automatically use Google favicon fallback.

### Step 4: Update Code for Production

In `src/data/bookmakers.ts`, change line 16:

```typescript
// Development (current)
const getLogoUrl = (key: string, useLocal: boolean = false): string => {

// Production (change to)
const getLogoUrl = (key: string, useLocal: boolean = true): string => {
```

Or use environment variable:

```typescript
const getLogoUrl = (key: string, useLocal: boolean = import.meta.env.PROD): string => {
```

### Step 5: Test Locally

```bash
# Build and preview production bundle
npm run build
npm run preview
```

Check that logos load correctly. Missing logos will automatically fall back to favicon service.

### Step 6: Deploy to Hostinger VPS

```bash
# Build production bundle
npm run build

# Upload dist/ folder to VPS
# Ensure public/assets/bookmaker-logos/ is included in build
```

## Logo File Specifications

### Format Requirements
- **Format:** PNG (preferred) or SVG
- **Size:** 128x128px to 256x256px
- **Background:** Transparent (PNG) or white background acceptable
- **File Size:** < 50KB per logo (optimize for web)

### Naming Convention
Must match bookmaker key from `bookmakers.ts`:
- ✅ `draftkings.png`
- ✅ `fanduel.png`
- ✅ `betmgm.png`
- ❌ `DraftKings.png` (wrong - must be lowercase)
- ❌ `draft-kings.png` (wrong - must match exact key)

### Optimization
Use tools to compress logos:
```bash
# Using imagemagick
mogrify -resize 128x128 -quality 85 *.png

# Using tinypng API or website
# https://tinypng.com/
```

## Usage in React Components

### Import and Use

```typescript
import { getBookmaker, BOOKMAKERS } from '@/data/bookmakers';

// Get single bookmaker
const draftkings = getBookmaker('draftkings');

// Use in component
<img
  src={draftkings.logo}
  alt={draftkings.name}
  onError={(e) => { e.currentTarget.src = draftkings.logoFallback }}
  className="w-8 h-8"
/>
```

### Display All Bookmakers

```typescript
import { getAllBookmakerKeys, getBookmaker } from '@/data/bookmakers';

function BookmakerList() {
  const bookmakers = getAllBookmakerKeys().map(getBookmaker);

  return (
    <div>
      {bookmakers.map(book => (
        <div key={book.key}>
          <img
            src={book.logo}
            alt={book.name}
            onError={(e) => { e.currentTarget.src = book.logoFallback }}
          />
          <span>{book.name}</span>
        </div>
      ))}
    </div>
  );
}
```

### Filter by Region

```typescript
import { getBookmakersByRegion } from '@/data/bookmakers';

const usBookmakers = getBookmakersByRegion('US');
const ukBookmakers = getBookmakersByRegion('UK');
const popularOnly = getPopularBookmakers();
```

## Performance Considerations

### Hostinger VPS Optimization

1. **Use CDN (Optional)**
   - Upload logos to Cloudflare CDN
   - Faster global delivery
   - Reduces VPS bandwidth

2. **Enable Gzip Compression**
   ```nginx
   # In nginx config
   gzip_types image/png image/svg+xml;
   ```

3. **Browser Caching**
   ```nginx
   # Cache logos for 30 days
   location /assets/bookmaker-logos/ {
     expires 30d;
     add_header Cache-Control "public, immutable";
   }
   ```

4. **Lazy Loading**
   ```typescript
   <img
     src={book.logo}
     loading="lazy"
     alt={book.name}
   />
   ```

## Backup Strategy

1. **Fallback to Google Favicon**
   - Already built into `logoFallback` property
   - Automatic via `onError` handler

2. **Default Placeholder**
   ```typescript
   const DEFAULT_LOGO = '/assets/default-bookmaker.png';

   <img
     src={book.logo}
     onError={(e) => {
       e.currentTarget.src = book.logoFallback;
       e.currentTarget.onerror = () => {
         e.currentTarget.src = DEFAULT_LOGO;
       }
     }}
   />
   ```

## Cost Analysis

### Self-Hosted (Recommended)
- **Storage:** 62 logos × 30KB = ~2MB total
- **Bandwidth:** Cached by browser, minimal impact
- **Cost:** $0 (included in VPS)
- **Performance:** ⭐⭐⭐⭐⭐ Fast

### Google Favicon Service
- **Storage:** $0
- **Bandwidth:** External requests
- **Cost:** $0
- **Performance:** ⭐⭐⭐ Medium (external dependency)
- **Risk:** Rate limiting, service changes

### CDN (Optional Premium)
- **Storage:** $0.01-0.05/month
- **Bandwidth:** $0.01/GB
- **Cost:** ~$1-5/month
- **Performance:** ⭐⭐⭐⭐⭐ Fastest global delivery

## Recommendation for Hostinger VPS

✅ **Best Approach:**
1. Self-host top 20 popular bookmaker logos (~600KB total)
2. Use Google favicon fallback for remaining 42 bookmakers
3. Add browser caching and gzip compression
4. Total storage: < 1MB, minimal bandwidth impact
5. 95% of users will see self-hosted logos (fast)
6. Remaining 5% use favicon fallback (still works)

This gives you **maximum performance at zero cost** with reliable fallback.

## Troubleshooting

### Logo Not Showing
1. Check file name matches bookmaker key exactly
2. Check file exists in `public/assets/bookmaker-logos/`
3. Check file permissions (readable by web server)
4. Check browser console for 404 errors
5. Fallback should automatically load

### Logo Quality Issues
1. Use higher resolution source (256x256px)
2. Download official logo from brand media kit
3. Use PNG with transparent background
4. Optimize with compression tools

### Build/Deploy Issues
1. Ensure `public/` folder is included in build
2. Check Vite config includes static assets
3. Verify uploaded files are on VPS
4. Check nginx serves static files correctly

## Additional Resources

- **Official Brand Guidelines:** Most bookmakers provide logo downloads in media centers
- **Logo APIs:** Clearbit, Brandfetch, Google Favicon
- **Image Optimization:** TinyPNG, ImageOptim, Squoosh
- **CDN Options:** Cloudflare (free), BunnyCDN ($1/month), AWS CloudFront

---

**Questions?** Refer to `src/data/bookmakers.ts` for the complete bookmaker database.
