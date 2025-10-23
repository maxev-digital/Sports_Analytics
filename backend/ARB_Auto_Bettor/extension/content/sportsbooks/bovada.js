/**
 * Bovada Auto-Betting Content Script
 * Finds and fills bet slips on bovada.lv
 */

class BovadaBetFiller {
  constructor() {
    this.betFinder = new BetFinder('Bovada');
    this.settings = null;
    this.isProcessing = false;

    this.log('🟢 Bovada Auto-Bettor initialized');
    this.init();
  }

  log(...args) {
    console.log('[BOVADA_FILLER]', ...args);
  }

  async init() {
    // Load settings
    await this.loadSettings();

    // Listen for messages from background script
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      this.handleMessage(message, sender, sendResponse);
      return true; // Keep channel open for async response
    });

    // Observe DOM changes (bet slip might load dynamically)
    this.observeDOM();

    this.log('✅ Ready to receive bet opportunities');
  }

  async loadSettings() {
    try {
      const result = await chrome.storage.sync.get('settings');
      this.settings = result.settings || {};
      this.log('Settings loaded:', this.settings);
    } catch (error) {
      this.log('Error loading settings:', error);
    }
  }

  handleMessage(message, sender, sendResponse) {
    this.log('📨 Message received:', message.type);

    if (message.type === 'fill_bet_slip') {
      this.fillBetSlip(message.opportunity, message.autoBetMode)
        .then(result => {
          sendResponse({ success: true, result });
        })
        .catch(error => {
          this.log('❌ Error filling bet slip:', error);
          sendResponse({ success: false, error: error.message });
        });
    } else if (message.type === 'highlight_bet') {
      this.highlightBet(message.opportunity)
        .then(result => {
          sendResponse({ success: true, result });
        })
        .catch(error => {
          sendResponse({ success: false, error: error.message });
        });
    }
  }

  /**
   * Main function to fill bet slip
   */
  async fillBetSlip(opportunity, autoBetMode = 'fill') {
    if (this.isProcessing) {
      this.log('⏳ Already processing a bet, skipping...');
      return { skipped: true, reason: 'Already processing' };
    }

    this.isProcessing = true;

    try {
      this.log('🎯 Attempting to fill bet slip for:', opportunity);

      // Step 1: Find the game on the page
      const gameElement = await this.findGame(opportunity);
      if (!gameElement) {
        throw new Error('Game not found on page');
      }

      // Step 2: Find and click the market (if needed)
      await this.findAndClickMarket(gameElement, opportunity.market_type);

      // Step 3: Find and click the bet button
      const betButton = await this.findAndClickBet(gameElement, opportunity);
      if (!betButton) {
        throw new Error('Bet button not found');
      }

      // Step 4: Wait for bet slip to appear
      await this.waitForBetSlip();

      // Step 5: Fill in the stake amount
      const filled = await this.fillStakeAmount(opportunity.stake_amount || opportunity.total_stake);
      if (!filled) {
        throw new Error('Could not fill stake amount');
      }

      // Step 6: Highlight confirm button
      if (autoBetMode === 'highlight' || autoBetMode === 'fill') {
        const confirmButton = this.betFinder.findConfirmButton();
        if (confirmButton) {
          this.betFinder.highlightElement(confirmButton, '#10b981', 5000);

          // Add pulsing animation
          confirmButton.classList.add('arb-bet-ready');
          this.injectPulseAnimation();
        }
      }

      this.log('✅ Bet slip filled successfully!');
      this.showSuccessNotification(opportunity);

      return {
        success: true,
        game: `${opportunity.away_team} @ ${opportunity.home_team}`,
        stake: opportunity.stake_amount || opportunity.total_stake
      };

    } catch (error) {
      this.log('❌ Error:', error.message);
      this.showErrorNotification(error.message);
      throw error;

    } finally {
      this.isProcessing = false;
    }
  }

  /**
   * Find game on Bovada page
   * Bovada has a unique structure, need to search carefully
   */
  async findGame(opportunity) {
    const { home_team, away_team } = opportunity;

    // Bovada-specific container selectors
    const containerSelectors = [
      '.coupon-container',
      '.events-holder',
      '[class*="event"]',
      'main',
      'body'
    ];

    for (const selector of containerSelectors) {
      const gameElement = this.betFinder.findGameElement(home_team, away_team, selector);
      if (gameElement) {
        this.betFinder.highlightElement(gameElement, '#3b82f6', 2000);
        return gameElement;
      }
    }

    return null;
  }

  /**
   * Find and click market tab or expand game
   */
  async findAndClickMarket(gameElement, marketType) {
    // Bovada might need to expand the game first
    // Look for expand button
    const expandButton = gameElement.querySelector('[class*="arrow"], [class*="expand"], .more-markets');

    if (expandButton) {
      this.log('📍 Expanding game markets');
      expandButton.click();
      await this.sleep(1000); // Wait for markets to load
    }

    // Now look for market tab
    const marketTab = this.betFinder.findMarketTab(marketType, gameElement);

    if (marketTab) {
      this.log('📍 Clicking market tab:', marketType);
      marketTab.click();
      await this.sleep(500);
      return marketTab;
    }

    this.log('⚠️ Market tab not found, assuming already on correct market');
    return null;
  }

  /**
   * Find and click bet button
   * Bovada has specific bet button structure
   */
  async findAndClickBet(gameElement, opportunity) {
    const { market_type, outcome, point, odds } = opportunity;

    // Search for bet button in the game area or nearby
    const searchArea = gameElement.closest('[class*="coupon"]') || gameElement.parentElement || gameElement;

    // Bovada bet buttons might be in specific market sections
    const buttons = searchArea.querySelectorAll(
      'button[class*="bet"], sp-outcome, .market-btn, [class*="outcome"]'
    );

    this.log(`🔍 Found ${buttons.length} potential bet buttons`);

    for (const button of buttons) {
      const buttonText = (button.textContent || '').toLowerCase();
      const dataOutcome = button.getAttribute('data-outcome') || '';

      // Check if button matches outcome (Over, Under, Home, Away, etc.)
      const outcomeMatch = buttonText.includes(outcome.toLowerCase()) ||
                          dataOutcome.toLowerCase().includes(outcome.toLowerCase());

      // Check if button contains the point value
      const pointMatch = point ? buttonText.includes(point.toString()) : true;

      if (outcomeMatch && pointMatch) {
        this.log('✅ Found bet button:', button.textContent.trim());

        // Verify odds if provided
        if (odds) {
          const oddsMatch = this.betFinder.oddsMatch(buttonText, odds, 20);
          if (!oddsMatch) {
            this.log('⚠️ Odds mismatch, but continuing anyway');
          }
        }

        // Highlight and click
        this.betFinder.highlightElement(button, '#f59e0b', 1500);
        await this.sleep(300);

        this.log('🖱️ Clicking bet button');
        button.click();

        return button;
      }
    }

    this.log('⚠️ Bet button not found');
    return null;
  }

  /**
   * Wait for bet slip to appear
   */
  async waitForBetSlip(timeout = 5000) {
    this.log('⏳ Waiting for bet slip...');

    const startTime = Date.now();

    while (Date.now() - startTime < timeout) {
      // Bovada bet slip selectors
      const betSlip = document.querySelector(
        '.betslip-container, [class*="betslip"], .bet-slip, #betslip'
      );

      if (betSlip && betSlip.offsetParent !== null) {
        const betSlipInput = this.betFinder.findBetSlipInput();
        if (betSlipInput) {
          this.log('✅ Bet slip appeared!');
          return true;
        }
      }

      await this.sleep(200);
    }

    throw new Error('Bet slip did not appear within timeout');
  }

  /**
   * Fill stake amount in bet slip
   */
  async fillStakeAmount(amount) {
    this.log('🔍 Looking for bet slip input field...');

    // First, let's find ALL inputs on the page and log them
    const allInputs = document.querySelectorAll('input');
    this.log(`📊 Found ${allInputs.length} total input fields on page`);

    // Log details about each visible input
    allInputs.forEach((input, index) => {
      if (input.offsetParent !== null) { // Only visible inputs
        this.log(`  Input ${index + 1}:`, {
          type: input.type,
          name: input.name,
          id: input.id,
          class: input.className,
          placeholder: input.placeholder,
          value: input.value
        });
      }
    });

    // Bovada-specific stake input selectors (expanded list)
    const selectors = [
      'input[class*="stake"]',
      'input[class*="risk"]',
      'input[class*="amount"]',
      'input[type="tel"]',  // Bovada often uses tel input
      'input[type="number"]',
      'input[name*="stake"]',
      'input[name*="risk"]',
      'input[name*="amount"]',
      'input[placeholder*="stake"]',
      'input[placeholder*="risk"]',
      'input[placeholder*="amount"]',
      '.betslip-container input',
      '.bet-slip input',
      '[class*="betslip"] input',
      '[class*="bet-slip"] input'
    ];

    let betSlipInput = null;

    for (const selector of selectors) {
      const inputs = document.querySelectorAll(selector);
      this.log(`  Trying selector: ${selector} - Found ${inputs.length} matches`);

      for (const input of inputs) {
        if (input && input.offsetParent !== null) { // Visible
          betSlipInput = input;
          this.log('✅ Found bet slip input:', selector);
          this.log('   Input details:', {
            type: input.type,
            name: input.name,
            id: input.id,
            class: input.className
          });
          break;
        }
      }

      if (betSlipInput) break;
    }

    if (!betSlipInput) {
      this.log('❌ Bet slip input not found with standard selectors');
      this.log('📋 PLEASE INSPECT THE BET SLIP AND FIND THE INPUT FIELD');
      this.log('   Right-click the input field → Inspect Element');
      this.log('   Look for: type, name, id, class attributes');

      // Show alert to user
      this.showErrorNotification('Bet slip input not found. Please inspect the stake input field (F12) and report the selector.');
      return false;
    }

    // Clear existing value
    betSlipInput.value = '';
    betSlipInput.focus();

    // Fill in stake amount
    const stakeAmount = Math.floor(amount); // Round down to whole number
    betSlipInput.value = stakeAmount.toString();

    this.log(`💰 Setting stake to: $${stakeAmount}`);

    // Trigger input events
    betSlipInput.dispatchEvent(new Event('input', { bubbles: true }));
    betSlipInput.dispatchEvent(new Event('change', { bubbles: true }));
    betSlipInput.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));

    // Sometimes Bovada needs a blur event
    betSlipInput.blur();
    await this.sleep(200);
    betSlipInput.focus();

    // Verify it was filled
    this.log(`✔️ Input value after fill: "${betSlipInput.value}"`);

    // Highlight the input
    this.betFinder.highlightElement(betSlipInput, '#10b981', 3000);

    this.log('💵 Stake filled:', stakeAmount);
    return true;
  }

  /**
   * Just highlight a bet without filling
   */
  async highlightBet(opportunity) {
    const gameElement = await this.findGame(opportunity);
    if (!gameElement) {
      throw new Error('Game not found');
    }

    const betButton = this.betFinder.findBetButton(
      gameElement,
      opportunity.market_type,
      opportunity.outcome,
      opportunity.point
    );

    if (betButton) {
      this.betFinder.highlightElement(betButton, '#10b981', 10000);
      return { success: true };
    }

    throw new Error('Bet button not found');
  }

  /**
   * Observe DOM changes (for dynamic content)
   */
  observeDOM() {
    const observer = new MutationObserver((mutations) => {
      // Watch for bet slip appearing
      for (const mutation of mutations) {
        if (mutation.addedNodes.length > 0) {
          const betSlip = document.querySelector('[class*="betslip"], .bet-slip');
          if (betSlip) {
            this.log('👀 Bet slip detected in DOM');
          }
        }
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  /**
   * Show success notification
   */
  showSuccessNotification(opportunity) {
    this.showNotification(
      '✅ Bet Slip Filled!',
      `${opportunity.away_team} @ ${opportunity.home_team}\n${opportunity.outcome} ${opportunity.point || ''}\nStake: $${opportunity.stake_amount || opportunity.total_stake}`,
      '#10b981'
    );
  }

  /**
   * Show error notification
   */
  showErrorNotification(message) {
    this.showNotification('❌ Auto-Bet Error', message, '#ef4444');
  }

  /**
   * Show floating notification on page
   */
  showNotification(title, message, color = '#3b82f6') {
    // Remove existing notification
    const existing = document.getElementById('arb-notification');
    if (existing) existing.remove();

    // Create notification element
    const notification = document.createElement('div');
    notification.id = 'arb-notification';
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: ${color};
      color: white;
      padding: 16px 20px;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      z-index: 999999;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
      font-size: 14px;
      max-width: 300px;
      animation: slideIn 0.3s ease;
    `;

    notification.innerHTML = `
      <div style="font-weight: 700; margin-bottom: 4px;">${title}</div>
      <div style="font-size: 12px; opacity: 0.9; white-space: pre-line;">${message}</div>
    `;

    document.body.appendChild(notification);

    // Auto-remove after 5 seconds
    setTimeout(() => {
      notification.style.animation = 'slideOut 0.3s ease';
      setTimeout(() => notification.remove(), 300);
    }, 5000);
  }

  /**
   * Inject pulse animation CSS
   */
  injectPulseAnimation() {
    if (document.getElementById('arb-pulse-style')) return;

    const style = document.createElement('style');
    style.id = 'arb-pulse-style';
    style.textContent = `
      @keyframes slideIn {
        from { transform: translateX(400px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
      }
      @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(400px); opacity: 0; }
      }
      @keyframes arbPulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        50% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
      }
      .arb-bet-ready {
        animation: arbPulse 2s infinite !important;
      }
    `;
    document.head.appendChild(style);
  }

  /**
   * Sleep utility
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    new BovadaBetFiller();
  });
} else {
  new BovadaBetFiller();
}
