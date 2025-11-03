import { useState, useEffect } from 'react';
import { getApiUrl } from '../config';

interface WeatherData {
  temperature: number;
  wind_speed: number;
  wind_direction: string;
  precipitation: string;
  precipitation_chance: number;
  conditions: string;
}

interface WeatherOpportunity {
  game_id: string;
  sport: string;
  home_team: string;
  away_team: string;
  stadium_location: string;
  market_total: number;
  adjusted_total: number;
  total_adjustment: number;
  edge_estimate: number;
  recommendation: string;
  confidence: number;
  impact_level: string;
  weather: WeatherData;
  key_factors: string[];
  reasoning: string;
  commence_time: string;
}

export function WeatherImpactAlerts() {
  const [opportunities, setOpportunities] = useState<WeatherOpportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchOpportunities = async () => {
    try {
      const response = await fetch(getApiUrl('weather-opportunities'));
      if (!response.ok) throw new Error('Failed to fetch weather opportunities');
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
    const interval = setInterval(fetchOpportunities, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  const getImpactColor = (level: string) => {
    if (level === 'EXTREME') return 'border-red-600 shadow-red-600/30';
    if (level === 'HIGH') return 'border-orange-600 shadow-orange-600/30';
    if (level === 'MODERATE') return 'border-yellow-600 shadow-yellow-600/20';
    return 'border-slate-600';
  };

  const getImpactBadge = (level: string) => {
    if (level === 'EXTREME') return 'bg-red-600 text-white';
    if (level === 'HIGH') return 'bg-orange-600 text-white';
    if (level === 'MODERATE') return 'bg-yellow-600 text-white';
    return 'bg-slate-600 text-white';
  };

  const getWeatherEmoji = (conditions: string, precip: string) => {
    if (precip === 'snow') return '❄️';
    if (precip === 'rain') return '🌧️';
    if (conditions.toLowerCase().includes('cloud')) return '☁️';
    return '☀️';
  };

  const getTempColor = (temp: number) => {
    if (temp <= 20) return 'text-blue-400';
    if (temp >= 95) return 'text-red-400';
    return 'text-white';
  };

  if (loading) {
    return (
      <div className="bg-slate-800 border-2 border-slate-700 p-12 text-center">
        <div className="text-slate-400 text-lg">Loading weather impact opportunities...</div>
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
        <div className="text-slate-400 text-lg">No significant weather impacts detected</div>
        <div className="text-slate-500 text-sm mt-2">
          Monitoring outdoor NFL stadiums for wind, precipitation, and extreme temperatures
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {opportunities.map((opp, idx) => (
        <div
          key={idx}
          className={`bg-slate-900 border-4 p-6 transition-all ${getImpactColor(opp.impact_level)} shadow-lg`}
        >
          {/* Header */}
          <div className="flex items-start justify-between mb-6">
            <div className="flex items-center gap-3">
              <span className="px-3 py-1 text-xs font-bold text-white bg-green-600">
                NFL
              </span>
              <span className="px-3 py-1 text-xs font-bold bg-green-900/50 text-green-300">
                📊 PRE-GAME
              </span>
              <span className="text-xl font-bold text-white">
                {opp.away_team} @ {opp.home_team}
              </span>
            </div>
            <div className="text-right">
              <div className={`inline-block px-4 py-2 ${getImpactBadge(opp.impact_level)} text-sm font-bold mb-1`}>
                {opp.impact_level} IMPACT
              </div>
              <div className="text-slate-400 text-xs">
                {opp.stadium_location}
              </div>
            </div>
          </div>

          {/* Recommendation Card */}
          <div className="bg-gradient-to-br from-slate-800 to-black border-2 border-slate-700 p-6 mb-6">
            <div className="text-center mb-4">
              <div className="inline-block px-8 py-3 bg-blue-600 text-white text-2xl font-bold shadow-lg mb-2">
                {opp.recommendation} {opp.market_total}
              </div>
              <div className="text-slate-300 text-sm mt-2">
                Market Total: {opp.market_total} → Weather-Adjusted: {opp.adjusted_total}
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="bg-slate-900/50 border border-slate-700 p-3 text-center">
                <div className="text-slate-400 text-xs mb-1">Edge</div>
                <div className="text-xl font-bold text-green-400">
                  +{opp.edge_estimate}
                </div>
                <div className="text-slate-500 text-xs">points</div>
              </div>

              <div className="bg-slate-900/50 border border-slate-700 p-3 text-center">
                <div className="text-slate-400 text-xs mb-1">Adjustment</div>
                <div className="text-xl font-bold text-red-400">
                  {opp.total_adjustment}
                </div>
                <div className="text-slate-500 text-xs">points</div>
              </div>

              <div className="bg-slate-900/50 border border-slate-700 p-3 text-center">
                <div className="text-slate-400 text-xs mb-1">Confidence</div>
                <div className="text-xl font-bold text-white">
                  {(opp.confidence * 100).toFixed(0)}%
                </div>
                <div className="text-slate-500 text-xs">certainty</div>
              </div>
            </div>
          </div>

          {/* Weather Conditions */}
          <div className="bg-gradient-to-br from-blue-900/20 to-purple-900/20 border-2 border-blue-700/50 p-6 mb-4">
            <div className="text-center mb-4">
              <div className="text-6xl mb-2">
                {getWeatherEmoji(opp.weather.conditions, opp.weather.precipitation)}
              </div>
              <div className="text-xl font-bold text-white mb-1">{opp.weather.conditions}</div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-slate-900/50 border border-slate-700 p-3 text-center">
                <div className="text-slate-400 text-xs mb-1">Temperature</div>
                <div className={`text-2xl font-bold ${getTempColor(opp.weather.temperature)}`}>
                  {opp.weather.temperature}°F
                </div>
              </div>

              <div className="bg-slate-900/50 border border-slate-700 p-3 text-center">
                <div className="text-slate-400 text-xs mb-1">Wind</div>
                <div className="text-2xl font-bold text-white">
                  {opp.weather.wind_speed}
                </div>
                <div className="text-slate-400 text-xs">
                  MPH {opp.weather.wind_direction}
                </div>
              </div>

              <div className="bg-slate-900/50 border border-slate-700 p-3 text-center">
                <div className="text-slate-400 text-xs mb-1">Precipitation</div>
                <div className="text-lg font-bold text-white capitalize">
                  {opp.weather.precipitation}
                </div>
                <div className="text-slate-400 text-xs">
                  {opp.weather.precipitation_chance}% chance
                </div>
              </div>

              <div className="bg-slate-900/50 border border-slate-700 p-3 text-center">
                <div className="text-slate-400 text-xs mb-1">Location</div>
                <div className="text-sm font-bold text-white">
                  {opp.stadium_location}
                </div>
                <div className="text-slate-400 text-xs">Outdoor</div>
              </div>
            </div>
          </div>

          {/* Key Factors */}
          <div className="bg-orange-900/20 border border-orange-700/50 p-4 mb-4">
            <div className="text-sm font-bold text-orange-300 mb-3">⚠️ Weather Impact Factors:</div>
            <div className="space-y-2">
              {opp.key_factors.map((factor, i) => (
                <div key={i} className="flex items-start gap-2">
                  <div className="text-orange-400 font-bold">•</div>
                  <div className="text-sm text-slate-300">{factor}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Reasoning */}
          <div className="bg-blue-900/20 border border-blue-700/50 p-4">
            <div className="text-sm font-bold text-blue-300 mb-2">📊 Full Analysis:</div>
            <div className="text-sm text-slate-300 leading-relaxed">
              {opp.reasoning}
            </div>
          </div>

          {/* Footer Info */}
          <div className="mt-4 flex items-center justify-between text-xs text-slate-500">
            <div>Game Time: {new Date(opp.commence_time).toLocaleString()}</div>
            <div>Game ID: {opp.game_id}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
