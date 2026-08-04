import { useState } from 'react';
import { RefereeLeaderboard } from '../components/referee/RefereeLeaderboard';
import { RefereeProfileCard } from '../components/referee/RefereeProfileCard';
import { useRefereeList, useRefereeProfile } from '../hooks/useRefereeData';

type SortKey = 'games' | 'avg_total' | 'over_rate' | 'home_cover_pct';

export function RefereeTracker() {
  const [sort, setSort]               = useState<SortKey>('games');
  const [minGames, setMinGames]       = useState(10);
  const [selectedName, setSelectedName] = useState<string | null>(null);

  const { data: listData, isLoading: listLoading } = useRefereeList(sort, minGames);
  const { data: profile, isLoading: profileLoading } = useRefereeProfile(selectedName);

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
              O/U tendencies, home cover rates, and scoring patterns by referee — 2022 through 2025
            </p>
          </div>
          {listData && (
            <div className="text-sm text-slate-400">
              <span className="text-white font-bold">{listData.count}</span> referees tracked
            </div>
          )}
        </div>

        {/* Filters */}
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Min Games:</span>
            {[5, 10, 20].map(n => (
              <button key={n} onClick={() => setMinGames(n)}
                className={`px-3 py-1.5 rounded text-xs font-bold transition-all
                  ${minGames === n ? 'bg-yellow-500 text-black' : 'bg-slate-800 text-slate-400 hover:text-white'}`}
              >{n}+</button>
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
