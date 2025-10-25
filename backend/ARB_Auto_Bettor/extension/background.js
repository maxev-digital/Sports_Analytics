/**
 * ARB Auto Bettor™ - Background Service Worker
 * Connects to backend WebSocket for real-time arbitrage alerts
 * Manages notifications and coordinates with content scripts
 */

// Backend URLs - try production first, fallback to localhost if unreachable
let BACKEND_URL = 'https://max-ev-sports.com';
let WS_URL = 'wss://max-ev-sports.com/ws';
const BACKEND_FALLBACK = 'http://localhost:8000';
const WS_FALLBACK = 'ws://localhost:8000/ws';
const USE_WEBSOCKET = false; // Temporarily disabled - using REST polling instead
const POLL_INTERVAL = 5000; // Poll every 5 seconds

// Test backend connectivity and set appropriate URL
async function detectBackendURL() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/games`, { method: 'HEAD', signal: AbortSignal.timeout(3000) });
    if (response.ok) {
      console.log('✅ Connected to production backend:', BACKEND_URL);
      return;
    }
  } catch (error) {
    console.log('⚠️ Production backend unreachable, trying localhost...');
  }

  // Try localhost fallback
  try {
    const response = await fetch(`${BACKEND_FALLBACK}/api/games`, { method: 'HEAD', signal: AbortSignal.timeout(3000) });
    if (response.ok) {
      BACKEND_URL = BACKEND_FALLBACK;
      WS_URL = WS_FALLBACK;
      console.log('✅ Connected to localhost backend:', BACKEND_URL);
    }
  } catch (error) {
    console.error('❌ No backend available');
  }
}

// Detect backend on startup
detectBackendURL();

// URL Builder functions (inlined to avoid importScripts issues in Manifest V3)
function slugify(teamName) {
  return teamName
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^a-z0-9-]/g, '')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
}

function getSportKey(sportKey) {
  if (!sportKey) return 'basketball';
  if (sportKey.includes('basketball')) return 'basketball';
  if (sportKey.includes('football_nfl')) return 'americanfootball';
  if (sportKey.includes('football_ncaaf')) return 'americanfootball';
  if (sportKey.includes('baseball')) return 'baseball';
  if (sportKey.includes('hockey')) return 'icehockey';
  if (sportKey.includes('soccer')) return 'soccer';
  return 'basketball';
}

function getLeague(sportKey) {
  if (!sportKey) return 'nba';
  if (sportKey.includes('nba')) return 'nba';
  if (sportKey.includes('nfl')) return 'nfl';
  if (sportKey.includes('ncaaf')) return 'ncaaf';
  if (sportKey.includes('mlb')) return 'mlb';
  if (sportKey.includes('nhl')) return 'nhl';
  if (sportKey.includes('mls')) return 'mls';
  if (sportKey.includes('epl')) return 'epl';
  return 'nba';
}

function buildBookmakerURL(bookmaker, game = null) {
  const sport = game ? getSportKey(game.sport_key || game.sport) : 'basketball';
  const league = game ? getLeague(game.sport_key || game.sport) : 'nba';

  const urlPatterns = {
    'draftkings': { base: 'https://sportsbook.draftkings.com', path: `/leagues/${sport}/${league}` },
    'fanduel': { base: 'https://sportsbook.fanduel.com', path: `/navigation/${league}` },
    'betmgm': { base: 'https://sports.betmgm.com', path: `/en/sports/${sport}-7/betting/usa-9/${league}` },
    'caesars': { base: 'https://www.caesars.com/sportsbook-and-casino', path: `/${sport}/${league}` },
    'betrivers': { base: 'https://www.betrivers.com', path: `/?page=sportsbook#${sport}` },
    'bovada': { base: 'https://www.bovada.lv', path: `/sports/${sport}/${league}` },
    'betonlineag': { base: 'https://www.betonline.ag', path: `/sportsbook/${sport}/${league}` },
    'mybookieag': { base: 'https://www.mybookie.ag', path: `/sportsbook/${league}/` },
    'betus': { base: 'https://www.betus.com.pa', path: `/sportsbook/${sport}/` },
    'lowvig': { base: 'https://lowvig.ag', path: `/sports/${sport}` },
    'williamhill_us': { base: 'https://www.williamhill.com/us', path: `/bet/en/betting/t/${sport}/${league}` }
  };

  const config = urlPatterns[bookmaker];
  if (!config) {
    console.warn(`[ARB] No URL pattern for bookmaker: ${bookmaker}`);
    return null;
  }

  return `${config.base}${config.path}`;
}

