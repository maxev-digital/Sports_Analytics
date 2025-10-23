/**
 * Bovada Content Script
 * Simple test mode - fills bet slip with specified stake
 */

console.log('[ARB] Bovada content script loaded');
console.log('[ARB BOVADA] Current URL:', window.location.href);
console.log('[ARB BOVADA] Page title:', document.title);

// VISUAL CONFIRMATION - Show banner at top of page
function showBanner() {
  const banner = document.createElement('div');
  banner.id = 'arb-extension-banner';
  banner.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: white;
    padding: 12px 20px;
    text-align: center;
    font-family: Arial, sans-serif;
    font-size: 14px;
    font-weight: bold;
    z-index: 999999;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
  `;
  banner.innerHTML = '✅ ARB Auto Bettor Extension Active - Click a bet to test auto-fill';

  // Wait for body to exist
  const addBanner = () => {
    if (document.body) {
      document.body.insertBefore(banner, document.body.firstChild);
      console.log('[ARB BOVADA] ✅ Banner added to page - extension is working!');

      // Remove after 5 seconds
      setTimeout(() => banner.remove(), 5000);
    } else {
      setTimeout(addBanner, 100);
    }
  };

  addBanner();
}

// Show banner immediately
showBanner();

// Show alert so you KNOW the script is running
setTimeout(() => {
  console.log('[ARB BOVADA] Script is alive! Waiting for bet slip...');
}, 1000);

let currentOpportunity = null;

// Listen for messages from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'fill_bet_slip') {
    currentOpportunity = message.opportunity;
    fillBetSlip(message.opportunity, message.forBook);
    sendResponse({ success: true });
  } else if (message.type === 'test_bet_slip') {
    // Simple test mode - just fill with test data
    testBetSlipFill(message.stake || 5);
    sendResponse({ success: true });
  }
});

async function testBetSlipFill(stake) {
  console.log('[ARB BOVADA] TEST MODE - Looking for bet slip with stake:', stake);
  console.log('[ARB BOVADA] Current page HTML length:', document.body.innerHTML.length);

  // Wait a bit for page to load
  await new Promise(resolve => setTimeout(resolve, 2000));

  // Debug: Show all input fields on page
  const allInputs = document.querySelectorAll('input');
  console.log('[ARB BOVADA] Found', allInputs.length, 'total input fields on page');

  allInputs.forEach((input, index) => {
    if (input.type === 'number' || input.type === 'text') {
      console.log(`[ARB BOVADA] Input ${index}:`, {
        type: input.type,
        name: input.name,
        className: input.className,
        placeholder: input.placeholder,
        id: input.id
      });
    }
  });

  // Try to find stake input on Bovada
  const stakeInput = findStakeInput();

  if (stakeInput) {
    console.log('[ARB BOVADA] ✅ Found stake input, filling with $' + stake);
    console.log('[ARB BOVADA] Stake input details:', {
      type: stakeInput.type,
      name: stakeInput.name,
      className: stakeInput.className,
      placeholder: stakeInput.placeholder
    });
    fillStakeAmount(stakeInput, stake);
    highlightPlaceBetButton();
  } else {
    console.log('[ARB BOVADA] ❌ Could not find stake input with any selector.');
    console.log('[ARB BOVADA] Please click a bet first, then check console for input fields.');
    showManualInstructions(stake);
  }
}

async function fillBetSlip(opportunity, forBook) {
  console.log('[ARB BOVADA] Filling bet slip for:', opportunity);

  // Determine which side to bet
  const isBook1 = forBook === opportunity.book1 || forBook === opportunity.bookmaker1;
  const selection = isBook1 ? opportunity.selection1 : opportunity.selection2;
  const odds = isBook1 ? opportunity.odds1 : opportunity.odds2;
  const stake = isBook1 ? opportunity.stake1 : opportunity.stake2;

  console.log('[ARB BOVADA] Looking for:', { selection, odds, stake });

  // Wait for bet slip to be open
  await waitForElement('.bet-slip, .betslip, [class*="betslip"]', 5000).catch(() => {
    console.log('[ARB BOVADA] Bet slip not found yet');
  });

  // Fill stake
  setTimeout(() => {
    const stakeInput = findStakeInput();
    if (stakeInput) {
      fillStakeAmount(stakeInput, stake);
      highlightPlaceBetButton();
    }
  }, 1000);
}

function findStakeInput() {
  // Try multiple common selectors for Bovada
  const selectors = [
    'input[name="stake"]',
    'input[placeholder*="Stake"]',
    'input[placeholder*="stake"]',
    'input[type="number"]',
    'input[type="text"][class*="stake"]',
    'input[class*="risk"]',
    'input[class*="amount"]',
    '.bet-slip input[type="number"]',
    '.betslip input[type="number"]',
    '[class*="betslip"] input[type="number"]',
    '[class*="bet-container"] input[type="number"]'
  ];

  for (const selector of selectors) {
    const input = document.querySelector(selector);
    if (input && input.offsetParent !== null) { // Check if visible
      console.log('[ARB BOVADA] Found stake input with selector:', selector);
      return input;
    }
  }

  return null;
}

function fillStakeAmount(input, stake) {
  // Clear existing value
  input.value = '';
  input.focus();

  // Set new value
  input.value = stake.toFixed(2);

  // Trigger events to ensure Bovada registers the change
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.dispatchEvent(new Event('change', { bubbles: true }));
  input.dispatchEvent(new Event('blur', { bubbles: true }));

  console.log('[ARB BOVADA] ✅ Stake filled:', stake.toFixed(2));
}

function highlightPlaceBetButton() {
  // Find "Place Bet" button on Bovada
  const selectors = [
    'button[class*="place-bet"]',
    'button[class*="submit"]',
    'button:has-text("Place Bet")',
    'button:has-text("Place Bets")',
    'button:has-text("Submit")',
    '.bet-slip button[type="submit"]',
    '.betslip button[type="submit"]',
    '[class*="betslip"] button[type="submit"]'
  ];

  let placeBetBtn = null;

  // Try selectors
  for (const selector of selectors) {
    placeBetBtn = document.querySelector(selector);
    if (placeBetBtn) break;
  }

  // Also try finding by text content
  if (!placeBetBtn) {
    const buttons = document.querySelectorAll('button');
    for (const btn of buttons) {
      const text = btn.textContent.toLowerCase();
      if (text.includes('place bet') || text.includes('submit bet')) {
        placeBetBtn = btn;
        break;
      }
    }
  }

  if (placeBetBtn) {
    // Add highlighting styles
    placeBetBtn.style.animation = 'arb-pulse 1.5s infinite';
    placeBetBtn.style.boxShadow = '0 0 20px 5px #10b981';
    placeBetBtn.style.border = '3px solid #10b981';
    placeBetBtn.style.outline = '3px solid #10b981';

    // Add pulsing animation
    if (!document.getElementById('arb-pulse-style')) {
      const style = document.createElement('style');
      style.id = 'arb-pulse-style';
      style.textContent = `
        @keyframes arb-pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.05); }
        }
      `;
      document.head.appendChild(style);
    }

    console.log('[ARB BOVADA] ✅ "Place Bet" button highlighted - CLICK IT MANUALLY');

    // Show notification overlay
    showSuccessOverlay();
  } else {
    console.log('[ARB BOVADA] ⚠️ Could not find "Place Bet" button');
  }
}

function showSuccessOverlay() {
  // Create overlay notification
  const overlay = document.createElement('div');
  overlay.id = 'arb-success-overlay';
  overlay.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    z-index: 999999;
    font-family: Arial, sans-serif;
    max-width: 300px;
  `;
  overlay.innerHTML = `
    <div style="font-size: 16px; font-weight: bold; margin-bottom: 8px;">
      ✅ Bet Slip Filled!
    </div>
    <div style="font-size: 14px; margin-bottom: 12px;">
      Stake amount entered. The "Place Bet" button is highlighted below.
    </div>
    <div style="font-size: 12px; background: rgba(255,255,255,0.2); padding: 8px; border-radius: 4px;">
      👆 Click the green pulsing button to place your bet
    </div>
    <button onclick="this.parentElement.remove()" style="
      margin-top: 12px;
      background: white;
      color: #059669;
      border: none;
      padding: 8px 16px;
      border-radius: 4px;
      cursor: pointer;
      font-weight: bold;
    ">Got it!</button>
  `;

  document.body.appendChild(overlay);

  // Auto-remove after 10 seconds
  setTimeout(() => {
    overlay.remove();
  }, 10000);
}

