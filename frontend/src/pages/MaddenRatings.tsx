import { useState, useEffect, useCallback } from 'react';
import { getApiUrl } from '../config';
import { MaddenPlayerTable, type MaddenPlayer } from '../components/madden/MaddenPlayerTable';
import { MaddenTeamSelector } from '../components/madden/MaddenTeamSelector';
import { MaddenPositionLeaders } from '../components/madden/MaddenPositionLeaders';

type Tab = 'top' | 'team' | 'position';

const POS_GROUPS = ['QB', 'RB', 'WR', 'TE', 'OL', 'DL', 'LB', 'DB', 'K', 'P'] as const;
type PosGroup = (typeof POS_GROUPS)[number];

interface StatusData {
  available: boolean;
  game?: string;
  season?: string;
  scraped_at?: string;
  player_count?: number;
  ovr_threshold?: number;
}

interface PlayersResponse {
  count: number;
  players: MaddenPlayer[];
}

interface TeamResponse {
  team: string;
  player_count: number;
  roster: MaddenPlayer[];
  by_position: Record<string, MaddenPlayer[]>;
}

function useStatus() {
  const [status, setStatus] = useState<StatusData | null>(null);
  useEffect(() => {
    fetch(getApiUrl('f5/madden/status'))
      .then(r => r.json() as Promise<StatusData>)
      .then(setStatus)
      .catch(() => setStatus({ available: false }));
  }, []);
  return status;
}

