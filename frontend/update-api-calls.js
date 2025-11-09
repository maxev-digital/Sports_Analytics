/**
 * Script to automatically update all API calls to use getApiUrl helper
 * This ensures the desktop app works in both development and production modes
 */

const fs = require('fs');
const path = require('path');

// Files to update (relative to frontend/src)
const filesToUpdate = [
  'pages/Analytics.tsx',
  'pages/Props.tsx',
  'pages/Odds.tsx',
  'pages/MultiSport.tsx',
  'pages/SignUp.tsx',
  'pages/Pricing.tsx',
  'utils/betTracking.ts',
  'hooks/useSettings.ts',
  'components/tools/SteamMoveDetector.tsx',
  'components/tools/LineMovementTracker.tsx',
  'components/tools/ArbitrageFinder.tsx',
  'components/MomentumAlert.tsx',
  'components/HalftimeTrackerAlert.tsx',
  'components/GoaliePullAlert.tsx',
  'components/FavoriteComebackAlert.tsx'
];

const srcDir = path.join(__dirname, 'src');

filesToUpdate.forEach(file => {
  const filePath = path.join(srcDir, file);

  if (!fs.existsSync(filePath)) {
    console.log(`⚠️  Skipping ${file} (not found)`);
    return;
  }

  let content = fs.readFileSync(filePath, 'utf-8');
  let modified = false;

  // Check if getApiUrl is already imported
  const hasImport = content.includes("import { getApiUrl }") || content.includes("import { getApiUrl");

  // Add import if not present and file has fetch calls
  if (!hasImport && content.includes("fetch('/api/")) {
    // Find the last import statement
    const lines = content.split('\n');
    let lastImportIndex = -1;

    for (let i = 0; i < lines.length; i++) {
      if (lines[i].trim().startsWith('import ')) {
        lastImportIndex = i;
      }
    }

    if (lastImportIndex !== -1) {
      lines.splice(lastImportIndex + 1, 0, "import { getApiUrl } from '../config';");
      content = lines.join('\n');
      modified = true;
      console.log(`✅ Added import to ${file}`);
    }
  }

  // Replace all fetch('/api/...' with fetch(getApiUrl('...
  const originalContent = content;
  content = content.replace(/fetch\(['"]\/api\/([\w\-?=&/]+)['"]\)/g, "fetch(getApiUrl('$1'))");

  if (content !== originalContent) {
    modified = true;
    console.log(`✅ Updated API calls in ${file}`);
  }

  if (modified) {
    fs.writeFileSync(filePath, content, 'utf-8');
  } else {
    console.log(`ℹ️  No changes needed for ${file}`);
  }
});

console.log('\n✅ All files updated successfully!');
