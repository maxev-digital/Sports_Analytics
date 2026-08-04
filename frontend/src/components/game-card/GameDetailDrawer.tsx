import { LiveGame } from '../../types';
import { detectSport } from '../../utils/sportDetection';
import { NBAPanel } from './panels/NBAPanel';
import { NHLPanel } from './panels/NHLPanel';
import { MLBPanel } from './panels/MLBPanel';
import { NFLPanel } from './panels/NFLPanel';
import { MMAPanel } from './panels/MMAPanel';
import { TennisPanel } from './panels/TennisPanel';

interface GameDetailDrawerProps {
  game: LiveGame;
  isOpen: boolean;
  onClose: () => void;
}

export function GameDetailDrawer({ game, isOpen, onClose }: GameDetailDrawerProps) {
  if (!isOpen) return null;

  const sport = detectSport(game);
  const { state } = game;
  const isLive = state.status === 'live';

  const renderPanel = () => {
    switch (sport) {
      case 'NBA':
      case 'NCAAB':
        return (
          <NBAPanel
            state={state}
            homeStats={game.home_team_stats}
            awayStats={game.away_team_stats}
            homeMomentum={game.home_nba_momentum}
            awayMomentum={game.away_nba_momentum}
            isLive={isLive}
          />
        );
      case 'NHL':
        return (
          <NHLPanel
            state={state}
            homeStats={game.home_nhl_stats}
            awayStats={game.away_nhl_stats}
            homeMomentum={game.home_nhl_momentum}
            awayMomentum={game.away_nhl_momentum}
            isLive={isLive}
          />
        );
      case 'MLB':
        return (
          <MLBPanel
            state={state}
            homeStats={game.home_mlb_stats}
            awayStats={game.away_mlb_stats}
            homePitcher={game.home_probable_pitcher}
            awayPitcher={game.away_probable_pitcher}
            ballpark={game.ballpark}
            umpire={game.hp_umpire}
          />
        );
      case 'NFL':
      case 'NCAAF':
        return (
          <NFLPanel
            state={state}
            homeStats={sport === 'NCAAF' ? game.home_ncaaf_stats : game.home_nfl_stats}
            awayStats={sport === 'NCAAF' ? game.away_ncaaf_stats : game.away_nfl_stats}
            homeMomentum={sport === 'NCAAF' ? game.home_ncaaf_momentum : game.home_nfl_momentum}
            awayMomentum={sport === 'NCAAF' ? game.away_ncaaf_momentum : game.away_nfl_momentum}
            homeLive={game.home_nfl_live_stats}
            awayLive={game.away_nfl_live_stats}
            isLive={isLive}
            isNCAAF={sport === 'NCAAF'}
          />
        );
      case 'MMA':
        return (
          <MMAPanel
            state={state}
            homeStats={game.home_mma_stats ?? null}
            awayStats={game.away_mma_stats ?? null}
          />
        );
      case 'TENNIS':
        return (
          <TennisPanel
            state={state}
            round={game.tennis_round}
            tournament={game.tennis_tournament}
          />
        );
      default:
        return <div className="text-slate-500 text-sm italic text-center py-4">No additional stats available</div>;
    }
  };

  return (
    <div className="mt-2 pt-2 border-t border-slate-600">
      <div className="flex justify-between items-center mb-2">
        <span className="text-xs font-bold text-slate-400 uppercase tracking-wide">Game Details</span>
        <button
          onClick={onClose}
          className="text-slate-500 hover:text-slate-300 text-lg leading-none transition-colors"
          aria-label="Close details"
        >
          ✕
        </button>
      </div>
      {renderPanel()}
    </div>
  );
}
