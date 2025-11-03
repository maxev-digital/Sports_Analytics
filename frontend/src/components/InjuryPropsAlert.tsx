import { useState, useEffect } from 'react';
import { getApiUrl } from '../config';

interface InjuryPropsOpportunity {
  player_name: string;
  team: string;
  sport: string;
  injury_status: string;
  prop_type: string;
  prop_line: number;
  prop_side: string;
  best_odds: number;
  best_book: string;
  expected_value: number;
  confidence: number;
  reasoning: string;
  time_since_tweet: number;
  timestamp: string;
}

export function InjuryPropsAlerts() {
  const [opportunities, setOpportunities] = useState<InjuryPropsOpportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchOpportunities = async () => {
    try {
      const response = await fetch(getApiUrl('injuries/props'));
      if (!response.ok) throw new Error('Failed to fetch injury props opportunities');
      const data = await response.json();
      setOpportunities(data.opportunities || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOpportunities();
    // Poll every 5 seconds (fast for 60-second window)
    const interval = setInterval(fetchOpportunities, 5000);
    return () => clearInterval(interval);
  }, []);

  const formatOdds = (odds: number) => {
    if (odds > 0) return `+${odds}`;
    return `${odds}`;
  };

  const getTimeRemaining = (timeSinceTweet: number) => {
    const remaining = Math.max(0, 60 - timeSinceTweet);
    return Math.floor(remaining);
  };

  const getUrgencyClass = (timeSinceTweet: number) => {
    const remaining = 60 - timeSinceTweet;
    if (remaining <= 15) return 'border-red-500 animate-pulse';
    if (remaining <= 30) return 'border-orange-500';
    return 'border-yellow-500';
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 75) return 'text-green-400';
    if (confidence >= 60) return 'text-yellow-400';
    return 'text-orange-400';
  };

  if (loading) {
    return (
      <div className="bg-slate-800 border-2 border-slate-700 p-12 text-center">
        <div className="text-slate-400 text-lg">Loading injury props opportunities...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-slate-800 border-2 border-red-700 p-12 text-center">
        <div className="text-red-400 text-lg">Error: {error}</div>
      </div>
    );
  }

  if (opportunities.length === 0) {
    return (
      <div className="bg-slate-800 border-2 border-slate-700 p-12 text-center">
        <div className="text-slate-300 text-xl mb-3">⚡ Monitoring Twitter for Injuries</div>
        <div className="text-slate-400">
          Watching 11 Tier 1 reporters (Woj, Shams, Schefter, etc.) for instant injury updates
        </div>
        <div className="text-slate-500 text-sm mt-2">
          When star players are ruled out, ML analysis finds mispriced props in &lt;60 seconds
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {opportunities.map((opp, index) => {
        const timeRemaining = getTimeRemaining(opp.time_since_tweet);

        return (
          <div
            key={index}
            className={`border-4 ${getUrgencyClass(opp.time_since_tweet)} bg-gradient-to-br from-red-900/90 via-red-800/80 to-red-900/90 rounded-lg p-6 shadow-2xl`}
          >
            {/* Header with urgency timer */}
            <div className="flex justify-between items-start mb-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-2xl">🚨</span>
                  <span className="text-red-200 font-bold text-lg">INJURY PROPS OPPORTUNITY</span>
                </div>
                <div className="text-slate-300 text-sm mt-1">
                  <span className="font-semibold">{opp.team}</span> - {opp.injury_status}
                </div>
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-red-300">⏱️ {timeRemaining}s</div>
                <div className="text-red-200 text-sm">remaining</div>
              </div>
            </div>

            {/* Player & Prop Info */}
            <div className="bg-slate-900/60 rounded-lg p-4 mb-4">
              <div className="text-xl font-bold text-white mb-2">{opp.player_name}</div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="text-slate-400">Prop</div>
                  <div className="text-white font-semibold">
                    {opp.prop_type.toUpperCase()} {opp.prop_side.toUpperCase()} {opp.prop_line}
                  </div>
                </div>
                <div>
                  <div className="text-slate-400">Best Odds</div>
                  <div className="text-white font-semibold">
                    {opp.best_book} {formatOdds(opp.best_odds)}
                  </div>
                </div>
              </div>
            </div>

            {/* EV & Confidence */}
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="bg-green-900/40 rounded-lg p-3 text-center border-2 border-green-600">
                <div className="text-green-200 text-sm">Expected Value</div>
                <div className="text-green-300 font-bold text-2xl">+{opp.expected_value.toFixed(1)}%</div>
              </div>
              <div className="bg-slate-900/40 rounded-lg p-3 text-center border-2 border-slate-600">
                <div className="text-slate-300 text-sm">Confidence</div>
                <div className={`${getConfidenceColor(opp.confidence)} font-bold text-2xl`}>
                  {opp.confidence}%
                </div>
              </div>
            </div>

            {/* ML Reasoning */}
            <div className="bg-slate-900/60 rounded-lg p-4 border-l-4 border-blue-500">
              <div className="text-blue-300 text-xs uppercase font-semibold mb-1">ML Analysis</div>
              <div className="text-slate-200 text-sm">{opp.reasoning}</div>
            </div>

            {/* Sport Badge */}
            <div className="mt-4">
              <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                opp.sport === 'NBA' ? 'bg-orange-600 text-white' :
                opp.sport === 'NFL' ? 'bg-green-600 text-white' :
                'bg-blue-600 text-white'
              }`}>
                {opp.sport}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
