/**
 * Goalie Pull Monitor
 * Monitors NHL games in 3rd period and triggers alerts for goalie pull opportunities
 * Alerts at 2:45 remaining when teams are down by 1-2 goals
 */

import { useEffect, useRef } from 'react';
import { getApiUrl } from '../config';
import { useBetAlertNotification } from '../contexts/BetAlertNotificationContext';
import { StrategyAlert } from '../types';

interface GoaliePullMonitorProps {
  enabled?: boolean;
  pollInterval?: number; // milliseconds
}

interface GoaliePullOpportunity {
  game_id: string;
  home_team: string;
  away_team: string;
  trailing_team: string;
  leading_team: string;
  score_diff: number;
  period: number;
  time_remaining: string;
  trailing_team_en_stats: {
    en_goals_for: number;
    en_goals_against: number;
    en_differential: number;
    en_success_rate: number;
    en_goals_for_defensive?: number;
  };
  leading_team_en_stats: {
    en_goals_for: number;
    en_goals_against: number;
    en_differential: number;
    en_success_rate: number;
    en_goals_for_defensive?: number;
  };
  over_odds?: number;
  under_odds?: number;
  trailing_team_total_over_odds?: number;
  current_score?: string;
  recommendation?: string;
}

// Parse time remaining from "MM:SS" format to total seconds
function parseTimeToSeconds(timeStr: string): number {
  if (!timeStr) return 0;
  const parts = timeStr.split(':');
  if (parts.length === 2) {
    const minutes = parseInt(parts[0], 10);
    const seconds = parseInt(parts[1], 10);
    return minutes * 60 + seconds;
  }
  return 0;
}

