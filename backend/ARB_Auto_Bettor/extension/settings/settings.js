/**
 * ARB Auto Bettor - Settings Page
 * Manages user preferences and bankroll configuration
 */

// Default settings
const DEFAULT_SETTINGS = {
  // Bankroll Management
  totalBankroll: 10000,
  maxBetPercentage: 2.0,
  minProfitThreshold: 2.0,
  betSizingMethod: 'flat_percentage',
  fixedBetAmount: 100,

  // Sportsbook Balances and Enabled Status
  sportsbooks: {
    draftkings: { enabled: true, balance: 0 },
    fanduel: { enabled: true, balance: 0 },
    betmgm: { enabled: false, balance: 0 },
    caesars: { enabled: false, balance: 0 },
    betrivers: { enabled: false, balance: 0 }
  },

  // Auto-Bet Behavior
  autoBetMode: 'fill', // 'off', 'fill', 'highlight'
  skipInsufficientFunds: true,
  alertOnSkipped: false,

  // Alerts & Notifications
  enableArbitrageAlerts: true,
  enableSteamAlerts: true,
  enableLineAlerts: true,
  enableGoalieAlerts: true,
  soundEnabled: true,
  voiceEnabled: true,
  soundVolume: 0.5,
  lowBalanceWarnings: true,

  // Thresholds (from existing settings)
  minProfit: 1.0,
  maxStake: 1000,
  autoOpen: true,
  autoFill: true,
  voiceRate: 1.0,
  voicePitch: 1.0
};

// Load settings on page load
document.addEventListener('DOMContentLoaded', async () => {
  await loadSettings();
  setupEventListeners();
});

// Load settings from chrome.storage
async function loadSettings() {
  try {
    const result = await chrome.storage.sync.get('settings');
    const settings = result.settings || DEFAULT_SETTINGS;

    // Bankroll Management
    document.getElementById('totalBankroll').value = settings.totalBankroll || DEFAULT_SETTINGS.totalBankroll;
    document.getElementById('maxBetPercentage').value = settings.maxBetPercentage || DEFAULT_SETTINGS.maxBetPercentage;
    document.getElementById('minProfitThreshold').value = settings.minProfitThreshold || DEFAULT_SETTINGS.minProfitThreshold;
    document.getElementById('betSizingMethod').value = settings.betSizingMethod || DEFAULT_SETTINGS.betSizingMethod;
    document.getElementById('fixedBetAmount').value = settings.fixedBetAmount || DEFAULT_SETTINGS.fixedBetAmount;

    // Show/hide fixed amount input based on method
    toggleFixedAmountInput(settings.betSizingMethod || DEFAULT_SETTINGS.betSizingMethod);

    // Sportsbooks
    const sportsbooks = settings.sportsbooks || DEFAULT_SETTINGS.sportsbooks;
    for (const [key, data] of Object.entries(sportsbooks)) {
      const enableCheckbox = document.getElementById(`enable${capitalize(key)}`);
      const balanceInput = document.getElementById(`balance${capitalize(key)}`);

      if (enableCheckbox) enableCheckbox.checked = data.enabled;
      if (balanceInput) balanceInput.value = data.balance;
    }

    // Auto-Bet Behavior
    document.getElementById('autoBetMode').value = settings.autoBetMode || DEFAULT_SETTINGS.autoBetMode;
    document.getElementById('skipInsufficientFunds').checked = settings.skipInsufficientFunds !== undefined ? settings.skipInsufficientFunds : DEFAULT_SETTINGS.skipInsufficientFunds;
    document.getElementById('alertOnSkipped').checked = settings.alertOnSkipped !== undefined ? settings.alertOnSkipped : DEFAULT_SETTINGS.alertOnSkipped;

    // Alerts & Notifications
    document.getElementById('enableArbitrageAlerts').checked = settings.enableArbitrageAlerts !== undefined ? settings.enableArbitrageAlerts : DEFAULT_SETTINGS.enableArbitrageAlerts;
    document.getElementById('enableSteamAlerts').checked = settings.enableSteamAlerts !== undefined ? settings.enableSteamAlerts : DEFAULT_SETTINGS.enableSteamAlerts;
    document.getElementById('enableLineAlerts').checked = settings.enableLineAlerts !== undefined ? settings.enableLineAlerts : DEFAULT_SETTINGS.enableLineAlerts;
    document.getElementById('enableGoalieAlerts').checked = settings.enableGoalieAlerts !== undefined ? settings.enableGoalieAlerts : DEFAULT_SETTINGS.enableGoalieAlerts;
    document.getElementById('soundEnabled').checked = settings.soundEnabled !== undefined ? settings.soundEnabled : DEFAULT_SETTINGS.soundEnabled;
    document.getElementById('voiceEnabled').checked = settings.voiceEnabled !== undefined ? settings.voiceEnabled : DEFAULT_SETTINGS.voiceEnabled;

    const volumePercent = Math.round((settings.soundVolume || DEFAULT_SETTINGS.soundVolume) * 100);
    document.getElementById('soundVolume').value = volumePercent;
    document.getElementById('volumeValue').textContent = `${volumePercent}%`;

    document.getElementById('lowBalanceWarnings').checked = settings.lowBalanceWarnings !== undefined ? settings.lowBalanceWarnings : DEFAULT_SETTINGS.lowBalanceWarnings;

    console.log('[SETTINGS] Loaded settings:', settings);
  } catch (error) {
    console.error('[SETTINGS] Error loading settings:', error);
    showNotification('Error loading settings', 'error');
  }
}

