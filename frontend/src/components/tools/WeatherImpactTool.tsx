import { useState } from 'react';

export function WeatherImpactTool() {
  const [originalTotal, setOriginalTotal] = useState<string>('');
  const [sport, setSport] = useState<'nfl' | 'mlb'>('nfl');
  const [temperature, setTemperature] = useState<string>('');
  const [windSpeed, setWindSpeed] = useState<string>('');
  const [precipitation, setPrecipitation] = useState<'none' | 'rain' | 'snow'>('none');
  const [isDome, setIsDome] = useState<boolean>(false);
  const [result, setResult] = useState<{
    adjustedTotal: number;
    totalAdjustment: number;
    tempAdjustment: number;
    windAdjustment: number;
    precipAdjustment: number;
    recommendation: string;
  } | null>(null);

  const calculateWeatherImpact = () => {
    const totalNum = parseFloat(originalTotal);
    const tempNum = parseFloat(temperature);
    const windNum = parseFloat(windSpeed);

    if (isNaN(totalNum)) {
      alert('Please enter a valid original total');
      return;
    }

    if (isDome) {
      setResult({
        adjustedTotal: totalNum,
        totalAdjustment: 0,
        tempAdjustment: 0,
        windAdjustment: 0,
        precipAdjustment: 0,
        recommendation: 'Game is indoors - no weather impact',
      });
      return;
    }

    let tempAdjustment = 0;
    let windAdjustment = 0;
    let precipAdjustment = 0;

    if (sport === 'nfl') {
      // Temperature impact (NFL)
      if (!isNaN(tempNum)) {
        if (tempNum < 20) {
          tempAdjustment = -4.5; // Very cold significantly lowers scoring
        } else if (tempNum < 32) {
          tempAdjustment = -2.5; // Freezing conditions
        } else if (tempNum < 40) {
          tempAdjustment = -1.0; // Cold weather
        } else if (tempNum > 85) {
          tempAdjustment = -1.5; // Extreme heat can lower scoring
        }
      }

      // Wind impact (NFL)
      if (!isNaN(windNum)) {
        if (windNum > 20) {
          windAdjustment = -6.0; // Very high winds severely impact passing
        } else if (windNum > 15) {
          windAdjustment = -3.5; // Strong winds
        } else if (windNum > 10) {
          windAdjustment = -1.5; // Moderate winds
        }
      }

      // Precipitation impact (NFL)
      if (precipitation === 'rain') {
        precipAdjustment = -2.0; // Rain lowers scoring, more turnovers
      } else if (precipitation === 'snow') {
        precipAdjustment = -4.0; // Snow significantly impacts game
      }
    } else if (sport === 'mlb') {
      // Temperature impact (MLB)
      if (!isNaN(tempNum)) {
        if (tempNum > 85) {
          tempAdjustment = +1.5; // Hot weather helps ball carry
        } else if (tempNum > 75) {
          tempAdjustment = +0.5; // Warm weather slightly favors offense
        } else if (tempNum < 50) {
          tempAdjustment = -1.0; // Cold weather suppresses offense
        }
      }

      // Wind impact (MLB)
      if (!isNaN(windNum)) {
        // Wind direction matters more in MLB, but we'll use speed as approximation
        if (windNum > 15) {
          windAdjustment = +2.0; // Strong winds can help home runs
        } else if (windNum > 10) {
          windAdjustment = +1.0; // Moderate winds
        }
      }

      // Precipitation impact (MLB)
      if (precipitation === 'rain') {
        precipAdjustment = -1.5; // Rain delays, affects play
      }
    }

    const totalAdjustment = tempAdjustment + windAdjustment + precipAdjustment;
    const adjustedTotal = totalNum + totalAdjustment;

    // Generate recommendation
    let recommendation = '';
    if (Math.abs(totalAdjustment) >= 5) {
      recommendation = totalAdjustment < 0
        ? `Strong Under lean - weather significantly lowers expected scoring`
        : `Strong Over lean - weather significantly increases expected scoring`;
    } else if (Math.abs(totalAdjustment) >= 2) {
      recommendation = totalAdjustment < 0
        ? `Moderate Under lean - weather conditions favor lower scoring`
        : `Moderate Over lean - weather conditions favor higher scoring`;
    } else if (Math.abs(totalAdjustment) >= 0.5) {
      recommendation = totalAdjustment < 0
        ? `Slight Under lean - minor weather impact`
        : `Slight Over lean - minor weather impact`;
    } else {
      recommendation = `Minimal weather impact - trust your original analysis`;
    }

    setResult({
      adjustedTotal: Math.round(adjustedTotal * 2) / 2, // Round to nearest 0.5
      totalAdjustment,
      tempAdjustment,
      windAdjustment,
      precipAdjustment,
      recommendation,
    });
  };

  const reset = () => {
    setOriginalTotal('');
    setSport('nfl');
    setTemperature('');
    setWindSpeed('');
    setPrecipitation('none');
    setIsDome(false);
    setResult(null);
  };

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <h2 className="text-xl font-bold text-white mb-4">Weather Impact Tool</h2>
      <p className="text-slate-400 text-sm mb-6">
        Adjust game totals based on weather conditions for outdoor sports
      </p>

      <div className="space-y-4">
        {/* Sport Selection */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Sport
          </label>
          <div className="flex gap-3">
            <button
              onClick={() => setSport('nfl')}
              className={`px-4 py-2 rounded font-medium transition-colors ${
                sport === 'nfl'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              NFL
            </button>
            <button
              onClick={() => setSport('mlb')}
              className={`px-4 py-2 rounded font-medium transition-colors ${
                sport === 'mlb'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              MLB
            </button>
          </div>
        </div>

        {/* Original Total */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Original Total
          </label>
          <input
            type="number"
            value={originalTotal}
            onChange={(e) => setOriginalTotal(e.target.value)}
            placeholder={sport === 'nfl' ? '47.5' : '8.5'}
            step="0.5"
            className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Dome Check */}
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={isDome}
            onChange={(e) => setIsDome(e.target.checked)}
            className="w-4 h-4"
            id="dome-check"
          />
          <label htmlFor="dome-check" className="text-slate-300 cursor-pointer">
            Game is in a dome/indoor stadium (no weather impact)
          </label>
        </div>

        {/* Weather Conditions */}
        {!isDome && (
          <div className="bg-slate-700 rounded-lg p-4 space-y-4">
            <h3 className="text-sm font-semibold text-slate-300">Weather Conditions</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-slate-400 mb-2">
                  Temperature (°F)
                </label>
                <input
                  type="number"
                  value={temperature}
                  onChange={(e) => setTemperature(e.target.value)}
                  placeholder="65"
                  className="w-full bg-slate-600 border border-slate-500 rounded px-3 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm text-slate-400 mb-2">
                  Wind Speed (mph)
                </label>
                <input
                  type="number"
                  value={windSpeed}
                  onChange={(e) => setWindSpeed(e.target.value)}
                  placeholder="10"
                  className="w-full bg-slate-600 border border-slate-500 rounded px-3 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-2">
                Precipitation
              </label>
              <div className="flex gap-3">
                {(['none', 'rain', 'snow'] as const).map(type => (
                  <button
                    key={type}
                    onClick={() => setPrecipitation(type)}
                    className={`px-4 py-2 rounded font-medium transition-colors capitalize ${
                      precipitation === type
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-600 text-slate-300 hover:bg-slate-500'
                    }`}
                  >
                    {type}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Buttons */}
        <div className="flex gap-3">
          <button
            onClick={calculateWeatherImpact}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded font-medium transition-colors"
          >
            Calculate Impact
          </button>
          <button
            onClick={reset}
            className="bg-slate-700 hover:bg-slate-600 text-white px-6 py-2 rounded font-medium transition-colors"
          >
            Reset
          </button>
        </div>

        {/* Results */}
        {result && (
          <div className="space-y-4">
            {/* Adjusted Total */}
            <div className={`rounded-lg p-4 ${
              Math.abs(result.totalAdjustment) >= 2
                ? result.totalAdjustment < 0
                  ? 'bg-blue-900/30 border border-blue-700/50'
                  : 'bg-orange-900/30 border border-orange-700/50'
                : 'bg-slate-700'
            }`}>
              <div className="flex justify-between items-center">
                <div>
                  <div className="text-sm text-slate-400 mb-1">Adjusted Total</div>
                  <div className="text-4xl font-bold text-white">
                    {result.adjustedTotal}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-slate-400 mb-1">Adjustment</div>
                  <div className={`text-3xl font-bold ${
                    result.totalAdjustment < 0 ? 'text-blue-400' :
                    result.totalAdjustment > 0 ? 'text-orange-400' : 'text-slate-400'
                  }`}>
                    {result.totalAdjustment > 0 ? '+' : ''}{result.totalAdjustment.toFixed(1)}
                  </div>
                </div>
              </div>
            </div>

            {/* Breakdown */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-slate-700 rounded-lg p-4">
                <div className="text-sm text-slate-400 mb-1">Temperature</div>
                <div className={`text-2xl font-bold ${
                  result.tempAdjustment < 0 ? 'text-blue-400' :
                  result.tempAdjustment > 0 ? 'text-orange-400' : 'text-slate-300'
                }`}>
                  {result.tempAdjustment > 0 ? '+' : ''}{result.tempAdjustment.toFixed(1)}
                </div>
              </div>

              <div className="bg-slate-700 rounded-lg p-4">
                <div className="text-sm text-slate-400 mb-1">Wind</div>
                <div className={`text-2xl font-bold ${
                  result.windAdjustment < 0 ? 'text-blue-400' :
                  result.windAdjustment > 0 ? 'text-orange-400' : 'text-slate-300'
                }`}>
                  {result.windAdjustment > 0 ? '+' : ''}{result.windAdjustment.toFixed(1)}
                </div>
              </div>

              <div className="bg-slate-700 rounded-lg p-4">
                <div className="text-sm text-slate-400 mb-1">Precipitation</div>
                <div className={`text-2xl font-bold ${
                  result.precipAdjustment < 0 ? 'text-blue-400' :
                  result.precipAdjustment > 0 ? 'text-orange-400' : 'text-slate-300'
                }`}>
                  {result.precipAdjustment > 0 ? '+' : ''}{result.precipAdjustment.toFixed(1)}
                </div>
              </div>
            </div>

            {/* Recommendation */}
            <div className={`rounded-lg p-4 ${
              result.totalAdjustment < -2 ? 'bg-blue-900/30 border border-blue-700/50' :
              result.totalAdjustment > 2 ? 'bg-orange-900/30 border border-orange-700/50' :
              'bg-slate-700'
            }`}>
              <h4 className="text-sm font-semibold text-slate-300 mb-2">Recommendation</h4>
              <p className="text-slate-200">{result.recommendation}</p>
            </div>

            {/* How to Use */}
            <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-blue-400 mb-2">How to bet with weather:</h4>
              <ul className="text-sm text-slate-300 space-y-1">
                <li>• If adjusted total is 2+ points below market, consider Under</li>
                <li>• If adjusted total is 2+ points above market, consider Over</li>
                <li>• Weather impact compounds - multiple factors = bigger edge</li>
                <li>• {sport === 'nfl' ? 'Wind impacts passing games most' : 'Wind direction matters - check if blowing in/out'}</li>
                <li>• Check forecast close to game time for updates</li>
              </ul>
            </div>
          </div>
        )}

        {/* Weather Guidelines */}
        {!result && (
          <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-blue-400 mb-2">
              {sport === 'nfl' ? 'NFL' : 'MLB'} Weather Guidelines
            </h4>
            {sport === 'nfl' ? (
              <ul className="text-sm text-slate-300 space-y-1">
                <li>• <strong>Temperature:</strong> Below 32°F significantly lowers scoring</li>
                <li>• <strong>Wind:</strong> 15+ mph impacts passing game heavily</li>
                <li>• <strong>Rain:</strong> More fumbles, harder to throw, lower scoring</li>
                <li>• <strong>Snow:</strong> Major impact on all aspects of the game</li>
                <li>• <strong>Extreme conditions:</strong> Can create 8+ point swing in totals</li>
              </ul>
            ) : (
              <ul className="text-sm text-slate-300 space-y-1">
                <li>• <strong>Heat:</strong> Ball carries better, more home runs</li>
                <li>• <strong>Wind:</strong> Direction matters - wind out favors hitters</li>
                <li>• <strong>Cold:</strong> Ball doesn't carry as well</li>
                <li>• <strong>Rain:</strong> Games delayed/postponed, affects hitting</li>
                <li>• <strong>Humidity:</strong> High humidity helps ball carry</li>
              </ul>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
