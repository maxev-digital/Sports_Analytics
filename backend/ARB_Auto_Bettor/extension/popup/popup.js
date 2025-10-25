let opportunities = [];
let steamMoves = [];
let lineMovements = [];
let goaliePulls = [];

// Sport emoji helper - using Microsoft Fluent Emoji CDN
function getSportEmoji(sport) {
  const sportEmojis = {
    'NBA': 'https://em-content.zobj.net/source/microsoft-teams/363/basketball_1f3c0.png',
    'NFL': 'https://em-content.zobj.net/source/microsoft-teams/363/american-football_1f3c8.png',
    'NHL': 'https://em-content.zobj.net/source/microsoft-teams/363/black-circle_26ab.png', // Puck
    'MLB': 'https://em-content.zobj.net/source/microsoft-teams/363/baseball_26be-fe0f.png',
    'NCAAF': 'https://em-content.zobj.net/source/microsoft-teams/363/american-football_1f3c8.png',
    'SOCCER': 'https://em-content.zobj.net/source/microsoft-teams/363/soccer-ball_26bd.png'
  };
  return sportEmojis[sport] || sportEmojis['NBA'];
}

// Get sport from game data
function detectSport(opportunity) {
  const sport_key = opportunity.sport_key || opportunity.sport || '';
  if (sport_key.includes('basketball_nba')) return 'NBA';
  if (sport_key.includes('americanfootball_nfl')) return 'NFL';
  if (sport_key.includes('americanfootball_ncaaf')) return 'NCAAF';
  if (sport_key.includes('icehockey_nhl')) return 'NHL';
  if (sport_key.includes('baseball_mlb')) return 'MLB';
  if (sport_key.includes('soccer')) return 'SOCCER';
  return 'NBA'; // default
}

// Format timestamp to "X mins ago" or "X hours ago"
function formatTimeAgo(timestamp) {
  if (!timestamp) return 'Just now';

  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins === 1) return '1 min ago';
  if (diffMins < 60) return `${diffMins} mins ago`;
  if (diffHours === 1) return '1 hour ago';
  if (diffHours < 24) return `${diffHours} hours ago`;
  if (diffDays === 1) return '1 day ago';
  return `${diffDays} days ago`;
}

// Format game date/time
function formatGameTime(commence_time) {
  if (!commence_time) return '';

  const date = new Date(commence_time);
  const now = new Date();
  const isToday = date.toDateString() === now.toDateString();
  const isTomorrow = date.toDateString() === new Date(now.getTime() + 86400000).toDateString();

  const timeStr = date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  });

  if (isToday) return `Today ${timeStr}`;
  if (isTomorrow) return `Tomorrow ${timeStr}`;

  const dateStr = date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric'
  });
  return `${dateStr} ${timeStr}`;
}

// Bookmaker data helper
function getBookmaker(key) {
  const nameMap = {
    'draftkings': 'DraftKings',
    'fanduel': 'FanDuel',
    'betmgm': 'BetMGM',
    'betrivers': 'BetRivers',
    'williamhill_us': 'William Hill',
    'fanatics': 'Fanatics',
    'espnbet': 'ESPN BET',
    'caesars': 'Caesars',
    'pointsbet': 'PointsBet',
    'ballybet': 'Bally Bet',
    'betonlineag': 'BetOnline',
    'bovada': 'Bovada',
    'mybookieag': 'MyBookie',
    'lowvig': 'LowVig',
    'betway': 'Betway',
    'betus': 'BetUS'
  };

  return {
    name: nameMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    logo: `https://www.google.com/s2/favicons?domain=${key.replace('_us', '').replace('ag', '.ag').replace('mybookie', 'mybookie.ag')}.com&sz=64`
  };
}

// Load opportunities on popup open
document.addEventListener('DOMContentLoaded', () => {
  loadOpportunities();
  checkConnectionStatus();
  loadSoundSettings();

  // Event listeners
  document.getElementById('refreshBtn').addEventListener('click', loadOpportunities);
  document.getElementById('settingsBtn').addEventListener('click', () => {
    // Open settings page in new tab
    chrome.tabs.create({ url: chrome.runtime.getURL('settings/settings.html') });
  });

  // Sound control listeners
  document.getElementById('soundToggleBtn').addEventListener('click', toggleSound);
  document.getElementById('testSoundBtn').addEventListener('click', testSound);

  // Voice control listeners
  document.getElementById('voiceToggleBtn').addEventListener('click', toggleVoice);
  document.getElementById('testVoiceBtn').addEventListener('click', testVoice);

  // Tab switching
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });

  // Stat card clicking switches to that tab
  document.getElementById('statArbitrage').addEventListener('click', () => switchTab('arbitrage'));
  document.getElementById('statSteam').addEventListener('click', () => switchTab('steam'));
  document.getElementById('statLines').addEventListener('click', () => switchTab('lines'));
});

