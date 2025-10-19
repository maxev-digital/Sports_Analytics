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
 * - Shifts left when away team has momentum
 * - Shifts right when home team has momentum
 * - Shows team colors to make it instantly recognizable
 */
export const MomentumBar: React.FC<MomentumBarProps> = ({
  homeTeam,
  awayTeam,
  homeMomentum,
  awayMomentum,
  homeColor = '#1e40af', // Default blue for home
  awayColor = '#dc2626',  // Default red for away
}) => {
  // Normalize momentum to 0-100 scale
  // If home has +50 momentum and away has -50, home gets 75% of bar
  const totalMomentum = Math.abs(homeMomentum) + Math.abs(awayMomentum);

  // Calculate percentage for each team (0-100)
  let homePercentage = 50;  // Default: neutral
  if (totalMomentum > 0) {
    homePercentage = ((homeMomentum + 100) / 200) * 100;
  }

  const awayPercentage = 100 - homePercentage;

  // Determine momentum label
  const getMomentumLabel = (momentum: number): string => {
    const absMomentum = Math.abs(momentum);
    if (absMomentum > 70) return 'DOMINANT';
    if (absMomentum > 50) return 'STRONG';
    if (absMomentum > 30) return 'MODERATE';
    if (absMomentum > 10) return 'SLIGHT';
    return 'EVEN';
  };

  const momentumLabel = homeMomentum > awayMomentum
    ? `${getMomentumLabel(homeMomentum)} ${homeTeam}`
    : homeMomentum < awayMomentum
    ? `${getMomentumLabel(awayMomentum)} ${awayTeam}`
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
          className="absolute left-0 top-0 h-full flex items-center justify-start px-2 text-white font-semibold text-sm transition-all duration-500 ease-in-out"
          style={{
            width: `${awayPercentage}%`,
            backgroundColor: awayColor,
            opacity: awayPercentage > 10 ? 1 : 0.5,
          }}
        >
          {awayPercentage > 20 && (
            <span className="text-white drop-shadow-md">{awayTeam}</span>
          )}
        </div>

        {/* Home team side (right) */}
        <div
          className="absolute right-0 top-0 h-full flex items-center justify-end px-2 text-white font-semibold text-sm transition-all duration-500 ease-in-out"
          style={{
            width: `${homePercentage}%`,
            backgroundColor: homeColor,
            opacity: homePercentage > 10 ? 1 : 0.5,
          }}
        >
          {homePercentage > 20 && (
            <span className="text-white drop-shadow-md">{homeTeam}</span>
          )}
        </div>

        {/* Center line indicator */}
        <div className="absolute left-1/2 top-0 w-0.5 h-full bg-white opacity-30 transform -translate-x-1/2" />
      </div>

      {/* Momentum values */}
      <div className="momentum-values flex justify-between mt-1 text-xs text-gray-500 dark:text-gray-400">
        <span>{awayMomentum > 0 ? '+' : ''}{Math.round(awayMomentum)}</span>
        <span>{homeMomentum > 0 ? '+' : ''}{Math.round(homeMomentum)}</span>
      </div>
    </div>
  );
};