// DEPRECATED: Old static URL mapping (replaced by url_builder.js)
// Kept for backwards compatibility
const BOOKMAKER_URLS_OLD = {
  'draftkings': 'https://sportsbook.draftkings.com/leagues/basketball/nba',
  'fanduel': 'https://sportsbook.fanduel.com/navigation/nba',
  'betmgm': 'https://sports.betmgm.com/en/sports/basketball-7/betting/usa-9/nba-6004',
  'betrivers': 'https://www.betrivers.com/?page=sportsbook#basketball',
  'williamhill_us': 'https://www.williamhill.com/us/nv/bet/en/betting/t/basketball/nba',
  'fanatics': 'https://fanatics.com/sportsbook/basketball/nba',
  'espnbet': 'https://espnbet.com/sport/basketball/usa/nba',
  'caesars': 'https://www.caesars.com/sportsbook-and-casino/basketball/nba',
  'pointsbet': 'https://pointsbet.com/sports/basketball/nba',
  'ballybet': 'https://ballybet.com/sports/basketball',
  'betonlineag': 'https://www.betonline.ag/sportsbook/basketball/nba',
  'bovada': 'https://www.bovada.lv/sports/basketball',
  'mybookieag': 'https://www.mybookie.ag/sportsbook/nba/',
  'lowvig': 'https://lowvig.ag/sports/basketball',
  'betway': 'https://sports.betway.com/en/sports/grp/basketball',
  'betus': 'https://www.betus.com.pa/sportsbook/basketball/'
};

function getBookmaker(key) {
  return {
    name: key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    url: BOOKMAKER_URLS[key] || '#',
    logo: `https://www.google.com/s2/favicons?domain=${key.replace('_us', '').replace('ag', '.ag').replace('mybookie', 'mybookie.ag')}.com&sz=64`
  };
}

let ws = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY = 3000; // 3 seconds
let pollIntervalId = null;

// Extension state
let extensionEnabled = true;
let currentOpportunities = [];
let seenOpportunityIds = new Set(); // Track seen opportunities to avoid duplicate alerts

// Steam moves and line movements
let currentSteamMoves = [];
let currentLineMovements = [];
let seenSteamMoveIds = new Set();
let seenLineMovementIds = new Set();

// Goalie pull opportunities
let currentGoaliePulls = [];
let seenGoaliePullIds = new Set();

let settings = {
  autoOpen: true,  // Auto-open sportsbook tabs
  autoFill: true,  // Auto-fill bet slips
  minProfit: 1.0,  // Minimum profit % to alert
  maxStake: 1000,  // Maximum stake per bet
  soundEnabled: true,  // Sound alerts enabled
  soundVolume: 0.5,  // Volume 0.0 to 1.0
  voiceEnabled: true,  // Voice announcements enabled
  voiceRate: 1.0,  // Speech rate (0.1 to 10)
  voicePitch: 1.0,  // Voice pitch (0 to 2)
  // Alert type toggles
  enableArbitrageAlerts: true,
  enableSteamAlerts: true,
  enableLineAlerts: true,
  enableGoalieAlerts: true,
  enabledBooks: {
    draftkings: true,
    fanduel: true,
    betmgm: true,
    caesars: true,
    betrivers: true
  }
};

// Load settings from storage
async function loadSettings() {
  try {
    const result = await chrome.storage.sync.get('settings');
    if (result.settings) {
      settings = { ...settings, ...result.settings };
      console.log('[ARB] Settings loaded:', settings);
    }
  } catch (error) {
    console.error('[ARB] Error loading settings:', error);
  }
}

// Call loadSettings on startup
loadSettings();

// Sound Alert System (routes audio to offscreen document)
class SoundAlerts {
  constructor() {
    // No longer need audioContext here - using offscreen document
  }

  async playBeep(frequency = 800, duration = 0.2, type = 'sine') {
    if (!settings.soundEnabled) return;

    try {
      await ensureOffscreenDocument();
      await chrome.runtime.sendMessage({
        type: 'play_beep',
        frequency: frequency,
        duration: duration,
        type: type,
        volume: settings.soundVolume
      });
    } catch (error) {
      console.error('[SOUND] Error playing beep:', error);
    }
  }

  async playSequence(notes) {
    if (!settings.soundEnabled) return;

    try {
      await ensureOffscreenDocument();
      await chrome.runtime.sendMessage({
        type: 'play_sequence',
        notes: notes,
        volume: settings.soundVolume
      });
    } catch (error) {
      console.error('[SOUND] Error playing sequence:', error);
    }
  }

  async playHighPriority() {
    console.log('[SOUND] 🔊 HIGH priority alert');
    await this.playSequence([
      { f: 1200, d: 0.15, t: 'square' },
      { f: 1400, d: 0.15, t: 'square', g: 0.05 },
      { f: 1200, d: 0.15, t: 'square', g: 0.05 },
      { f: 1400, d: 0.15, t: 'square' }
    ]);
  }

  async playMediumPriority() {
    console.log('[SOUND] 🔔 MEDIUM priority alert');
    await this.playSequence([
      { f: 900, d: 0.2, t: 'sine' },
      { f: 1100, d: 0.2, t: 'sine', g: 0.1 }
    ]);
  }

  async playLowPriority() {
    console.log('[SOUND] 🔕 LOW priority alert');
    await this.playBeep(700, 0.15, 'sine');
  }

  async playForOpportunity(profitPercentage) {
    if (profitPercentage >= 5.0) {
      await this.playHighPriority();
    } else if (profitPercentage >= 3.0) {
      await this.playMediumPriority();
    } else {
      await this.playLowPriority();
    }
  }

