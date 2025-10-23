/**
 * BetUS Auto-Betting Content Script
 * Finds and fills bet slips on betus.com
 */

// Import base bet finder
// Note: In manifest V3, we'll inject both scripts in order

class BetUSBetFiller {
  constructor() {
    this.betFinder = new BetFinder('BetUS');
    this.settings = null;
    this.isProcessing = false;

    this.log('🟢 BetUS Auto-Bettor initialized');
    this.init();
  }

  log(...args) {
    console.log('[BETUS_FILLER]', ...args);
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

      // Step 2: Find and click the market tab (if needed)
      const marketTab = await this.findAndClickMarket(gameElement, opportunity.market_type);

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

      // Step 6: Highlight confirm button (or click if mode = 'highlight')
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
   * Find game on BetUS page
   */
  async findGame(opportunity) {
    const { home_team, away_team } = opportunity;

    // BetUS-specific container selector (might need adjustment after inspecting live site)
    const containerSelectors = [
      '.events-list',
      '.games-list',
      '.betting-table',
      '[class*="event-container"]',
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
   * Find and click market tab
   */
  async findAndClickMarket(gameElement, marketType) {
    const marketTab = this.betFinder.findMarketTab(marketType, gameElement);

    if (marketTab) {
      this.log('📍 Clicking market tab:', marketType);
      marketTab.click();
      await this.sleep(500); // Wait for market to load
      return marketTab;
    }

    this.log('⚠️ Market tab not found, assuming already on correct market');
    return null;
  }

  /**
   * Find and click bet button
   */
  async findAndClickBet(gameElement, opportunity) {
    const { market_type, outcome, point, odds } = opportunity;

    // Try to find bet button
    const betButton = this.betFinder.findBetButton(gameElement, market_type, outcome, point);

    if (!betButton) {
      return null;
    }

    // Verify odds match (optional, within 10 point tolerance)
    if (odds) {
      const buttonText = betButton.textContent || '';
      const oddsMatch = this.betFinder.oddsMatch(buttonText, odds, 15);

      if (!oddsMatch) {
        this.log('⚠️ Odds mismatch! Expected:', odds, 'Found:', buttonText);
        // Continue anyway, but log warning
      }
    }

    // Highlight and click
    this.betFinder.highlightElement(betButton, '#f59e0b', 1500);
    await this.sleep(300);

    this.log('🖱️ Clicking bet button');
    betButton.click();

    return betButton;
  }

  /**
   * Wait for bet slip to appear
   */
  async waitForBetSlip(timeout = 5000) {
    this.log('⏳ Waiting for bet slip...');

    const startTime = Date.now();

    while (Date.now() - startTime < timeout) {
      const betSlipInput = this.betFinder.findBetSlipInput();
      if (betSlipInput) {
        this.log('✅ Bet slip appeared!');
        return true;
      }
      await this.sleep(200);
    }

    throw new Error('Bet slip did not appear within timeout');
  }

  /**
   * Fill stake amount in bet slip
   */
  async fillStakeAmount(amount) {
    const betSlipInput = this.betFinder.findBetSlipInput();

    if (!betSlipInput) {
      this.log('❌ Bet slip input not found');
      return false;
    }

    // Clear existing value
    betSlipInput.value = '';
    betSlipInput.focus();

    // Fill in stake amount
    const stakeAmount = Math.floor(amount); // Round down to whole number
    betSlipInput.value = stakeAmount.toString();

    // Trigger input events to ensure sportsbook detects the change
    betSlipInput.dispatchEvent(new Event('input', { bubbles: true }));
    betSlipInput.dispatchEvent(new Event('change', { bubbles: true }));
    betSlipInput.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));

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

    const betButton = this.betFinder.findBetButton(gameElement, opportunity.market_type, opportunity.outcome, opportunity.point);
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
          // Check if bet slip was added
          const betSlip = document.querySelector('[class*="bet-slip"], [class*="betslip"]');
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
    new BetUSBetFiller();
  });
} else {
  new BetUSBetFiller();
}