export function MaddenRatings() {
  const status = useStatus();
  const [tab, setTab] = useState<Tab>('top');
  const [posFilter, setPosFilter] = useState<PosGroup | null>(null);
  const [minOvr, setMinOvr] = useState(70);
  const [players, setPlayers] = useState<MaddenPlayer[]>([]);
  const [loadingPlayers, setLoadingPlayers] = useState(false);
  const [selectedTeam, setSelectedTeam] = useState<string | null>(null);
  const [teamData, setTeamData] = useState<TeamResponse | null>(null);
  const [loadingTeam, setLoadingTeam] = useState(false);

  const fetchPlayers = useCallback(() => {
    if (!status?.available) return;
    setLoadingPlayers(true);
    const params = new URLSearchParams({ limit: '300', min_ovr: String(minOvr) });
    if (posFilter) params.set('pos', posFilter);
    fetch(getApiUrl(`f5/madden/players?${params}`))
      .then(r => r.json() as Promise<PlayersResponse>)
      .then(d => setPlayers(d.players ?? []))
      .catch(() => setPlayers([]))
      .finally(() => setLoadingPlayers(false));
  }, [status?.available, posFilter, minOvr]);

  useEffect(() => { if (tab === 'top') fetchPlayers(); }, [tab, fetchPlayers]);

  useEffect(() => {
    if (tab !== 'team' || !selectedTeam || !status?.available) return;
    setLoadingTeam(true);
    fetch(getApiUrl(`f5/madden/team/${selectedTeam}`))
      .then(r => r.json() as Promise<TeamResponse>)
      .then(setTeamData)
      .catch(() => setTeamData(null))
      .finally(() => setLoadingTeam(false));
  }, [tab, selectedTeam, status?.available]);

  const tabBtn = (t: Tab, label: string) => (
    <button
      key={t}
      onClick={() => setTab(t)}
      className={`px-5 py-2.5 rounded-lg text-sm font-bold transition-all ${
        tab === t ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30' : 'bg-slate-800 text-slate-400 hover:text-white'
      }`}
    >
      {label}
    </button>
  );

  const notAvailable = status && !status.available;

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">

        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-black italic tracking-tight">
              MADDEN 26 <span className="text-blue-400">RATINGS</span>
            </h1>
            <p className="text-slate-400 mt-1">Player ratings database for roster analysis and scouting</p>
          </div>
          {status?.available && (
            <div className="flex items-center gap-4 text-sm text-slate-400">
              <span><span className="text-white font-bold">{status.player_count?.toLocaleString()}</span> players</span>
              <span>OVR ≥ <span className="text-white font-bold">{status.ovr_threshold}</span></span>
              <span className="text-slate-600">·</span>
              <span>Updated {status.scraped_at ? new Date(status.scraped_at).toLocaleDateString() : '—'}</span>
            </div>
          )}
        </div>

        {/* Not available state */}
        {notAvailable && (
          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-6 text-center">
            <div className="text-yellow-400 font-bold mb-1">Madden 26 data not yet loaded</div>
            <div className="text-slate-400 text-sm">Run <code className="bg-slate-800 px-1 rounded">python3 scrape_madden26.py</code> on the server to populate ratings.</div>
          </div>
        )}

        {/* Tabs */}
        {!notAvailable && (
          <>
            <div className="flex gap-2">
              {tabBtn('top',      'TOP PLAYERS')}
              {tabBtn('team',     'TEAM ROSTER')}
              {tabBtn('position', 'POSITION LEADERS')}
            </div>

            {/* TOP PLAYERS tab */}
            {tab === 'top' && (
              <div className="space-y-4">
                <div className="flex flex-wrap items-center gap-3">
                  <div className="flex flex-wrap gap-1.5">
                    <button
                      onClick={() => setPosFilter(null)}
                      className={`px-3 py-1 rounded text-xs font-bold transition-all ${!posFilter ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-white'}`}
                    >
                      ALL
                    </button>
                    {POS_GROUPS.map(p => (
                      <button
                        key={p}
                        onClick={() => setPosFilter(posFilter === p ? null : p)}
                        className={`px-3 py-1 rounded text-xs font-bold transition-all ${posFilter === p ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-white'}`}
                      >
                        {p}
                      </button>
                    ))}
                  </div>
                  <div className="flex items-center gap-2 ml-auto">
                    <span className="text-xs text-slate-400">Min OVR:</span>
                    {[60, 70, 75, 80, 85, 90].map(v => (
                      <button
                        key={v}
                        onClick={() => setMinOvr(v)}
                        className={`px-2 py-1 rounded text-xs font-bold transition-all ${minOvr === v ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-white'}`}
                      >
                        {v}+
                      </button>
                    ))}
                  </div>
                </div>
                <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
                  {loadingPlayers
                    ? <div className="py-12 text-center text-slate-500 animate-pulse">Loading players…</div>
                    : <MaddenPlayerTable players={players} showTeam showPos />
                  }
                </div>
              </div>
            )}

            {/* TEAM ROSTER tab */}
            {tab === 'team' && (
              <div className="space-y-6">
                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
                  <MaddenTeamSelector selected={selectedTeam} onSelect={setSelectedTeam} />
                </div>
                {loadingTeam && <div className="py-8 text-center text-slate-500 animate-pulse">Loading roster…</div>}
                {!loadingTeam && teamData && (
                  <div className="space-y-6">
                    <div className="flex items-center gap-3">
                      <h2 className="text-xl font-black italic">{teamData.team} ROSTER</h2>
                      <span className="text-slate-400 text-sm">{teamData.player_count} players</span>
                    </div>
                    {Object.entries(teamData.by_position).map(([pos, posPlayers]) => (
                      <div key={pos} className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
                        <div className="px-4 py-2 bg-slate-700/50 border-b border-slate-700">
                          <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">{pos}</span>
                          <span className="text-slate-500 text-xs ml-2">({posPlayers.length})</span>
                        </div>
                        <MaddenPlayerTable players={posPlayers} showTeam={false} showPos compact />
                      </div>
                    ))}
                  </div>
                )}
                {!loadingTeam && !teamData && selectedTeam && (
                  <div className="py-8 text-center text-slate-500">No roster data for {selectedTeam}.</div>
                )}
                {!selectedTeam && (
                  <div className="py-8 text-center text-slate-500">Select a team above to view their full roster.</div>
                )}
              </div>
            )}

            {/* POSITION LEADERS tab */}
            {tab === 'position' && <MaddenPositionLeaders />}
          </>
        )}
      </div>
    </div>
  );
}