// Save settings to chrome.storage
async function saveSettings() {
  try {
    // Build sportsbooks object
    const sportsbooks = {};
    const sportsbookKeys = ['draftkings', 'fanduel', 'betmgm', 'caesars', 'betrivers'];

    for (const key of sportsbookKeys) {
      const enableCheckbox = document.getElementById(`enable${capitalize(key)}`);
      const balanceInput = document.getElementById(`balance${capitalize(key)}`);

      sportsbooks[key] = {
        enabled: enableCheckbox ? enableCheckbox.checked : false,
        balance: balanceInput ? parseFloat(balanceInput.value) || 0 : 0
      };
    }

    // Build settings object
    const settings = {
      // Bankroll Management
      totalBankroll: parseFloat(document.getElementById('totalBankroll').value) || DEFAULT_SETTINGS.totalBankroll,
      maxBetPercentage: parseFloat(document.getElementById('maxBetPercentage').value) || DEFAULT_SETTINGS.maxBetPercentage,
      minProfitThreshold: parseFloat(document.getElementById('minProfitThreshold').value) || DEFAULT_SETTINGS.minProfitThreshold,
      betSizingMethod: document.getElementById('betSizingMethod').value,
      fixedBetAmount: parseFloat(document.getElementById('fixedBetAmount').value) || DEFAULT_SETTINGS.fixedBetAmount,

      // Sportsbooks
      sportsbooks: sportsbooks,

      // Auto-Bet Behavior
      autoBetMode: document.getElementById('autoBetMode').value,
      skipInsufficientFunds: document.getElementById('skipInsufficientFunds').checked,
      alertOnSkipped: document.getElementById('alertOnSkipped').checked,

      // Alerts & Notifications
      enableArbitrageAlerts: document.getElementById('enableArbitrageAlerts').checked,
      enableSteamAlerts: document.getElementById('enableSteamAlerts').checked,
      enableLineAlerts: document.getElementById('enableLineAlerts').checked,
      enableGoalieAlerts: document.getElementById('enableGoalieAlerts').checked,
      soundEnabled: document.getElementById('soundEnabled').checked,
      voiceEnabled: document.getElementById('voiceEnabled').checked,
      soundVolume: parseInt(document.getElementById('soundVolume').value) / 100,
      lowBalanceWarnings: document.getElementById('lowBalanceWarnings').checked,

      // Legacy settings (maintain compatibility)
      minProfit: parseFloat(document.getElementById('minProfitThreshold').value) || DEFAULT_SETTINGS.minProfitThreshold,
      maxStake: parseFloat(document.getElementById('totalBankroll').value) || DEFAULT_SETTINGS.totalBankroll,
      autoOpen: true,
      autoFill: document.getElementById('autoBetMode').value !== 'off',
      voiceRate: 1.0,
      voicePitch: 1.0,

      // Build enabled books object for background script
      enabledBooks: Object.fromEntries(
        Object.entries(sportsbooks).map(([key, data]) => [key, data.enabled])
      )
    };

    // Save to chrome.storage
    await chrome.storage.sync.set({ settings });

    // Also update the settings in the background script
    chrome.runtime.sendMessage({
      type: 'update_settings',
      settings: settings
    });

    console.log('[SETTINGS] Saved settings:', settings);
    showNotification('Settings saved successfully!');
  } catch (error) {
    console.error('[SETTINGS] Error saving settings:', error);
    showNotification('Error saving settings', 'error');
  }
}

