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
  await waitForElement('.sportsbook-event-list', 10000).catch(() => {
    console.log('[ARB DK] Event list not found, page may have different structure');
  });

  // Determine which side to bet (book1 or book2)
  const isBook1 = forBook === opportunity.book1 || forBook === opportunity.bookmaker1;
  const selection = isBook1 ? opportunity.selection1 : opportunity.selection2;
  const odds = isBook1 ? opportunity.odds1 : opportunity.odds2;
  const stake = isBook1 ? opportunity.stake1 : opportunity.stake2;

  console.log('[ARB DK] Looking for:', { selection, odds, stake });

  // Find and click the bet button
  const betButton = findBetButton(selection, odds);
  if (betButton) {
    betButton.click();
    console.log('[ARB DK] Bet button clicked');

    // Wait for bet slip to open
    await waitForElement('.betslip-container, .bet-slip, [class*="betslip"]', 3000).catch(() => {
      console.log('[ARB DK] Bet slip container not found');
    });

    // Fill in stake amount
    setTimeout(() => {
      fillStakeInput(stake);
      highlightPlaceBetButton();
    }, 1000); // Wait 1s for bet slip to fully load

  } else {
    console.log('[ARB DK] Could not find bet button for:', selection);
    showManualInstructions(selection, stake, odds);
  }
}

function findBetButton(selection, odds) {
  // Try multiple selectors (DraftKings updates their site frequently)
  const selectors = [
    '[data-testid="event-cell-button"]',
    '.event-cell__odd',
    '[class*="sportsbook-outcome"]',
    '[class*="event-cell"]',
    'button[class*="outcome"]'
  ];

  for (const selector of selectors) {
    const buttons = document.querySelectorAll(selector);

    for (const button of buttons) {
      const text = button.textContent.trim();

      // Check if button matches selection or odds
      if (text.includes(selection) ||
          text.includes(odds.toString()) ||
          text.includes(`+${odds}`) ||
          text.includes(`${odds}`)) {
        console.log('[ARB DK] Found matching button:', text);
        return button;
      }
    }
  }

  console.log('[ARB DK] No matching button found');
  return null;
}

function fillStakeInput(stake) {
  // Try multiple stake input selectors
  const selectors = [
    'input[name="stake"]',
    'input[placeholder*="Stake"]',
    'input[placeholder*="Amount"]',
    'input[class*="stake"]',
    'input[type="number"]',
    '.stake-input input',
    '[class*="bet-slip"] input[type="number"]'
  ];

  for (const selector of selectors) {
    const input = document.querySelector(selector);
    if (input && input.offsetParent !== null) { // Check if visible
      // Clear existing value
      input.value = '';

      // Set new value
      input.value = stake.toFixed(2);

      // Trigger events to ensure React/Angular detects the change
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
      input.dispatchEvent(new Event('blur', { bubbles: true }));

      // Also try setting the value via React if available
      const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype,
        'value'
      ).set;
      nativeInputValueSetter.call(input, stake.toFixed(2));
      input.dispatchEvent(new Event('input', { bubbles: true }));

      console.log('[ARB DK] Stake filled:', stake.toFixed(2), 'in', selector);
      return true;
    }
  }

  console.log('[ARB DK] Could not find stake input');
  return false;
}