  // Text-to-Speech Voice Announcements (using offscreen document)
  async speak(text) {
    if (!settings.voiceEnabled) return;

    try {
      // Ensure offscreen document is created
      await ensureOffscreenDocument();

      // Send message to offscreen document to speak
      await chrome.runtime.sendMessage({
        type: 'speak',
        text: text,
        rate: settings.voiceRate || 1.0,
        pitch: settings.voicePitch || 1.0,
        volume: settings.soundVolume || 0.5
      });

      console.log('[VOICE] 🗣️ Speaking via offscreen:', text);
    } catch (error) {
      console.error('[VOICE] Error speaking:', error);
    }
  }

  async announceOpportunity(profitPercentage, bookA, bookB, game) {
    if (!settings.voiceEnabled) return;

    const percentRounded = profitPercentage.toFixed(1);
    let announcement = '';

    // Different announcements based on priority
    if (profitPercentage >= 5.0) {
      announcement = `High priority arbitrage opportunity!`;
    } else if (profitPercentage >= 3.0) {
      announcement = `Arbitrage opportunity`;
    } else {
      announcement = `Arbitrage found`;
    }

    // Add game info
    if (game) {
      announcement += ` ${game}.`;
    }

    // Add ROI
    announcement += ` ${percentRounded} percent ROI`;

    // Add bookmaker info if provided
    if (bookA && bookB) {
      const book1Name = this.cleanBookmakerName(bookA);
      const book2Name = this.cleanBookmakerName(bookB);
      announcement += ` between ${book1Name} and ${book2Name}`;
    }

    await this.speak(announcement);
  }

  cleanBookmakerName(key) {
    // Convert bookmaker key to readable name
    const nameMap = {
      'draftkings': 'DraftKings',
      'fanduel': 'FanDuel',
      'betmgm': 'BetMGM',
      'caesars': 'Caesars',
      'betrivers': 'BetRivers',
      'williamhill_us': 'William Hill',
      'pointsbet': 'PointsBet',
      'espnbet': 'ESPN Bet',
      'fanatics': 'Fanatics',
      'betonlineag': 'Bet Online',
      'bovada': 'Bovada',
      'mybookieag': 'My Bookie'
    };
    return nameMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  }

  async playAndAnnounce(profitPercentage, bookA, bookB, game) {
    // Play sound alert first
    await this.playForOpportunity(profitPercentage);

    // Then speak the announcement
    // Small delay to let the beep finish
    await new Promise(resolve => setTimeout(resolve, 300));
    this.announceOpportunity(profitPercentage, bookA, bookB, game);
  }
}

const soundAlerts = new SoundAlerts();

// Offscreen document management for TTS
async function ensureOffscreenDocument() {
  // Check if offscreen document already exists
  const existingContexts = await chrome.runtime.getContexts({
    contextTypes: ['OFFSCREEN_DOCUMENT']
  });

  if (existingContexts.length > 0) {
    return; // Already exists
  }

  // Create offscreen document
  await chrome.offscreen.createDocument({
    url: 'offscreen.html',
    reasons: ['AUDIO_PLAYBACK'],
    justification: 'Text-to-speech voice announcements for arbitrage alerts'
  });

  console.log('[ARB] Offscreen document created for TTS');
}

// Load settings from storage
chrome.storage.sync.get(['settings'], (result) => {
  if (result.settings) {
    settings = { ...settings, ...result.settings };
  }
  console.log('[ARB] Settings loaded:', settings);
});