// Reset to default settings
async function resetSettings() {
  if (!confirm('Are you sure you want to reset all settings to defaults?')) {
    return;
  }

  try {
    await chrome.storage.sync.set({ settings: DEFAULT_SETTINGS });
    await loadSettings();
    showNotification('Settings reset to defaults');
  } catch (error) {
    console.error('[SETTINGS] Error resetting settings:', error);
    showNotification('Error resetting settings', 'error');
  }
}

// Setup event listeners
function setupEventListeners() {
  // Save button
  document.getElementById('saveBtn').addEventListener('click', saveSettings);

  // Reset button
  document.getElementById('resetBtn').addEventListener('click', resetSettings);

  // Close button
  document.getElementById('closeBtn').addEventListener('click', () => {
    window.close();
  });

  // Bet sizing method change
  document.getElementById('betSizingMethod').addEventListener('change', (e) => {
    toggleFixedAmountInput(e.target.value);
  });

  // Volume slider
  document.getElementById('soundVolume').addEventListener('input', (e) => {
    document.getElementById('volumeValue').textContent = `${e.target.value}%`;
  });

  // Auto-save on change (optional)
  // Uncomment to enable auto-save
  /*
  const inputs = document.querySelectorAll('input, select');
  inputs.forEach(input => {
    input.addEventListener('change', () => {
      saveSettings();
    });
  });
  */
}

// Toggle fixed amount input visibility
function toggleFixedAmountInput(method) {
  const fixedAmountRow = document.getElementById('fixedAmountRow');
  if (method === 'fixed_amount') {
    fixedAmountRow.style.display = 'flex';
  } else {
    fixedAmountRow.style.display = 'none';
  }
}

// Show notification
function showNotification(message, type = 'success') {
  const notification = document.getElementById('saveNotification');
  notification.textContent = message;
  notification.style.background = type === 'error'
    ? 'linear-gradient(135deg, #b91c1c 0%, #ef4444 100%)'
    : 'linear-gradient(135deg, #166534 0%, #16a34a 100%)';

  notification.classList.add('show');

  setTimeout(() => {
    notification.classList.remove('show');
  }, 3000);
}

// Capitalize first letter
function capitalize(str) {
  if (!str) return '';
  if (str === 'betmgm') return 'BetMGM';
  if (str === 'betrivers') return 'BetRivers';
  return str.charAt(0).toUpperCase() + str.slice(1);
}

// Calculate total balance across all enabled books
function calculateTotalBalance() {
  const sportsbookKeys = ['draftkings', 'fanduel', 'betmgm', 'caesars', 'betrivers'];
  let total = 0;

  for (const key of sportsbookKeys) {
    const enableCheckbox = document.getElementById(`enable${capitalize(key)}`);
    const balanceInput = document.getElementById(`balance${capitalize(key)}`);

    if (enableCheckbox && enableCheckbox.checked && balanceInput) {
      total += parseFloat(balanceInput.value) || 0;
    }
  }

  return total;
}