function highlightPlaceBetButton() {
  // Try multiple "Place Bet" button selectors
  const selectors = [
    '[data-testid="place-bet-button"]',
    'button:contains("Place Bet")',
    'button[class*="place-bet"]',
    'button[class*="submit-bet"]',
    '.bet-slip button[type="submit"]',
    '[class*="bet-slip"] button[class*="primary"]'
  ];

  let placeBetBtn = null;

  for (const selector of selectors) {
    placeBetBtn = document.querySelector(selector);
    if (placeBetBtn) break;
  }

  // Also try finding by text content
  if (!placeBetBtn) {
    const buttons = document.querySelectorAll('button');
    for (const btn of buttons) {
      if (btn.textContent.toLowerCase().includes('place bet') ||
          btn.textContent.toLowerCase().includes('submit')) {
        placeBetBtn = btn;
        break;
      }
    }
  }

  if (placeBetBtn) {
    // Apply pulsing animation and highlighting
    placeBetBtn.style.animation = 'pulse 1.5s infinite';
    placeBetBtn.style.boxShadow = '0 0 20px 5px #10b981';
    placeBetBtn.style.border = '3px solid #10b981';
    placeBetBtn.style.transition = 'all 0.3s';

    // Add pulsing animation if not already added
    if (!document.getElementById('arb-pulse-animation')) {
      const style = document.createElement('style');
      style.id = 'arb-pulse-animation';
      style.textContent = `
        @keyframes pulse {
          0%, 100% {
            transform: scale(1);
            box-shadow: 0 0 20px 5px #10b981;
          }
          50% {
            transform: scale(1.05);
            box-shadow: 0 0 30px 10px #10b981;
          }
        }
      `;
      document.head.appendChild(style);
    }

    console.log('[ARB DK] Place Bet button highlighted');

    // Add a visual overlay
    showReadyToPlaceIndicator();
  } else {
    console.log('[ARB DK] Could not find Place Bet button');
  }
}

function showReadyToPlaceIndicator() {
  // Remove existing indicator if present
  const existing = document.getElementById('arb-ready-indicator');
  if (existing) existing.remove();

  // Create floating indicator
  const indicator = document.createElement('div');
  indicator.id = 'arb-ready-indicator';
  indicator.innerHTML = `
    <div style="
      position: fixed;
      top: 20px;
      right: 20px;
      background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      color: white;
      padding: 16px 24px;
      border-radius: 12px;
      box-shadow: 0 4px 20px rgba(16, 185, 129, 0.4);
      z-index: 999999;
      font-family: Arial, sans-serif;
      font-size: 14px;
      font-weight: bold;
      animation: slideIn 0.3s ease-out;
    ">
      ✅ ARB Auto Bettor™ Ready<br>
      <span style="font-size: 12px; font-weight: normal; opacity: 0.9;">
        Click "Place Bet" to confirm
      </span>
    </div>
  `;

  // Add slide-in animation
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideIn {
      from {
        transform: translateX(400px);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }
  `;
  indicator.appendChild(style);

  document.body.appendChild(indicator);

  // Auto-remove after 10 seconds
  setTimeout(() => {
    if (indicator.parentElement) {
      indicator.style.animation = 'slideOut 0.3s ease-out';
      setTimeout(() => indicator.remove(), 300);
    }
  }, 10000);
}

function showManualInstructions(selection, stake, odds) {
  // Show overlay with manual instructions if auto-fill fails
  const overlay = document.createElement('div');
  overlay.id = 'arb-manual-overlay';
  overlay.innerHTML = `
    <div style="
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.8);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 999999;
      font-family: Arial, sans-serif;
    ">
      <div style="
        background: white;
        padding: 32px;
        border-radius: 16px;
        max-width: 500px;
        color: #1e293b;
      ">
        <h2 style="margin-top: 0; color: #10b981;">⚠️ Manual Bet Required</h2>
        <p>Auto-fill didn't work. Please place this bet manually:</p>
        <div style="background: #f1f5f9; padding: 16px; border-radius: 8px; margin: 16px 0;">
          <p><strong>Selection:</strong> ${selection}</p>
          <p><strong>Odds:</strong> ${odds > 0 ? '+' : ''}${odds}</p>
          <p><strong>Stake:</strong> $${stake.toFixed(2)}</p>
        </div>
        <button id="arb-close-overlay" style="
          background: #10b981;
          color: white;
          border: none;
          padding: 12px 24px;
          border-radius: 8px;
          font-size: 14px;
          font-weight: bold;
          cursor: pointer;
          width: 100%;
        ">Got It</button>
      </div>
    </div>
  `;

  document.body.appendChild(overlay);

  document.getElementById('arb-close-overlay').addEventListener('click', () => {
    overlay.remove();
  });
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

// Inject CSS for :contains selector polyfill
document.addEventListener('DOMContentLoaded', () => {
  console.log('[ARB DK] Page loaded, ready for opportunities');
});
