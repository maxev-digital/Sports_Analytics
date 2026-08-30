import { useState, useEffect } from 'react';
import { BookmakerLogo } from '../components/BookmakerLogo';
import { getBookmaker, getBookmakerUrl } from '../data/bookmakers';
import { OddsMetricsDashboard } from '../components/OddsMetricsDashboard';
import { formatTeamName } from '../utils/teamNames';
import { getTeamLogoUrl } from '../utils/teamLogos';
import { getApiUrl } from '../config';
import { useAuth } from '../contexts/AuthContext';
import { useBetSlip } from '../contexts/BetSlipContext';
import { openSportsbook } from '../utils/deepLinking';
import { useSettings } from '../hooks/useSettings';
import { logger } from '../utils/logger';

interface WeatherInfo {
  temp_high?: number;
  temp_low?: number;
  description?: string;
  wind_chill?: number;
  wind_speed?: number;
}

interface GameOdds {
  id: string;
  sport_key: string;
  home_team: string;
  away_team: string;
  home_score?: number;
  away_score?: number;
  commence_time: string;
  status: string;
  channel?: string;
  weather?: WeatherInfo;
  odds: Array<{
    bookmaker: string;
    total: number;
    over_price: number;
    under_price: number;
    home_spread: number;
    away_spread: number;
    home_spread_price: number;
    away_spread_price: number;
    home_ml: number;
    away_ml: number;
    is_best_over?: boolean;
    is_best_under?: boolean;
    latency_ms?: number;
    source?: string;  // Data source identifier
    source_speed?: string;  // 'fast' or 'standard'
  }>;
}

type SportKey = 'basketball_nba' | 'basketball_ncaab' | 'americanfootball_nfl' | 'americanfootball_ncaaf' | 'icehockey_nhl' | 'baseball_mlb' | 'basketball_wnba' | 'tennis_atp_wimbledon' | 'tennis_wta_wimbledon';
type BetType = 'moneyline' | 'spread' | 'total';
type OddsRow = GameOdds['odds'][number];
type BestOddsResult = { away: OddsRow; home: OddsRow } | { over: OddsRow; under: OddsRow } | null;

