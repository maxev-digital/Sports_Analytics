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

  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    if (!imgError) {
      // First error: try fallback favicon
      e.currentTarget.src = bookmaker.logoFallback;
      setImgError(true);
    } else {
      // Second error: show placeholder
      e.currentTarget.style.display = 'none';
    }
  };

  if (showName) {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        <img
          src={bookmaker.logo}
          alt={bookmaker.name}
          className={`${sizeClasses[size]} object-contain rounded`}
          onError={handleImageError}
        />
        <span className="text-sm font-semibold text-slate-100">
          {bookmaker.name}
        </span>
      </div>
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