async function loadOpportunities() {
  console.log('[POPUP] Loading opportunities...');
  try {
    // Get opportunities from background script
    chrome.runtime.sendMessage({ type: 'get_opportunities' }, (response) => {
      if (chrome.runtime.lastError) {
        console.error('[POPUP] Error getting opportunities:', chrome.runtime.lastError);
        return;
      }

      console.log('[POPUP] Received response:', response);

      if (response) {
        opportunities = response.opportunities || [];
        steamMoves = response.steamMoves || [];
        lineMovements = response.lineMovements || [];
        goaliePulls = response.goaliePulls || [];

        console.log('[POPUP] Opportunities count:', opportunities.length);
        console.log('[POPUP] Steam moves count:', steamMoves.length);
        console.log('[POPUP] Line movements count:', lineMovements.length);
        console.log('[POPUP] Goalie pulls count:', goaliePulls.length);

        if (opportunities.length > 0) {
          console.log('[POPUP] First opportunity:', opportunities[0]);
        }

        renderOpportunities();
        renderSteamMoves();
        renderLineMovements();
        renderGoaliePulls();
        updateStats();
      } else {
        console.warn('[POPUP] No response from background script');
      }
    });
  } catch (error) {
    console.error('[POPUP] Error loading opportunities:', error);
  }
}

