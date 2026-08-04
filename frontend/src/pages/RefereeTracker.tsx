import { useState } from 'react';
import { RefereeLeaderboard } from '../components/referee/RefereeLeaderboard';
import { RefereeProfileCard } from '../components/referee/RefereeProfileCard';
import { useRefereeList, useRefereeProfile } from '../hooks/useRefereeData';
import type { ColumnGroup } from '../types/referee';

type SortKey =
  | 'games' | 'avg_total' | 'over_rate' | 'home_cover_pct'
  | 'flags_per_game' | 'yards_per_game' | 'home_bias'
  | 'ot_rate' | 'dome_pct';

const COLUMN_GROUPS: { key: ColumnGroup; label: string }[] = [
  { key: 'betting',     label: 'BETTING' },
  { key: 'penalties',   label: 'PENALTIES' },
  { key: 'environment', label: 'ENVIRONMENT' },
];

export function RefereeTracker() {
  const [sort, setSort]                   = useState<SortKey>('games');
  const [minGames, setMinGames]           = useState(10);
  const [selectedName, setSelectedName]   = useState<string | null>(null);
  const [columnGroup, setColumnGroup]     = useState<ColumnGroup>('betting');

  const { data: listData, isLoading: listLoading } = useRefereeList(sort, minGames);
  const { data: profile, isLoading: profileLoading } = useRefereeProfile(selectedName);

  function handleColumnGroup(g: ColumnGroup) {
    setColumnGroup(g);
    // Reset sort to games when switching groups to avoid invalid sort key
    setSort('games');
  }

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">

        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-black italic tracking-tight">
              NFL <span className="text-yellow-400">REFEREE</span> TRACKER
            </h1>
            <p className="text-slate-400 mt-1">
              O/U tendencies, cover rates, penalty profiles, and environment stats — 2015 through 2025
            </p>
          </div>
          {listData && (
            <div className="text-sm text-slate-400">
              <span className="text-white font-bold">{listData.count}</span> referees tracked
            </div>
          )}
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-center gap-4">

          {/* Column group toggle */}
          <div className="flex items-center gap-1 bg-slate-800 rounded-lg p-1">
            {COLUMN_GROUPS.map(g => (
              <button
                key={g.key}
                onClick={() => handleColumnGroup(g.key)}
                className={`px-3 py-1.5 rounded text-xs font-bold transition-all
                  ${columnGroup === g.key
                    ? 'bg-yellow-500 text-black'
                    : 'text-slate-400 hover:text-white'}`}
              >
                {g.label}
              </button>
            ))}
          </div>

          {/* Min games filter */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Min Games:</span>
            {[5, 10, 20].map(n => (
              <button
                key={n}
                onClick={() => setMinGames(n)}
                className={`px-3 py-1.5 rounded text-xs font-bold transition-all
                  ${minGames === n ? 'bg-slate-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-white'}`}
              >
                {n}+
              </button>
            ))}
          </div>
        </div>

        {/* Leaderboard */}
        <RefereeLeaderboard
          referees={listData?.referees ?? []}
          loading={listLoading}
          selectedName={selectedName}
          onSelect={setSelectedName}
          sort={sort}
          onSort={setSort}
          columnGroup={columnGroup}
        />

        {/* Profile drill-down */}
        {selectedName && (
          <RefereeProfileCard
            profile={profile}
            loading={profileLoading}
            onClose={() => setSelectedName(null)}
          />
        )}
      </div>
    </div>
  );
}
