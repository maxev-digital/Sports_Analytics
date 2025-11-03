/**
 * BookmakerLogo Component
 * Displays bookmaker logos with automatic fallback to favicon service
 *
 * Usage:
 *   <BookmakerLogo bookmakerKey="draftkings" size="md" />
 */

import React, { useState } from 'react';
import { getBookmaker } from '../data/bookmakers';

interface BookmakerLogoProps {
  bookmakerKey: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  showName?: boolean;
}

const sizeClasses = {
  sm: 'w-6 h-6',
  md: 'w-8 h-8',
  lg: 'w-12 h-12',
  xl: 'w-16 h-16',
};

export const BookmakerLogo: React.FC<BookmakerLogoProps> = ({
  bookmakerKey,
  size = 'md',
  className = '',
  showName = false,
}) => {
  const bookmaker = getBookmaker(bookmakerKey);
  const [imgError, setImgError] = useState(false);

  if (!bookmaker) {
    return (
      <div className={`${sizeClasses[size]} bg-slate-700 rounded flex items-center justify-center ${className}`}>
        <span className="text-xs text-slate-400">?</span>
      </div>
    );
  }

  // Get colored badge background based on bookmaker key
  const getBadgeColors = (key: string) => {
    const colorMap: Record<string, { bg: string; text: string }> = {
      'draftkings': { bg: 'bg-green-900', text: 'text-green-200' },
      'fanduel': { bg: 'bg-blue-900', text: 'text-blue-200' },
      'betmgm': { bg: 'bg-yellow-900', text: 'text-yellow-200' },
      'caesars': { bg: 'bg-purple-900', text: 'text-purple-200' },
      'betrivers': { bg: 'bg-cyan-900', text: 'text-cyan-200' },
      'bovada': { bg: 'bg-red-900', text: 'text-red-200' },
      'betonlineag': { bg: 'bg-orange-900', text: 'text-orange-200' },
      'mybookieag': { bg: 'bg-pink-900', text: 'text-pink-200' },
      'betus': { bg: 'bg-indigo-900', text: 'text-indigo-200' },
      'lowvig': { bg: 'bg-teal-900', text: 'text-teal-200' },
    };
    return colorMap[key] || { bg: 'bg-slate-800', text: 'text-slate-200' };
  };

  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    if (!imgError) {
      // First error: try fallback favicon
      e.currentTarget.src = bookmaker.logoFallback;
      setImgError(true);
    } else {
      // Second error: show colored badge
      setImgError(true);
      e.currentTarget.style.display = 'none';
    }
  };

  const shortName = bookmaker.name.substring(0, 3).toUpperCase();
  const badgeColors = getBadgeColors(bookmakerKey);

  if (showName) {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        {imgError ? (
          <span className={`${sizeClasses[size]} flex items-center justify-center rounded px-1 py-0.5 font-bold text-xs ${badgeColors.bg} ${badgeColors.text}`}>
            {shortName}
          </span>
        ) : (
          <img
            src={bookmaker.logo}
            alt={bookmaker.name}
            className={`${sizeClasses[size]} object-contain rounded`}
            onError={handleImageError}
          />
        )}
        <span className="text-sm font-semibold text-slate-100">
          {bookmaker.name}
        </span>
      </div>
    );
  }

  if (imgError) {
    return (
      <span className={`${sizeClasses[size]} flex items-center justify-center rounded px-1 py-0.5 font-bold text-xs ${badgeColors.bg} ${badgeColors.text} ${className}`} title={bookmaker.name}>
        {shortName}
      </span>
    );
  }

  return (
    <img
      src={bookmaker.logo}
      alt={bookmaker.name}
      title={bookmaker.name}
      className={`${sizeClasses[size]} object-contain rounded ${className}`}
      onError={handleImageError}
    />
  );
};

/**
 * BookmakerBadge Component
 * Shows bookmaker logo with name in a badge format
 */
export const BookmakerBadge: React.FC<{
  bookmakerKey: string;
  className?: string;
}> = ({ bookmakerKey, className = '' }) => {
  const bookmaker = getBookmaker(bookmakerKey);

  if (!bookmaker) return null;

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg ${className}`}>
      <BookmakerLogo bookmakerKey={bookmakerKey} size="sm" />
      <span className="text-xs font-semibold text-slate-200">
        {bookmaker.name}
      </span>
    </div>
  );
};

/**
 * BookmakerLink Component
 * Clickable logo that opens bookmaker website
 */
export const BookmakerLink: React.FC<{
  bookmakerKey: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}> = ({ bookmakerKey, size = 'md', className = '' }) => {
  const bookmaker = getBookmaker(bookmakerKey);

  if (!bookmaker) return null;

  return (
    <a
      href={bookmaker.url}
      target="_blank"
      rel="noopener noreferrer"
      className={`inline-block hover:opacity-80 transition-opacity ${className}`}
      title={`Visit ${bookmaker.name}`}
    >
      <BookmakerLogo bookmakerKey={bookmakerKey} size={size} />
    </a>
  );
};

export default BookmakerLogo;