function renderOpportunities() {
  console.log('[POPUP] renderOpportunities() called with', opportunities.length, 'opportunities');
  const container = document.getElementById('opportunitiesList');

  if (!container) {
    console.error('[POPUP] opportunitiesList container not found!');
    return;
  }

  if (opportunities.length === 0) {
    console.log('[POPUP] No opportunities, showing empty state');
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">
          <img src="https://em-content.zobj.net/source/microsoft-teams/363/magnifying-glass-tilted-left_1f50d.png" alt="Search" style="width: 64px; height: 64px;">
        </div>
        <div>No arbitrage opportunities right now</div>
        <div style="font-size: 11px; margin-top: 8px;">Monitoring 11 sportsbooks...</div>
      </div>
    `;
    return;
  }

  console.log('[POPUP] Rendering', opportunities.length, 'opportunity cards');
  container.innerHTML = opportunities.map((op, index) => {
    const gameId = op.id || op.game_id || `op-${index}`;
    const game = op.game || `${op.away_team} @ ${op.home_team}` || 'Unknown Game';
    const profit = op.profit_percentage || op.profitPercentage || 0;
    const stake = op.total_stake || op.totalStake || 0;
    const guaranteedProfit = op.guaranteed_profit || op.guaranteedProfit || 0;
    const market = op.market_type || op.marketType || 'Unknown Market';

    // Extract bet details
    const side1 = op.side1 || op.side_a || op.bet1_side || '';
    const side2 = op.side2 || op.side_b || op.bet2_side || '';
    const odds1 = op.odds1 || op.odds_a || '';
    const odds2 = op.odds2 || op.odds_b || '';
    const point1 = op.point1 || op.point_a || op.bet1_point || '';
    const point2 = op.point2 || op.point_b || op.bet2_point || '';

    // Debug logging
    if (index === 0) {
      console.log('[POPUP] First opportunity data:', {
        side1, side2, point1, point2, odds1, odds2,
        raw_op: op
      });
    }

    // Format bet descriptions (e.g., "Over 5.5" or "Warriors -3.5")
    const bet1Description = point1 ? `${side1} ${point1}` : side1;
    const bet2Description = point2 ? `${side2} ${point2}` : side2;

    // Timestamps
    const alertTime = formatTimeAgo(op.timestamp);
    const gameTime = formatGameTime(op.commence_time);

    // Get sport and emoji
    const sport = detectSport(op);
    const sportEmoji = getSportEmoji(sport);

    // Get bookmaker data with logos
    const book1Key = op.book1 || op.book_a || op.bookmaker1 || '';
    const book2Key = op.book2 || op.book_b || op.bookmaker2 || '';
    const book1Data = getBookmaker(book1Key);
    const book2Data = getBookmaker(book2Key);

    return `
      <div class="opportunity-card" data-id="${gameId}" data-sport="${sport}">
        <div class="opportunity-header">
          <div class="opportunity-title">
            <img src="${sportEmoji}" alt="${sport}" style="width: 20px; height: 20px; margin-right: 6px; vertical-align: middle;">
            ${game}
          </div>
          <div class="opportunity-profit">+${profit.toFixed(2)}%</div>
        </div>
        <div class="opportunity-details">
          <strong>${market}</strong> | $${stake.toFixed(0)} stake → $${Math.abs(guaranteedProfit).toFixed(0)} profit
        </div>
        <div class="opportunity-books">
          <div class="book-badge book-left">
            <img src="${book1Data.logo}" alt="${book1Data.name}" class="book-logo" onerror="this.style.display='none'">
            <div class="book-info">
              <span class="book-name">${book1Data.name}</span>
              <span class="bet-details">${bet1Description} ${odds1 ? `(${odds1})` : ''}</span>
            </div>
          </div>
          <div class="book-badge book-right">
            <img src="${book2Data.logo}" alt="${book2Data.name}" class="book-logo" onerror="this.style.display='none'">
            <div class="book-info">
              <span class="book-name">${book2Data.name}</span>
              <span class="bet-details">${bet2Description} ${odds2 ? `(${odds2})` : ''}</span>
            </div>
          </div>
        </div>
        <div class="alert-timestamps">
          <span class="timestamp-alert">⏰ Alert: ${alertTime}</span>
          ${gameTime ? `<span class="timestamp-game">🎮 Game: ${gameTime}</span>` : ''}
        </div>
      </div>
    `;
  }).join('');

  // Add click handlers
  container.querySelectorAll('.opportunity-card').forEach(card => {
    card.addEventListener('click', () => {
      const id = card.dataset.id;
      const opportunity = opportunities.find((op, index) =>
        (op.id || op.game_id || `op-${index}`) === id
      );
      if (opportunity) {
        openOpportunity(opportunity);
      }
    });
  });
}

function updateStats() {
  document.getElementById('opportunityCount').textContent = opportunities.length;
  document.getElementById('steamCount').textContent = steamMoves.length;
  document.getElementById('lineCount').textContent = lineMovements.length;
  document.getElementById('goalieCount').textContent = goaliePulls.length;
}

function switchTab(tabName) {
  // Update tab buttons
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabName);
  });

  // Update tab content
  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.remove('active');
  });
  document.getElementById(`${tabName}-tab`).classList.add('active');
}

function renderSteamMoves() {
  const container = document.getElementById('steamMovesList');

  if (steamMoves.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">
          <img src="https://em-content.zobj.net/source/microsoft-teams/363/fire_1f525.png" alt="Fire" style="width: 64px; height: 64px;">
        </div>
        <div>No steam moves detected</div>
        <div style="font-size: 11px; margin-top: 8px;">Monitoring for line movements...</div>
      </div>
    `;
    return;
  }

  container.innerHTML = steamMoves.map((sm, index) => {
    const game = sm.game || `${sm.away_team} @ ${sm.home_team}`;
    const direction = sm.movement_direction || (sm.movement > 0 ? 'up' : 'down');
    const marketType = sm.market_type === 'totals' ? 'Total' : 'Spread';
    const booksMovedText = sm.books_moved ? sm.books_moved.slice(0, 2).join(', ') : 'Multiple books';
    const booksCount = sm.books_moved ? sm.books_moved.length : 0;

    // Timestamps
    const alertTime = formatTimeAgo(sm.timestamp);
    const gameTime = formatGameTime(sm.commence_time);

    // Get sport and emoji
    const sport = detectSport(sm);
    const sportEmoji = getSportEmoji(sport);

    // Get bookmaker info for stale book
    const staleBookData = sm.best_stale_book ? getBookmaker(sm.best_stale_book) : null;
    const staleLine = sm.best_stale_line ? sm.best_stale_line.toFixed(1) : '?';
    const staleOdds = sm.best_stale_odds || '?';

    return `
      <div class="steam-card" data-index="${index}">
        <div class="steam-header">
          <div class="steam-title">
            <img src="${sportEmoji}" alt="${sport}" style="width: 18px; height: 18px; margin-right: 6px; vertical-align: middle;">
            ${game}
          </div>
          <div class="steam-direction ${direction}">↑ ${direction.toUpperCase()}</div>
        </div>
        <div class="steam-details">
          ${marketType} • ${booksCount} books moved<br>
          ${booksMovedText}
        </div>
        ${sm.best_stale_book && sm.best_stale_book !== "All books moved" ? `
          <div class="steam-stale">
            <div class="steam-stale-title">
              <img src="https://em-content.zobj.net/source/microsoft-teams/363/high-voltage_26a1.png" alt="Lightning" style="width: 14px; height: 14px; margin-right: 4px; vertical-align: middle;">
              Best Stale Price
            </div>
            <div class="steam-stale-info">
              ${staleBookData.name}: ${staleLine} @ ${staleOdds}
            </div>
          </div>
        ` : `
          <div class="steam-details" style="color: #ef4444;">All books have moved!</div>
        `}
        <div class="alert-timestamps">
          <span class="timestamp-alert">⏰ Alert: ${alertTime}</span>
          ${gameTime ? `<span class="timestamp-game">🎮 Game: ${gameTime}</span>` : ''}
        </div>
      </div>
    `;
  }).join('');

  // Add click handlers
  container.querySelectorAll('.steam-card').forEach(card => {
    card.addEventListener('click', () => {
      const index = parseInt(card.dataset.index);
      const steamMove = steamMoves[index];
      if (steamMove) {
        openSteamMove(steamMove);
      }
    });
  });
}

