import { useState, useEffect } from 'react';
import { getApiUrl } from '../config';
import { ATSLeaderboard, type ATSRow } from '../components/nfl-trends/ATSLeaderboard';
import { EPARankings, type EPARow } from '../components/nfl-trends/EPARankings';
import { TeamTrendsProfile } from '../components/nfl-trends/TeamTrendsProfile';

type Tab = 'ats' | 'ou' | 'epa';
const SEASONS = [2022, 2023, 2024, 2025] as const;

const SEASON_LABELS: Record<number, string> = {
  2022: '2022-23', 2023: '2023-24', 2024: '2024-25', 2025: '2025-26',
};

interface StatusData { available: boolean; games_count?: number; last_run?: string; seasons?: string[]; }

function OULeaderboard({ rows, loading, onSelectTeam, selectedTeam }: {
  rows: ATSRow[]; loading: boolean; onSelectTeam: (t: string) => void; selectedTeam: string | null;
}) {
  const overall = rows.filter(r => r.situation === 'overall');
  const sorted  = [...overall].sort((a, b) => (b.over_pct ?? 0) - (a.over_pct ?? 0));
  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
      {loading ? <div className="py-12 text-center text-slate-500 animate-pulse">Loading O/U data…</div> : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700 bg-slate-800/80">
                <th className="px-3 py-2.5 text-left text-xs font-bold text-slate-400 w-8">#</th>
                <th className="px-3 py-2.5 text-left text-xs font-bold text-slate-400">TEAM</th>
                <th className="px-3 py-2.5 text-right text-xs font-bold text-slate-400">OVER</th>
                <th className="px-3 py-2.5 text-right text-xs font-bold text-slate-400">UNDER</th>
                <th className="px-3 py-2.5 text-right text-xs font-bold text-slate-400">OVER%</th>
                <th className="px-3 py-2.5 text-right text-xs font-bold text-slate-400">AVG TOTAL</th>
                <th className="px-3 py-2.5 text-right text-xs font-bold text-slate-400">PTS/G</th>
                <th className="px-3 py-2.5 text-right text-xs font-bold text-slate-400">OPP PTS/G</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((row, i) => {
                const pct = row.over_pct;
                const cls = pct !== null && pct >= 0.6 ? 'text-orange-400 font-bold' : pct !== null && pct <= 0.4 ? 'text-blue-400 font-bold' : 'text-slate-300';
                return (
                  <tr key={row.team}
                    onClick={() => onSelectTeam(row.team === selectedTeam ? '' : row.team)}
                    className={`border-b border-slate-800 cursor-pointer transition-colors ${selectedTeam === row.team ? 'bg-blue-900/30' : 'hover:bg-slate-800/40'}`}
                  >
                    <td className="px-3 py-2.5 text-slate-500 text-xs">{i + 1}</td>
                    <td className="px-3 py-2.5 font-bold text-white">{row.team}</td>
                    <td className="px-3 py-2.5 text-right text-orange-400 font-mono text-xs">{row.ou_over}</td>
                    <td className="px-3 py-2.5 text-right text-blue-400 font-mono text-xs">{row.ou_under}</td>
                    <td className={`px-3 py-2.5 text-right ${cls}`}>
                      {pct !== null ? `${(pct * 100).toFixed(1)}%` : '—'}
                    </td>
                    <td className="px-3 py-2.5 text-right text-xs text-slate-400">{row.avg_total ?? '—'}</td>
                    <td className="px-3 py-2.5 text-right text-xs text-slate-300">{row.avg_pts_scored ?? '—'}</td>
                    <td className="px-3 py-2.5 text-right text-xs text-slate-300">{row.avg_pts_allowed ?? '—'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export function NFLTrends() {
  const [tab, setTab]               = useState<Tab>('ats');
  const [season, setSeason]         = useState<number>(2025);
  const [selectedTeam, setSelectedTeam] = useState<string | null>(null);
  const [status, setStatus]         = useState<StatusData | null>(null);
  const [atsRows, setAtsRows]       = useState<ATSRow[]>([]);
  const [epaRows, setEpaRows]       = useState<EPARow[]>([]);
  const [loadingAts, setLoadingAts] = useState(false);
  const [loadingEpa, setLoadingEpa] = useState(false);

  useEffect(() => {
    fetch(getApiUrl('f5/nfl/status')).then(r => r.json()).then(setStatus).catch(() => {});
  }, []);

  useEffect(() => {
    setAtsRows([]); setLoadingAts(true);
    fetch(getApiUrl(`f5/nfl/ats?season=${season}`))
      .then(r => r.json()).then(d => setAtsRows(d.teams ?? [])).catch(() => setAtsRows([])).finally(() => setLoadingAts(false));
    setEpaRows([]); setLoadingEpa(true);
    fetch(getApiUrl(`f5/nfl/epa?season=${season}`))
      .then(r => r.json()).then(d => setEpaRows(d.teams ?? [])).catch(() => setEpaRows([])).finally(() => setLoadingEpa(false));
  }, [season]);

  const tabBtn = (t: Tab, label: string) => (
    <button key={t} onClick={() => setTab(t)}
      className={`px-5 py-2.5 rounded-lg text-sm font-bold transition-all ${tab === t ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30' : 'bg-slate-800 text-slate-400 hover:text-white'}`}
    >{label}</button>
  );

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-black italic tracking-tight">
              NFL <span className="text-blue-400">TRENDS</span>
            </h1>
            <p className="text-slate-400 mt-1">ATS records, O/U trends, and EPA rankings — 2022 through 2025-26</p>
          </div>
          {status?.available && (
            <div className="text-sm text-slate-400">
              <span className="text-white font-bold">{status.games_count?.toLocaleString()}</span> games · Updated {status.last_run ? new Date(status.last_run).toLocaleDateString() : '—'}
            </div>
          )}
        </div>

        {status && !status.available && (
          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-5 text-center">
            <p className="text-yellow-400 font-bold">NFL trends data not yet loaded</p>
            <p className="text-slate-400 text-sm mt-1">Run <code className="bg-slate-800 px-1 rounded">python3 build_nfl_trends.py</code> on the server.</p>
          </div>
        )}

        {/* Season selector */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Season:</span>
          {SEASONS.map(s => (
            <button key={s} onClick={() => { setSeason(s); setSelectedTeam(null); }}
              className={`px-3 py-1.5 rounded text-xs font-bold transition-all ${season === s ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-white'}`}
            >{SEASON_LABELS[s]}</button>
          ))}
        </div>

        {/* Tabs */}
        <div className="flex gap-2">
          {tabBtn('ats', 'ATS TRENDS')}
          {tabBtn('ou',  'O/U TRENDS')}
          {tabBtn('epa', 'EPA RANKINGS')}
        </div>

        {tab === 'ats' && <ATSLeaderboard rows={atsRows} loading={loadingAts} onSelectTeam={t => setSelectedTeam(t || null)} selectedTeam={selectedTeam} />}
        {tab === 'ou'  && <OULeaderboard  rows={atsRows} loading={loadingAts} onSelectTeam={t => setSelectedTeam(t || null)} selectedTeam={selectedTeam} />}
        {tab === 'epa' && <EPARankings    rows={epaRows} loading={loadingEpa} onSelectTeam={t => setSelectedTeam(t || null)} selectedTeam={selectedTeam} />}

        {/* Team profile panel */}
        {selectedTeam && (
          <TeamTrendsProfile team={selectedTeam} season={season} onClose={() => setSelectedTeam(null)} />
        )}
      </div>
    </div>
  );
}