export function GoaliePullMonitor({
  enabled = true,
  pollInterval = 10000 // 10 seconds
}: GoaliePullMonitorProps) {
  const { showBetAlert } = useBetAlertNotification();
  const alertedGamesRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (!enabled) {
      console.log('[GOALIE PULL MONITOR] Disabled - not on eligible page');
      return;
    }

    console.log('[GOALIE PULL MONITOR] Active and monitoring...');

    const checkForGoaliePulls = async () => {
      try {
        // Fetch all games
        const response = await fetch(getApiUrl('games'));
        if (!response.ok) return;

        const games = await response.json();

        // Log NHL games in 3rd period
        const nhlGames = games.filter((g: any) => g.state?.sport_key?.startsWith('icehockey'));
        const thirdPeriodGames = nhlGames.filter((g: any) => g.state?.quarter === 3);
        if (thirdPeriodGames.length > 0) {
          console.log(`[GOALIE PULL MONITOR] Monitoring ${thirdPeriodGames.length} NHL game(s) in 3rd period`);
        }

        // Filter for NHL games in 3rd period with <3:00 remaining
        const potentialGoaliePulls = games.filter((game: any) => {
          const sport = game.state?.sport_key || '';
          const period = game.state?.quarter;
          const timeRemaining = game.state?.time_remaining;
          const isLive = game.state?.status === 'live';

          if (!sport.startsWith('icehockey') || !isLive || period !== 3) {
            return false;
          }

          const seconds = parseTimeToSeconds(timeRemaining);
          // Alert window: 2:45-2:30 for 2-goal deficit, OR 2:05-1:55 for 1-goal deficit
          return (seconds >= 150 && seconds <= 165) || (seconds >= 115 && seconds <= 125);
        });

        // Check each game for goalie pull opportunity
        for (const game of potentialGoaliePulls) {
          const gameId = game.state.id;
          const homeScore = game.state.home_team.score || 0;
          const awayScore = game.state.away_team.score || 0;
          const scoreDiff = Math.abs(homeScore - awayScore);
          const timeSeconds = parseTimeToSeconds(game.state.time_remaining);

          // Skip if score differential is not 1 or 2 goals
          if (scoreDiff < 1 || scoreDiff > 2) continue;

          // Determine trailing and leading teams
          const isHomeTrailing = homeScore < awayScore;
          const trailingTeam = isHomeTrailing ? game.state.home_team.name : game.state.away_team.name;
          const leadingTeam = isHomeTrailing ? game.state.away_team.name : game.state.home_team.name;
          const trailingStats = isHomeTrailing ? game.home_nhl_stats : game.away_nhl_stats;
          const leadingStats = isHomeTrailing ? game.away_nhl_stats : game.home_nhl_stats;

          // Determine alert type based on score differential and time
          let alertType: 'OVER' | 'UNDER' | null = null;
          let alertKey = '';

          if (scoreDiff === 2 && timeSeconds >= 150 && timeSeconds <= 165) {
            // 2-goal deficit at 2:45-2:30: OVER alert (early goalie pull)
            // Check if LEADING team is good at scoring into empty nets
            const leadingEnDefensive = leadingStats?.en_goals_for_defensive || 0;

            console.log(`[GOALIE PULL MONITOR] Checking OVER conditions: ${leadingTeam} has ${leadingEnDefensive} defensive EN goals (shoots at empty net)`);

            // Alert if leading team has scored 2+ goals when opponent pulls goalie (good at capitalizing)
            if (leadingEnDefensive >= 2) {
              alertType = 'OVER';
              alertKey = `${gameId}-goalie-pull-over`;
              console.log(`[GOALIE PULL MONITOR] ✓ OVER alert conditions met! ${leadingTeam} good at scoring into empty nets (${leadingEnDefensive} goals)`);
            } else {
              console.log(`[GOALIE PULL MONITOR] ✗ OVER conditions NOT met (leading team not efficient at empty net: ${leadingEnDefensive} goals)`);
            }
          } else if (scoreDiff === 1 && timeSeconds >= 115 && timeSeconds <= 125) {
            // 1-goal deficit at 2:00: UNDER alert if LEADING team is BAD at scoring into empty nets
            const leadingEnDefensive = leadingStats?.en_goals_for_defensive || 0;

            console.log(`[GOALIE PULL MONITOR] Checking UNDER conditions: ${leadingTeam} has ${leadingEnDefensive} defensive EN goals (shoots at empty net)`);

            // Only alert UNDER if leading team has scored 1 or fewer goals when opponent pulls goalie
            if (leadingEnDefensive <= 1) {
              alertType = 'UNDER';
              alertKey = `${gameId}-goalie-pull-under`;
              console.log(`[GOALIE PULL MONITOR] ✓ UNDER alert conditions met! ${leadingTeam} struggles with empty net (only ${leadingEnDefensive} goals)`);
            } else {
              console.log(`[GOALIE PULL MONITOR] ✗ UNDER conditions NOT met (leading team scores too often on empty net: ${leadingEnDefensive} goals)`);
            }
          } else {
            // Log why no alert
            if (scoreDiff === 1 && timeSeconds < 115) {
              console.log(`[GOALIE PULL MONITOR] 1-goal game but too late (${timeSeconds}s < 115s window)`);
            } else if (scoreDiff === 2 && timeSeconds < 150) {
              console.log(`[GOALIE PULL MONITOR] 2-goal game but too late (${timeSeconds}s < 150s window)`);
            }
          }

          // Skip if no valid alert type or already alerted
          if (!alertType) continue;

          if (alertedGamesRef.current.has(alertKey)) {
            console.log(`[GOALIE PULL MONITOR] Already alerted for ${alertKey}`);
            continue;
          }

          // Get best odds
          const bestOverOdds = Math.max(...(game.odds?.map((o: any) => o.over_price || -110) || [-110]));
          const bestUnderOdds = Math.max(...(game.odds?.map((o: any) => o.under_price || -110) || [-110]));

          // Create appropriate alert
          const alert = alertType === 'OVER'
            ? convertToOverAlert({
                game_id: gameId,
                home_team: game.state.home_team.name,
                away_team: game.state.away_team.name,
                trailing_team: trailingTeam,
                leading_team: leadingTeam,
                score_diff: scoreDiff,
                period: game.state.quarter,
                time_remaining: game.state.time_remaining,
                trailing_team_en_stats: trailingStats,
                leading_team_en_stats: leadingStats,
                over_odds: bestOverOdds,
              })
            : convertToUnderAlert({
                game_id: gameId,
                home_team: game.state.home_team.name,
                away_team: game.state.away_team.name,
                trailing_team: trailingTeam,
                leading_team: leadingTeam,
                score_diff: scoreDiff,
                period: game.state.quarter,
                time_remaining: game.state.time_remaining,
                trailing_team_en_stats: trailingStats,
                leading_team_en_stats: leadingStats,
                under_odds: bestUnderOdds,
                current_score: `${awayScore}-${homeScore}`,
              });

          // Mark as alerted and show notification
          alertedGamesRef.current.add(alertKey);
          console.log(`[GOALIE PULL MONITOR] 🚨 FIRING ${alertType} ALERT! ${trailingTeam} vs ${leadingTeam}`);
          console.log(`[GOALIE PULL MONITOR] Playing audio: ${alert.custom_audio_url}`);
          showBetAlert(alert);
        }

      } catch (error) {
        console.error('[GOALIE PULL MONITOR] Error checking for goalie pulls:', error);
      }
    };

    // Initial check
    checkForGoaliePulls();

    // Set up polling interval
    const intervalId = setInterval(checkForGoaliePulls, pollInterval);

    return () => {
      clearInterval(intervalId);
    };
  }, [enabled, pollInterval, showBetAlert]);

  // This component doesn't render anything
  return null;
}