function showManualInstructions(stake) {
  const overlay = document.createElement('div');
  overlay.id = 'arb-manual-overlay';
  overlay.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    color: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    z-index: 999999;
    font-family: Arial, sans-serif;
    max-width: 300px;
  `;
  overlay.innerHTML = `
    <div style="font-size: 16px; font-weight: bold; margin-bottom: 8px;">
      ℹ️ Manual Mode
    </div>
    <div style="font-size: 14px; margin-bottom: 12px;">
      Please click a bet to open the bet slip, then:
    </div>
    <div style="font-size: 13px; background: rgba(255,255,255,0.2); padding: 12px; border-radius: 4px;">
      1. Enter stake: <strong>$${stake.toFixed(2)}</strong><br>
      2. Review odds<br>
      3. Click "Place Bet"
    </div>
    <button onclick="this.parentElement.remove()" style="
      margin-top: 12px;
      background: white;
      color: #d97706;
      border: none;
      padding: 8px 16px;
      border-radius: 4px;
      cursor: pointer;
      font-weight: bold;
    ">Got it!</button>
  `;

  document.body.appendChild(overlay);
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

// Auto-detect bet slip opening
let betSlipObserver = new MutationObserver(() => {
  const betSlip = document.querySelector('.bet-slip, .betslip, [class*="betslip"]');
  if (betSlip && !document.getElementById('arb-auto-fill-attempted')) {
    console.log('[ARB BOVADA] Bet slip detected opening');

    // Mark as attempted so we don't try multiple times
    const marker = document.createElement('div');
    marker.id = 'arb-auto-fill-attempted';
    marker.style.display = 'none';
    document.body.appendChild(marker);
  }
});

betSlipObserver.observe(document.body, {
  childList: true,
  subtree: true
});

console.log('[ARB BOVADA] Ready for auto-fill. Waiting for bet slip...');
console.log('[ARB BOVADA] ⚡ MANUAL TEST: Type "testFill()" in console to test auto-fill');

// Make test function globally accessible for manual testing
window.testFill = function() {
  console.log('[ARB BOVADA] Manual test triggered!');
  testBetSlipFill(5);
};
