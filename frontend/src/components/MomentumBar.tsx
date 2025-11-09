import React from 'react';

interface MomentumBarProps {
  homeTeam: string;
  awayTeam: string;
  homeMomentum: number;  // -100 to 100
  awayMomentum: number;  // -100 to 100
  homeColor?: string;    // Team primary color
  awayColor?: string;    // Team primary color
}

/**
 * MomentumBar component displays a visual representation of game momentum
 *
 * The bar shows which team has momentum:
 * - Shifts left when away team has momentum (RED)
 * - Shifts right when home team has momentum (GREEN)
 * - Shows team colors to make it instantly recognizable
 */
export const MomentumBar: React.FC<MomentumBarProps> = ({
  homeTeam,
  awayTeam,
  homeMomentum,
  awayMomentum,
  homeColor,
  awayColor,
}) => {
  // Backend sends momentum as -100 to +100 scale
  // Positive = team has momentum, Negative = losing momentum, 0 = neutral
  // We need to convert to bar percentages

  // Convert -100/+100 scale to 0-100 percentages
  // If home = +50 and away = -50, convert to: home = 75%, away = 25%
  // Formula: (momentum + 100) / 2 = percentage (0-100)

  const homeNormalized = (homeMomentum + 100) / 2;  // -100 to +100 → 0 to 100
  const awayNormalized = (awayMomentum + 100) / 2;  // -100 to +100 → 0 to 100

  // Calculate bar percentages based on normalized values
  const total = homeNormalized + awayNormalized;
  const homePercentage = total > 0 ? (homeNormalized / total) * 100 : 50;
  const awayPercentage = 100 - homePercentage;

  // DEBUG: Log momentum values
  console.log('🎯 MomentumBar DEBUG:', {
    homeTeam,
    awayTeam,
    'Raw homeMomentum (-100 to +100)': homeMomentum,
    'Raw awayMomentum (-100 to +100)': awayMomentum,
    'Normalized home (0-100)': homeNormalized.toFixed(1),
    'Normalized away (0-100)': awayNormalized.toFixed(1),
    homePercentage: homePercentage.toFixed(1) + '%',
    awayPercentage: awayPercentage.toFixed(1) + '%'
  });

  // Determine which team is dominant
  const homeIsDominant = homePercentage > 50;
  const awayIsDominant = awayPercentage > 50;

  // Use gradient colors that pulse/shift based on momentum
  const finalHomeColor = homeIsDominant ? '#10b981' : '#059669'; // Brighter green when dominant
  const finalAwayColor = awayIsDominant ? '#dc2626' : '#b91c1c';  // Brighter red when dominant

  // Determine momentum label based on percentage difference
  const getMomentumLabel = (percentage: number): string => {
    const diff = Math.abs(percentage - 50);  // Distance from 50% (neutral)
    if (diff > 30) return 'DOMINANT';      // 80%+ or 20%- is dominant
    if (diff > 20) return 'STRONG';        // 70%+ or 30%- is strong
    if (diff > 10) return 'MODERATE';      // 60%+ or 40%- is moderate
    if (diff > 5) return 'SLIGHT';         // 55%+ or 45%- is slight
    return 'EVEN';
  };

  const momentumLabel = homePercentage > 50
    ? `${getMomentumLabel(homePercentage)} ${homeTeam}`
    : homePercentage < 50
    ? `${getMomentumLabel(awayPercentage)} ${awayTeam}`
    : 'NEUTRAL';

  return (
    <div className="momentum-bar-container">
      <div className="momentum-header">
        <span className="momentum-label text-xs font-medium text-gray-500 dark:text-gray-400">
          MOMENTUM: {momentumLabel}
        </span>
      </div>

      <div className="momentum-bar-wrapper relative w-full h-8 bg-gray-200 dark:bg-gray-700 rounded-lg overflow-hidden mt-2">
        {/* Away team side (left) */}
        <div
          className={`absolute left-0 top-0 h-full flex items-center justify-start px-2 text-white font-semibold text-sm transition-all duration-700 ease-in-out ${awayIsDominant && awayPercentage > 65 ? 'animate-pulse' : ''}`}
          style={{
            width: `${awayPercentage}%`,
            backgroundColor: finalAwayColor,
            opacity: awayPercentage > 10 ? (awayIsDominant ? 1 : 0.7) : 0.3,
            boxShadow: awayIsDominant ? '0 0 15px rgba(220, 38, 38, 0.5)' : 'none',
          }}
        >
          {awayPercentage > 20 && (
            <span className="text-white drop-shadow-md font-bold">{awayTeam}</span>
          )}
        </div>

        {/* Home team side (right) */}
        <div
          className={`absolute right-0 top-0 h-full flex items-center justify-end px-2 text-white font-semibold text-sm transition-all duration-700 ease-in-out ${homeIsDominant && homePercentage > 65 ? 'animate-pulse' : ''}`}
          style={{
            width: `${homePercentage}%`,
            backgroundColor: finalHomeColor,
            opacity: homePercentage > 10 ? (homeIsDominant ? 1 : 0.7) : 0.3,
            boxShadow: homeIsDominant ? '0 0 15px rgba(16, 185, 129, 0.5)' : 'none',
          }}
        >
          {homePercentage > 20 && (
            <span className="text-white drop-shadow-md font-bold">{homeTeam}</span>
          )}
        </div>

        {/* Center line indicator */}
        <div className="absolute left-1/2 top-0 w-0.5 h-full bg-white opacity-40 transform -translate-x-1/2" />
      </div>

      {/* Momentum values */}
      <div className="momentum-values flex justify-between mt-1 text-xs text-gray-500 dark:text-gray-400">
        <span>{awayMomentum > 0 ? '+' : ''}{Math.round(awayMomentum)}</span>
        <span>{homeMomentum > 0 ? '+' : ''}{Math.round(homeMomentum)}</span>
      </div>
    </div>
  );
};