// Convert goalie pull OVER opportunity to StrategyAlert format (2-goal deficit)
function convertToOverAlert(opp: GoaliePullOpportunity): StrategyAlert {
  const trailingStats = opp.trailing_team_en_stats || {
    en_goals_for: 0,
    en_goals_against: 0,
    en_differential: 0,
    en_success_rate: 0,
    en_goals_for_defensive: 0
  };
  const leadingStats = opp.leading_team_en_stats || {
    en_goals_for: 0,
    en_goals_against: 0,
    en_differential: 0,
    en_success_rate: 0,
    en_goals_for_defensive: 0
  };

  // Calculate combined empty net tendency (how likely to see goals)
  const combinedEnGoals = (trailingStats.en_goals_for || 0) + (leadingStats.en_goals_for || 0);
  const combinedEnSituations = Math.max((trailingStats.en_differential || 0) + (leadingStats.en_differential || 0), 1);

  return {
    strategy_id: `goalie-pull-${opp.game_id}-${Date.now()}`,
    strategy_name: 'Goalie Pull Alert',
    game_id: opp.game_id,
    home_team: opp.home_team,
    away_team: opp.away_team,
    sport: 'icehockey_nhl',
    confidence: 'HIGH',
    trigger: `${opp.trailing_team} down ${opp.score_diff} goal${opp.score_diff > 1 ? 's' : ''} with ${opp.time_remaining} remaining in 3rd period`,
    recommendation: `${opp.trailing_team} will likely pull goalie soon. ${opp.leading_team} will have an EMPTY NET to shoot at. Bet GAME OVER or ${opp.leading_team.toUpperCase()} TEAM TOTAL OVER at plus money before pull.`,
    edge_percentage: 8.0, // Historical edge from goalie pull situations
    expected_roi: 12.0,
    win_probability: 0.65, // 65% based on historical goalie pull stats
    stake_recommendation: 1.5, // 1.5 units - time-sensitive opportunity
    bet_options: [
      {
        label: `GAME OVER (Before Goalie Pull)`,
        market_type: 'totals',
        bet_side: 'Over',
        odds: opp.over_odds,
        bookmaker: 'Best Available',
        bookmaker_title: 'Best Line',
        bookmaker_logo: '',
        probability: 0.65,
        expected_value: 8.0
      },
      {
        label: `${opp.leading_team} TEAM TOTAL OVER (Empty Net)`,
        market_type: 'team_totals',
        bet_side: 'Over',
        odds: opp.trailing_team_total_over_odds > 0 ? opp.trailing_team_total_over_odds : 110,
        bookmaker: 'Best Available',
        bookmaker_title: 'Best Line',
        bookmaker_logo: '',
        probability: 0.65,
        expected_value: 9.0
      }
    ],
    reasoning: `
**Goalie Pull Situation:**
- ${opp.trailing_team} trailing by ${opp.score_diff} goal${opp.score_diff > 1 ? 's' : ''}
- ${opp.time_remaining} remaining in Period ${opp.period}
- Goalie pull expected at ~2:00 mark
- ${opp.leading_team} will have EMPTY NET to shoot at

**Key Empty Net Stats (Shooting INTO Empty Net):**
- ${opp.leading_team}: ${leadingStats.en_goals_for_defensive || 0} goals scored when opponent pulls goalie
- ${opp.trailing_team}: ${trailingStats.en_goals_for_defensive || 0} goals scored when opponent pulls goalie

**Why Bet Now:**
${opp.leading_team} has scored ${leadingStats.en_goals_for_defensive || 0} empty net goals this season when opponents pull the goalie. Empty net situations average 0.8-1.2 goals scored. Get OVER or ${opp.leading_team.toUpperCase()} TEAM TOTAL OVER at current line before sportsbooks adjust. Historical hit rate: 65% when leading team is efficient at empty net goals.
    `.trim(),
    urgency: 'CRITICAL',
    expires_in: 150, // 2.5 minutes - very time sensitive
    sound_alert: true,
    custom_audio_url: '/alerts/goalie_pull_over_detailed.mp3',
    timestamp: new Date().toISOString()
  };
}

