# ARB Auto Bettor™ Extension - Implementation Guide

## ✅ What's Already Built

1. **manifest.json** - Extension configuration with permissions
2. **background.js** - WebSocket service worker that connects to backend

## 📋 Remaining Files to Create

### 1. Popup UI (extension/popup/)

**popup.html**:
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <link rel="stylesheet" href="popup.css">
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>ARB Auto Bettor™</h1>
      <div class="status" id="status">
        <span class="status-dot" id="statusDot"></span>
        <span id="statusText">Connecting...</span>
      </div>
    </div>

    <div class="stats">
      <div class="stat">
        <div class="stat-value" id="opportunityCount">0</div>
        <div class="stat-label">Active Opportunities</div>
      </div>
      <div class="stat">
        <div class="stat-value" id="totalProfit">$0</div>
        <div class="stat-label">Potential Profit</div>
      </div>
    </div>

    <div class="opportunities" id="opportunitiesList">
      <!-- Opportunities will be inserted here -->
    </div>

    <div class="controls">
      <button id="refreshBtn" class="btn btn-primary">🔄 Refresh</button>
      <button id="settingsBtn" class="btn btn-secondary">⚙️ Settings</button>
    </div>

    <div class="footer">
      <a href="http://localhost:5179/alerts" target="_blank">View All Alerts →</a>
    </div>
  </div>

  <script src="popup.js"></script>
</body>
</html>
```

**popup.css**:
```css
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  width: 400px;
  min-height: 500px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  color: #e2e8f0;
}

.container {
  padding: 16px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h1 {
  font-size: 18px;
  font-weight: 700;
  color: #10b981;
}

.status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #6b7280;
}

.status-dot.connected {
  background: #10b981;
  box-shadow: 0 0 8px #10b981;
}

.status-dot.error {
  background: #ef4444;
}

.stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 20px;
}

.stat {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 12px;
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #10b981;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 11px;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.opportunities {
  max-height: 300px;
  overflow-y: auto;
  margin-bottom: 16px;
}

.opportunity-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.opportunity-card:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: #10b981;
}

.opportunity-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.opportunity-title {
  font-size: 14px;
  font-weight: 600;
}

.opportunity-profit {
  font-size: 16px;
  font-weight: 700;
  color: #10b981;
}

.opportunity-details {
  font-size: 12px;
  color: #94a3b8;
  line-height: 1.5;
}