export function Odds() {
  const { username } = useAuth();
  const { openBetSlip } = useBetSlip();
  const { settings } = useSettings('default');
  const [activeSport, setActiveSport] = useState<SportKey>('americanfootball_nfl');
  const [activeBetType, setActiveBetType] = useState<BetType>('moneyline');
  const [games, setGames] = useState<GameOdds[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalInfo, setModalInfo] = useState<{type: 'tv' | 'weather', game: GameOdds} | null>(null);

  useEffect(() => {
    fetchGames();
  }, [activeSport, username]);

  const fetchGames = async () => {
    setLoading(true);
    logger.info('🎮 Loading games for sport:', activeSport);

    try {
      const response = await fetch(getApiUrl(`games?user_id=default&sport_key=${activeSport}`));
      if (!response.ok) throw new Error('API not available');

      const apiGames = await response.json();
      logger.info('📊 API returned:', apiGames.length, 'games for', activeSport);

      const transformedGames: GameOdds[] = apiGames.map((game: any) => ({
        id: game.state.id,
        sport_key: game.state.sport_key,
        home_team: game.state.home_team.name,
        away_team: game.state.away_team.name,
        home_score: game.state.home_team.score,
        away_score: game.state.away_team.score,
        commence_time: game.state.commence_time,
        status: game.state.status,
        channel: game.channel,
        weather: game.weather,
        odds: game.odds
      }));

      transformedGames.sort((a, b) => new Date(a.commence_time).getTime() - new Date(b.commence_time).getTime());
      logger.info('✅ Showing', transformedGames.length, 'games for', activeSport);
      setGames(transformedGames);
    } catch (error) {
      logger.error('❌ API error:', error);
      setGames([]);
    } finally {
      setLoading(false);
    }
  };

  const getSportDisplayName = (sport: SportKey): string => {
    const sportNames: Record<SportKey, string> = {
      'baseball_mlb': 'MLB',
      'basketball_wnba': 'WNBA',
      'tennis_atp_wimbledon': 'ATP Wimbledon',
      'tennis_wta_wimbledon': 'WTA Wimbledon',
      'basketball_nba': 'NBA',
      'basketball_ncaab': 'NCAAB',
      'americanfootball_nfl': 'NFL',
      'americanfootball_ncaaf': 'NCAAF',
      'icehockey_nhl': 'NHL',
    };
    return sportNames[sport] || sport;
  };

  const getSportIcon = (sport: SportKey): string => {
    const sportIcons: Record<SportKey, string> = {
      'baseball_mlb': '⚾',
      'basketball_wnba': '🏀',
      'tennis_atp_wimbledon': '🎾',
      'tennis_wta_wimbledon': '🎾',
      'basketball_nba': '🏀',
      'basketball_ncaab': '🏀',
      'americanfootball_nfl': '🏈',
      'americanfootball_ncaaf': '🏈',
      'icehockey_nhl': '🏒',
    };
    return sportIcons[sport] || '🏆';
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const today = new Date();
    const gameDate = new Date(dateStr);

    if (gameDate.toDateString() === today.toDateString()) {
      return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit'
      });
    }

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  const formatCompactDateTime = (dateStr: string): string => {
    const date = new Date(dateStr);
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const time = date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
    return `${month}/${day} - ${time}`;
  };

  const formatOdds = (price: number | null | undefined): string => {
    if (price == null) return '—';
    if (price > 0) return `+${price}`;
    return price.toString();
  };

  const normalizeBookmakerKey = (bookmaker: string): string => {
    return bookmaker
      .toLowerCase()
      .replace(/\s+/g, '')
      .replace(/\./g, '')
      .replace(/\(au\)/g, '');
  };

  // Find best odds for a game based on bet type
  const getBestOdds = (game: GameOdds): BestOddsResult => {
    // Only consider bookmakers the user has enabled - otherwise "best odds"
    // could point at a book that's filtered out of the table right below it.
    const odds = settings?.enabled_bookmakers?.length
      ? game.odds.filter(odd => settings.enabled_bookmakers.includes(normalizeBookmakerKey(odd.bookmaker)))
      : game.odds;
    if (odds.length === 0) return null;

    if (activeBetType === 'moneyline') {
      const mlOdds = odds.filter(o => o.away_ml != null && o.home_ml != null);
      if (!mlOdds.length) return null;
      const bestAway = mlOdds.reduce((best, curr) => (curr.away_ml ?? -Infinity) > (best.away_ml ?? -Infinity) ? curr : best);
      const bestHome = mlOdds.reduce((best, curr) => (curr.home_ml ?? -Infinity) > (best.home_ml ?? -Infinity) ? curr : best);
      return { away: bestAway, home: bestHome };
    } else if (activeBetType === 'spread') {
      const spOdds = odds.filter(o => o.away_spread_price != null && o.home_spread_price != null);
      if (!spOdds.length) return null;
      const bestAway = spOdds.reduce((best, curr) => (curr.away_spread_price ?? -Infinity) > (best.away_spread_price ?? -Infinity) ? curr : best);
      const bestHome = spOdds.reduce((best, curr) => (curr.home_spread_price ?? -Infinity) > (best.home_spread_price ?? -Infinity) ? curr : best);
      return { away: bestAway, home: bestHome };
    } else {
      const ouOdds = odds.filter(o => o.over_price != null && o.under_price != null);
      if (!ouOdds.length) return null;
      const bestOver  = ouOdds.reduce((best, curr) => (curr.over_price  ?? -Infinity) > (best.over_price  ?? -Infinity) ? curr : best);
      const bestUnder = ouOdds.reduce((best, curr) => (curr.under_price ?? -Infinity) > (best.under_price ?? -Infinity) ? curr : best);
      return { over: bestOver, under: bestUnder };
    }
  };

  const getTimeUntilGame = (dateStr: string): string => {
    const now = new Date();
    const gameTime = new Date(dateStr);
    const diffMs = gameTime.getTime() - now.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 0) return 'LIVE';
    if (diffMins < 60) return `${diffMins}m`;
    if (diffHours < 24) return `${diffHours}h ${diffMins % 60}m`;
    return `${diffDays}d ${diffHours % 24}h`;
  };

  // Handle opening bet slip with pre-filled data
  const handleTrackBet = (game: GameOdds, betType: 'moneyline' | 'spread' | 'total', betSide: string, odds: number, bookmaker: string, line?: number) => {
    // CRITICAL: Get bookmaker info and open sportsbook IMMEDIATELY to avoid popup blockers
    // Must be first lines - browsers block window.open() if not direct user action
    const bookmakerInfo = getBookmaker(bookmaker);
    if (bookmakerInfo) {
      openSportsbook(getBookmakerUrl(bookmaker, game.sport_key), bookmakerInfo.name);
    }

    // If user is not logged in, just open sportsbook (already done above) and return
    if (!username) {
      return;
    }

    // Then open bet slip with pre-filled data (so when they return, they can track the bet)
    openBetSlip({
      sport: game.sport_key,
      homeTeam: formatTeamName(game.home_team, game.sport_key),
      awayTeam: formatTeamName(game.away_team, game.sport_key),
      gameId: game.id,
      commenceTime: game.commence_time,
      betType,
      betSide,
      line,
      odds,
      bookmaker,
    });
  };

  if (loading) {
    return (
      <div className="analytics-page flex items-center justify-center">
        <div className="text-slate-400 text-lg">Loading odds...</div>
      </div>
    );
  }

  // All bookmakers that actually have lines in the current game data
  const allBookmakers = Array.from(new Set(games.flatMap(game =>
    game.odds.map(odd => normalizeBookmakerKey(odd.bookmaker))
  ))).sort();

  // Show only enabled bookmakers that have at least one game with actual odds.
  // This means toggling a book on in Settings shows it if it has data, and
  // hides it cleanly if it has no lines for the current sport.
  // Falls back to all books from game data if settings haven't loaded yet.
  const bookmakers = settings?.enabled_bookmakers?.length
    ? allBookmakers.filter(bm => settings.enabled_bookmakers.includes(bm))
    : allBookmakers;

  return (
    <div className="analytics-page p-4">
      <div className="w-full mx-auto">
        {/* Header with Bet Type Selector */}
        <div className="mb-6 flex items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-100 mb-2" style={{ textTransform: 'uppercase', letterSpacing: '-0.02em' }}>ODDS COMPARISON</h1>
            <p className="text-slate-400 text-sm">Real-time betting lines across top sportsbooks</p>
          </div>

          {/* Bet Type Selector */}
          <div className="flex gap-1 bg-slate-900 p-1 rounded border border-slate-700">
            <button
              onClick={() => setActiveBetType('moneyline')}
              className={`px-4 py-1.5 rounded text-xs font-semibold transition-all ${
                activeBetType === 'moneyline'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Moneyline
            </button>
            <button
              onClick={() => setActiveBetType('spread')}
              className={`px-4 py-1.5 rounded text-xs font-semibold transition-all ${
                activeBetType === 'spread'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Spread
            </button>
            <button
              onClick={() => setActiveBetType('total')}
              className={`px-4 py-1.5 rounded text-xs font-semibold transition-all ${
                activeBetType === 'total'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Total
            </button>
          </div>
        </div>

        {/* Sport Tabs — horizontal row */}
        <div className="flex flex-wrap gap-2 mb-3">
          {(['baseball_mlb', 'basketball_wnba', 'tennis_atp_wimbledon', 'tennis_wta_wimbledon', 'basketball_nba', 'basketball_ncaab', 'americanfootball_nfl', 'americanfootball_ncaaf', 'icehockey_nhl'] as SportKey[]).map((sport) => (
            <button
              key={sport}
              onClick={() => setActiveSport(sport)}
              className={`px-3 py-1.5 rounded text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-2 ${
                activeSport === sport
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/50'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'
              }`}
            >
              <span className="text-sm">{getSportIcon(sport)}</span>
              {getSportDisplayName(sport)}
            </button>
          ))}
        </div>

        {/* Metrics Dashboard */}
        <div className="mb-2">
          <OddsMetricsDashboard />
        </div>

        {/* Compact Odds Grid */}
        <div className="bg-slate-900 rounded-lg overflow-hidden border-2 border-slate-700 shadow-2xl">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              {/* Header Row with Bookmaker Logos */}
              <thead className="bg-slate-800">
                <tr>
                  {/* Info Column - First Column */}
                  <th className="py-2 px-2 text-center min-w-[100px] border-b-2 border-slate-600 border-r border-slate-600 bg-slate-800 sticky left-0 z-20">
                    <div className="flex flex-col items-center gap-1">
                      <span className="text-slate-300 font-bold text-xs uppercase tracking-wider">ℹ️ Info</span>
                    </div>
                  </th>
                  <th className="text-left py-2 px-2 text-slate-300 font-bold text-xs uppercase tracking-wider bg-slate-800 border-r border-b-2 border-slate-600">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{getSportIcon(activeSport)}</span>
                      {getSportDisplayName(activeSport)} Games
                    </div>
                  </th>
                  <th className="py-2 px-3 text-center min-w-[120px] border-r border-b-2 border-slate-600 bg-slate-800">
                    <div className="flex flex-col items-center gap-1">
                      <span className="text-slate-300 font-bold text-xs uppercase tracking-wider">⭐ Best Line</span>
                    </div>
                  </th>
                  {bookmakers.map((bookmaker, index) => {
                    const bookmakerData = getBookmaker(bookmaker);
                    const displayName = bookmakerData?.name || bookmaker.toUpperCase();
                    return (
                      <th key={bookmaker} className={`py-0.5 px-0.5 text-center min-w-[55px] border-b-2 border-slate-600 border-r border-slate-600`}>
                        <a
                          href={getBookmakerUrl(bookmaker, activeSport)}
                          target="_blank"
                          rel="noopener noreferrer"
                          referrerPolicy="no-referrer"
                          className="flex flex-col items-center gap-0 hover:opacity-80 transition-opacity cursor-pointer py-0.5"
                          title={`Visit ${displayName}`}
                        >
                          <BookmakerLogo
                            bookmakerKey={bookmaker}
                            size="sm"
                            showName={false}
                          />
                          <span className="text-sm font-medium text-slate-100 leading-tight">{displayName}</span>
                        </a>
                      </th>
                    );
                  })}
                </tr>
              </thead>

              <tbody>
                {games.map((game, gameIndex) => (
                  <tr
                    key={game.id}
                    className={`hover:bg-slate-800/30 transition-colors ${
                      game.status === 'live' ? 'bg-red-900/10' : ''
                    } ${gameIndex < games.length - 1 ? 'border-b border-slate-700' : ''}`}
                  >
                    {/* Info Column - First Column */}
                    <td className="py-1 px-1 text-center border-r border-slate-600 sticky left-0 bg-slate-900/95 backdrop-blur-sm z-10">
                      <div className="flex flex-col items-center gap-1">
                        {/* Compact Date/Time */}
                        <div className="text-xs font-medium text-slate-300 bg-slate-800 px-2 py-0.5 rounded">
                          {formatCompactDateTime(game.commence_time)}
                        </div>
                        {/* Info Icons */}
                        <div className="flex items-center gap-1">
                          {game.channel && (
                            <button
                              onClick={() => setModalInfo({type: 'tv', game})}
                              className="text-lg hover:scale-110 transition-transform cursor-pointer"
                              title={`TV: ${game.channel}`}
                            >
                              📺
                            </button>
                          )}
                          {game.weather && (
                            <button
                              onClick={() => setModalInfo({type: 'weather', game})}
                              className="text-lg hover:scale-110 transition-transform cursor-pointer"
                              title="Weather Info"
                            >
                              🌤️
                            </button>
                          )}
                        </div>
                      </div>
                    </td>

                    {/* Game Info Column */}
                    <td className="py-0.5 px-2 bg-slate-900/95 backdrop-blur-sm border-r border-slate-600">
                      <div className="flex flex-col justify-center h-full">
                        {/* Teams */}
                        <div className="space-y-0.5">
                          <div className="flex items-center gap-2">
                            {(() => { const logo = getTeamLogoUrl(game.away_team, game.sport_key, 50); return logo ? <img src={logo} alt="" style={{ width: 18, height: 18, objectFit: 'contain', flexShrink: 0 }} onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} /> : null; })()}
                            <span className="text-white font-semibold text-base">
                              <span className="text-slate-400 text-sm">(A)</span> {formatTeamName(game.away_team, game.sport_key)}
                            </span>
                            {game.away_score !== undefined && (
                              <span className="text-base font-semibold text-blue-400 ml-2 tabular-nums">
                                {game.away_score}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-2">
                            {(() => { const logo = getTeamLogoUrl(game.home_team, game.sport_key, 50); return logo ? <img src={logo} alt="" style={{ width: 18, height: 18, objectFit: 'contain', flexShrink: 0 }} onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} /> : null; })()}
                            <span className="text-white font-semibold text-base">
                              <span className="text-slate-400 text-sm">(H)</span> {formatTeamName(game.home_team, game.sport_key)}
                            </span>
                            {game.home_score !== undefined && (
                              <span className="text-base font-semibold text-blue-400 ml-2 tabular-nums">
                                {game.home_score}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </td>

                    {/* Best Line Column */}
                    <td className="py-2 px-2 border-r border-slate-600 bg-gradient-to-r from-green-900/20 to-slate-900/50">
                      {(() => {
                        const bestOdds = getBestOdds(game);
                        if (!bestOdds) return <div className="text-slate-600 text-xs">—</div>;

                        return (
                          <div>
                            {/* Moneyline */}
                            {activeBetType === 'moneyline' && 'away' in bestOdds && (
                              <div className="space-y-0.5">
                                <div className="flex items-center justify-between gap-2 bg-slate-800/50 rounded px-3 py-0.5">
                                  <a
                                    href={getBookmakerUrl(normalizeBookmakerKey(bestOdds.away.bookmaker), game.sport_key)}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    referrerPolicy="no-referrer"
                                    className="hover:opacity-70 transition-opacity"
                                    title={`Visit ${getBookmaker(normalizeBookmakerKey(bestOdds.away.bookmaker))?.name}`}
                                  >
                                    <BookmakerLogo bookmakerKey={normalizeBookmakerKey(bestOdds.away.bookmaker)} size="sm" />
                                  </a>
                                  <div className="text-lg font-bold text-green-300 leading-tight">
                                    {formatOdds(bestOdds.away.away_ml)}
                                  </div>
                                </div>
                                <div className="flex items-center justify-between gap-2 bg-slate-800/50 rounded px-3 py-0.5">
                                  <a
                                    href={getBookmakerUrl(normalizeBookmakerKey(bestOdds.home.bookmaker), game.sport_key)}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    referrerPolicy="no-referrer"
                                    className="hover:opacity-70 transition-opacity"
                                    title={`Visit ${getBookmaker(normalizeBookmakerKey(bestOdds.home.bookmaker))?.name}`}
                                  >
                                    <BookmakerLogo bookmakerKey={normalizeBookmakerKey(bestOdds.home.bookmaker)} size="sm" />
                                  </a>
                                  <div className="text-lg font-bold text-green-300 leading-tight">
                                    {formatOdds(bestOdds.home.home_ml)}
                                  </div>
                                </div>
                              </div>
                            )}

                            {/* Spread */}
                            {activeBetType === 'spread' && 'away' in bestOdds && (
                              <div className="space-y-0.5">
                                <div className="flex items-center justify-between gap-3 bg-slate-800/50 rounded px-3 py-0.5">
                                  <a
                                    href={getBookmakerUrl(normalizeBookmakerKey(bestOdds.away.bookmaker), game.sport_key)}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    referrerPolicy="no-referrer"
                                    className="hover:opacity-70 transition-opacity"
                                    title={`Visit ${getBookmaker(normalizeBookmakerKey(bestOdds.away.bookmaker))?.name}`}
                                  >
                                    <BookmakerLogo bookmakerKey={normalizeBookmakerKey(bestOdds.away.bookmaker)} size="sm" />
                                  </a>
                                  <div className="flex items-center gap-2">
                                    <div className="text-base font-bold text-slate-100 leading-tight">
                                      {bestOdds.away.away_spread != null ? `${bestOdds.away.away_spread > 0 ? '+' : ''}${bestOdds.away.away_spread}` : '—'}
                                    </div>
                                    <div className="text-sm text-green-300 font-semibold leading-tight">
                                      {formatOdds(bestOdds.away.away_spread_price)}
                                    </div>
                                  </div>
                                </div>
                                <div className="flex items-center justify-between gap-3 bg-slate-800/50 rounded px-3 py-0.5">
                                  <a
                                    href={getBookmakerUrl(normalizeBookmakerKey(bestOdds.home.bookmaker), game.sport_key)}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    referrerPolicy="no-referrer"
                                    className="hover:opacity-70 transition-opacity"
                                    title={`Visit ${getBookmaker(normalizeBookmakerKey(bestOdds.home.bookmaker))?.name}`}
                                  >
                                    <BookmakerLogo bookmakerKey={normalizeBookmakerKey(bestOdds.home.bookmaker)} size="sm" />
                                  </a>
                                  <div className="flex items-center gap-2">
                                    <div className="text-base font-bold text-slate-100 leading-tight">
                                      {bestOdds.home.home_spread != null ? `${bestOdds.home.home_spread > 0 ? '+' : ''}${bestOdds.home.home_spread}` : '—'}
                                    </div>
                                    <div className="text-sm text-green-300 font-semibold leading-tight">
                                      {formatOdds(bestOdds.home.home_spread_price)}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            )}

                            {/* Total */}
                            {activeBetType === 'total' && 'over' in bestOdds && (
                              <div className="space-y-0.5">
                                <div className="flex items-center gap-3 bg-slate-800/50 rounded px-3 py-0.5">
                                  <a
                                    href={getBookmakerUrl(normalizeBookmakerKey(bestOdds.over.bookmaker), game.sport_key)}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    referrerPolicy="no-referrer"
                                    className="hover:opacity-70 transition-opacity"
                                    title={`Visit ${getBookmaker(normalizeBookmakerKey(bestOdds.over.bookmaker))?.name}`}
                                  >
                                    <BookmakerLogo bookmakerKey={normalizeBookmakerKey(bestOdds.over.bookmaker)} size="sm" />
                                  </a>
                                  <span className="text-base font-bold text-green-300 leading-tight w-4">
                                    O
                                  </span>
                                  <span className="text-base font-medium text-green-200 leading-tight flex-1">
                                    {bestOdds.over.total}
                                  </span>
                                  <span className="text-base font-medium text-green-100 leading-tight">
                                    {formatOdds(bestOdds.over.over_price)}
                                  </span>
                                </div>
                                <div className="flex items-center gap-3 bg-slate-800/50 rounded px-3 py-0.5">
                                  <a
                                    href={getBookmakerUrl(normalizeBookmakerKey(bestOdds.under.bookmaker), game.sport_key)}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    referrerPolicy="no-referrer"
                                    className="hover:opacity-70 transition-opacity"
                                    title={`Visit ${getBookmaker(normalizeBookmakerKey(bestOdds.under.bookmaker))?.name}`}
                                  >
                                    <BookmakerLogo bookmakerKey={normalizeBookmakerKey(bestOdds.under.bookmaker)} size="sm" />
                                  </a>
                                  <span className="text-base font-bold text-red-300 leading-tight w-4">
                                    U
                                  </span>
                                  <span className="text-base font-medium text-red-200 leading-tight flex-1">
                                    {bestOdds.under.total}
                                  </span>
                                  <span className="text-base font-medium text-red-100 leading-tight">
                                    {formatOdds(bestOdds.under.under_price)}
                                  </span>
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })()}
                    </td>

                    {/* Bookmaker Odds Cells */}
                    {bookmakers.map((bookmaker, bookIndex) => {
                      const bookOdds = game.odds.find(o => normalizeBookmakerKey(o.bookmaker) === bookmaker);

                      return (
                        <td key={bookmaker} className={`py-0.5 px-0.5 text-center ${
                          bookIndex < bookmakers.length - 1 ? 'border-r border-slate-700' : ''
                        }`}>
                          {bookOdds ? (
                            <div>
                              {/* Moneyline */}
                              {activeBetType === 'moneyline' && (
                                <div className="space-y-0 divide-y divide-slate-700">
                                  <button
                                    onClick={() => handleTrackBet(game, 'moneyline', formatTeamName(game.away_team, game.sport_key), bookOdds.away_ml, bookmaker)}
                                    className="hover:bg-slate-800 transition-colors cursor-pointer px-0.5 py-2 block w-full"
                                    title={`Track bet: ${formatTeamName(game.away_team, game.sport_key)} ${formatOdds(bookOdds.away_ml)} on ${getBookmaker(bookmaker)?.name}`}
                                  >
                                    <div className="text-xl font-medium text-blue-300 leading-tight">
                                      {formatOdds(bookOdds.away_ml)}
                                    </div>
                                  </button>
                                  <button
                                    onClick={() => handleTrackBet(game, 'moneyline', formatTeamName(game.home_team, game.sport_key), bookOdds.home_ml, bookmaker)}
                                    className="hover:bg-slate-800 transition-colors cursor-pointer px-0.5 py-2 block w-full"
                                    title={`Track bet: ${formatTeamName(game.home_team, game.sport_key)} ${formatOdds(bookOdds.home_ml)} on ${getBookmaker(bookmaker)?.name}`}
                                  >
                                    <div className="text-xl font-medium text-green-300 leading-tight">
                                      {formatOdds(bookOdds.home_ml)}
                                    </div>
                                  </button>
                                </div>
                              )}

                              {/* Spread */}
                              {activeBetType === 'spread' && (
                                <div className="space-y-0 divide-y divide-slate-700">
                                  <button
                                    onClick={() => handleTrackBet(
                                      game,
                                      'spread',
                                      `${formatTeamName(game.away_team, game.sport_key)} ${bookOdds.away_spread > 0 ? '+' : ''}${bookOdds.away_spread}`,
                                      bookOdds.away_spread_price,
                                      bookmaker,
                                      bookOdds.away_spread
                                    )}
                                    className="hover:bg-slate-800 transition-colors cursor-pointer px-0.5 py-2 block w-full"
                                    title={`Track bet: ${formatTeamName(game.away_team, game.sport_key)} ${bookOdds.away_spread > 0 ? '+' : ''}${bookOdds.away_spread} ${formatOdds(bookOdds.away_spread_price)} on ${getBookmaker(bookmaker)?.name}`}
                                  >
                                    <div className="text-lg font-medium text-slate-100 leading-tight">
                                      {bookOdds.away_spread != null ? `${bookOdds.away_spread > 0 ? '+' : ''}${bookOdds.away_spread}` : '—'}
                                    </div>
                                    <div className="text-base text-slate-400 mt-0 leading-tight">
                                      {formatOdds(bookOdds.away_spread_price)}
                                    </div>
                                  </button>
                                  <button
                                    onClick={() => handleTrackBet(
                                      game,
                                      'spread',
                                      `${formatTeamName(game.home_team, game.sport_key)} ${bookOdds.home_spread > 0 ? '+' : ''}${bookOdds.home_spread}`,
                                      bookOdds.home_spread_price,
                                      bookmaker,
                                      bookOdds.home_spread
                                    )}
                                    className="hover:bg-slate-800 transition-colors cursor-pointer px-0.5 py-2 block w-full"
                                    title={`Track bet: ${formatTeamName(game.home_team, game.sport_key)} ${bookOdds.home_spread > 0 ? '+' : ''}${bookOdds.home_spread} ${formatOdds(bookOdds.home_spread_price)} on ${getBookmaker(bookmaker)?.name}`}
                                  >
                                    <div className="text-lg font-medium text-slate-100 leading-tight">
                                      {bookOdds.home_spread != null ? `${bookOdds.home_spread > 0 ? '+' : ''}${bookOdds.home_spread}` : '—'}
                                    </div>
                                    <div className="text-base text-slate-400 mt-0 leading-tight">
                                      {formatOdds(bookOdds.home_spread_price)}
                                    </div>
                                  </button>
                                </div>
                              )}

                              {/* Total */}
                              {activeBetType === 'total' && (
                                <div className="space-y-0">
                                  <button
                                    onClick={() => handleTrackBet(
                                      game,
                                      'total',
                                      'OVER',
                                      bookOdds.over_price,
                                      bookmaker,
                                      bookOdds.total
                                    )}
                                    className={`hover:bg-slate-800 transition-colors cursor-pointer px-0.5 py-2 block w-full ${
                                      bookOdds.is_best_over ? 'bg-green-900/30' : ''
                                    }`}
                                    title={`Track bet: Over ${bookOdds.total} ${formatOdds(bookOdds.over_price)} on ${getBookmaker(bookmaker)?.name}`}
                                  >
                                    <div className="flex items-center gap-1">
                                      <span className={`text-base font-medium ${bookOdds.is_best_over ? 'text-green-300' : 'text-slate-400'} leading-tight w-4`}>
                                        O
                                      </span>
                                      <span className={`text-base font-normal ${bookOdds.is_best_over ? 'text-green-200' : 'text-slate-200'} leading-tight flex-1`}>
                                        {bookOdds.total}
                                      </span>
                                      <span className={`text-base font-normal ${bookOdds.is_best_over ? 'text-green-100' : 'text-slate-100'} leading-tight`}>
                                        {formatOdds(bookOdds.over_price)}
                                      </span>
                                    </div>
                                  </button>
                                  <button
                                    onClick={() => handleTrackBet(
                                      game,
                                      'total',
                                      'UNDER',
                                      bookOdds.under_price,
                                      bookmaker,
                                      bookOdds.total
                                    )}
                                    className={`hover:bg-slate-800 transition-colors cursor-pointer px-0.5 py-2 block w-full ${
                                      bookOdds.is_best_under ? 'bg-red-900/30' : ''
                                    }`}
                                    title={`Track bet: Under ${bookOdds.total} ${formatOdds(bookOdds.under_price)} on ${getBookmaker(bookmaker)?.name}`}
                                  >
                                    <div className="flex items-center gap-1">
                                      <span className={`text-base font-medium ${bookOdds.is_best_under ? 'text-red-300' : 'text-slate-400'} leading-tight w-4`}>
                                        U
                                      </span>
                                      <span className={`text-base font-normal ${bookOdds.is_best_under ? 'text-red-200' : 'text-slate-200'} leading-tight flex-1`}>
                                        {bookOdds.total}
                                      </span>
                                      <span className={`text-base font-normal ${bookOdds.is_best_under ? 'text-red-100' : 'text-slate-100'} leading-tight`}>
                                        {formatOdds(bookOdds.under_price)}
                                      </span>
                                    </div>
                                  </button>
                                </div>
                              )}
                            </div>
                          ) : (
                            <div className="text-slate-600 text-xs py-1">—</div>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Stats Footer */}
        <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="stat-card" style={{ textAlign: 'center' }}>
            <div className="stat-label">Games</div>
            <div className="stat-value">{games.length}</div>
          </div>
          <div className="stat-card" style={{ textAlign: 'center' }}>
            <div className="stat-label">Sportsbooks</div>
            <div className="stat-value" style={{ color: 'var(--color-emerald-400)' }}>{bookmakers.length}</div>
          </div>
          <div className="stat-card" style={{ textAlign: 'center' }}>
            <div className="stat-label">Live Now</div>
            <div className="stat-value" style={{ color: 'var(--brand-red)' }}>
              {games.filter(g => g.status === 'live').length}
            </div>
          </div>
          <div className="stat-card" style={{ textAlign: 'center' }}>
            <div className="stat-label">Total Lines</div>
            <div className="stat-value" style={{ color: 'var(--color-blue-500)' }}>
              {games.reduce((sum, g) => sum + g.odds.length, 0)}
            </div>
          </div>
        </div>

        {/* Best Odds Legend */}
        {activeBetType === 'total' && (
          <div className="mt-4 text-xs text-slate-400 flex items-center gap-6 justify-center">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-600 rounded ring-2 ring-green-400"></div>
              <span>Best Over Odds</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-red-600 rounded ring-2 ring-red-400"></div>
              <span>Best Under Odds</span>
            </div>
          </div>
        )}
      </div>

      {/* Info Modal */}
      {modalInfo && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          onClick={() => setModalInfo(null)}
        >
          <div
            className="rounded-lg p-6 max-w-md w-full mx-4"
            style={{ background: 'var(--card)', border: '1px solid var(--border-strong)' }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                {modalInfo.type === 'tv' ? '📺 TV Info' : '🌤️ Weather Info'}
              </h3>
              <button
                onClick={() => setModalInfo(null)}
                className="text-slate-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>

            {modalInfo.type === 'tv' && modalInfo.game.channel && (
              <div className="space-y-3">
                <div className="bg-slate-900 rounded p-4">
                  <div className="text-sm text-slate-400 mb-1">Channel</div>
                  <div className="text-2xl font-bold text-white">{modalInfo.game.channel}</div>
                </div>
                <div className="text-sm text-slate-400">
                  {formatTeamName(modalInfo.game.away_team, modalInfo.game.sport_key)} @ {formatTeamName(modalInfo.game.home_team, modalInfo.game.sport_key)}
                </div>
              </div>
            )}

            {modalInfo.type === 'weather' && modalInfo.game.weather && (
              <div className="space-y-3">
                {modalInfo.game.weather.description && (
                  <div className="bg-slate-900 rounded p-4">
                    <div className="text-sm text-slate-400 mb-1">Conditions</div>
                    <div className="text-lg font-medium text-white">{modalInfo.game.weather.description}</div>
                  </div>
                )}
                <div className="grid grid-cols-2 gap-3">
                  {modalInfo.game.weather.temp_high !== undefined && (
                    <div className="bg-slate-900 rounded p-3">
                      <div className="text-xs text-slate-400 mb-1">High</div>
                      <div className="text-xl font-bold text-orange-400">{modalInfo.game.weather.temp_high}°F</div>
                    </div>
                  )}
                  {modalInfo.game.weather.temp_low !== undefined && (
                    <div className="bg-slate-900 rounded p-3">
                      <div className="text-xs text-slate-400 mb-1">Low</div>
                      <div className="text-xl font-bold text-blue-400">{modalInfo.game.weather.temp_low}°F</div>
                    </div>
                  )}
                  {modalInfo.game.weather.wind_speed !== undefined && (
                    <div className="bg-slate-900 rounded p-3">
                      <div className="text-xs text-slate-400 mb-1">Wind Speed</div>
                      <div className="text-xl font-bold text-slate-200">{modalInfo.game.weather.wind_speed} mph</div>
                    </div>
                  )}
                  {modalInfo.game.weather.wind_chill !== undefined && (
                    <div className="bg-slate-900 rounded p-3">
                      <div className="text-xs text-slate-400 mb-1">Wind Chill</div>
                      <div className="text-xl font-bold text-cyan-400">{modalInfo.game.weather.wind_chill}°F</div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// Mock data for development
const mockData: Record<SportKey, GameOdds[]> = {
  basketball_nba: [
    {
      id: 'nba_game_1',
      sport_key: 'basketball_nba',
      home_team: 'Los Angeles Lakers',
      away_team: 'Boston Celtics',
      commence_time: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(), // 2 hours from now
      status: 'upcoming',
      odds: [
        { bookmaker: 'DraftKings', total: 228.5, over_price: -105, under_price: -115, home_spread: -2.5, away_spread: 2.5, home_spread_price: -110, away_spread_price: -110, home_ml: -150, away_ml: 130, is_best_over: true },
        { bookmaker: 'FanDuel', total: 229.0, over_price: -108, under_price: -112, home_spread: -2.5, away_spread: 2.5, home_spread_price: -110, away_spread_price: -110, home_ml: -155, away_ml: 135 },
        { bookmaker: 'BetMGM', total: 228.0, over_price: -110, under_price: -110, home_spread: -3.0, away_spread: 3.0, home_spread_price: -115, away_spread_price: -105, home_ml: -145, away_ml: 125, is_best_under: true },
        { bookmaker: 'Caesars', total: 228.5, over_price: -107, under_price: -113, home_spread: -2.5, away_spread: 2.5, home_spread_price: -108, away_spread_price: -112, home_ml: -152, away_ml: 132 },
        { bookmaker: 'BetRivers', total: 229.0, over_price: -109, under_price: -111, home_spread: -3.0, away_spread: 3.0, home_spread_price: -110, away_spread_price: -110, home_ml: -148, away_ml: 128 },
        { bookmaker: 'PointsBet', total: 228.0, over_price: -112, under_price: -108, home_spread: -2.5, away_spread: 2.5, home_spread_price: -112, away_spread_price: -108, home_ml: -153, away_ml: 133 }
      ]
    },
    {
      id: 'nba_game_2',
      sport_key: 'basketball_nba',
      home_team: 'Golden State Warriors',
      away_team: 'Phoenix Suns',
      commence_time: new Date(Date.now() + 4 * 60 * 60 * 1000).toISOString(), // 4 hours from now
      status: 'upcoming',
      odds: [
        { bookmaker: 'DraftKings', total: 232.5, over_price: -110, under_price: -110, home_spread: 3.5, away_spread: -3.5, home_spread_price: -110, away_spread_price: -110, home_ml: 145, away_ml: -165 },
        { bookmaker: 'FanDuel', total: 233.0, over_price: -108, under_price: -112, home_spread: 3.5, away_spread: -3.5, home_spread_price: -112, away_spread_price: -108, home_ml: 150, away_ml: -170, is_best_over: true },
        { bookmaker: 'BetMGM', total: 232.0, over_price: -115, under_price: -105, home_spread: 4.0, away_spread: -4.0, home_spread_price: -115, away_spread_price: -105, home_ml: 140, away_ml: -160, is_best_under: true },
        { bookmaker: 'Caesars', total: 232.5, over_price: -111, under_price: -109, home_spread: 3.5, away_spread: -3.5, home_spread_price: -110, away_spread_price: -110, home_ml: 148, away_ml: -168 },
        { bookmaker: 'BetRivers', total: 233.0, over_price: -110, under_price: -110, home_spread: 3.5, away_spread: -3.5, home_spread_price: -108, away_spread_price: -112, home_ml: 142, away_ml: -162 },
        { bookmaker: 'PointsBet', total: 232.0, over_price: -113, under_price: -107, home_spread: 4.0, away_spread: -4.0, home_spread_price: -110, away_spread_price: -110, home_ml: 146, away_ml: -166 }
      ]
    },
    {
      id: 'nba_game_3',
      sport_key: 'basketball_nba',
      home_team: 'Milwaukee Bucks',
      away_team: 'Philadelphia 76ers',
      home_score: 98,
      away_score: 92,
      commence_time: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(), // Started 1 hour ago
      status: 'live',
      odds: [
        { bookmaker: 'DraftKings', total: 225.5, over_price: -110, under_price: -110, home_spread: -4.5, away_spread: 4.5, home_spread_price: -110, away_spread_price: -110, home_ml: -180, away_ml: 155 },
        { bookmaker: 'FanDuel', total: 226.0, over_price: -108, under_price: -112, home_spread: -4.5, away_spread: 4.5, home_spread_price: -112, away_spread_price: -108, home_ml: -185, away_ml: 160 },
        { bookmaker: 'BetMGM', total: 225.0, over_price: -112, under_price: -108, home_spread: -5.0, away_spread: 5.0, home_spread_price: -115, away_spread_price: -105, home_ml: -175, away_ml: 150 },
        { bookmaker: 'Caesars', total: 225.5, over_price: -109, under_price: -111, home_spread: -4.5, away_spread: 4.5, home_spread_price: -110, away_spread_price: -110, home_ml: -182, away_ml: 157 },
        { bookmaker: 'BetRivers', total: 226.0, over_price: -110, under_price: -110, home_spread: -4.5, away_spread: 4.5, home_spread_price: -108, away_spread_price: -112, home_ml: -178, away_ml: 152 },
        { bookmaker: 'PointsBet', total: 225.0, over_price: -111, under_price: -109, home_spread: -5.0, away_spread: 5.0, home_spread_price: -110, away_spread_price: -110, home_ml: -180, away_ml: 155 }
      ]
    },
    {
      id: 'nba_game_4',
      sport_key: 'basketball_nba',
      home_team: 'Dallas Mavericks',
      away_team: 'Denver Nuggets',
      commence_time: new Date(Date.now() + 6 * 60 * 60 * 1000).toISOString(), // 6 hours from now
      status: 'upcoming',
      odds: [
        { bookmaker: 'DraftKings', total: 230.5, over_price: -112, under_price: -108, home_spread: 1.5, away_spread: -1.5, home_spread_price: -110, away_spread_price: -110, home_ml: -115, away_ml: -105 },
        { bookmaker: 'FanDuel', total: 231.0, over_price: -110, under_price: -110, home_spread: 1.5, away_spread: -1.5, home_spread_price: -108, away_spread_price: -112, home_ml: -118, away_ml: -102 },
        { bookmaker: 'BetMGM', total: 230.0, over_price: -115, under_price: -105, home_spread: 2.0, away_spread: -2.0, home_spread_price: -112, away_spread_price: -108, home_ml: -120, away_ml: 100, is_best_under: true },
        { bookmaker: 'Caesars', total: 230.5, over_price: -113, under_price: -107, home_spread: 1.5, away_spread: -1.5, home_spread_price: -110, away_spread_price: -110, home_ml: -116, away_ml: -104 },
        { bookmaker: 'BetRivers', total: 231.0, over_price: -110, under_price: -110, home_spread: 1.5, away_spread: -1.5, home_spread_price: -110, away_spread_price: -110, home_ml: -117, away_ml: -103 },
        { bookmaker: 'PointsBet', total: 230.5, over_price: -111, under_price: -109, home_spread: 2.0, away_spread: -2.0, home_spread_price: -110, away_spread_price: -110, home_ml: -119, away_ml: -101, is_best_over: true }
      ]
    }
  ],
  basketball_ncaab: [],
  americanfootball_nfl: [],
  americanfootball_ncaaf: [],
  icehockey_nhl: [],
  baseball_mlb: [],
  basketball_wnba: [],
  tennis_atp_wimbledon: [],
  tennis_wta_wimbledon: []
};