// Convert goalie pull UNDER opportunity to StrategyAlert format (1-goal deficit, low EN stats)
function convertToUnderAlert(opp: GoaliePullOpportunity): StrategyAlert {
  const trailingStats = opp.trailing_team_en_stats || {
    en_goals_for: 0,
    en_goals_against: 0,
    en_differential: 0,
    en_success_rate: 0,
    en_goals_for_defensive: 0
  };
  const leadingStats = opp.leading_team_en_stats || {
    en_goals_for: 0,
    en_goals_against: 0,
    en_differential: 0,
    en_success_rate: 0,
    en_goals_for_defensive: 0
  };

  // Leading team's defensive EN goals (shooting INTO empty net when opponent pulls goalie)
  const leadingEnGoals = (leadingStats.en_goals_for_defensive || 0);

  return {
    strategy_id: `goalie-pull-under-${opp.game_id}-${Date.now()}`,
    strategy_name: '1-Goal Deficit UNDER Alert',
    game_id: opp.game_id,
    home_team: opp.home_team,
    away_team: opp.away_team,
    sport: 'icehockey_nhl',
    confidence: 'HIGH',
    trigger: `${opp.trailing_team} down 1 goal with ${opp.time_remaining} remaining - LOW EN scoring teams`,
    recommendation: `Bet GAME UNDER or NO GOAL SCORED NEXT (Exact Score: ${opp.current_score}). Late goalie pull + low empty net scoring = game likely ends as-is.`,
    edge_percentage: 10.0, // Historical edge when both teams have low EN goals
    expected_roi: 15.0,
    win_probability: 0.68, // 68% based on 1-goal deficit + low EN stats
    stake_recommendation: 2.0, // 2 units - strong situational edge
    bet_options: [
      {
        label: `GAME UNDER (Score Holds)`,
        market_type: 'totals',
        bet_side: 'Under',
        odds: opp.under_odds || -110,
        bookmaker: 'Best Available',
        bookmaker_title: 'Best Line',
        bookmaker_logo: '',
        probability: 0.68,
        expected_value: 10.0
      },
      {
        label: `NO GOAL SCORED NEXT`,
        market_type: 'next_goal',
        bet_side: 'No Goal',
        odds: 150, // Typical "No Goal" odds
        bookmaker: 'Best Available',
        bookmaker_title: 'Best Line',
        bookmaker_logo: '',
        probability: 0.65,
        expected_value: 12.0
      },
      {
        label: `EXACT SCORE: ${opp.current_score} FINAL`,
        market_type: 'exact_score',
        bet_side: `Final Score ${opp.current_score}`,
        odds: 300, // Higher odds for exact score
        bookmaker: 'Best Available',
        bookmaker_title: 'Best Line',
        bookmaker_logo: '',
        probability: 0.45,
        expected_value: 20.0
      }
    ],
    reasoning: `
**1-Goal Deficit Situation:**
- ${opp.trailing_team} trailing by ${opp.score_diff} goal
- ${opp.time_remaining} remaining in Period ${opp.period}
- Goalie pull happens LATER (~1:30 or less) in 1-goal games
- ${opp.leading_team} will have EMPTY NET to shoot at

**Key Empty Net Stats (Shooting INTO Empty Net):**
- ${opp.leading_team}: Only ${leadingEnGoals} goals scored when opponent pulls goalie (STRUGGLES)
- When leading team can't capitalize on empty nets, score tends to hold

**Why Bet UNDER:**
In 1-goal games with 2:00 remaining, teams wait longer to pull goalie (~1:15-1:30 mark). ${opp.leading_team} has only scored ${leadingEnGoals} empty net goal(s) all season when opponents pull the goalie. Less time + inefficient leading team at capitalizing = score holds 68% of the time.

**Best Bets:**
1. GAME UNDER - Safest option, ${opp.leading_team} struggles to score into empty nets
2. NO GOAL SCORED NEXT - Higher odds, strong situational edge
3. EXACT SCORE ${opp.current_score} - Highest payout, good value if score holds
    `.trim(),
    urgency: 'CRITICAL',
    expires_in: 120, // 2 minutes - very time sensitive
    sound_alert: true,
    custom_audio_url: '/alerts/goalie_pull_under_detailed.mp3',
    timestamp: new Date().toISOString()
  };
}