// Initialize WebSocket connection
function connectWebSocket() {
  if (!USE_WEBSOCKET) {
    console.log('[ARB] WebSocket disabled - using REST API polling');
    return;
  }

  if (ws && ws.readyState === WebSocket.OPEN) {
    console.log('[ARB] WebSocket already connected');
    return;
  }

  console.log('[ARB] Connecting to WebSocket:', WS_URL);

  try {
    ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      console.log('[ARB] ✅ WebSocket connected');
      reconnectAttempts = 0;

      // Update extension badge
      chrome.action.setBadgeText({ text: 'ON' });
      chrome.action.setBadgeBackgroundColor({ color: '#93c5fd' }); // Blue 300

      // Send initial connection message
      ws.send(JSON.stringify({
        type: 'subscribe',
        channel: 'arbitrage_alerts'
      }));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('[ARB] Message received:', data);

        if (data.type === 'arbitrage_opportunity') {
          handleArbitrageOpportunity(data.opportunity);
        } else if (data.type === 'steam_move') {
          handleSteamMove(data.alert);
        } else if (data.type === 'line_movement') {
          handleLineMovement(data.alert);
        } else if (data.type === 'opportunities_update') {
          handleOpportunitiesUpdate(data.opportunities);
        }
      } catch (error) {
        console.error('[ARB] Error parsing message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('[ARB] WebSocket error:', error);
      chrome.action.setBadgeText({ text: 'ERR' });
      chrome.action.setBadgeBackgroundColor({ color: '#EF4444' }); // Red
    };

    ws.onclose = () => {
      console.log('[ARB] WebSocket closed');
      chrome.action.setBadgeText({ text: 'OFF' });
      chrome.action.setBadgeBackgroundColor({ color: '#6B7280' }); // Gray

      // Attempt to reconnect
      if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttempts++;
        console.log(`[ARB] Reconnecting in ${RECONNECT_DELAY}ms (attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);
        setTimeout(connectWebSocket, RECONNECT_DELAY);
      } else {
        console.error('[ARB] Max reconnect attempts reached');
      }
    };

  } catch (error) {
    console.error('[ARB] Error creating WebSocket:', error);
  }
}

// Handle arbitrage opportunity alert
function handleArbitrageOpportunity(opportunity) {
  console.log('[ARB] 🎯 Arbitrage opportunity:', opportunity);

  // Check if meets minimum profit requirement
  if (opportunity.profit_percentage < settings.minProfit) {
    console.log(`[ARB] Skipping - below minimum profit (${opportunity.profit_percentage}% < ${settings.minProfit}%)`);
    return;
  }

  // Generate unique ID for opportunity
  const oppId = `${opportunity.game_id || opportunity.game}_${opportunity.book_a}_${opportunity.book_b}_${opportunity.market_type}`;

  // Check if this is a NEW opportunity
  const isNew = !seenOpportunityIds.has(oppId);
  if (isNew) {
    seenOpportunityIds.add(oppId);
    // Play sound and voice alert for NEW opportunities only
    const game = opportunity.game || `${opportunity.away_team} at ${opportunity.home_team}`;
    soundAlerts.playAndAnnounce(
      opportunity.profit_percentage,
      opportunity.book_a || opportunity.book1,
      opportunity.book_b || opportunity.book2,
      game
    );
    console.log(`[ARB] 🆕 NEW opportunity detected - playing alert with voice announcement`);
  }

  // Add to current opportunities
  currentOpportunities.push(opportunity);

  // Update badge with count
  chrome.action.setBadgeText({ text: currentOpportunities.length.toString() });
  chrome.action.setBadgeBackgroundColor({ color: '#93c5fd' }); // Blue 300

  // Send browser notification
  const priority = opportunity.profit_percentage >= 5.0 ? 'HIGH' :
                   opportunity.profit_percentage >= 3.0 ? 'MEDIUM' : 'LOW';

  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'icons/icon.svg',
    title: `${priority} PRIORITY Arbitrage - ${opportunity.profit_percentage.toFixed(2)}%`,
    message: `${opportunity.game}\n${opportunity.market_type}\n$${opportunity.total_stake.toFixed(2)} stake → $${opportunity.guaranteed_profit.toFixed(2)} profit`,
    priority: priority === 'HIGH' ? 2 : 1,
    requireInteraction: priority === 'HIGH', // Stays visible for HIGH priority
    buttons: [
      { title: 'Open Bets' },
      { title: 'Dismiss' }
    ]
  }, (notificationId) => {
    // Store opportunity ID with notification for button clicks
    chrome.storage.local.set({
      [`notification_${notificationId}`]: opportunity
    });
  });

  // If auto-open enabled, open sportsbook tabs
  if (settings.autoOpen) {
    openSportsbookTabs(opportunity);
  }
}

// Handle steam move alert
function handleSteamMove(alert) {
  console.log('[ARB] 📈 Steam move:', alert);

  // Less intrusive notification for steam moves
  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'icons/icon.svg',
    title: `Steam Move - ${alert.consensus_percentage}% consensus`,
    message: `${alert.game}\n${alert.move_direction} movement on ${alert.market_type}`,
    priority: 0
  });
}

// Handle line movement alert
function handleLineMovement(alert) {
  console.log('[ARB] 📊 Line movement:', alert);
  // Only log, don't send notification (too frequent)
}

// Handle opportunities update (batch)
function handleOpportunitiesUpdate(opportunities) {
  console.log(`[ARB] 📋 Opportunities update: ${opportunities.length} active`);

  // Normalize field names from REST API to match extension expectations
  const normalizedOpportunities = opportunities.map(op => ({
    ...op,
    profit_percentage: op.profit_percent || op.profit_percentage || 0,
    book1: op.book_a || op.book1,
    book2: op.book_b || op.book2,
    game: op.game || `${op.away_team} @ ${op.home_team}`
  }));

  // Filter by minimum profit threshold
  currentOpportunities = normalizedOpportunities.filter(op =>
    op.profit_percentage >= settings.minProfit
  );

  console.log(`[ARB] 📊 ${currentOpportunities.length} opportunities above ${settings.minProfit}% threshold`);

  // Build set of current opportunity IDs
  const currentOppIds = new Set(
    currentOpportunities.map(op =>
      `${op.game_id || op.game}_${op.book_a || op.book1}_${op.book_b || op.book2}_${op.market_type}`
    )
  );

  // Remove old opportunity IDs that are no longer active
  for (const oppId of seenOpportunityIds) {
    if (!currentOppIds.has(oppId)) {
      seenOpportunityIds.delete(oppId);
    }
  }

  // Check for NEW opportunities and play alerts (ONLY if arbitrage alerts enabled)
  if (settings.enableArbitrageAlerts) {
    currentOpportunities.forEach(op => {
      const oppId = `${op.game_id || op.game}_${op.book_a || op.book1}_${op.book_b || op.book2}_${op.market_type}`;
      const isNew = !seenOpportunityIds.has(oppId);

      if (isNew) {
        seenOpportunityIds.add(oppId);
        // Play sound and voice alert for NEW opportunities
        soundAlerts.playAndAnnounce(
          op.profit_percentage,
          op.book_a || op.book1,
          op.book_b || op.book2
        );
        console.log(`[ARB] 🆕 NEW arbitrage opportunity: ${op.game} - ${op.profit_percentage.toFixed(2)}% profit`);
      }
    });
  } else {
    console.log('[ARB] ⏭️ Arbitrage alerts disabled, skipping sound alerts');
  }

  // Update badge with total alerts
  updateBadge();
}

// Handle steam moves update
function handleSteamMovesUpdate(steamMoves) {
  console.log(`[STEAM] 🔥 Steam moves update: ${steamMoves.length} active`);

  currentSteamMoves = steamMoves;

  // Build set of current steam move IDs
  const currentSteamIds = new Set(
    steamMoves.map(sm => `${sm.game_id}_${sm.bookmaker}_${sm.market_type}_${sm.timestamp}`)
  );

  // Remove old steam move IDs
  for (const steamId of seenSteamMoveIds) {
    if (!currentSteamIds.has(steamId)) {
      seenSteamMoveIds.delete(steamId);
    }
  }

  // Check for NEW steam moves and play alerts (ONLY if steam alerts enabled)
  if (settings.enableSteamAlerts) {
    steamMoves.forEach(sm => {
      const steamId = `${sm.game_id}_${sm.bookmaker}_${sm.market_type}_${sm.timestamp}`;
      const isNew = !seenSteamMoveIds.has(steamId);

      if (isNew) {
        seenSteamMoveIds.add(steamId);
        // Play steam move alert (different sound/voice)
        playSteamMoveAlert(sm);
        console.log(`[STEAM] 🆕 NEW steam move: ${sm.game || sm.home_team + ' vs ' + sm.away_team}`);
      }
    });
  } else {
    console.log('[STEAM] ⏭️ Steam move alerts disabled, skipping sound alerts');
  }

  updateBadge();
}

// Handle line movements update
function handleLineMovementsUpdate(lineMovements) {
  console.log(`[LINE] 📈 Line movements update: ${lineMovements.length} active`);

  currentLineMovements = lineMovements;

  // Build set of current line movement IDs
  const currentLineIds = new Set(
    lineMovements.map(lm => `${lm.game_id}_${lm.market_type}_${lm.timestamp}`)
  );

  // Remove old line movement IDs
  for (const lineId of seenLineMovementIds) {
    if (!currentLineIds.has(lineId)) {
      seenLineMovementIds.delete(lineId);
    }
  }

  // Check for NEW line movements (ONLY if line alerts enabled)
  if (settings.enableLineAlerts) {
    lineMovements.forEach(lm => {
      const lineId = `${lm.game_id}_${lm.market_type}_${lm.timestamp}`;
      const isNew = !seenLineMovementIds.has(lineId);

      if (isNew) {
        seenLineMovementIds.add(lineId);
        console.log(`[LINE] 🆕 NEW line movement: ${lm.game || lm.home_team + ' vs ' + lm.away_team}`);
        // Could add line movement sound alerts here if desired
      }
    });
  } else {
    console.log('[LINE] ⏭️ Line movement alerts disabled, skipping alerts');
  }

  updateBadge();
}

// Handle goalie pull opportunities update
function handleGoaliePullsUpdate(goaliePulls) {
  console.log(`[GOALIE] 🏒 Goalie pull opportunities: ${goaliePulls.length} active`);

  currentGoaliePulls = goaliePulls;

  // Build set of current goalie pull IDs
  const currentGoalieIds = new Set(
    goaliePulls.map(gp => `${gp.game_id}_${gp.timestamp}`)
  );

  // Remove old goalie pull IDs
  for (const goalieId of seenGoaliePullIds) {
    if (!currentGoalieIds.has(goalieId)) {
      seenGoaliePullIds.delete(goalieId);
    }
  }

  // Check for NEW goalie pulls and play alerts (ONLY if goalie alerts enabled)
  if (settings.enableGoalieAlerts) {
    goaliePulls.forEach(gp => {
      const goalieId = `${gp.game_id}_${gp.timestamp}`;
      const isNew = !seenGoaliePullIds.has(goalieId);

      if (isNew) {
        seenGoaliePullIds.add(goalieId);
        // Play goalie pull alert
        playGoaliePullAlert(gp);
        console.log(`[GOALIE] 🆕 NEW goalie pull opportunity: ${gp.game}`);
      }
    });
  } else {
    console.log('[GOALIE] ⏭️ Goalie pull alerts disabled, skipping sound alerts');
  }

  updateBadge();
}

// Update badge with total alert count
function updateBadge() {
  const totalAlerts = currentOpportunities.length + currentSteamMoves.length + currentLineMovements.length + currentGoaliePulls.length;

  if (totalAlerts > 0) {
    chrome.action.setBadgeText({ text: totalAlerts.toString() });

    // Color based on priority
    const highPriorityArbs = currentOpportunities.filter(op => op.profit_percentage >= 5.0);
    const mediumPriorityArbs = currentOpportunities.filter(op => op.profit_percentage >= 3.0 && op.profit_percentage < 5.0);

    if (highPriorityArbs.length > 0) {
      // RED for high priority arbitrage (5%+)
      chrome.action.setBadgeBackgroundColor({ color: '#ef4444' });
    } else if (mediumPriorityArbs.length > 0 || currentSteamMoves.length > 0) {
      // ORANGE for medium priority arbs or steam moves
      chrome.action.setBadgeBackgroundColor({ color: '#f97316' });
    } else {
      // BLUE for low priority alerts
      chrome.action.setBadgeBackgroundColor({ color: '#3b82f6' });
    }
  } else {
    // Clear badge when no alerts
    chrome.action.setBadgeText({ text: '' });
  }
}

// Play steam move alert (different from arbitrage)
async function playSteamMoveAlert(steamMove) {
  if (!settings.soundEnabled && !settings.voiceEnabled) return;

  // Play a distinctive "steam" sound (higher pitched, faster)
  if (settings.soundEnabled) {
    await soundAlerts.playSequence([
      { f: 1400, d: 0.1, t: 'triangle' },
      { f: 1600, d: 0.1, t: 'triangle', g: 0.05 },
      { f: 1400, d: 0.1, t: 'triangle', g: 0.05 }
    ]);
  }

  // Voice announcement for steam move with stale line info
  if (settings.voiceEnabled) {
    const game = steamMove.game || `${steamMove.away_team} at ${steamMove.home_team}`;
    const direction = steamMove.movement_direction || (steamMove.movement > 0 ? 'up' : 'down');
    const movedBooks = steamMove.books_moved ? steamMove.books_moved.length : 0;
    const marketType = steamMove.market_type === 'totals' ? 'total' : 'spread';

    // Format moved books for announcement
    const booksMovedText = steamMove.books_moved && steamMove.books_moved.length > 0
      ? steamMove.books_moved.slice(0, 2).join(' and ')
      : 'multiple books';

    // Build announcement
    let announcement = `Steam move detected! ${game}. ${marketType} moved ${direction}. `;
    announcement += `${movedBooks} books moved including ${booksMovedText}. `;

    // Add stale line info - THIS IS THE KEY!
    if (steamMove.best_stale_book && steamMove.best_stale_book !== "All books moved") {
      const cleanStaleName = cleanBookmakerName(steamMove.best_stale_book);
      const oldLine = steamMove.best_stale_line ? steamMove.best_stale_line.toFixed(1) : 'unknown';
      announcement += `Best stale price at ${cleanStaleName}, line ${oldLine}. Bet now!`;
    } else {
      announcement += `All books have moved!`;
    }

    await soundAlerts.speak(announcement);
  }
}

// Play goalie pull alert
async function playGoaliePullAlert(goaliePull) {
  if (!settings.soundEnabled && !settings.voiceEnabled) return;

  // Play urgent alert sound (pulsing, urgent)
  if (settings.soundEnabled) {
    await soundAlerts.playSequence([
      { f: 800, d: 0.15, t: 'square' },
      { f: 1000, d: 0.15, t: 'square', g: 0.1 },
      { f: 800, d: 0.15, t: 'square', g: 0.1 },
      { f: 1000, d: 0.3, t: 'square' }
    ]);
  }

  // Voice announcement
  if (settings.voiceEnabled) {
    const game = goaliePull.game || 'Unknown game';
    const score = goaliePull.score || '';
    const time = goaliePull.time_remaining || '';

    const announcement = `Goalie pull alert! ${game}. Score: ${score}. Time: ${time} remaining. Two goal game. Prepare Bovada now!`;

    await soundAlerts.speak(announcement);
  }
}

// Helper to clean bookmaker names for voice
function cleanBookmakerName(key) {
  const nameMap = {
    'draftkings': 'DraftKings',
    'fanduel': 'FanDuel',
    'betmgm': 'BetMGM',
    'caesars': 'Caesars',
    'betrivers': 'BetRivers',
    'williamhill_us': 'William Hill',
    'pointsbet': 'PointsBet',
    'espnbet': 'ESPN Bet',
    'fanatics': 'Fanatics',
    'betonlineag': 'Bet Online',
    'bovada': 'Bovada',
    'mybookieag': 'My Bookie',
    'lowvig': 'Low Vig'
  };
  return nameMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

// Open sportsbook tabs for an opportunity
async function openSportsbookTabs(opportunity) {
  console.log('[ARB] Opening sportsbook tabs for:', opportunity);

  const book1Key = opportunity.book1 || opportunity.book_a || '';
  const book2Key = opportunity.book2 || opportunity.book_b || '';

  console.log('[ARB] Opening tabs for books:', book1Key, 'and', book2Key);

  // Build game data object for URL builder
  const gameData = {
    sport_key: opportunity.sport || opportunity.sport_key || 'basketball_nba',
    home_team: opportunity.home_team || '',
    away_team: opportunity.away_team || '',
    commence_time: opportunity.commence_time || new Date().toISOString()
  };

  // Build URLs using URL builder (dynamic based on sport/game)
  const book1Url = buildBookmakerURL(book1Key, gameData);
  const book2Url = buildBookmakerURL(book2Key, gameData);

  const openedTabs = [];

  // Open tab for book 1
  if (book1Url) {
    console.log('[ARB] Opening', book1Key, 'tab at', book1Url);
    const tab1 = await chrome.tabs.create({ url: book1Url, active: false });
    openedTabs.push({ tab: tab1, bookKey: book1Key });
  } else {
    console.log('[ARB] No URL found for book:', book1Key);
  }

  // Open tab for book 2
  if (book2Url) {
    console.log('[ARB] Opening', book2Key, 'tab at', book2Url);
    const tab2 = await chrome.tabs.create({ url: book2Url, active: true });
    openedTabs.push({ tab: tab2, bookKey: book2Key });
  } else {
    console.log('[ARB] No URL found for book:', book2Key);
  }

  // Send opportunity data to tabs after they load
  // Wait for page to load, then send fill_bet_slip message
  setTimeout(async () => {
    for (const { tab, bookKey } of openedTabs) {
      try {
        console.log('[ARB] Sending fill_bet_slip message to', bookKey, 'tab ID:', tab.id);

        // Send message to content script
        await chrome.tabs.sendMessage(tab.id, {
          type: 'fill_bet_slip',
          opportunity: {
            ...opportunity,
            // Add stake amount based on book
            stake_amount: bookKey === book1Key ? opportunity.stake_book1 : opportunity.stake_book2
          },
          autoBetMode: settings.autoBetMode || 'fill',
          forBook: bookKey
        });

        console.log('[ARB] ✅ Message sent successfully to', bookKey);
      } catch (error) {
        console.error('[ARB] Error sending message to tab:', error);
        // Tab might not be ready yet, content script might not be injected
      }
    }
  }, 3000); // Wait 3 seconds for pages to load
}

// Handle notification button clicks
chrome.notifications.onButtonClicked.addListener((notificationId, buttonIndex) => {
  if (buttonIndex === 0) {
    // "Open Bets" button clicked
    chrome.storage.local.get([`notification_${notificationId}`], (result) => {
      const opportunity = result[`notification_${notificationId}`];
      if (opportunity) {
        openSportsbookTabs(opportunity);
      }
    });
  }

  // Clear notification
  chrome.notifications.clear(notificationId);
});

// Handle messages from popup or content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('[ARB] Message received:', message);

  if (message.type === 'get_opportunities') {
    sendResponse({
      opportunities: currentOpportunities,
      steamMoves: currentSteamMoves,
      lineMovements: currentLineMovements,
      goaliePulls: currentGoaliePulls
    });
    return true;
  }

  if (message.type === 'get_status') {
    const connected = USE_WEBSOCKET
      ? (ws && ws.readyState === WebSocket.OPEN)
      : (pollIntervalId !== null); // Connected if polling is active
    sendResponse({ connected });
    return true;
  }

  if (message.type === 'get_settings') {
    sendResponse({ settings });
    return true;
  }

  if (message.type === 'update_settings') {
    settings = { ...settings, ...message.settings };
    chrome.storage.sync.set({ settings });
    sendResponse({ success: true });
    return true;
  }

  if (message.type === 'toggle_enabled') {
    extensionEnabled = !extensionEnabled;
    if (extensionEnabled) {
      if (USE_WEBSOCKET) {
        connectWebSocket();
      } else {
        startPolling();
      }
    } else {
      if (USE_WEBSOCKET && ws) {
        ws.close();
      } else {
        stopPolling();
      }
    }
    sendResponse({ enabled: extensionEnabled });
    return true;
  }

  if (message.type === 'open_opportunity') {
    openSportsbookTabs(message.opportunity);
    sendResponse({ success: true });
    return true;
  }

  if (message.type === 'dismiss_opportunity') {
    currentOpportunities = currentOpportunities.filter(
      op => op.id !== message.opportunityId
    );
    chrome.action.setBadgeText({
      text: currentOpportunities.length > 0 ? currentOpportunities.length.toString() : ''
    });
    sendResponse({ success: true });
    return true;
  }

  // Sound control messages
  if (message.type === 'toggle_sound') {
    settings.soundEnabled = !settings.soundEnabled;
    chrome.storage.sync.set({ settings });
    console.log(`[ARB] Sound alerts ${settings.soundEnabled ? 'enabled' : 'disabled'}`);
    sendResponse({ enabled: settings.soundEnabled });
    return true;
  }

  if (message.type === 'set_volume') {
    settings.soundVolume = Math.max(0, Math.min(1, message.volume));
    chrome.storage.sync.set({ settings });
    console.log(`[ARB] Volume set to ${(settings.soundVolume * 100).toFixed(0)}%`);
    sendResponse({ volume: settings.soundVolume });
    return true;
  }

  if (message.type === 'test_sound') {
    const priority = message.priority || 'medium';
    console.log(`[ARB] Testing ${priority} priority sound`);

    (async () => {
      if (priority === 'high') {
        await soundAlerts.playHighPriority();
      } else if (priority === 'medium') {
        await soundAlerts.playMediumPriority();
      } else {
        await soundAlerts.playLowPriority();
      }
      sendResponse({ success: true });
    })();

    return true; // Keep channel open for async response
  }

  // Voice control messages
  if (message.type === 'toggle_voice') {
    settings.voiceEnabled = !settings.voiceEnabled;
    chrome.storage.sync.set({ settings });
    console.log(`[ARB] Voice announcements ${settings.voiceEnabled ? 'enabled' : 'disabled'}`);
    sendResponse({ enabled: settings.voiceEnabled });
    return true;
  }

  if (message.type === 'test_voice') {
    const testProfit = message.profit || 3.5;
    console.log(`[ARB] Testing voice announcement with ${testProfit}% profit`);
    soundAlerts.announceOpportunity(testProfit, 'draftkings', 'fanduel').then(() => {
      sendResponse({ success: true });
    });
    return true; // Keep channel open for async response
  }

  if (message.type === 'test_full_alert') {
    const testProfit = message.profit || 3.5;
    console.log(`[ARB] Testing full alert (sound + voice) with ${testProfit}% profit`);
    soundAlerts.playAndAnnounce(testProfit, 'draftkings', 'fanduel').then(() => {
      sendResponse({ success: true });
    });
    return true; // Keep channel open for async response
  }

  // Play goalie pull alert
  if (message.type === 'play_goalie_alert') {
    console.log('[ARB] 🏒 Playing goalie pull alert');
    const goaliePull = {
      game: message.game || 'Unknown game',
      score: message.score || '',
      time_remaining: message.time || '5:00'
    };
    playGoaliePullAlert(goaliePull).then(() => {
      sendResponse({ success: true });
    });
    return true;
  }
});

// Fetch opportunities from REST API
async function fetchOpportunities() {
  try {
    console.log('[ARB] Fetching opportunities from REST API...');
    const response = await fetch(`${BACKEND_URL}/api/alerts/all`);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    console.log('[ARB] REST API response:', data);

    // Extract arbitrage alerts
    let opportunities = [];
    if (data.arbitrage && data.arbitrage.alerts && Array.isArray(data.arbitrage.alerts)) {
      opportunities = data.arbitrage.alerts;
    }

    // Extract steam moves
    let steamMoves = [];
    if (data.steam_moves && data.steam_moves.alerts && Array.isArray(data.steam_moves.alerts)) {
      steamMoves = data.steam_moves.alerts;
    }

    // Extract line movements
    let lineMovements = [];
    if (data.line_movements && data.line_movements.alerts && Array.isArray(data.line_movements.alerts)) {
      lineMovements = data.line_movements.alerts;
    }

    // Fetch goalie pull opportunities separately
    let goaliePulls = [];
    try {
      const goalieResponse = await fetch(`${BACKEND_URL}/api/goalie-pull-opportunities`);
      if (goalieResponse.ok) {
        const goalieData = await goalieResponse.json();
        goaliePulls = goalieData.opportunities || [];
      }
    } catch (error) {
      console.error('[ARB] Error fetching goalie pull opportunities:', error);
    }

    console.log(`[ARB] Received: ${opportunities.length} arbitrage, ${steamMoves.length} steam moves, ${lineMovements.length} line movements, ${goaliePulls.length} goalie pulls`);

    // Update opportunities and UI
    handleOpportunitiesUpdate(opportunities);
    handleSteamMovesUpdate(steamMoves);
    handleLineMovementsUpdate(lineMovements);
    handleGoaliePullsUpdate(goaliePulls);

    // Update badge to show connected status
    chrome.action.setBadgeBackgroundColor({ color: '#93c5fd' }); // Blue 300

  } catch (error) {
    console.error('[ARB] Error fetching opportunities:', error);
    chrome.action.setBadgeText({ text: 'ERR' });
    chrome.action.setBadgeBackgroundColor({ color: '#EF4444' }); // Red
  }
}

// Start REST API polling
function startPolling() {
  console.log(`[ARB] Starting REST API polling (interval: ${POLL_INTERVAL}ms)`);

  // Initial fetch
  fetchOpportunities();

  // Clear any existing interval
  if (pollIntervalId) {
    clearInterval(pollIntervalId);
  }

  // Set up polling interval
  pollIntervalId = setInterval(fetchOpportunities, POLL_INTERVAL);
}

// Stop polling
function stopPolling() {
  console.log('[ARB] Stopping REST API polling');
  if (pollIntervalId) {
    clearInterval(pollIntervalId);
    pollIntervalId = null;
  }
}

// Initialize on extension load
console.log('[ARB] ARB Auto Bettor™ background service worker starting...');

if (USE_WEBSOCKET) {
  connectWebSocket();
  // Reconnect WebSocket if connection drops
  setInterval(() => {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      console.log('[ARB] WebSocket not connected, attempting reconnect...');
      connectWebSocket();
    }
  }, 30000);
} else {
  // Use REST API polling
  console.log('[ARB] Starting REST API polling (WebSocket disabled)...');
  startPolling();
}
