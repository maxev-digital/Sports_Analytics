import { useState, useEffect } from 'react';
import { getApiUrl } from '../config';

interface GolferOdds {
  name: string;
  bestOdds: number;
  bestBook: string;
  allOdds: { book: string; price: number }[];
}

interface Tournament {
  id: string;
  sport_title: string;
  commence_time: string;
  golfers: GolferOdds[];
}

function formatOdds(price: number): string {
  return price > 0 ? `+${price}` : `${price}`;
}

function impliedProb(price: number): string {
  const prob = price > 0 ? 100 / (price + 100) : (-price) / (-price + 100);
  return `${(prob * 100).toFixed(1)}%`;
}

export function GolfOddsBoard() {
  const [tournaments, setTournaments] = useState<Tournament[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  useEffect(() => {
    fetchGolfOdds();
    const interval = setInterval(fetchGolfOdds, 120000);
    return () => clearInterval(interval);
  }, []);

  const fetchGolfOdds = async () => {
    try {
      const res = await fetch(getApiUrl('golf-odds'));
      if (!res.ok) { setLoading(false); return; }
      const data = await res.json();
      setTournaments(data);
      const initial: Record<string, boolean> = {};
      data.forEach((t: Tournament) => { initial[t.id] = true; });
      setExpanded(prev => ({ ...initial, ...prev }));
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-slate-300 text-lg">Loading tournament odds...</div>
      </div>
    );
  }

  if (!tournaments.length) {
    return (
      <div className="text-center py-20">
        <div className="text-6xl mb-4">⛳</div>
        <h3 className="text-xl font-semibold text-slate-300 mb-2">No active golf tournaments</h3>
        <p className="text-slate-400">Check back when the next event is posted</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {tournaments.map(tournament => (
        <div key={tournament.id} className="rounded-xl overflow-hidden border border-slate-700/60 bg-black/50 backdrop-blur-sm">
          {/* Tournament Header */}
          <div
            className="flex items-center justify-between px-5 py-4 bg-gradient-to-r from-green-900/80 to-green-800/60 cursor-pointer"
            onClick={() => setExpanded(p => ({ ...p, [tournament.id]: !p[tournament.id] }))}
          >
            <div className="flex items-center gap-3">
              <span className="text-2xl">⛳</span>
              <div>
                <h2 className="text-lg font-bold text-white">{tournament.sport_title}</h2>
                <p className="text-xs text-green-300">Outright Winner Odds · {tournament.golfers.length} players</p>
              </div>
            </div>
            <span className="text-slate-400 text-sm">{expanded[tournament.id] ? '▲' : '▼'}</span>
          </div>

          {expanded[tournament.id] && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700/50 text-xs text-slate-400 uppercase tracking-wider">
                    <th className="text-left px-4 py-3 w-8">#</th>
                    <th className="text-left px-4 py-3">Player</th>
                    <th className="text-center px-4 py-3">Best Odds</th>
                    <th className="text-center px-4 py-3">Implied %</th>
                    <th className="text-center px-4 py-3">Best Book</th>
                    <th className="text-center px-4 py-3">All Books</th>
                  </tr>
                </thead>
                <tbody>
                  {tournament.golfers.map((golfer, i) => (
                    <tr
                      key={golfer.name}
                      className={`border-b border-slate-800/40 transition-colors hover:bg-white/5 ${i < 3 ? 'bg-green-950/20' : ''}`}
                    >
                      <td className="px-4 py-3 text-slate-500 font-mono">{i + 1}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          {i === 0 && <span className="text-yellow-400 text-xs">🏆</span>}
                          {i === 1 && <span className="text-slate-300 text-xs">🥈</span>}
                          {i === 2 && <span className="text-orange-400 text-xs">🥉</span>}
                          <span className="font-semibold text-slate-100">{golfer.name}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="font-bold text-green-400 text-base">{formatOdds(golfer.bestOdds)}</span>
                      </td>
                      <td className="px-4 py-3 text-center text-slate-400">
                        {impliedProb(golfer.bestOdds)}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="px-2 py-0.5 bg-slate-700 rounded text-xs text-slate-300">{golfer.bestBook}</span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <div className="flex flex-wrap justify-center gap-1">
                          {golfer.allOdds.map(o => (
                            <span
                              key={o.book}
                              className={`px-1.5 py-0.5 rounded text-xs ${o.price === golfer.bestOdds ? 'bg-green-700 text-green-100' : 'bg-slate-800 text-slate-400'}`}
                              title={o.book}
                            >
                              {formatOdds(o.price)}
                            </span>
                          ))}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
