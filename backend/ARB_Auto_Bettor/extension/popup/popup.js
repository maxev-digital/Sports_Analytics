let opportunities = [];
let steamMoves = [];
let middles = [];
let goaliePulls = [];
let quarterReversals = [];
let injuryProps = [];
let injuryAlerts = [];

// Sport emoji helper - using Microsoft Fluent Emoji CDN
function getSportEmoji(sport) {
  const sportEmojis = {
    'NBA': 'https://em-content.zobj.net/source/microsoft-teams/363/basketball_1f3c0.png',
    'NFL': 'https://em-content.zobj.net/source/microsoft-teams/363/american-football_1f3c8.png',
    'NHL': 'https://em-content.zobj.net/source/microsoft-teams/363/ice-hockey_1f3d2.png', // Ice hockey stick and puck
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
  const bookmakerMap = {
    'draftkings': { name: 'DraftKings', domain: 'draftkings.com' },
    'fanduel': { name: 'FanDuel', domain: 'fanduel.com' },
    'betmgm': { name: 'BetMGM', domain: 'betmgm.com' },
    'betrivers': { name: 'BetRivers', domain: 'betrivers.com' },
    'williamhill_us': { name: 'William Hill', domain: 'williamhill.com' },
    'fanatics': { name: 'Fanatics', domain: 'fanatics.com' },
    'espnbet': { name: 'ESPN BET', domain: 'espnbet.com' },
    'caesars': { name: 'Caesars', domain: 'caesars.com' },
    'pointsbet': { name: 'PointsBet', domain: 'pointsbet.com' },
    'ballybet': { name: 'Bally Bet', domain: 'ballybet.com' },
    'betonlineag': { name: 'BetOnline', domain: 'betonline.ag' },
    'bovada': { name: 'Bovada', domain: 'bovada.lv' },
    'mybookieag': { name: 'MyBookie', domain: 'mybookie.ag' },
    'lowvig': { name: 'LowVig', domain: 'lowvig.ag' },
    'betway': { name: 'Betway', domain: 'betway.com' },
    'betus': { name: 'BetUS', domain: 'betus.com.pa' },
    'superbook': { name: 'SuperBook', domain: 'superbook.com' },
    'wynnbet': { name: 'WynnBet', domain: 'wynnbet.com' },
    'unibet_us': { name: 'Unibet', domain: 'unibet.com' },
    'twinspires': { name: 'TwinSpires', domain: 'twinspires.com' },
    'sugarhouse': { name: 'SugarHouse', domain: 'sugarhousecasino.com' },
    'betfred': { name: 'Betfred', domain: 'betfred.com' },
    'hardrockbet': { name: 'Hard Rock', domain: 'hardrock.com' },
    'sisportsbook': { name: 'SI Sportsbook', domain: 'sisportsbook.com' },
    'barstool': { name: 'Barstool', domain: 'barstoolsportsbook.com' }
  };

  const bookmaker = bookmakerMap[key];
  if (bookmaker) {
    return {
      name: bookmaker.name,
      logo: `https://www.google.com/s2/favicons?domain=${bookmaker.domain}&sz=64`
    };
  }

  // Fallback for unknown bookmakers
  return {
    name: key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    logo: `https://www.google.com/s2/favicons?domain=${key}.com&sz=64`
  };
}

// Load opportunities on popup open
document.addEventListener('DOMContentLoaded', () => {
  loadOpportunities();
  checkConnectionStatus();
  loadSoundSettings();

  // Event listeners
  document.getElementById('refreshBtn').addEventListener('click', () => loadOpportunities(true));
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
  document.getElementById('statMiddles').addEventListener('click', () => switchTab('middles'));
  document.getElementById('statGoalie').addEventListener('click', () => switchTab('goalie'));
  document.getElementById('statQuarterReversal').addEventListener('click', () => switchTab('quarterreversal'));
});

async function loadOpportunities(forceRefresh = false) {
  console.log('[POPUP] Loading opportunities...', forceRefresh ? '(force refresh)' : '(cached)');
  try {
    // Get opportunities from background script
    const messageType = forceRefresh ? 'refresh' : 'get_opportunities';
    chrome.runtime.sendMessage({ type: messageType }, (response) => {
      if (chrome.runtime.lastError) {
        console.error('[POPUP] Error getting opportunities:', chrome.runtime.lastError);
        return;
      }

      console.log('[POPUP] Received response:', response);

      if (response) {
        opportunities = response.opportunities || [];
        steamMoves = response.steamMoves || [];
        middles = response.middles || [];
        goaliePulls = response.goaliePulls || [];
        quarterReversals = response.quarterReversals || [];
        injuryProps = response.injuryProps || [];
        injuryAlerts = response.injuryAlerts || [];

        console.log('[POPUP] Opportunities count:', opportunities.length);
        console.log('[POPUP] Steam moves count:', steamMoves.length);
        console.log('[POPUP] Middles count:', middles.length);
        console.log('[POPUP] Goalie pulls count:', goaliePulls.length);
        console.log('[POPUP] Quarter reversals count:', quarterReversals.length);
        console.log('[POPUP] Injury props count:', injuryProps.length);
        console.log('[POPUP] Injury alerts count:', injuryAlerts.length);

        if (opportunities.length > 0) {
          console.log('[POPUP] First opportunity:', opportunities[0]);
        }

        renderAlertFeed(); // Render unified alert feed
        updateStats();
      } else {
        console.warn('[POPUP] No response from background script');
      }
    });
  } catch (error) {
    console.error('[POPUP] Error loading opportunities:', error);
  }
}

// UNIFIED ALERT FEED (Priority-Based, Filterable, Scales to 50+ strategies)
function renderAlertFeed(filter = 'all') {
  console.log('[POPUP] renderAlertFeed() called with filter:', filter);
  const container = document.getElementById('alertFeed');
  console.log('[POPUP] alertFeed container:', container);

  // Combine all alerts into unified array with metadata
  const allAlerts = [
    ...injuryAlerts.map(alert => ({ type: 'injury-alert', data: alert, strategy: 'Injury Alert', category: 'live', urgency: (alert.confidence || 0) * 100, tab: 'injuryalerts' })),
    ...injuryProps.map(alert => ({ type: 'injury-props', data: alert, strategy: 'Injury Props', category: 'live', urgency: 100 - (alert.time_since_tweet || 60), tab: 'injuryprops' })),
    ...goaliePulls.map(alert => ({ type: 'goalie-pull', data: alert, strategy: 'Goalie Pull', category: 'live', urgency: alert.urgency || 50, tab: 'goalie' })),
    ...quarterReversals.map(alert => ({ type: 'quarter-reversal', data: alert, strategy: 'Q Reversal', category: 'live', urgency: alert.alert_level === 'CRITICAL' ? 90 : alert.alert_level === 'HIGH' ? 70 : 50, tab: 'quarterreversal' })),
    ...opportunities.map(alert => ({ type: 'arbitrage', data: alert, strategy: 'Arbitrage', category: 'arbitrage', urgency: alert.profit_percentage || 0, tab: 'arbitrage' })),
    ...steamMoves.map(alert => ({ type: 'steam', data: alert, strategy: 'Steam Move', category: 'movement', urgency: 60, tab: 'steam' })),
    ...middles.map(alert => ({ type: 'middle', data: alert, strategy: 'Middle', category: 'arbitrage', urgency: alert.profit_percentage || 0, tab: 'middles' }))
  ];

  console.log('[POPUP] Total alerts before filter:', allAlerts.length);

  // Filter by tab
  const filteredAlerts = filter === 'all' ? allAlerts : allAlerts.filter(alert => alert.tab === filter);
  console.log('[POPUP] Filtered alerts:', filteredAlerts.length, 'for filter:', filter);

  // Sort by urgency (highest first)
  filteredAlerts.sort((a, b) => b.urgency - a.urgency);

  // Empty state
  if (filteredAlerts.length === 0) {
    const filterName = filter === 'all' ? 'alerts' : filter.replace(/([a-z])([A-Z])/g, '$1 $2').toLowerCase();
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">
          <img src="https://em-content.zobj.net/source/microsoft-teams/363/magnifying-glass-tilted-left_1f50d.png" alt="Search" style="width: 64px; height: 64px;">
        </div>
        <div>No ${filterName} found</div>
        <div style="font-size: 11px; margin-top: 8px;">
          Monitoring for new opportunities...
        </div>
      </div>
    `;
    return;
  }

  // Render alerts with strategy badges
  container.innerHTML = filteredAlerts.map((alert, index) => {
    const badgeClass = alert.category;
    const badge = `<div class="strategy-badge ${badgeClass}">${alert.strategy}</div>`;

    // Render alert card based on type
    let alertCard = '';

    if (alert.type === 'injury-alert') {
      const ia = alert.data;
      const alertTime = formatTimeAgo(ia.published);
      const confidencePercent = Math.round((ia.confidence || 0) * 100);
      const urgencyClass = confidencePercent >= 95 ? 'qr-card-critical' : confidencePercent >= 85 ? 'qr-card-high' : 'qr-card-medium';
      const urgencyBadge = confidencePercent >= 95 ? '🚨 HIGH CONFIDENCE' : confidencePercent >= 85 ? '⚠️ CONFIRMED' : '📰 REPORTED';
      const reporter = (ia.source || '').replace('nitter:', '@');
      const players = (ia.entities_guess || []).join(', ') || 'N/A';
      const isTestMode = ia.test_mode === true;

      alertCard = `
        <div class="${urgencyClass}" style="border: 3px solid ${confidencePercent >= 95 ? '#ef4444' : confidencePercent >= 85 ? '#f97316' : '#3b82f6'};">
          <div class="qr-header">
            <div class="qr-title">🚨 ${ia.title}</div>
            <div class="qr-alert-badge" style="background: ${confidencePercent >= 95 ? '#dc2626' : confidencePercent >= 85 ? '#ea580c' : '#2563eb'};">${urgencyBadge}</div>
          </div>
          ${isTestMode ? '<div style="background: rgba(234, 179, 8, 0.2); border: 2px solid #eab308; border-radius: 8px; padding: 8px; margin-bottom: 12px; text-align: center; font-size: 11px; color: #fde047;">🧪 TEST MODE (Mock Alert)</div>' : ''}
          <div class="qr-details">
            <div class="qr-detail-row">
              <span><strong>Reporter:</strong> ${reporter}</span>
              <span><strong>Confidence:</strong> ${confidencePercent}%</span>
            </div>
            <div class="qr-detail-row">
              <span><strong>Players:</strong> ${players}</span>
              <span><strong>Time:</strong> ${alertTime}</span>
            </div>
          </div>
          <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.1); font-size: 11px; color: rgba(255,255,255,0.6);">
            <a href="${ia.link}" target="_blank" style="color: #60a5fa; text-decoration: none;">View Source →</a>
          </div>
        </div>
      `;
    } else if (alert.type === 'injury-props') {
      const ip = alert.data;
      const timeRemaining = Math.max(0, Math.floor(60 - ip.time_since_tweet));
      const alertTime = formatTimeAgo(ip.timestamp);
      const urgencyClass = timeRemaining <= 15 ? 'qr-card-critical' : timeRemaining <= 30 ? 'qr-card-high' : 'qr-card-medium';
      const urgencyBadge = timeRemaining <= 15 ? '🚨 CRITICAL' : timeRemaining <= 30 ? '🔥 URGENT' : '⚡ LIVE';
      const sportEmoji = ip.sport === 'NBA' ? '🏀' : ip.sport === 'NFL' ? '🏈' : ip.sport === 'NHL' ? '🏒' : '🎯';
      const formattedOdds = ip.best_odds > 0 ? `+${ip.best_odds}` : `${ip.best_odds}`;

      alertCard = `
        <div class="${urgencyClass}" style="border: 3px solid ${timeRemaining <= 15 ? '#ef4444' : timeRemaining <= 30 ? '#f97316' : '#eab308'};">
          <div class="qr-header">
            <div class="qr-title">${sportEmoji} ${ip.player_name} - ${ip.team}</div>
            <div class="qr-alert-badge" style="background: ${timeRemaining <= 15 ? '#dc2626' : timeRemaining <= 30 ? '#ea580c' : '#ca8a04'};">${urgencyBadge}</div>
          </div>
          <div style="background: rgba(239, 68, 68, 0.2); border: 2px solid #ef4444; border-radius: 8px; padding: 12px; margin-bottom: 12px; text-align: center;">
            <div style="font-size: 32px; font-weight: bold; color: #fca5a5;">⏱️ ${timeRemaining}s</div>
            <div style="font-size: 11px; color: #fecaca; margin-top: 4px;">REMAINING</div>
          </div>
          <div class="qr-trigger"><strong>Status:</strong> ${ip.injury_status}</div>
          <div class="qr-details">
            <div class="qr-detail-row">
              <span><strong>Prop:</strong> ${ip.prop_type.toUpperCase()}</span>
              <span><strong>Line:</strong> ${ip.prop_side.toUpperCase()} ${ip.prop_line}</span>
            </div>
          </div>
          <div class="qr-stats">
            <div class="qr-stat">
              <div class="qr-stat-label">Expected Value</div>
              <div class="qr-stat-value critical-text">+${ip.expected_value.toFixed(1)}%</div>
            </div>
            <div class="qr-stat">
              <div class="qr-stat-label">Confidence</div>
              <div class="qr-stat-value">${ip.confidence}%</div>
            </div>
          </div>
        </div>
      `;
    } else if (alert.type === 'arbitrage' || alert.type === 'steam' || alert.type === 'middle') {
      // Render arbitrage, steam moves, and middles with bookmaker cards
      const op = alert.data;
      const game = op.game || `${op.away_team} @ ${op.home_team}` || 'Unknown Game';
      const profit = op.profit_percentage || op.profitPercentage || 0;
      const stake = op.total_stake || op.totalStake || 0;
      const guaranteedProfit = op.guaranteed_profit || op.guaranteedProfit || 0;
      const market = op.market_type || op.marketType || 'Unknown Market';
      // Middles use different field names than arbitrage
      const side1 = op.side1 || op.side_a || op.side_low || op.bet1_side || '';
      const side2 = op.side2 || op.side_b || op.side_high || op.bet2_side || '';
      const odds1 = op.odds1 || op.odds_a || op.odds_low || '';
      const odds2 = op.odds2 || op.odds_b || op.odds_high || '';
      const point1 = op.point1 || op.point_a || op.low_line || op.bet1_point || '';
      const point2 = op.point2 || op.point_b || op.high_line || op.bet2_point || '';
      const bet1Description = point1 ? `${side1} ${point1}` : side1;
      const bet2Description = point2 ? `${side2} ${point2}` : side2;
      const alertTime = formatTimeAgo(op.timestamp);
      const gameTime = formatGameTime(op.commence_time);
      const sport = detectSport(op);
      const sportEmoji = getSportEmoji(sport);
      // Middles use book_low/book_high, arbitrage uses book_a/book_b
      const book1Key = op.book1 || op.book_a || op.book_low || op.bookmaker1 || '';
      const book2Key = op.book2 || op.book_b || op.book_high || op.bookmaker2 || '';
      console.log('[POPUP] Book keys:', { book1Key, book2Key, opportunity: op });
      const book1Data = getBookmaker(book1Key);
      const book2Data = getBookmaker(book2Key);
      console.log('[POPUP] Book data:', { book1Data, book2Data });

      alertCard = `
        <div class="opportunity-card" data-sport="${sport}">
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
              <img src="${book1Data.logo}" alt="${book1Data.name}" class="book-logo">
              <div class="book-info">
                <span class="book-name">${book1Data.name}</span>
                <span class="bet-details">${bet1Description} ${odds1 ? `(${odds1})` : ''}</span>
              </div>
            </div>
            <div class="book-badge book-right">
              <img src="${book2Data.logo}" alt="${book2Data.name}" class="book-logo">
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
    } else if (alert.type === 'goalie-pull') {
      // Render goalie pull alerts
      const gp = alert.data;
      alertCard = `
        <div class="qr-card-high">
          <div class="qr-header">
            <div class="qr-title">🏒 ${gp.home_team} vs ${gp.away_team}</div>
            <div class="qr-alert-badge" style="background: #2563eb;">🥅 GOALIE PULL</div>
          </div>
          <div class="qr-trigger"><strong>Situation:</strong> ${gp.situation || 'Live game - goalie pull likely'}</div>
          <div class="qr-recommendation">Live betting opportunity detected</div>
        </div>
      `;
    } else if (alert.type === 'quarter-reversal') {
      // Render quarter reversal alerts
      const qr = alert.data;
      const urgencyClass = qr.alert_level === 'CRITICAL' ? 'qr-card-critical' : qr.alert_level === 'HIGH' ? 'qr-card-high' : 'qr-card-medium';
      const urgencyBadge = qr.alert_level === 'CRITICAL' ? '🚨 CRITICAL' : qr.alert_level === 'HIGH' ? '🔥 HIGH' : '⚡ MEDIUM';

      alertCard = `
        <div class="${urgencyClass}">
          <div class="qr-header">
            <div class="qr-title">🏀 ${qr.matchup}</div>
            <div class="qr-alert-badge" style="background: ${qr.alert_level === 'CRITICAL' ? '#dc2626' : qr.alert_level === 'HIGH' ? '#ea580c' : '#ca8a04'};">${urgencyBadge}</div>
          </div>
          <div class="qr-trigger"><strong>Trigger:</strong> ${qr.trigger || 'Quarter reversal pattern detected'}</div>
          <div class="qr-stats">
            <div class="qr-stat">
              <div class="qr-stat-label">Edge</div>
              <div class="qr-stat-value critical-text">+${qr.edge || 0}%</div>
            </div>
            <div class="qr-stat">
              <div class="qr-stat-label">Confidence</div>
              <div class="qr-stat-value">${qr.confidence || 0}%</div>
            </div>
          </div>
        </div>
      `;
    } else {
      // Fallback for any other strategy types
      alertCard = `
        <div class="qr-card-medium">
          <div class="qr-header">
            <div class="qr-title">Alert from ${alert.strategy}</div>
          </div>
          <div style="padding: 12px; text-align: center; color: #94a3b8;">
            ${alert.strategy} rendering - Full implementation coming soon
          </div>
        </div>
      `;
    }

    return `<div style="margin-bottom: 12px;">${badge}${alertCard}</div>`;
  }).join('');
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

