import { useState, useEffect } from 'react';
import { StrategyAlert } from '../types';
import { useBetSlip } from '../contexts/BetSlipContext';
import { openSportsbook } from '../utils/deepLinking';
import { getBookmaker } from '../utils/bookmakers';

interface BetAlertToastProps {
  alert: StrategyAlert;
  onDismiss: () => void;
  position: number; // 0 = bottom, 1 = second from bottom, etc.
}

export function BetAlertToast({ alert, onDismiss, position }: BetAlertToastProps) {
  const [timeElapsed, setTimeElapsed] = useState(0);
  const [isExiting, setIsExiting] = useState(false);
  const { openBetSlip } = useBetSlip();

  // Update timer every second
  useEffect(() => {
    const interval = setInterval(() => {
      setTimeElapsed(prev => prev + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  // Play chained audio sequence when toast appears
  useEffect(() => {
    const playAudioChain = async () => {
      const audioChain: string[] = [];
      const strategyName = alert.strategy_name.toLowerCase();
      const confidence = alert.urgency || alert.confidence;

      // 1. Strategy alert
      if (strategyName.includes('arbitrage')) {
        audioChain.push(confidence === 'CRITICAL' ? '/alerts/arbitrage_critical.mp3' :
                       confidence === 'HIGH' ? '/alerts/arbitrage_high.mp3' :
                       '/alerts/arbitrage_found.mp3');
      } else if (strategyName.includes('steam')) {
        audioChain.push(confidence === 'CRITICAL' ? '/alerts/steam_critical.mp3' :
                       confidence === 'HIGH' ? '/alerts/steam_high.mp3' :
                       '/alerts/steam_medium.mp3');
      } else if (strategyName.includes('middle')) {
        audioChain.push(confidence === 'CRITICAL' ? '/alerts/middle_critical.mp3' :
                       confidence === 'HIGH' ? '/alerts/middle_high.mp3' :
                       '/alerts/middle_medium.mp3');
      } else if (strategyName.includes('goalie')) {
        audioChain.push(confidence === 'CRITICAL' ? '/alerts/goalie_pull_critical.mp3' :
                       '/alerts/goalie_pull_warning.mp3');
      } else {
        audioChain.push(confidence === 'HIGH' ? '/alerts/alert_high.mp3' :
                       confidence === 'MEDIUM' ? '/alerts/alert_medium.mp3' :
                       '/alerts/alert_low.mp3');
      }

      // 2. Bet action + teams for first bet option
      if (alert.bet_options && alert.bet_options.length > 0) {
        const firstBet = alert.bet_options[0];

        // Bet action phrase
        if (firstBet.market_type === 'totals') {
          audioChain.push(firstBet.bet_side === 'over' ? '/alerts/bet_the_over.mp3' : '/alerts/bet_the_under.mp3');
        } else if (firstBet.market_type === 'spreads') {
          // Determine if home or away based on bet_side
          if (alert.home_team && alert.away_team) {
            const isHome = firstBet.bet_side?.toLowerCase().includes(alert.home_team.toLowerCase());
            audioChain.push(isHome ? '/alerts/bet_home_spread.mp3' : '/alerts/bet_away_spread.mp3');
          }
        } else if (firstBet.market_type === 'h2h') {
          if (alert.home_team && alert.away_team) {
            const isHome = firstBet.bet_side?.toLowerCase().includes(alert.home_team.toLowerCase());
            audioChain.push(isHome ? '/alerts/bet_home_moneyline.mp3' : '/alerts/bet_away_moneyline.mp3');
          }
        }

        // Team names (if not totals)
        if (firstBet.market_type !== 'totals' && alert.home_team && alert.away_team) {
          const teamToSay = firstBet.bet_side?.toLowerCase().includes(alert.home_team.toLowerCase()) ? alert.home_team : alert.away_team;
          const teamFileName = teamToSay.toLowerCase().replace(/ /g, '_').replace(/\./g, '').replace(/&/g, 'and').replace(/\(/g, '').replace(/\)/g, '');
          audioChain.push(`/alerts/team_${teamFileName}.mp3`);
        }

        // 3. Sportsbook for first bet
        const bookFileName = firstBet.bookmaker.toLowerCase().replace(/_/g, '');
        audioChain.push(`/alerts/${bookFileName}_alert.mp3`);

        // 4. For middles/arbitrage, add second bet option
        if (strategyName.includes('middle') || strategyName.includes('arbitrage')) {
          if (alert.bet_options.length > 1) {
            const secondBet = alert.bet_options[1];

            // "and"
            audioChain.push('/alerts/and.mp3');

            // Second bet action
            if (secondBet.market_type === 'spreads' && alert.home_team && alert.away_team) {
              const isHome = secondBet.bet_side?.toLowerCase().includes(alert.home_team.toLowerCase());
              audioChain.push(isHome ? '/alerts/bet_home_spread.mp3' : '/alerts/bet_away_spread.mp3');

              // Second team name
              const teamToSay = isHome ? alert.home_team : alert.away_team;
              const teamFileName = teamToSay.toLowerCase().replace(/ /g, '_').replace(/\./g, '').replace(/&/g, 'and').replace(/\(/g, '').replace(/\)/g, '');
              audioChain.push(`/alerts/team_${teamFileName}.mp3`);
            }

            // Second sportsbook
            const book2FileName = secondBet.bookmaker.toLowerCase().replace(/_/g, '');
            audioChain.push(`/alerts/${book2FileName}_alert.mp3`);
          }
        }
      }

      // Play audio chain sequentially
      for (const audioFile of audioChain) {
        try {
          const audio = new Audio(audioFile);
          audio.volume = 0.7;

          await new Promise<void>((resolve, reject) => {
            audio.onended = () => resolve();
            audio.onerror = () => reject();
            audio.play().catch(() => reject());
          });

          // Small pause between audio clips
          await new Promise(resolve => setTimeout(resolve, 200));
        } catch (err) {
          console.log('Audio play failed:', audioFile, err);
        }
      }
    };

    playAudioChain();
  }, []); // Only run once when component mounts

  // Auto-dismiss based on urgency
  useEffect(() => {
    let dismissTime: number;

    switch (alert.urgency || alert.confidence) {
      case 'CRITICAL':
        dismissTime = 60000; // 60 seconds for critical alerts
        break;
      case 'HIGH':
        dismissTime = 45000; // 45 seconds for high urgency
        break;
      case 'MEDIUM':
        dismissTime = 30000; // 30 seconds for medium
        break;
      default:
        dismissTime = 20000; // 20 seconds for low
    }

    const timer = setTimeout(() => {
      handleDismiss();
    }, dismissTime);

    return () => clearTimeout(timer);
  }, [alert.urgency, alert.confidence]);

  const handleDismiss = () => {
    setIsExiting(true);
    setTimeout(onDismiss, 300); // Wait for exit animation
  };

  // Format time elapsed as MM:SS
  const formatTimeElapsed = () => {
    const minutes = Math.floor(timeElapsed / 60);
    const seconds = timeElapsed % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  // Alert type-specific styling (BLACK backgrounds with WHITE borders, colored inner windows)
  const getConfidenceStyles = () => {
    const strategyName = alert.strategy_name.toLowerCase();

    // Arbitrage = Black background with RED inner windows (CRITICAL urgency)
    // Risk-free profit by betting both sides
    if (strategyName.includes('arbitrage')) {
      return {
        bg: 'bg-gradient-to-br from-black via-gray-900 to-slate-900',
        border: 'border-white',
        glow: 'shadow-2xl shadow-white/30',
        pulse: 'animate-pulse',
        emoji: '🚨',
        timerColor: 'text-white',
        infoBg: 'bg-black/40',
        bookCardBg: 'bg-red-600/80 border-white',
        bookCardHover: 'hover:bg-red-500/90 hover:border-white'
      };
    }

    // Steam Move = Black background with BLUE inner windows
    // Multiple books moving lines within minutes - bet stale numbers at books that haven't moved yet
    if (strategyName.includes('steam')) {
      return {
        bg: 'bg-gradient-to-br from-black via-gray-900 to-slate-900',
        border: 'border-white',
        glow: 'shadow-xl shadow-white/25',
        pulse: '',
        emoji: '🔥',
        timerColor: 'text-white',
        infoBg: 'bg-black/40',
        bookCardBg: 'bg-blue-600/80 border-white',
        bookCardHover: 'hover:bg-blue-500/90 hover:border-white'
      };
    }

    // Middle Opportunity = Black background, RED info windows, GREEN book cards
    // Bet both sides with gap - chance to win both or push one
    if (strategyName.includes('middle')) {
      return {
        bg: 'bg-gradient-to-br from-black via-gray-900 to-slate-900',
        border: 'border-white',
        glow: 'shadow-lg shadow-white/20',
        pulse: '',
        emoji: '⚡',
        timerColor: 'text-white',
        infoBg: 'bg-gradient-to-r from-red-900 to-red-800',
        bookCardBg: 'bg-green-600/80 border-white',
        bookCardHover: 'hover:bg-green-500/90 hover:border-white'
      };
    }

    // All other strategies = Black background with ORANGE inner windows
    return {
      bg: 'bg-gradient-to-br from-black via-gray-900 to-slate-900',
      border: 'border-white',
      glow: 'shadow-lg shadow-white/20',
      pulse: '',
      emoji: '💡',
      timerColor: 'text-white',
      infoBg: 'bg-black/40',
      bookCardBg: 'bg-orange-600/80 border-white',
      bookCardHover: 'hover:bg-orange-500/90 hover:border-white'
    };
  };

  const styles = getConfidenceStyles();

  // Calculate bottom position based on index (stack them up)
  const bottomPosition = position * 180 + 16; // 180px per notification + 16px base

  return (
    <div
      className={`
        ${styles.bg} ${styles.border} ${styles.glow} ${styles.pulse}
        fixed right-4 z-50 w-96 border-4 rounded-xl overflow-hidden
        transition-all duration-300 ease-out
        ${isExiting ? 'opacity-0 translate-x-full' : 'opacity-100 translate-x-0'}
      `}
      style={{ bottom: `${bottomPosition}px` }}
    >
      {/* Header - Strategy Name & Timer */}
      <div className="flex items-center justify-between bg-black/30 px-4 py-2 border-b-2 border-white/20">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{styles.emoji}</span>
          <div>
            <div className="font-bold text-white text-sm">{alert.strategy_name}</div>
            {alert.home_team && alert.away_team && (
              <div className="text-xs text-white/80 font-semibold mt-0.5">
                {alert.away_team} @ {alert.home_team}
              </div>
            )}
            <div className="text-xs text-white/70 uppercase">{alert.confidence} Confidence</div>
          </div>
        </div>

        {/* Time Decay Counter */}
        <div className="text-right">
          <div className={`font-mono font-bold text-lg ${styles.timerColor}`}>
            {formatTimeElapsed()}
          </div>
          <div className="text-xs text-white/60">Age</div>
        </div>
      </div>

      {/* Alert Body */}
      <div className="p-4 space-y-3">
        {/* Trigger */}
        <div className={`${styles.infoBg} rounded-lg p-3 border border-white/20`}>
          <div className="text-xs font-semibold text-white/70 mb-1">TRIGGER</div>
          <div className="text-sm text-white font-medium leading-tight">
            {alert.trigger}
          </div>
        </div>

        {/* Recommendation */}
        <div className={`${styles.infoBg} rounded-lg p-3 border border-white/20`}>
          <div className="text-xs font-semibold text-white/70 mb-1">RECOMMENDATION</div>
          <div className="text-sm text-white font-bold">
            {alert.recommendation}
          </div>
        </div>

        {/* Bet Options - Books with Icons (CLICKABLE) */}
        {alert.bet_options && alert.bet_options.length > 0 && (
          <div className="space-y-2">
            <div className="text-xs font-semibold text-white/70">BOOKS & ODDS (Click to Open)</div>
            {alert.bet_options.slice(0, 3).map((option, idx) => {
              const bookmakerInfo = getBookmaker(option.bookmaker);
              return (
                <button
                  key={idx}
                  onClick={() => {
                    // Open sportsbook in new tab
                    openSportsbook(`https://${bookmakerInfo.domain}`, bookmakerInfo.name);

                    // Also open bet slip with pre-filled data
                    openBetSlip({
                      sport: alert.sport,
                      homeTeam: alert.home_team,
                      awayTeam: alert.away_team,
                      gameId: alert.game_id,
                      betType: option.market_type === 'totals' ? 'total' :
                               option.market_type === 'spreads' ? 'spread' :
                               option.market_type === 'h2h' ? 'moneyline' : 'total',
                      betSide: option.bet_side,
                      line: option.line,
                      odds: option.odds,
                      bookmaker: option.bookmaker,
                      confidence: alert.confidence,
                      edgePercent: alert.edge_percentage,
                      strategy: alert.strategy_name
                    });
                  }}
                  className={`w-full rounded-lg p-2 border-2 flex items-center justify-between transition-all cursor-pointer ${styles.bookCardBg} ${styles.bookCardHover}`}
                >
                  <div className="flex items-center gap-2">
                    {/* Bookmaker Logo */}
                    {option.bookmaker_logo && (
                      <img
                        src={option.bookmaker_logo}
                        alt={option.bookmaker_title || option.bookmaker}
                        className="w-8 h-8 rounded"
                        onError={(e) => {
                          // Hide image if it fails to load
                          (e.target as HTMLImageElement).style.display = 'none';
                        }}
                      />
                    )}
                    <div className="flex flex-col text-left">
                      <div className="text-white font-semibold text-sm">
                        {option.bookmaker_title || option.bookmaker}
                      </div>
                      <div className="text-white/70 text-xs">{option.label}</div>
                    </div>
                  </div>
                  <div className="text-white font-bold text-sm">
                    {typeof option.odds === 'number'
                      ? (option.odds > 0 ? `+${Math.round(option.odds)}` : Math.round(option.odds))
                      : option.odds}
                  </div>
                </button>
              );
            })}
          </div>
        )}

        {/* Stats Row */}
        <div className="grid grid-cols-3 gap-2 pt-2 border-t border-white/20">
          <div className="text-center">
            <div className="text-white font-bold text-lg">+{alert.edge_percentage.toFixed(1)}%</div>
            <div className="text-white/60 text-xs font-semibold">Edge</div>
          </div>
          <div className="text-center">
            <div className="text-white font-bold text-lg">+{alert.expected_roi.toFixed(1)}%</div>
            <div className="text-white/60 text-xs font-semibold">ROI</div>
          </div>
          <div className="text-center">
            <div className="text-white font-bold text-lg">{alert.stake_recommendation.toFixed(1)}u</div>
            <div className="text-white/60 text-xs font-semibold">Stake</div>
          </div>
        </div>

        {/* Win Probability */}
        <div className={`${styles.infoBg} rounded-lg p-2 border border-white/20`}>
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-white/70">Win Probability</span>
            <span className="text-white font-bold">{(alert.win_probability * 100).toFixed(1)}%</span>
          </div>
          <div className="w-full bg-white/20 rounded-full h-2 mt-1">
            <div
              className="bg-green-400 h-2 rounded-full transition-all duration-500"
              style={{ width: `${alert.win_probability * 100}%` }}
            />
          </div>
        </div>

        {/* Expiration Warning */}
        {alert.expires_in && alert.expires_in < 300 && (
          <div className="bg-red-500/20 border border-red-400 rounded-lg p-2 text-center">
            <div className="text-red-200 text-xs font-bold">
              ⏱️ Expires in {Math.floor(alert.expires_in / 60)}:{(alert.expires_in % 60).toString().padStart(2, '0')}
            </div>
          </div>
        )}
      </div>

      {/* Close Button */}
      <button
        onClick={handleDismiss}
        className="absolute top-2 right-2 text-white/60 hover:text-white transition-colors text-xl font-bold w-6 h-6 flex items-center justify-between"
      >
        ×
      </button>
    </div>
  );
}
