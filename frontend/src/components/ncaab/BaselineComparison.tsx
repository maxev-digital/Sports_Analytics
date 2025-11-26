import React from 'react';
import { uiEmojis } from '../../utils/sportDetection';

interface ShootingVariance {
  fg_pct: number;
  fg_variance: number;
  three_pct: number;
  three_variance: number;
  ft_pct: number;
  ft_variance: number;
  is_hot_fg: boolean;
  is_cold_fg: boolean;
  is_hot_three: boolean;
  is_cold_three: boolean;
}

interface PaceVariance {
  live_possessions: number;
  expected_possessions: number;
  pace_variance: number;
  is_faster: boolean;
  is_slower: boolean;
  projected_total_possessions: number;
}

interface EfficiencyVariance {
  live_efficiency: number;
  season_efficiency: number;
  efficiency_variance: number;
  is_underperforming: boolean;
  is_overperforming: boolean;
}

interface EmojiIndicator {
  emoji: string;
  level: string;
  count: number;
}

interface RegressionOpportunity {
  has_regression_opportunity: boolean;
  confidence: string;
  reason: string;
  expected_regression_points: number;
}

interface TeamAnalysis {
  team_name: string;
  team_abv: string;
  possessions: number;
  shooting: ShootingVariance;
  pace: PaceVariance;
  efficiency: EfficiencyVariance;
  regression: RegressionOpportunity;
  shooting_emoji: EmojiIndicator;
  pace_emoji: EmojiIndicator;
  period: number;
  clock: string;
}

interface BaselineComparisonProps {
  homeAnalysis: TeamAnalysis;
  awayAnalysis: TeamAnalysis;
  textLabel: string;
  textValue: string;
  textMuted: string;
  textSecondary: string;
  dividerClass: string;
}
const BaselineComparison: React.FC<BaselineComparisonProps> = ({
  homeAnalysis,
  awayAnalysis,
  textLabel,
  textValue,
  textMuted,
  textSecondary,
  dividerClass,
}) => {
  const getEmojiSrc = (emojiIndicator: EmojiIndicator, type: 'shooting' | 'pace') => {
    if (type === 'shooting') {
      if (emojiIndicator.emoji.includes('FIRE')) return uiEmojis.fire;
      if (emojiIndicator.emoji.includes('SNOW')) return uiEmojis.snowflake;
      return uiEmojis.checkMark;
    } else {
      if (emojiIndicator.emoji.includes('LIGHTNING')) return uiEmojis.lightning;
      if (emojiIndicator.emoji.includes('TURTLE')) return uiEmojis.turtle;
      return uiEmojis.checkMark;
    }
  };

  const renderTeamAnalysis = (analysis: TeamAnalysis) => (
    <div className="space-y-2">
      <div className={'text-sm font-bold border-b border-slate-800/40 pb-1 ' + textValue}>
        {analysis.team_abv}
      </div>
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <span className={textLabel}>3PT:</span>
          <span className={'flex items-center gap-2 ' + textValue}>
            <span className="font-mono">{analysis.shooting.three_pct != null ? analysis.shooting.three_pct.toFixed(1) : '0.0'}%</span>
            <span className={'text-xs ' + (analysis.shooting.three_variance > 0 ? 'text-green-400' : 'text-red-400')}>
              ({analysis.shooting.three_variance > 0 ? '+' : ''}{analysis.shooting.three_variance != null ? analysis.shooting.three_variance.toFixed(1) : '0.0'}%)
            </span>
            {analysis.shooting_emoji.count > 0 && (
              <div className="flex gap-0.5">
                {Array(analysis.shooting_emoji.count).fill(0).map((_, i) => (
                  <img 
                    key={i}
                    src={getEmojiSrc(analysis.shooting_emoji, 'shooting')}
                    alt={analysis.shooting_emoji.level}
                    className="w-4 h-4"
                  />
                ))}
              </div>
            )}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className={textLabel}>FG:</span>
          <span className={'flex items-center gap-2 ' + textValue}>
            <span className="font-mono">{analysis.shooting.fg_pct != null ? analysis.shooting.fg_pct.toFixed(1) : '0.0'}%</span>
            <span className={'text-xs ' + (analysis.shooting.fg_variance > 0 ? 'text-green-400' : 'text-red-400')}>
              ({analysis.shooting.fg_variance > 0 ? '+' : ''}{analysis.shooting.fg_variance != null ? analysis.shooting.fg_variance.toFixed(1) : '0.0'}%)
            </span>
          </span>
        </div>
      </div>
      <div className="flex items-center justify-between">
        <span className={textLabel}>Pace:</span>
        <span className={'flex items-center gap-2 ' + textValue}>
          <span className="font-mono">{analysis.pace.live_possessions != null ? analysis.pace.live_possessions.toFixed(0) : '0'} poss</span>
          <span className={'text-xs ' + textMuted}>
            vs {analysis.pace.expected_possessions != null ? analysis.pace.expected_possessions.toFixed(0) : '0'}
          </span>
          {analysis.pace_emoji.count > 0 && (
            <div className="flex gap-0.5">
              {Array(analysis.pace_emoji.count).fill(0).map((_, i) => (
                <img 
                  key={i}
                  src={getEmojiSrc(analysis.pace_emoji, 'pace')}
                  alt={analysis.pace_emoji.level}
                  className="w-4 h-4"
                />
              ))}
            </div>
          )}
        </span>
      </div>
      <div className="flex items-center justify-between">
        <span className={textLabel}>Off Eff:</span>
        <span className={'flex items-center gap-2 ' + textValue}>
          <span className="font-mono">{analysis.efficiency.live_efficiency != null ? analysis.efficiency.live_efficiency.toFixed(1) : '0.0'}</span>
          <span className={'text-xs ' + (analysis.efficiency.efficiency_variance > 0 ? 'text-green-400' : 'text-red-400')}>
            ({analysis.efficiency.efficiency_variance > 0 ? '+' : ''}{analysis.efficiency.efficiency_variance != null ? analysis.efficiency.efficiency_variance.toFixed(1) : '0.0'})
          </span>
        </span>
      </div>
    </div>
  );

  const hasRegression = homeAnalysis.regression.has_regression_opportunity || 
                       awayAnalysis.regression.has_regression_opportunity;

  return (
    <div className={dividerClass + ' mt-2 pt-2 space-y-3'}>
      <div className={'text-lg font-bold mb-2 ' + textSecondary}>
        LIVE VS BASELINE
      </div>
      {renderTeamAnalysis(homeAnalysis)}
      {renderTeamAnalysis(awayAnalysis)}
      {hasRegression && (
        <div className="mt-3 p-3 rounded-lg bg-gradient-to-r from-cyan-900/50 to-blue-900/50 border border-cyan-800">
          <div className="flex items-start gap-2">
            <img src={uiEmojis.snowflake} alt="Regression" className="w-5 h-5 mt-0.5" />
            <div className="flex-1">
              <div className="text-xs font-bold text-cyan-300 mb-1">REGRESSION OPPORTUNITY</div>
              {homeAnalysis.regression.has_regression_opportunity && (
                <div className={'text-xs ' + textSecondary}>
                  {homeAnalysis.team_abv}: {homeAnalysis.regression.reason}
                </div>
              )}
              {awayAnalysis.regression.has_regression_opportunity && (
                <div className={'text-xs mt-1 ' + textSecondary}>
                  {awayAnalysis.team_abv}: {awayAnalysis.regression.reason}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BaselineComparison;
