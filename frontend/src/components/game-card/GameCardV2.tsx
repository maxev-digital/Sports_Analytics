import { useState } from 'react';
import { LiveGame, GameOdds } from '../../types';
import { detectSport, getSportBorderClass } from '../../utils/sportDetection';
import { formatTeamName } from '../../utils/teamNames';
import { getTeamLogoUrl } from '../../utils/teamLogos';
import { openSportsbook } from '../../utils/deepLinking';
import { trackBetClick } from '../../utils/betTracking';
import { useAuth } from '../../contexts/AuthContext';
import { useBetSlip } from '../../contexts/BetSlipContext';
import { useSettings } from '../../hooks/useSettings';
import { OddsStrip } from './OddsStrip';
import { SignalBar } from './SignalBar';
import { GameDetailDrawer } from './GameDetailDrawer';

interface PickSummary {
  id: number;
  pick_side: string;
  pick_type: string;
  edge_pct: number;
  market_odds: number;
  confidence_tier: string | null;
  total_line: number | null;
}

interface GameCardV2Props {
  game: LiveGame;
  isPinned?: boolean;
  onTogglePin?: (gameId: string) => void;
  matchingPicks?: PickSummary[];
}

type Market = 'spread' | 'moneyline' | 'totals' | 'halves';

const SPORT_LABELS: Record<string, string> = {
  NBA: '🏀 NBA', NCAAB: '🏀 NCAAB', NFL: '🏈 NFL', NCAAF: '🏈 NCAAF',
  NHL: '🏒 NHL', MLB: '⚾ MLB', WNBA: '🏀 WNBA', TENNIS: '🎾 Tennis', MMA: 'MMA', SOCCER: '⚽ Soccer',
};