function renderLineMovements() {
  const container = document.getElementById('lineMovementsList');

  if (lineMovements.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">
          <img src="https://em-content.zobj.net/source/microsoft-teams/363/chart-increasing_1f4c8.png" alt="Chart" style="width: 64px; height: 64px;">
        </div>
        <div>No significant line movements</div>
        <div style="font-size: 11px; margin-top: 8px;">Tracking 1.0+ point moves...</div>
      </div>
    `;
    return;
  }

  container.innerHTML = lineMovements.map((lm, index) => {
    const game = lm.game || `${lm.away_team} @ ${lm.home_team}`;
    const bookData = getBookmaker(lm.bookmaker);
    const movement = (lm.movement || 0).toFixed(1);
    const direction = lm.movement > 0 ? 'up' : 'down';

    // Timestamps
    const alertTime = formatTimeAgo(lm.timestamp);
    const gameTime = formatGameTime(lm.commence_time);

    return `
      <div class="opportunity-card">
        <div class="opportunity-header">
          <div class="opportunity-title">${game}</div>
          <div class="opportunity-profit">${movement} pts</div>
        </div>
        <div class="opportunity-details">
          ${bookData.name} • ${lm.market_type}<br>
          ${lm.original_line} → ${lm.new_line} (${direction})
        </div>
        <div class="alert-timestamps">
          <span class="timestamp-alert">⏰ Alert: ${alertTime}</span>
          ${gameTime ? `<span class="timestamp-game">🎮 Game: ${gameTime}</span>` : ''}
        </div>
      </div>
    `;
  }).join('');
}

function renderGoaliePulls() {
  const container = document.getElementById('goaliePullList');

  if (goaliePulls.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">
          <img src="https://em-content.zobj.net/source/microsoft-teams/363/ice-hockey_1f3d2.png" alt="Hockey" style="width: 64px; height: 64px;">
        </div>
        <div>No goalie pull opportunities</div>
        <div style="font-size: 11px; margin-top: 8px;">Monitoring NHL games...</div>
      </div>
    `;
    return;
  }

  container.innerHTML = goaliePulls.map((gp, index) => {
    const game = gp.game || 'Unknown game';
    const score = gp.score || '';
    const time = gp.time_remaining || '';
    const trailing = gp.trailing_team || '';

    // Timestamps
    const alertTime = formatTimeAgo(gp.timestamp);

    // Build Bovada URL for NHL
    const bovadaUrl = 'https://www.bovada.lv/sports/hockey/nhl';

    return `
      <div class="goalie-card" data-index="${index}">
        <div class="goalie-header">
          <div class="goalie-title">🏒 ${game}</div>
          <div class="goalie-alert-badge">2-GOAL GAME</div>
        </div>
        <div class="goalie-details">
          <strong>Score:</strong> ${score}<br>
          <strong>Time:</strong> ${time} remaining (3rd period)<br>
          <strong>Trailing:</strong> ${trailing}
        </div>
        <div class="goalie-action">
          <a href="${bovadaUrl}" target="_blank" class="goalie-bet-btn" data-index="${index}">
            🎯 Open Bovada NHL
          </a>
        </div>
        <div class="alert-timestamps">
          <span class="timestamp-alert">⏰ Alert: ${alertTime}</span>
          <span class="timestamp-game">🏒 Live Game</span>
        </div>
      </div>
    `;
  }).join('');

  // Add click handlers for Bovada buttons
  document.querySelectorAll('.goalie-bet-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const index = parseInt(btn.dataset.index);
      const goaliePull = goaliePulls[index];
      if (goaliePull) {
        openGoaliePull(goaliePull);
      }
    });
  });
}