function renderInjuryProps() {
  const container = document.getElementById('injuryPropsList');

  if (injuryProps.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">
          <img src="https://em-content.zobj.net/source/microsoft-teams/363/high-voltage_26a1.png" alt="Lightning" style="width: 64px; height: 64px;">
        </div>
        <div>⚡ Monitoring Twitter for Injuries</div>
        <div style="font-size: 11px; margin-top: 8px;">Watching 11 Tier 1 reporters (Woj, Shams, Schefter, etc.) for instant injury updates</div>
      </div>
    `;
    return;
  }

  container.innerHTML = injuryProps.map((ip, index) => {
    const timeRemaining = Math.max(0, Math.floor(60 - ip.time_since_tweet));
    const alertTime = formatTimeAgo(ip.timestamp);

    // Urgency styling based on time remaining
    const urgencyClass = timeRemaining <= 15 ? 'qr-card-critical' :
                         timeRemaining <= 30 ? 'qr-card-high' :
                         'qr-card-medium';
    const urgencyBadge = timeRemaining <= 15 ? '🚨 CRITICAL' :
                         timeRemaining <= 30 ? '🔥 URGENT' :
                         '⚡ LIVE';

    // Sport emoji
    const sportEmoji = ip.sport === 'NBA' ? '🏀' :
                       ip.sport === 'NFL' ? '🏈' :
                       ip.sport === 'NHL' ? '🏒' :
                       ip.sport === 'MLB' ? '⚾' : '🎯';

    // Format odds
    const formattedOdds = ip.best_odds > 0 ? `+${ip.best_odds}` : `${ip.best_odds}`;

    return `
      <div class="${urgencyClass}" data-index="${index}" style="border: 3px solid ${timeRemaining <= 15 ? '#ef4444' : timeRemaining <= 30 ? '#f97316' : '#eab308'}; animation: ${timeRemaining <= 15 ? 'pulse 1s infinite' : 'none'};">
        <div class="qr-header">
          <div class="qr-title">${sportEmoji} ${ip.player_name} - ${ip.team}</div>
          <div class="qr-alert-badge" style="background: ${timeRemaining <= 15 ? '#dc2626' : timeRemaining <= 30 ? '#ea580c' : '#ca8a04'};">
            ${urgencyBadge}
          </div>
        </div>

        <!-- COUNTDOWN TIMER (60-second window!) -->
        <div style="background: rgba(239, 68, 68, 0.2); border: 2px solid #ef4444; border-radius: 8px; padding: 12px; margin-bottom: 12px; text-align: center;">
          <div style="font-size: 32px; font-weight: bold; color: #fca5a5;">⏱️ ${timeRemaining}s</div>
          <div style="font-size: 11px; color: #fecaca; margin-top: 4px;">REMAINING TO PLACE BET</div>
        </div>

        <!-- Injury Status -->
        <div class="qr-trigger">
          <strong>Status:</strong> ${ip.injury_status}
        </div>

        <!-- Prop Details -->
        <div class="qr-details">
          <div class="qr-detail-row">
            <span><strong>Prop:</strong> ${ip.prop_type.toUpperCase()}</span>
            <span><strong>Line:</strong> ${ip.prop_side.toUpperCase()} ${ip.prop_line}</span>
          </div>
          <div class="qr-detail-row">
            <span><strong>Best Book:</strong> ${ip.best_book}</span>
            <span><strong>Odds:</strong> ${formattedOdds}</span>
          </div>
        </div>

        <!-- EV & Confidence Stats -->
        <div class="qr-stats">
          <div class="qr-stat">
            <div class="qr-stat-label">Expected Value</div>
            <div class="qr-stat-value critical-text">+${ip.expected_value.toFixed(1)}%</div>
          </div>
          <div class="qr-stat">
            <div class="qr-stat-label">Confidence</div>
            <div class="qr-stat-value ${ip.confidence >= 75 ? 'high-text' : 'medium-text'}">${ip.confidence}%</div>
          </div>
        </div>

        <!-- ML Reasoning -->
        <div class="qr-recommendation">
          <div class="qr-rec-header">🤖 ML Analysis</div>
          <div style="font-size: 12px; color: #cbd5e1; line-height: 1.4; margin-top: 6px;">
            ${ip.reasoning}
          </div>
        </div>

        <!-- Place Bet Button -->
        <div style="margin-top: 12px;">
          <button class="qr-place-bet-btn" onclick="window.open('https://www.draftkings.com', '_blank')" style="width: 100%; background: linear-gradient(135deg, #dc2626, #991b1b); border: none; padding: 12px; font-weight: bold; font-size: 14px; cursor: pointer; border-radius: 6px; color: white;">
            ⚡ PLACE BET NOW (${timeRemaining}s) →
          </button>
        </div>

        <!-- Alert Time -->
        <div style="font-size: 10px; color: #94a3b8; margin-top: 8px; text-align: center;">
          Detected ${alertTime}
        </div>
      </div>
    `;
  }).join('');

  // Add click handlers for cards
  container.querySelectorAll('[data-index]').forEach(card => {
    card.addEventListener('click', (e) => {
      if (e.target.tagName === 'BUTTON') return; // Skip if clicking button
      const index = parseInt(card.dataset.index);
      const injuryProp = injuryProps[index];
      if (injuryProp) {
        console.log('[POPUP] Clicked injury prop:', injuryProp);
      }
    });
  });
}

function updateStats() {
  document.getElementById('opportunityCount').textContent = opportunities.length;
  document.getElementById('steamCount').textContent = steamMoves.length;
  document.getElementById('middlesCount').textContent = middles.length;
  document.getElementById('goalieCount').textContent = goaliePulls.length;
  document.getElementById('quarterReversalCount').textContent = quarterReversals.length;
  document.getElementById('injuryPropsCount').textContent = injuryProps.length;
  document.getElementById('injuryAlertsCount').textContent = injuryAlerts.length;
}

let currentFilter = 'all'; // Global filter state

function switchTab(tabName) {
  console.log('[POPUP] Switching to tab:', tabName);
  currentFilter = tabName;

  // Update tab buttons styling
  document.querySelectorAll('.tab-btn').forEach(btn => {
    if (btn.dataset.tab === tabName) {
      btn.style.background = '#3b82f6';
      btn.style.color = 'white';
      btn.classList.add('active');
    } else {
      btn.style.background = '#334155';
      btn.style.color = '#94a3b8';
      btn.classList.remove('active');
    }
  });

  // Re-render with filter
  renderAlertFeed(tabName);
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

function renderMiddles() {
  const container = document.getElementById('middlesList');

  if (middles.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">
          <img src="https://em-content.zobj.net/source/microsoft-teams/363/bullseye_1f3af.png" alt="Bullseye" style="width: 64px; height: 64px;">
        </div>
        <div>No middle opportunities</div>
        <div style="font-size: 11px; margin-top: 8px;">Tracking NHL (1+ goal gap) and NBA (3+ point gap)...</div>
      </div>
    `;
    return;
  }

  container.innerHTML = middles.map((m, index) => {
    const game = m.game || `${m.away_team} @ ${m.home_team}`;

    // Map sport_key to display name
    let sport = 'Unknown';
    if (m.sport) {
      if (m.sport.includes('basketball_nba')) sport = 'NBA';
      else if (m.sport.includes('hockey')) sport = 'NHL';
      else if (m.sport.includes('football_nfl')) sport = 'NFL';
      else if (m.sport.includes('baseball')) sport = 'MLB';
      else sport = m.sport;
    }

    const sportEmoji = getSportEmoji(sport);
    const bookLow = getBookmaker(m.book_low);
    const bookHigh = getBookmaker(m.book_high);
    const gap = (m.gap || 0).toFixed(1);

    // Timestamps
    const alertTime = formatTimeAgo(m.timestamp);
    const gameTime = formatGameTime(m.commence_time);

    return `
      <div class="opportunity-card" data-sport="${sport}">
        <div class="opportunity-header">
          <div class="opportunity-title">
            <img src="${sportEmoji}" alt="${sport}" style="width: 20px; height: 20px; vertical-align: middle; margin-right: 6px;">
            ${game}
          </div>
          <div class="opportunity-profit">${gap} gap</div>
        </div>
        <div class="opportunity-details">
          ${m.market_type.toUpperCase()} MIDDLE<br>
          ${m.side_low} (${m.odds_low})<br>
          ${m.side_high} (${m.odds_high})
        </div>
        <div class="opportunity-books">
          <div class="book-badge book-left">
            <img src="${bookLow.logo}" alt="${bookLow.name}" class="book-logo">
            <div class="book-info">
              <div class="book-name">${bookLow.name}</div>
              <div class="bet-details">${m.side_low} (${m.odds_low})</div>
            </div>
          </div>
          <div class="book-badge book-right">
            <img src="${bookHigh.logo}" alt="${bookHigh.name}" class="book-logo">
            <div class="book-info">
              <div class="book-name">${bookHigh.name}</div>
              <div class="bet-details">${m.side_high} (${m.odds_high})</div>
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

function renderQuarterReversals() {
  const container = document.getElementById('quarterReversalList');

  if (quarterReversals.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">
          <img src="https://em-content.zobj.net/source/microsoft-teams/363/basketball_1f3c0.png" alt="Basketball" style="width: 64px; height: 64px;">
        </div>
        <div>No quarter reversal opportunities</div>
        <div style="font-size: 11px; margin-top: 8px;">Monitoring live NBA games...</div>
      </div>
    `;
    return;
  }

  container.innerHTML = quarterReversals.map((qr, index) => {
    const isCritical = qr.alert_level === 'CRITICAL';
    const isHigh = qr.alert_level === 'HIGH';
    const matchup = qr.matchup || 'Unknown game';
    const alertTime = formatTimeAgo(qr.timestamp);

    // Card styling based on alert level
    const cardClass = isCritical ? 'qr-card-critical' : isHigh ? 'qr-card-high' : 'qr-card-medium';
    const badgeEmoji = isCritical ? '🚨' : isHigh ? '🔥' : '📈';
    const badgeText = isCritical ? 'CRITICAL' : isHigh ? 'HIGH' : 'MEDIUM';

    // Top recommendation
    const topRec = qr.recommendations && qr.recommendations.length > 0 ? qr.recommendations[0] : null;

    return `
      <div class="${cardClass}" data-index="${index}">
        <div class="qr-header">
          <div class="qr-title">🏀 ${matchup}</div>
          <div class="qr-alert-badge ${isCritical ? 'critical-badge' : isHigh ? 'high-badge' : 'medium-badge'}">
            ${badgeEmoji} ${badgeText}
          </div>
        </div>

        <div class="qr-trigger">
          <strong>Trigger:</strong> ${qr.trigger || 'N/A'}
        </div>

        <div class="qr-details">
          <div class="qr-detail-row">
            <span><strong>Hot Team:</strong> ${qr.hot_team || 'N/A'}</span>
            <span><strong>Reversal Team:</strong> ${qr.reversal_team || 'N/A'}</span>
          </div>
          <div class="qr-detail-row">
            <span><strong>Quarter:</strong> ${qr.quarter || 'N/A'}</span>
            <span><strong>Strategy:</strong> ${qr.strategy || 'N/A'}</span>
          </div>
        </div>

        <div class="qr-stats">
          <div class="qr-stat">
            <div class="qr-stat-label">Win Probability</div>
            <div class="qr-stat-value">${qr.reversal_prob || 'N/A'}</div>
          </div>
          <div class="qr-stat">
            <div class="qr-stat-label">Expected ROI</div>
            <div class="qr-stat-value ${isCritical ? 'critical-text' : 'high-text'}">${qr.expected_roi || 'N/A'}</div>
          </div>
        </div>

        ${topRec ? `
          <div class="qr-recommendation">
            <div class="qr-rec-header">💰 Top Recommendation</div>
            <div class="qr-rec-bet">${topRec.label || 'N/A'}</div>
            <div class="qr-rec-details">
              <span>Win Prob: ${(topRec.probability * 100).toFixed(1)}%</span>
              <span>EV: ${topRec.expected_value > 0 ? '+' : ''}${(topRec.expected_value * 100).toFixed(1)}%</span>
              ${topRec.kelly_size ? `<span>Kelly: $${topRec.kelly_size.toFixed(2)}</span>` : ''}
            </div>

            ${topRec.bookmaker ? `
              <div class="qr-bookmakers">
                <div class="qr-book-label">📍 Best Odds:</div>
                <div class="qr-primary-book">
                  <img src="${getBookmaker(topRec.bookmaker).logo}" alt="${topRec.bookmaker_title || getBookmaker(topRec.bookmaker).name}" class="book-logo">
                  <span class="book-name">${topRec.bookmaker_title || getBookmaker(topRec.bookmaker).name}</span>
                  <span class="book-odds">${topRec.odds || 'N/A'}</span>
                  <button class="qr-place-bet-btn" data-bookmaker="${topRec.bookmaker}" data-qr-index="${index}">
                    Place Bet →
                  </button>
                </div>

                ${topRec.alt_bookmakers && topRec.alt_bookmakers.length > 0 ? `
                  <div class="qr-alt-books">
                    <div class="qr-alt-label">Also available at:</div>
                    ${topRec.alt_bookmakers.map(alt => `
                      <div class="qr-alt-book">
                        <img src="${getBookmaker(alt.bookmaker).logo}" alt="${alt.bookmaker_title || getBookmaker(alt.bookmaker).name}" class="book-logo-sm">
                        <span class="alt-book-name">${alt.bookmaker_title || getBookmaker(alt.bookmaker).name}</span>
                        <span class="alt-book-odds">${alt.odds}</span>
                      </div>
                    `).join('')}
                  </div>
                ` : ''}
              </div>
            ` : ''}
          </div>
        ` : ''}

        <div class="qr-reasoning">
          <strong>Why this works:</strong> ${qr.reasoning || 'N/A'}
        </div>

        <div class="alert-timestamps">
          <span class="timestamp-alert">⏰ Alert: ${alertTime}</span>
          <span class="timestamp-game">🏀 Live Game</span>
        </div>
      </div>
    `;
  }).join('');

  // Add click handlers for Place Bet buttons
  document.querySelectorAll('.qr-place-bet-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const bookmaker = btn.dataset.bookmaker;
      const qrIndex = parseInt(btn.dataset.qrIndex);
      if (bookmaker && quarterReversals[qrIndex]) {
        openQuarterReversalBet(bookmaker, quarterReversals[qrIndex]);
      }
    });
  });
}

function openQuarterReversalBet(bookmaker, qr) {
  // Map bookmaker to URL
  const bookmakerUrls = {
    'draftkings': 'https://sportsbook.draftkings.com/leagues/basketball/nba',
    'fanduel': 'https://sportsbook.fanduel.com/navigation/nba',
    'betmgm': 'https://sports.betmgm.com/en/sports/basketball-7/betting/usa-9/nba-6004',
    'caesars': 'https://www.williamhill.com/us/nj/bet/basketball',
    'betrivers': 'https://nj.betrivers.com/?page=sportsbook#basketball',
    'espnbet': 'https://espnbet.com/sport/basketball/organization/united-states/competition/nba',
    'fanatics': 'https://fanatics.com/sports/basketball/nba',
    'pointsbet': 'https://nj.pointsbet.com/sports/basketball/NBA',
    'bovada': 'https://www.bovada.lv/sports/basketball/nba'
  };

  const url = bookmakerUrls[bookmaker] || `https://${bookmaker}.com`;

  console.log('[POPUP] Opening Quarter Reversal bet at:', bookmaker, 'for game:', qr.matchup);
  chrome.tabs.create({ url: url, active: true });
  window.close(); // Close popup after opening
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