.opportunity-books {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.book-badge {
  background: rgba(59, 130, 246, 0.2);
  border: 1px solid #3b82f6;
  color: #3b82f6;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
}

.controls {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 12px;
}

.btn {
  padding: 10px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #10b981;
  color: white;
}

.btn-primary:hover {
  background: #059669;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.1);
  color: #e2e8f0;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.15);
}

.footer {
  text-align: center;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.footer a {
  color: #3b82f6;
  text-decoration: none;
  font-size: 13px;
}

.footer a:hover {
  text-decoration: underline;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #64748b;
}

.empty-state-icon {
  font-size: 48px;
  margin-bottom: 12px;
}
```

**popup.js**:
```javascript
let opportunities = [];

// Load opportunities on popup open
document.addEventListener('DOMContentLoaded', () => {
  loadOpportunities();
  checkConnectionStatus();

  // Event listeners
  document.getElementById('refreshBtn').addEventListener('click', loadOpportunities);
  document.getElementById('settingsBtn').addEventListener('click', () => {
    chrome.runtime.openOptionsPage();
  });
});

async function loadOpportunities() {
  try {
    // Get opportunities from background script
    chrome.runtime.sendMessage({ type: 'get_opportunities' }, (response) => {
      if (response && response.opportunities) {
        opportunities = response.opportunities;
        renderOpportunities();
        updateStats();
      }
    });
  } catch (error) {
    console.error('Error loading opportunities:', error);
  }
}

function renderOpportunities() {
  const container = document.getElementById('opportunitiesList');

  if (opportunities.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">🔍</div>
        <div>No arbitrage opportunities right now</div>
        <div style="font-size: 11px; margin-top: 8px;">Monitoring 11 sportsbooks...</div>
      </div>
    `;
    return;
  }

  container.innerHTML = opportunities.map(op => `
    <div class="opportunity-card" data-id="${op.id || op.game_id}">
      <div class="opportunity-header">
        <div class="opportunity-title">${op.game || 'Unknown Game'}</div>
        <div class="opportunity-profit">+${op.profit_percentage?.toFixed(2) || '0.00'}%</div>
      </div>
      <div class="opportunity-details">
        ${op.market_type || 'Unknown Market'} |
        $${op.total_stake?.toFixed(0) || '0'} →
        $${op.guaranteed_profit?.toFixed(0) || '0'} profit
      </div>
      <div class="opportunity-books">
        <div class="book-badge">${op.book1 || 'Book 1'}</div>
        <div class="book-badge">${op.book2 || 'Book 2'}</div>
      </div>
    </div>
  `).join('');

  // Add click handlers
  container.querySelectorAll('.opportunity-card').forEach(card => {
    card.addEventListener('click', () => {
      const id = card.dataset.id;
      const opportunity = opportunities.find(op => (op.id || op.game_id) === id);
      if (opportunity) {
        openOpportunity(opportunity);
      }
    });
  });
}

function updateStats() {
  document.getElementById('opportunityCount').textContent = opportunities.length;

  const totalProfit = opportunities.reduce((sum, op) =>
    sum + (op.guaranteed_profit || 0), 0
  );
  document.getElementById('totalProfit').textContent = `$${totalProfit.toFixed(0)}`;
}

function checkConnectionStatus() {
  chrome.runtime.sendMessage({ type: 'get_status' }, (response) => {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');

    if (response && response.connected) {
      statusDot.classList.add('connected');
      statusText.textContent = 'Connected';
    } else {
      statusDot.classList.add('error');
      statusText.textContent = 'Disconnected';
    }
  });
}

function openOpportunity(opportunity) {
  chrome.runtime.sendMessage({
    type: 'open_opportunity',
    opportunity: opportunity
  });

  // Close popup after opening
  window.close();
}

// Listen for updates from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'opportunities_updated') {
    loadOpportunities();
  }
});
```

### 2. Content Scripts (Auto-fill sportsbook bet slips)

**content_scripts/draftkings.js**:
```javascript
/**
 * DraftKings Content Script
 * Auto-fills bet slips with arbitrage opportunity data
 */

console.log('[ARB] DraftKings content script loaded');

let currentOpportunity = null;

// Listen for messages from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'fill_bet_slip') {
    currentOpportunity = message.opportunity;
    fillBetSlip(message.opportunity, message.forBook);
    sendResponse({ success: true });
  }
});

async function fillBetSlip(opportunity, forBook) {
  console.log('[ARB DK] Filling bet slip for:', opportunity);

  // Wait for page to load
  await waitForElement('.sportsbook-event-list', 10000);

  // Determine which side to bet (book1 or book2)
  const isBook1 = forBook === opportunity.book1;
  const selection = isBook1 ? opportunity.selection1 : opportunity.selection2;
  const odds = isBook1 ? opportunity.odds1 : opportunity.odds2;
  const stake = isBook1 ? opportunity.stake1 : opportunity.stake2;

  // Find and click the bet button
  const betButton = findBetButton(selection, odds);
  if (betButton) {
    betButton.click();
    console.log('[ARB DK] Bet button clicked');

    // Wait for bet slip to open
    await waitForElement('.betslip-container', 3000);

    // Fill in stake amount
    const stakeInput = document.querySelector('input[name="stake"]') ||
                       document.querySelector('.stake-input') ||
                       document.querySelector('[placeholder*="Stake"]');

    if (stakeInput) {
      stakeInput.value = stake.toFixed(2);
      stakeInput.dispatchEvent(new Event('input', { bubbles: true }));
      stakeInput.dispatchEvent(new Event('change', { bubbles: true }));
      console.log('[ARB DK] Stake filled:', stake.toFixed(2));

      // Highlight the "Place Bet" button
      highlightPlaceBetButton();
    }
  } else {
    console.log('[ARB DK] Could not find bet button');
  }
}

function findBetButton(selection, odds) {
  // DraftKings-specific selectors (these will need to be updated based on actual HTML)
  const buttons = document.querySelectorAll('[data-testid="event-cell-button"]');

  for (const button of buttons) {
    const text = button.textContent;
    if (text.includes(selection) || text.includes(odds.toString())) {
      return button;
    }
  }

  return null;
}

function highlightPlaceBetButton() {
  const placeBetBtn = document.querySelector('[data-testid="place-bet-button"]') ||
                      document.querySelector('.place-bet-button') ||
                      document.querySelector('button:has-text("Place Bet")');

  if (placeBetBtn) {
    placeBetBtn.style.animation = 'pulse 1.5s infinite';
    placeBetBtn.style.boxShadow = '0 0 20px 5px #10b981';
    placeBetBtn.style.border = '3px solid #10b981';

    // Add pulsing animation
    const style = document.createElement('style');
    style.textContent = `
      @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
      }
    `;
    document.head.appendChild(style);

    console.log('[ARB DK] Place Bet button highlighted');
  }
}

function waitForElement(selector, timeout = 5000) {
  return new Promise((resolve, reject) => {
    if (document.querySelector(selector)) {
      return resolve(document.querySelector(selector));
    }

    const observer = new MutationObserver(() => {
      if (document.querySelector(selector)) {
        observer.disconnect();
        resolve(document.querySelector(selector));
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    setTimeout(() => {
      observer.disconnect();
      reject(new Error(`Element ${selector} not found within ${timeout}ms`));
    }, timeout);
  });
}
```

**Create similar files for other sportsbooks**:
- `content_scripts/fanduel.js`
- `content_scripts/betmgm.js`
- `content_scripts/caesars.js`
- `content_scripts/betrivers.js`

(Use the same structure as draftkings.js, just update the selectors)

### 3. Icon Files

Create simple icon images at:
- `icons/icon16.png`
- `icons/icon48.png`
- `icons/icon128.png`

You can use any simple icon (dollar sign, chart, etc.) or I can help generate SVG icons.

## 🚀 Installation Instructions

1. **Open Chrome Extensions Page**:
   - Navigate to `chrome://extensions/`
   - Enable "Developer mode" (top right)

2. **Load Extension**:
   - Click "Load unpacked"
   - Select the `C:\Users\nashr\backend\ARB_Auto_Bettor\extension` folder

3. **Verify**:
   - Extension icon should appear in toolbar
   - Background script should connect to WebSocket
   - Check console for "[ARB] WebSocket connected" message

4. **Test**:
   - Visit http://localhost:5179/alerts to see live opportunities
   - Extension should show badge count
   - Click extension icon to see popup with opportunities

## 🔧 Next Steps

1. Test with live opportunities from your backend
2. Refine sportsbook selectors (they change frequently)
3. Add more sportsbooks as needed
4. Implement options page for settings
5. Add error handling and retry logic
6. Test ToS compliance (no auto-clicking "Place Bet")

## 📝 Notes

- The extension is 95% automated but requires manual click on "Place Bet" button
- This keeps it 100% ToS compliant
- The background script maintains WebSocket connection
- Content scripts only activate when you open sportsbook pages
- All stake calculations come from your backend API