function openGoaliePull(goaliePull) {
  // Open Bovada NHL page
  const bovadaUrl = 'https://www.bovada.lv/sports/hockey/nhl';
  console.log('[POPUP] Opening Bovada NHL for goalie pull:', goaliePull.game);
  chrome.tabs.create({ url: bovadaUrl, active: true });
  window.close(); // Close popup after opening
}

function openSteamMove(steamMove) {
  if (!steamMove.best_stale_book || steamMove.best_stale_book === "All books moved") {
    console.log('No stale book available');
    return;
  }

  // Get bookmaker URL
  const bookData = getBookmaker(steamMove.best_stale_book);

  if (bookData.url && bookData.url !== '#') {
    console.log('[POPUP] Opening stale book:', bookData.name, 'at', bookData.url);
    chrome.tabs.create({ url: bookData.url, active: true });
    window.close(); // Close popup after opening
  } else {
    console.log('[POPUP] No URL found for book:', steamMove.best_stale_book);
  }
}

function checkConnectionStatus() {
  // Check if background script is connected
  chrome.runtime.sendMessage({ type: 'get_status' }, (response) => {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');

    if (chrome.runtime.lastError) {
      statusDot.classList.add('error');
      statusText.textContent = 'Error';
      return;
    }

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
  }, (response) => {
    if (chrome.runtime.lastError) {
      console.error('Error opening opportunity:', chrome.runtime.lastError);
      return;
    }
    console.log('Opportunity opened successfully');
    // Close popup after opening
    window.close();
  });
}

// Listen for updates from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'opportunities_updated') {
    loadOpportunities();
  }
});

// Refresh opportunities every 10 seconds while popup is open
setInterval(loadOpportunities, 10000);

// Sound control functions
function loadSoundSettings() {
  chrome.runtime.sendMessage({ type: 'get_settings' }, (response) => {
    if (chrome.runtime.lastError) {
      console.error('Error getting settings:', chrome.runtime.lastError);
      return;
    }

    if (response && response.settings) {
      updateSoundButton(response.settings.soundEnabled);
      updateVoiceButton(response.settings.voiceEnabled);
    }
  });
}

function toggleSound() {
  chrome.runtime.sendMessage({ type: 'toggle_sound' }, (response) => {
    if (chrome.runtime.lastError) {
      console.error('Error toggling sound:', chrome.runtime.lastError);
      return;
    }

    if (response) {
      updateSoundButton(response.enabled);
      console.log(`Sound ${response.enabled ? 'enabled' : 'disabled'}`);
    }
  });
}

function updateSoundButton(enabled) {
  const btn = document.getElementById('soundToggleBtn');
  if (enabled) {
    btn.textContent = '🔊 Sound ON';
    btn.classList.remove('btn-primary');
    btn.classList.add('btn-secondary');
  } else {
    btn.textContent = '🔇 Sound OFF';
    btn.classList.remove('btn-secondary');
    btn.classList.add('btn-primary');
  }
}

function testSound() {
  // Test medium priority sound
  chrome.runtime.sendMessage({ type: 'test_sound', priority: 'medium' }, (response) => {
    if (chrome.runtime.lastError) {
      console.error('Error testing sound:', chrome.runtime.lastError);
      return;
    }
    console.log('Test sound played');
  });
}

// Voice control functions
function toggleVoice() {
  chrome.runtime.sendMessage({ type: 'toggle_voice' }, (response) => {
    if (chrome.runtime.lastError) {
      console.error('Error toggling voice:', chrome.runtime.lastError);
      return;
    }

    if (response) {
      updateVoiceButton(response.enabled);
      console.log(`Voice ${response.enabled ? 'enabled' : 'disabled'}`);
    }
  });
}

function updateVoiceButton(enabled) {
  const btn = document.getElementById('voiceToggleBtn');
  if (enabled) {
    btn.textContent = '🗣️ Voice ON';
    btn.classList.remove('btn-primary');
    btn.classList.add('btn-secondary');
  } else {
    btn.textContent = '🔇 Voice OFF';
    btn.classList.remove('btn-secondary');
    btn.classList.add('btn-primary');
  }
}

function testVoice() {
  // Test full alert with voice announcement
  chrome.runtime.sendMessage({ type: 'test_full_alert', profit: 3.5 }, (response) => {
    if (chrome.runtime.lastError) {
      console.error('Error testing voice:', chrome.runtime.lastError);
      return;
    }
    console.log('Test voice announcement played');
  });
}
