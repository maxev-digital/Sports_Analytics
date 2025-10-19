/**
 * Logo Downloader Script
 * Downloads bookmaker logos from Google Favicon service to local files
 * Run: node scripts/download-logos.js
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

// Top 20 priority bookmakers to download
const PRIORITY_BOOKMAKERS = [
  'draftkings',
  'fanduel',
  'betmgm',
  'caesars',
  'betrivers',
  'pointsbet',
  'williamhill_us',
  'fanatics',
  'espnbet',
  'betonlineag',
  'bovada',
  'mybookieag',
  'pinnacle',
  'bet365',
  'williamhill',
  'ladbrokes',
  'sportsbet',
  'tab',
  'bwin',
  'betway'
];

// Domain mapping for special cases
const DOMAIN_MAP = {
  'williamhill_us': 'williamhill.com',
  'mybookieag': 'mybookie.ag',
  'betonlineag': 'betonline.ag',
  'betus': 'betus.com.pa',
  'lowvig': 'lowvig.ag',
  'sport888': '888sport.com',
  'sport_interaction': 'sportsinteraction.com',
  'unibet_eu': 'unibet.eu',
};

const OUTPUT_DIR = path.join(__dirname, '..', 'public', 'assets', 'bookmaker-logos');

// Ensure output directory exists
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  console.log(`✅ Created directory: ${OUTPUT_DIR}`);
}

// Download a single logo
function downloadLogo(bookmakerKey) {
  return new Promise((resolve, reject) => {
    const domain = DOMAIN_MAP[bookmakerKey] || `${bookmakerKey}.com`;
    const url = `https://www.google.com/s2/favicons?domain=${domain}&sz=128`;
    const outputPath = path.join(OUTPUT_DIR, `${bookmakerKey}.png`);

    console.log(`📥 Downloading ${bookmakerKey} from ${domain}...`);

    https.get(url, (response) => {
      if (response.statusCode !== 200) {
        reject(new Error(`Failed to download ${bookmakerKey}: ${response.statusCode}`));
        return;
      }

      const fileStream = fs.createWriteStream(outputPath);
      response.pipe(fileStream);

      fileStream.on('finish', () => {
        fileStream.close();
        console.log(`✅ Saved: ${bookmakerKey}.png`);
        resolve();
      });

      fileStream.on('error', (err) => {
        fs.unlink(outputPath, () => {});
        reject(err);
      });
    }).on('error', (err) => {
      reject(err);
    });
  });
}

// Download all logos sequentially
async function downloadAll() {
  console.log('🚀 Starting logo download...\n');
  console.log(`📦 Downloading ${PRIORITY_BOOKMAKERS.length} bookmaker logos\n`);

  let successful = 0;
  let failed = 0;

  for (const bookmaker of PRIORITY_BOOKMAKERS) {
    try {
      await downloadLogo(bookmaker);
      successful++;
      // Wait 500ms between requests to be polite
      await new Promise(resolve => setTimeout(resolve, 500));
    } catch (error) {
      console.error(`❌ Failed to download ${bookmaker}:`, error.message);
      failed++;
    }
  }

  console.log('\n=================================');
  console.log(`✅ Downloaded: ${successful}/${PRIORITY_BOOKMAKERS.length}`);
  console.log(`❌ Failed: ${failed}`);
  console.log(`📁 Location: ${OUTPUT_DIR}`);
  console.log('=================================\n');
}

// Run the download
downloadAll().catch(console.error);
