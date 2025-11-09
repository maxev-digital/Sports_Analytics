import React, { useRef } from 'react';
import { LiveGame } from '../types';
import { formatTeamName } from '../utils/teamNames';
import { sportEmojis } from '../utils/sportDetection';

interface LiveGamesTickerProps {
  games: LiveGame[];
  onGameClick: (gameId: string) => void;
}

export function LiveGamesTicker({ games, onGameClick }: LiveGamesTickerProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Only show live games
  const liveGames = games.filter(game => game.state.status === 'live');

  if (liveGames.length === 0) {
    return null;
  }

  const getTeamAbbreviation = (teamName: string, sportKey: string): string => {
    const formatted = formatTeamName(teamName, sportKey);
    // Get last word (team name) and take first 3-4 letters
    const parts = formatted.split(' ');
    const teamWord = parts[parts.length - 1];
    return teamWord.substring(0, 3).toUpperCase();
  };

  const getPeriodLabel = (quarter: number | null, sportKey: string): string => {
    if (!quarter) return '';

    if (sportKey.includes('basketball')) {
      if (quarter <= 2) return '1H';
      if (quarter <= 4) return '2H';
      return `OT${quarter - 4}`;
    }

    if (sportKey.includes('football')) {
      if (quarter <= 4) return `Q${quarter}`;
      return `OT${quarter - 4}`;
    }

    if (sportKey.includes('hockey')) {
      if (quarter <= 3) return `P${quarter}`;
      return `OT${quarter - 3}`;
    }

    if (sportKey.includes('baseball')) {
      return `T${quarter}`;
    }

    return `Q${quarter}`;
  };

  const getSportEmoji = (sportKey: string): string | null => {
    if (sportKey.includes('basketball_nba')) return sportEmojis.NBA;
    if (sportKey.includes('basketball_ncaab')) return sportEmojis.NCAAB;
    if (sportKey.includes('americanfootball_nfl')) return sportEmojis.NFL;
    if (sportKey.includes('americanfootball_ncaaf')) return sportEmojis.NCAAF;
    if (sportKey.includes('icehockey_nhl')) return sportEmojis.NHL;
    if (sportKey.includes('baseball_mlb')) return sportEmojis.MLB;
    if (sportKey.includes('tennis')) return sportEmojis.TENNIS;
    if (sportKey.includes('mma')) return sportEmojis.MMA;
    if (sportKey.includes('golf')) return sportEmojis.PGA;
    return null;
  };

  const getSportBorderColor = (sportKey: string): string => {
    if (sportKey.includes('basketball_nba')) return 'border-orange-500/50';
    if (sportKey.includes('basketball_ncaab')) return 'border-blue-500/50';
    if (sportKey.includes('americanfootball_nfl')) return 'border-green-500/50';
    if (sportKey.includes('americanfootball_ncaaf')) return 'border-yellow-500/50';
    if (sportKey.includes('icehockey_nhl')) return 'border-cyan-500/50';
    if (sportKey.includes('baseball_mlb')) return 'border-red-500/50';
    if (sportKey.includes('tennis')) return 'border-lime-500/50';
    if (sportKey.includes('mma')) return 'border-purple-500/50';
    if (sportKey.includes('golf')) return 'border-emerald-500/50';
    return 'border-slate-600';
  };

  return (
    <div className="mb-4 bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
      <div
        ref={scrollRef}
        className="flex overflow-x-auto scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-slate-800 gap-3 p-3"
        style={{ scrollbarWidth: 'thin' }}
      >
        {liveGames.map((game) => {
          const awayAbbr = getTeamAbbreviation(game.state.away_team.name, game.state.sport_key);
          const homeAbbr = getTeamAbbreviation(game.state.home_team.name, game.state.sport_key);
          const period = getPeriodLabel(game.state.quarter, game.state.sport_key);
          const awayScore = game.state.away_team.score || 0;
          const homeScore = game.state.home_team.score || 0;
          const isAwayWinning = awayScore > homeScore;
          const isHomeWinning = homeScore > awayScore;
          const sportEmoji = getSportEmoji(game.state.sport_key);
          const borderColor = getSportBorderColor(game.state.sport_key);

          return (
            <button
              key={game.state.id}
              onClick={() => onGameClick(game.state.id)}
              className={`flex-shrink-0 bg-slate-900 hover:bg-slate-700 border-2 ${borderColor} rounded-lg px-4 py-2.5 transition-all hover:shadow-lg cursor-pointer min-w-[200px]`}
            >
              <div className="flex items-center gap-3 text-sm">
                {/* Sport Emoji */}
                {sportEmoji && (
                  <img
                    src={sportEmoji}
                    alt="Sport"
                    className="w-5 h-5 flex-shrink-0"
                    style={{ imageRendering: 'crisp-edges' }}
                  />
                )}

                {/* Away Team */}
                <div className="flex items-center gap-1.5 flex-1">
                  <span className={`font-bold text-xs ${isAwayWinning ? 'text-white' : 'text-slate-400'}`}>
                    {awayAbbr}
                  </span>
                  <span className={`font-bold ${isAwayWinning ? 'text-white' : 'text-slate-400'}`}>
                    {awayScore}
                  </span>
                </div>

                {/* Vertical Divider */}
                <div className="h-10 w-px bg-slate-600"></div>

                {/* Live indicator & Time */}
                <div className="flex flex-col items-center justify-center px-1.5">
                  <div className="flex items-center gap-1">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                    <span className="text-xs font-semibold text-slate-300">{period}</span>
                  </div>
                  <span className="text-xs text-slate-400">{game.state.time_remaining || ''}</span>
                </div>

                {/* Vertical Divider */}
                <div className="h-10 w-px bg-slate-600"></div>

                {/* Home Team */}
                <div className="flex items-center gap-1.5 flex-1 justify-end">
                  <span className={`font-bold ${isHomeWinning ? 'text-white' : 'text-slate-400'}`}>
                    {homeScore}
                  </span>
                  <span className={`font-bold text-xs ${isHomeWinning ? 'text-white' : 'text-slate-400'}`}>
                    {homeAbbr}
                  </span>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
