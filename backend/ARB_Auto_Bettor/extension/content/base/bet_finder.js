/**
 * Base Bet Finder - Core logic for locating bets on any sportsbook
 * Provides team matching, market detection, and line verification
 */

class BetFinder {
  constructor(sportsbookName) {
    this.sportsbookName = sportsbookName;
    this.debug = true;
  }

  log(...args) {
    if (this.debug) {
      console.log(`[BET_FINDER:${this.sportsbookName}]`, ...args);
    }
  }

  /**
   * Match team names with fuzzy logic
   * Handles variations like "LA Lakers" vs "Lakers", "Golden State" vs "Warriors"
   */
  normalizeTeamName(teamName) {
    if (!teamName) return '';

    return teamName
      .toLowerCase()
      .trim()
      // Remove common prefixes
      .replace(/^(los angeles|la|new york|ny|golden state)\s+/i, '')
      // Remove special characters
      .replace(/[^a-z0-9\s]/g, '')
      // Collapse whitespace
      .replace(/\s+/g, ' ');
  }

  /**
   * Check if team name matches with fuzzy logic
   */
  teamsMatch(team1, team2) {
    const normalized1 = this.normalizeTeamName(team1);
    const normalized2 = this.normalizeTeamName(team2);

    // Exact match
    if (normalized1 === normalized2) return true;

    // Partial match (one contains the other)
    if (normalized1.includes(normalized2) || normalized2.includes(normalized1)) {
      return true;
    }

    // Check for common abbreviations
    const abbrevMap = {
      'warriors': ['gsw', 'golden state'],
      'lakers': ['lal', 'los angeles'],
      'clippers': ['lac'],
      'knicks': ['nyk', 'new york'],
      'nets': ['bkn', 'brooklyn'],
      'celtics': ['bos', 'boston'],
      'heat': ['mia', 'miami'],
      'bulls': ['chi', 'chicago'],
      'cavaliers': ['cavs', 'cle', 'cleveland'],
      'mavericks': ['mavs', 'dal', 'dallas'],
      'nuggets': ['den', 'denver'],
      'rockets': ['hou', 'houston'],
      'thunder': ['okc', 'oklahoma city'],
      'spurs': ['sas', 'san antonio'],
      'suns': ['phx', 'phoenix'],
      'trail blazers': ['blazers', 'por', 'portland'],
      'kings': ['sac', 'sacramento'],
      'timberwolves': ['wolves', 'min', 'minnesota'],
      'pelicans': ['nop', 'new orleans'],
      'grizzlies': ['mem', 'memphis'],
      'bucks': ['mil', 'milwaukee'],
      'pistons': ['det', 'detroit'],
      'pacers': ['ind', 'indiana'],
      'hawks': ['atl', 'atlanta'],
      'hornets': ['cha', 'charlotte'],
      'wizards': ['wsh', 'washington'],
      'raptors': ['tor', 'toronto'],
      'magic': ['orl', 'orlando'],
      '76ers': ['sixers', 'phi', 'philadelphia']
    };

    // Check if either team matches known abbreviations
    for (const [fullName, abbrevs] of Object.entries(abbrevMap)) {
      if (normalized1.includes(fullName) || abbrevs.some(a => normalized1.includes(a))) {
        if (normalized2.includes(fullName) || abbrevs.some(a => normalized2.includes(a))) {
          return true;
        }
      }
    }

    return false;
  }

  /**
   * Find game element on page by team names
   */
  findGameElement(homeTeam, awayTeam, containerSelector = 'body') {
    this.log('Searching for game:', awayTeam, '@', homeTeam);

    const container = document.querySelector(containerSelector);
    if (!container) {
      this.log('Container not found:', containerSelector);
      return null;
    }

    // Get all text content and check for team names
    const allElements = container.querySelectorAll('*');
    const potentialGameElements = [];

    for (const element of allElements) {
      const text = element.textContent || '';

      // Check if this element contains both team names
      const hasHomeTeam = this.teamsMatch(text, homeTeam);
      const hasAwayTeam = this.teamsMatch(text, awayTeam);

      if (hasHomeTeam && hasAwayTeam) {
        potentialGameElements.push({
          element,
          text: text.substring(0, 200), // First 200 chars for debugging
          score: this.calculateMatchScore(text, homeTeam, awayTeam)
        });
      }
    }

    if (potentialGameElements.length === 0) {
      this.log('❌ No game elements found matching teams');
      return null;
    }

    // Sort by match score and return best match
    potentialGameElements.sort((a, b) => b.score - a.score);
    this.log('✅ Found', potentialGameElements.length, 'potential matches');
    this.log('Best match:', potentialGameElements[0].text);

    return potentialGameElements[0].element;
  }

  /**
   * Calculate how well a text matches the teams (higher = better)
   */
  calculateMatchScore(text, homeTeam, awayTeam) {
    let score = 0;
    const lowerText = text.toLowerCase();
    const normalizedHome = this.normalizeTeamName(homeTeam);
    const normalizedAway = this.normalizeTeamName(awayTeam);

    // Exact team name match = +10 points each
    if (lowerText.includes(normalizedHome)) score += 10;
    if (lowerText.includes(normalizedAway)) score += 10;

    // Contains both teams close together = +5
    const homeIndex = lowerText.indexOf(normalizedHome);
    const awayIndex = lowerText.indexOf(normalizedAway);
    if (homeIndex !== -1 && awayIndex !== -1 && Math.abs(homeIndex - awayIndex) < 50) {
      score += 5;
    }

    // Shorter text = more likely to be the game title (prefer concise)
    if (text.length < 100) score += 3;
    if (text.length < 50) score += 2;

    return score;
  }

