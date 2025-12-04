import { useEffect, useState } from 'react';
import { Trophy, TrendingUp, Target, Flame } from 'lucide-react';
import { TierGate } from '../components/TierGate';
import { API_BASE_URL } from '../config';

interface PlatformPick {
  site: string;
  logo: string;
  gradient: string;
  bestPlay: string;
  trueWinRate: string;
  payout: string;
  ev: string;
  demonScore: number;
  entriesToday: number;
}

export default function DfsCrusher() {
  const [liveData, setLiveData] = useState<PlatformPick[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch live DFS picks
    fetch(`${API_BASE_URL}/ui/dfs-best-picks`)
      .then(res => res.json())
      .then(data => {
        if (data.plays && data.plays.length > 0) {
          setLiveData(data.plays);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching DFS picks:', err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white p-6">
      <TierGate feature="dfs_crusher">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-2">
              <Flame className="w-8 h-8 text-orange-500" />
              <h1 className="text-4xl font-bold bg-gradient-to-r from-orange-400 to-red-500 bg-clip-text text-transparent">
                DFS CRUSHER
              </h1>
            </div>
            <p className="text-slate-400 text-lg">
              Best picks from PrizePicks, Underdog, Fliff, and more
            </p>
          </div>

          {loading && (
            <div className="flex items-center justify-center py-20">
              <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-orange-500"></div>
            </div>
          )}

          {!loading && liveData.length === 0 && (
            <div className="bg-slate-800 rounded-xl p-12 text-center border border-slate-700">
              <Trophy className="w-16 h-16 mx-auto mb-4 text-slate-600" />
              <h3 className="text-xl font-semibold text-slate-400 mb-2">No DFS picks available</h3>
              <p className="text-slate-500">Check back later for today's best plays</p>
            </div>
          )}

          {!loading && liveData.length > 0 && (
            <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
              {/* Table Header */}
              <div className="grid grid-cols-7 gap-4 p-4 bg-slate-900 border-b border-slate-700 font-semibold text-sm text-slate-400">
                <div>Platform</div>
                <div className="col-span-2">Best Play</div>
                <div className="text-center">Win Rate</div>
                <div className="text-center">Payout</div>
                <div className="text-center">Edge</div>
                <div className="text-center">Props Today</div>
              </div>

              {/* Table Rows */}
              <div className="divide-y divide-slate-700">
                {liveData.map((pick, index) => (
                  <div
                    key={index}
                    className="grid grid-cols-7 gap-4 p-4 hover:bg-slate-750 transition-colors cursor-pointer"
                    onClick={() => {
                      navigator.clipboard.writeText(pick.bestPlay);
                      alert(`Copied: ${pick.bestPlay}`);
                    }}
                  >
                    {/* Platform */}
                    <div className="flex items-center gap-2">
                      {pick.demonScore >= 15 && (
                        <Flame className="w-4 h-4 text-orange-500 animate-pulse" />
                      )}
                      <span className="font-semibold">{pick.site}</span>
                    </div>

                    {/* Best Play */}
                    <div className="col-span-2 font-medium text-slate-200">
                      {pick.bestPlay}
                    </div>

                    {/* Win Rate */}
                    <div className="text-center">
                      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-green-500/10 text-green-400 font-semibold">
                        <TrendingUp className="w-3 h-3" />
                        {pick.trueWinRate}
                      </span>
                    </div>

                    {/* Payout */}
                    <div className="text-center">
                      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-yellow-500/10 text-yellow-400 font-semibold">
                        <Target className="w-3 h-3" />
                        {pick.payout}
                      </span>
                    </div>

                    {/* Edge */}
                    <div className="text-center">
                      <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full font-bold ${
                        parseFloat(pick.ev) >= 50
                          ? 'bg-orange-500/20 text-orange-400'
                          : 'bg-blue-500/10 text-blue-400'
                      }`}>
                        {pick.ev}
                      </span>
                    </div>

                    {/* Props Today */}
                    <div className="text-center text-slate-400">
                      {pick.entriesToday}
                    </div>
                  </div>
                ))}
              </div>

              {/* Footer Note */}
              <div className="p-4 bg-slate-900 border-t border-slate-700 text-center text-sm text-slate-500">
                Click any row to copy the play to your clipboard
              </div>
            </div>
          )}
        </div>
      </TierGate>
    </div>
  );
}