export function GameCardV2({ game, isPinned = false, onTogglePin, matchingPicks = [] }: GameCardV2Props) {
  const { state, odds: rawOdds, projection, alternate_lines } = game;
  const { settings } = useSettings('default');
  const { username } = useAuth();
  const { openBetSlip } = useBetSlip();

  const [selectedMarket, setSelectedMarket] = useState<Market>('totals');
  const [isDetailOpen, setIsDetailOpen] = useState(false);

  const sport = detectSport(game);
  const isLive = state.status === 'live';

  // Respect user's enabled bookmakers
  const odds = settings?.enabled_bookmakers?.length
    ? rawOdds.filter(o => {
        const k = o.bookmaker.toLowerCase().replace(/\s+/g, '').replace(/\./g, '');
        return settings.enabled_bookmakers.includes(k) || settings.enabled_bookmakers.includes(k.replace(/_/g, ''));
      })
    : rawOdds;

  const gameTime = new Date(state.commence_time).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', timeZone: 'America/Chicago' });
  const gameDate = new Date(state.commence_time).toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'America/Chicago' });

  const getPeriodLabel = (): string | null => {
    if (!isLive || !state.quarter) return null;
    const q = state.quarter;
    if (sport === 'MLB') { const inn = Math.ceil(q / 2); return `${q % 2 === 1 ? 'T' : 'B'}${inn}`; }
    if (sport === 'NHL') { const ordinals = ['', '1st', '2nd', '3rd']; return q <= 3 ? ordinals[q] : q === 4 ? 'OT' : `${q - 3}OT`; }
    if (sport === 'NCAAB') { return q <= 2 ? '1H' : q <= 4 ? '2H' : q === 5 ? 'OT' : `${q - 4}OT`; }
    return q <= 4 ? `Q${q}` : q === 5 ? 'OT' : `${q - 4}OT`;
  };

  const handleBetClick = async (bookmakerName: string, odd: GameOdds, url: string) => {
    openSportsbook(url, bookmakerName);
    if (!username) return;
    let betType: 'spread' | 'total' | 'moneyline' | 'prop' = 'total';
    let betSide = '';
    let betOdds = 0;
    if (selectedMarket === 'totals') {
      betType = 'total'; betSide = projection.recommendation ?? 'OVER'; betOdds = projection.recommendation === 'UNDER' ? odd.under_price : odd.over_price;
    } else if (selectedMarket === 'spread') {
      betType = 'spread'; betSide = `${formatTeamName(state.home_team.name, state.sport_key)} ${(odd.home_spread ?? 0) > 0 ? '+' : ''}${odd.home_spread}`; betOdds = odd.home_spread_price ?? 0;
    } else {
      betType = 'moneyline'; betSide = formatTeamName(state.home_team.name, state.sport_key); betOdds = odd.home_ml ?? 0;
    }
    await trackBetClick({ userId: username, gameId: state.id, sport: state.sport_key, homeTeam: formatTeamName(state.home_team.name, state.sport_key), awayTeam: formatTeamName(state.away_team.name, state.sport_key), commenceTime: state.commence_time, bookmaker: bookmakerName, betType, betSide, odds: betOdds });
    openBetSlip({ sport: state.sport_key, homeTeam: formatTeamName(state.home_team.name, state.sport_key), awayTeam: formatTeamName(state.away_team.name, state.sport_key), gameId: state.id, commenceTime: state.commence_time, betType, betSide, odds: betOdds, bookmaker: bookmakerName });
  };

  const borderClass = getSportBorderClass(sport);
  const periodLabel = getPeriodLabel();
  const hasDetail = !!(game.home_team_stats || game.away_team_stats || game.home_nhl_stats || game.home_mlb_stats || game.home_nfl_stats || game.home_mma_stats || game.tennis_round);

  return (
    <div className={`bg-slate-800 rounded-lg p-3 border-2 ${borderClass} hover:shadow-lg transition-shadow`}>
      {/* Header */}
      <div className="flex justify-between items-start mb-2">
        <div className="flex items-start gap-2">
          {onTogglePin && (
            <button onClick={e => { e.stopPropagation(); onTogglePin(state.id); }} className="mt-0.5 hover:scale-125 transition-transform text-xl">
              {isPinned ? '⭐' : '☆'}
            </button>
          )}
          <div>
            <div className="text-xs text-slate-400">{gameDate}</div>
            <div className="text-sm font-semibold text-slate-300">{gameTime} CST</div>
          </div>
        </div>
        <div className="flex flex-col items-end gap-1">
          <span className="px-2 py-0.5 bg-slate-700 rounded text-xs font-bold text-slate-200">
            {SPORT_LABELS[sport] ?? sport}
          </span>
          {isLive && periodLabel && (
            <div className="flex items-center gap-1.5">
              <span className="bg-red-600 text-white px-2 py-0.5 rounded text-xs font-bold">{periodLabel}</span>
              {state.time_remaining && <span className="text-xs font-bold text-slate-300">{state.time_remaining}</span>}
            </div>
          )}
          {isLive && !periodLabel && (
            <span className="bg-red-600 text-white px-2 py-0.5 rounded text-xs font-bold">LIVE</span>
          )}
        </div>
      </div>

      {/* Teams */}
      <div className="space-y-1.5 mb-2">
        {[
          { team: state.away_team, label: 'Away' },
          { team: state.home_team, label: 'Home' },
        ].map(({ team }) => {
          const logo = getTeamLogoUrl(team.name, state.sport_key, 50);
          return (
            <div key={team.name} className="flex justify-between items-center">
              <div className="flex items-center gap-2">
                {logo && <img src={logo} alt="" className="w-5 h-5 object-contain flex-shrink-0" onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />}
                <span className="text-base font-bold text-white">{formatTeamName(team.name, state.sport_key)}</span>
              </div>
              {team.score !== null && <span className="text-2xl font-bold text-white">{team.score}</span>}
            </div>
          );
        })}
      </div>

      {/* Odds */}
      {odds.length > 0 && (
        <OddsStrip
          odds={odds}
          state={state}
          selectedMarket={selectedMarket}
          onMarketChange={setSelectedMarket}
          onBetClick={handleBetClick}
          alternateLine={alternate_lines}
        />
      )}

      {/* Signal Bar */}
      <SignalBar projection={projection} matchingPicks={matchingPicks} sport={sport} isLive={isLive} />

      {/* Detail toggle */}
      {hasDetail && (
        <button
          onClick={() => setIsDetailOpen(v => !v)}
          className="mt-2 w-full text-xs text-slate-500 hover:text-slate-300 transition-colors text-left flex items-center gap-1"
        >
          <span>{isDetailOpen ? '▼' : '▶'}</span>
          <span>{isDetailOpen ? 'Hide details' : 'View details'}</span>
        </button>
      )}

      {/* Detail drawer */}
      <GameDetailDrawer game={game} isOpen={isDetailOpen} onClose={() => setIsDetailOpen(false)} />
    </div>
  );
}
