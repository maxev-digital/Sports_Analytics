import { GameOdds, AlternateMarketLine, GameState } from '../../types';
import { BOOKMAKERS } from '../../data/bookmakers';
import { getGameSpecificUrl } from '../../utils/gameUrls';
import { formatTeamName } from '../../utils/teamNames';
import { getBookmakerInfo } from './utils';

type Market = 'spread' | 'moneyline' | 'totals' | 'halves';

interface OddsStripProps {
  odds: GameOdds[];
  state: GameState;
  selectedMarket: Market;
  onMarketChange: (m: Market) => void;
  onBetClick: (bookmaker: string, odd: GameOdds, url: string) => void;
  alternateLine?: AlternateMarketLine[] | null;
  recommendedBook?: string | null; // bookmaker key with best edge
}

const TAB_CLASS = (active: boolean) =>
  `flex-1 px-3 py-2 rounded-lg text-xs font-bold uppercase transition-all ${
    active
      ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/40'
      : 'bg-slate-800 text-slate-400 hover:bg-slate-700 border border-slate-700'
  }`;

export function OddsStrip({
  odds, state, selectedMarket, onMarketChange, onBetClick, alternateLine, recommendedBook
}: OddsStripProps) {
  const hasAlternate = alternateLine && alternateLine.length > 0;
  const away = formatTeamName(state.away_team.name, state.sport_key).split(' ').pop() ?? '';
  const home = formatTeamName(state.home_team.name, state.sport_key).split(' ').pop() ?? '';

  const uniqueOdds = odds.filter((o, i, arr) => arr.findIndex(x => x.bookmaker === o.bookmaker) === i);

  return (
    <div className="mt-2 pt-2 border-t border-slate-700">
      {/* Market tabs */}
      <div className="flex gap-1.5 mb-2">
        <button className={TAB_CLASS(selectedMarket === 'spread')} onClick={() => onMarketChange('spread')}>Spread</button>
        <button className={TAB_CLASS(selectedMarket === 'totals')} onClick={() => onMarketChange('totals')}>O/U</button>
        <button className={TAB_CLASS(selectedMarket === 'moneyline')} onClick={() => onMarketChange('moneyline')}>ML</button>
        {hasAlternate && (
          <button className={TAB_CLASS(selectedMarket === 'halves')} onClick={() => onMarketChange('halves')}>1H/2H</button>
        )}
      </div>

      {/* Book rows */}
      {selectedMarket !== 'halves' && (
        <div className="space-y-0.5">
          {uniqueOdds.map((odd, idx) => {
            const withUnderscore = odd.bookmaker.toLowerCase().replace(/\s+/g, '').replace(/\./g, '');
            const normalizedKey = BOOKMAKERS[withUnderscore] ? withUnderscore : withUnderscore.replace(/_/g, '');
            const bookData = BOOKMAKERS[normalizedKey];
            const gameUrl = getGameSpecificUrl(normalizedKey,
              formatTeamName(state.home_team.name, state.sport_key),
              formatTeamName(state.away_team.name, state.sport_key),
              state.sport_key, state.commence_time);
            const url = gameUrl || bookData?.url || '#';
            const info = getBookmakerInfo(odd.bookmaker);
            const isRecommended = recommendedBook === normalizedKey;

            return (
              <div key={idx} className={`flex items-center justify-between px-2 py-1 rounded text-sm ${isRecommended ? 'bg-blue-900/40 border border-blue-500/50' : 'bg-slate-800/60'}`}>
                <button onClick={() => onBetClick(odd.bookmaker, odd, url)} className="flex items-center gap-2 hover:opacity-70 transition-opacity">
                  {info.logo
                    ? <img src={info.logo} alt={odd.bookmaker} className="w-4 h-4 object-contain" onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                    : <span className={`text-xs font-bold px-1 rounded ${info.bg} ${info.text}`}>{info.short}</span>
                  }
                  <span className="text-slate-400 text-xs">{odd.bookmaker}</span>
                  {isRecommended && <span className="text-blue-400 text-xs">★</span>}
                </button>
                <div className="flex items-center gap-3">
                  <span className="text-slate-200 font-bold">
                    {selectedMarket === 'totals' && <>O/U <strong>{odd.total}</strong> <span className="text-slate-400 font-normal">({odd.over_price > 0 ? '+' : ''}{odd.over_price}/{odd.under_price > 0 ? '+' : ''}{odd.under_price})</span></>}
                    {selectedMarket === 'spread' && <>{home}: <strong>{(odd.home_spread ?? 0) > 0 ? '+' : ''}{odd.home_spread}</strong> · {away}: <strong>{(odd.away_spread ?? 0) > 0 ? '+' : ''}{odd.away_spread}</strong></>}
                    {selectedMarket === 'moneyline' && <>{home}: <strong>{(odd.home_ml ?? 0) > 0 ? '+' : ''}{odd.home_ml}</strong> · {away}: <strong>{(odd.away_ml ?? 0) > 0 ? '+' : ''}{odd.away_ml}</strong></>}
                  </span>
                  <button onClick={() => onBetClick(odd.bookmaker, odd, url)} className="px-2.5 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-bold transition-colors whitespace-nowrap">
                    Bet
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Halves */}
      {selectedMarket === 'halves' && hasAlternate && (
        <div className="space-y-2">
          {(['1H', '2H'] as const).map(half => {
            const lines = alternateLine!.filter(l => l.market_type === half);
            if (!lines.length) return null;
            return (
              <div key={half}>
                <div className="text-xs text-slate-400 font-semibold mb-1">{half === '1H' ? 'First Half' : 'Second Half'}</div>
                {lines.map((line, i) => (
                  <div key={i} className="flex justify-between text-xs text-slate-300 px-2 py-1 bg-slate-800/60 rounded mb-0.5">
                    <span>{line.bookmaker}</span>
                    <span className="font-bold">O/U {line.total} {line.over_price && line.under_price && `(${line.over_price > 0 ? '+' : ''}${line.over_price}/${line.under_price > 0 ? '+' : ''}${line.under_price})`}</span>
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
