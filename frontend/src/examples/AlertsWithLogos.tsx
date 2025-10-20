/**
 * Example: How to integrate BookmakerLogo into your Alerts page
 *
 * This shows how to replace the current bookmaker display in Alerts.tsx
 * with the new BookmakerLogo component
 */

import React from 'react';
import { BookmakerLogo, BookmakerBadge, BookmakerLink } from '../components/BookmakerLogo';

// ============================================
// EXAMPLE 1: Replace bookmaker text with logo badges
// ============================================

// Before (in your Alerts.tsx):
/*
<div className="text-sm text-slate-400 mb-2">Book A: {alert.book_a}</div>
<div className="text-sm text-slate-400 mb-2">Book B: {alert.book_b}</div>
*/

// After:
function ArbitrageAlertCardExample({ alert }: { alert: any }) {
  return (
    <div className="bg-green-900 border-2 border-green-700 rounded p-6">
      {/* Game header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="text-lg font-bold text-white">
            {alert.away_team} @ {alert.home_team}
          </span>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-green-400">
            +{alert.profit_percent.toFixed(2)}%
          </div>
        </div>
      </div>

      {/* Bookmaker odds - NEW VERSION with logos */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        {/* Book A */}
        <div className="bg-slate-800 border-2 border-slate-700 rounded p-4">
          {/* Show logo + name */}
          <div className="mb-3">
            <BookmakerBadge bookmakerKey={alert.book_a} />
          </div>
          <div className="text-xl font-bold text-white mb-1">
            {alert.odds_a > 0 ? `+${alert.odds_a}` : alert.odds_a}
          </div>
          <div className="text-sm text-slate-300">
            Stake: ${alert.stake_a.toFixed(2)}
          </div>
        </div>

        {/* Book B */}
        <div className="bg-slate-800 border-2 border-slate-700 rounded p-4">
          {/* Show logo + name */}
          <div className="mb-3">
            <BookmakerBadge bookmakerKey={alert.book_b} />
          </div>
          <div className="text-xl font-bold text-white mb-1">
            {alert.odds_b > 0 ? `+${alert.odds_b}` : alert.odds_b}
          </div>
          <div className="text-sm text-slate-300">
            Stake: ${alert.stake_b.toFixed(2)}
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================
// EXAMPLE 2: Compact logo-only display
// ============================================

function CompactArbitrageCard({ alert }: { alert: any }) {
  return (
    <div className="bg-green-900 border-2 border-green-700 rounded p-4">
      <div className="flex items-center justify-between">
        {/* Left: Bookmakers */}
        <div className="flex items-center gap-2">
          <BookmakerLogo bookmakerKey={alert.book_a} size="md" />
          <span className="text-slate-400">vs</span>
          <BookmakerLogo bookmakerKey={alert.book_b} size="md" />
        </div>

        {/* Middle: Game */}
        <div className="flex-1 px-4 text-center">
          <div className="text-sm font-semibold text-white">
            {alert.away_team} @ {alert.home_team}
          </div>
          <div className="text-xs text-slate-400">{alert.market_type}</div>
        </div>

        {/* Right: Profit */}
        <div className="text-right">
          <div className="text-xl font-bold text-green-400">
            +{alert.profit_percent.toFixed(2)}%
          </div>
          <div className="text-xs text-slate-400">
            ${alert.guaranteed_profit.toFixed(2)}
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================
// EXAMPLE 3: Clickable logos that open bookmaker sites
// ============================================

function InteractiveArbitrageCard({ alert }: { alert: any }) {
  return (
    <div className="bg-green-900 border-2 border-green-700 rounded p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="text-lg font-bold text-white mb-2">
            {alert.away_team} @ {alert.home_team}
          </div>
          <div className="flex items-center gap-3">
            {/* Clickable logos */}
            <BookmakerLink bookmakerKey={alert.book_a} size="lg" />
            <span className="text-slate-400">vs</span>
            <BookmakerLink bookmakerKey={alert.book_b} size="lg" />
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-green-400">
            +{alert.profit_percent.toFixed(2)}%
          </div>
          <div className="text-sm text-slate-400">
            ${alert.guaranteed_profit.toFixed(2)} profit
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="text-center">
          <div className="text-xs text-slate-400 mb-1">Book A Odds</div>
          <div className="text-lg font-bold text-white">
            {alert.odds_a > 0 ? `+${alert.odds_a}` : alert.odds_a}
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs text-slate-400 mb-1">Book B Odds</div>
          <div className="text-lg font-bold text-white">
            {alert.odds_b > 0 ? `+${alert.odds_b}` : alert.odds_b}
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================
// EXAMPLE 4: Grid of all available bookmakers
// ============================================

import { getBookmakersByRegion, getPopularBookmakers } from '../data/bookmakers';

function BookmakerGrid() {
  const usBookmakers = getBookmakersByRegion('US');

  return (
    <div>
      <h2 className="text-xl font-bold text-slate-100 mb-4">US Bookmakers</h2>
      <div className="grid grid-cols-4 gap-4">
        {usBookmakers.map((book) => (
          <div
            key={book.key}
            className="bg-slate-800 border border-slate-700 rounded p-4 text-center hover:border-blue-500 transition-colors"
          >
            <BookmakerLink bookmakerKey={book.key} size="lg" className="mx-auto" />
            <div className="text-xs text-slate-300 mt-2">{book.name}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================
// EXAMPLE 5: Dropdown/Select with bookmaker logos
// ============================================

import { getAllBookmakerKeys, getBookmaker } from '../data/bookmakers';

function BookmakerSelector() {
  const [selected, setSelected] = React.useState('draftkings');
  const allBooks = getAllBookmakerKeys().map(getBookmaker).filter(Boolean);

  return (
    <div className="relative">
      <label className="block text-sm font-semibold text-slate-300 mb-2">
        Select Bookmaker
      </label>
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-2">
        <div className="flex items-center gap-2">
          <BookmakerLogo bookmakerKey={selected} size="sm" />
          <select
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
            className="flex-1 bg-transparent text-slate-100 outline-none"
          >
            {allBooks.map((book) => (
              <option key={book.key} value={book.key}>
                {book.name}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}

// ============================================
// EXAMPLE 6: Popular bookmakers quick access bar
// ============================================

function PopularBookmarkersBar() {
  const popular = getPopularBookmakers();

  return (
    <div className="bg-slate-900 border-y border-slate-700 py-4">
      <div className="max-w-7xl mx-auto px-4">
        <div className="text-xs font-semibold text-slate-400 mb-3 uppercase tracking-wide">
          Quick Access
        </div>
        <div className="flex items-center gap-3 overflow-x-auto">
          {popular.map((book) => (
            <BookmakerLink
              key={book.key}
              bookmakerKey={book.key}
              size="lg"
              className="flex-shrink-0"
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export {
  ArbitrageAlertCardExample,
  CompactArbitrageCard,
  InteractiveArbitrageCard,
  BookmakerGrid,
  BookmakerSelector,
  PopularBookmarkersBar,
};