  /**
   * Find market tab (Spread, Total, Moneyline, etc.)
   */
  findMarketTab(marketType, gameElement) {
    this.log('Looking for market type:', marketType);

    if (!gameElement) return null;

    const marketKeywords = {
      'totals': ['total', 'over/under', 'o/u'],
      'spreads': ['spread', 'point spread', 'handicap'],
      'h2h': ['moneyline', 'money line', 'ml', 'winner']
    };

    const keywords = marketKeywords[marketType] || [marketType];

    // Look for buttons/tabs within or near the game element
    const searchArea = gameElement.closest('.game-container, .event-row, .game-card, [class*="game"]') || gameElement;
    const buttons = searchArea.querySelectorAll('button, a, [role="tab"], .tab, [class*="tab"]');

    for (const button of buttons) {
      const buttonText = (button.textContent || '').toLowerCase();

      for (const keyword of keywords) {
        if (buttonText.includes(keyword)) {
          this.log('✅ Found market tab:', button.textContent.trim());
          return button;
        }
      }
    }

    this.log('⚠️ Market tab not found for:', marketType);
    return null;
  }

  /**
   * Find specific bet button (Over 225.5, Lakers -3.5, etc.)
   */
  findBetButton(gameElement, marketType, outcome, point) {
    this.log('Looking for bet:', outcome, point);

    if (!gameElement) return null;

    const searchArea = gameElement.closest('.game-container, .event-row, .game-card, [class*="game"]') || gameElement;
    const buttons = searchArea.querySelectorAll('button, a, [class*="bet"], [class*="odd"], [data-outcome]');

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
        return button;
      }
    }

    this.log('⚠️ Bet button not found');
    return null;
  }

  /**
   * Verify odds match (within tolerance)
   */
  oddsMatch(displayedOdds, expectedOdds, tolerance = 10) {
    // Convert American odds to numbers
    const displayed = this.parseOdds(displayedOdds);
    const expected = this.parseOdds(expectedOdds);

    if (displayed === null || expected === null) return false;

    return Math.abs(displayed - expected) <= tolerance;
  }

  /**
   * Parse American odds from text (e.g., "-110", "+150")
   */
  parseOdds(oddsText) {
    if (typeof oddsText === 'number') return oddsText;

    const match = String(oddsText).match(/([+-]?\d+)/);
    return match ? parseInt(match[1]) : null;
  }

  /**
   * Find bet slip input field
   */
  findBetSlipInput() {
    // Common selectors for bet slip input
    const selectors = [
      'input[name*="stake"]',
      'input[name*="amount"]',
      'input[placeholder*="amount"]',
      'input[placeholder*="stake"]',
      'input[type="number"]',
      '.bet-slip input[type="text"]',
      '#stake-input',
      '#bet-amount'
    ];

    for (const selector of selectors) {
      const input = document.querySelector(selector);
      if (input && input.offsetParent !== null) { // Check if visible
        this.log('✅ Found bet slip input:', selector);
        return input;
      }
    }

    this.log('⚠️ Bet slip input not found');
    return null;
  }

  /**
   * Find bet slip confirm button
   */
  findConfirmButton() {
    const selectors = [
      'button[class*="place-bet"]',
      'button[class*="confirm"]',
      'button[class*="submit"]',
      'button:has-text("Place Bet")',
      'button:has-text("Confirm")',
      '.bet-slip button[type="submit"]'
    ];

    for (const selector of selectors) {
      try {
        const button = document.querySelector(selector);
        if (button && button.offsetParent !== null) {
          this.log('✅ Found confirm button:', selector);
          return button;
        }
      } catch (e) {
        // :has-text() might not work in all browsers
        continue;
      }
    }

    // Fallback: find button with "place" or "bet" or "confirm" text
    const buttons = document.querySelectorAll('button, input[type="submit"]');
    for (const button of buttons) {
      const text = (button.textContent || button.value || '').toLowerCase();
      if (text.includes('place') || text.includes('confirm') || text.includes('submit bet')) {
        this.log('✅ Found confirm button by text:', button.textContent || button.value);
        return button;
      }
    }

    this.log('⚠️ Confirm button not found');
    return null;
  }

  /**
   * Highlight an element with visual indicator
   */
  highlightElement(element, color = '#10b981', duration = 3000) {
    if (!element) return;

    // Create highlight overlay
    const originalBorder = element.style.border;
    const originalBoxShadow = element.style.boxShadow;
    const originalTransition = element.style.transition;

    element.style.transition = 'all 0.3s ease';
    element.style.border = `3px solid ${color}`;
    element.style.boxShadow = `0 0 15px ${color}`;

    // Scroll into view
    element.scrollIntoView({ behavior: 'smooth', block: 'center' });

    // Remove highlight after duration
    if (duration > 0) {
      setTimeout(() => {
        element.style.border = originalBorder;
        element.style.boxShadow = originalBoxShadow;
        element.style.transition = originalTransition;
      }, duration);
    }
  }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = BetFinder;
}
