import React, { useState } from 'react';
import {
  CALIBRATION_METRICS,
  CLV_METRICS,
  TIMELINESS_METRICS,
  REALIZED_RETURNS,
  AB_TEST_RESULTS,
  LATENCY_TARGETS,
  EXAMPLE_ALERT,
  TECH_STACK,
  formatCLV,
  formatROI,
  formatConfidenceInterval
} from '../data/evidenceArchitecture';

/**
 * Evidence & Architecture Page
 *
 * Proves model quality through:
 * - Calibration (Brier score, log-loss vs baselines)
 * - CLV (Closing Line Value - beat the close %)
 * - Timeliness (lead time to market moves)
 * - Realized returns (ROI after costs with confidence intervals)
 *
 * Focus: Show EVIDENCE, not promises. Measure edge through standard market metrics.
 */
export const EvidenceArchitecture: React.FC = () => {
  const [methodologyOpen, setMethodologyOpen] = useState(false);
  const [showSmallSamples, setShowSmallSamples] = useState(false);

  const filteredReturns = showSmallSamples
    ? REALIZED_RETURNS
    : REALIZED_RETURNS.filter(r => r.sample_size >= 100);

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 py-20 px-4 border-b border-slate-800">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-8">
            <h1 className="text-5xl font-bold text-white mb-6">
              Evidence & Architecture
            </h1>
            <p className="text-2xl text-blue-400 font-semibold mb-6">
              Price ≠ True Probability
            </p>
            <p className="text-lg text-slate-300 max-w-3xl mx-auto">
              We collect, process, and predict faster than the market so you can act when{' '}
              <strong className="text-white">price ≠ true probability</strong>. We measure edge by{' '}
              <strong className="text-blue-400">calibration, CLV, and timeliness</strong>, then report{' '}
              <strong className="text-white">realized ROI after costs</strong> with confidence intervals.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-8">
            <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700 text-center">
              <div className="text-blue-400 text-sm font-semibold mb-1">WE PROVE</div>
              <div className="text-white text-lg">Calibration</div>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700 text-center">
              <div className="text-green-400 text-sm font-semibold mb-1">WE TRACK</div>
              <div className="text-white text-lg">CLV</div>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700 text-center">
              <div className="text-purple-400 text-sm font-semibold mb-1">WE MEASURE</div>
              <div className="text-white text-lg">Speed</div>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700 text-center">
              <div className="text-orange-400 text-sm font-semibold mb-1">WE REPORT</div>
              <div className="text-white text-lg">Real ROI</div>
            </div>
          </div>
        </div>
      </section>

      {/* Evidence Section 1: Calibration */}
      <section className="py-16 px-4 bg-slate-900">
        <div className="max-w-6xl mx-auto">
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-white mb-3">
              1. Probability Quality (Calibration)
            </h2>
            <p className="text-slate-400">
              Lower Brier score and log-loss = better probability estimates. We compare against ELO and power rating baselines.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-800 border-b-2 border-slate-700">
                <tr>
                  <th className="text-left p-4 text-slate-300 font-semibold">Sport</th>
                  <th className="text-left p-4 text-slate-300 font-semibold">Model</th>
                  <th className="text-center p-4 text-slate-300 font-semibold">Brier Score</th>
                  <th className="text-center p-4 text-slate-300 font-semibold">Δ vs Baseline</th>
                  <th className="text-center p-4 text-slate-300 font-semibold">Log-Loss</th>
                  <th className="text-center p-4 text-slate-300 font-semibold">Δ vs Baseline</th>
                  <th className="text-center p-4 text-slate-300 font-semibold">N</th>
                </tr>
              </thead>
              <tbody>
                {CALIBRATION_METRICS.map((metric, idx) => {
                  const isOurModel = metric.model.includes('Max EV');
                  return (
                    <tr
                      key={idx}
                      className={`border-b border-slate-800 ${isOurModel ? 'bg-blue-950/20' : ''}`}
                    >
                      <td className="p-4 text-white font-semibold">{metric.sport}</td>
                      <td className="p-4">
                        <span className={isOurModel ? 'text-blue-400' : 'text-slate-400'}>
                          {metric.model}
                        </span>
                      </td>
                      <td className="p-4 text-center text-white">{metric.brier_score.toFixed(3)}</td>
                      <td className="p-4 text-center">
                        {metric.brier_delta_vs_elo !== 0 ? (
                          <span className={metric.brier_delta_vs_elo < 0 ? 'text-green-400 font-semibold' : 'text-red-400'}>
                            {metric.brier_delta_vs_elo.toFixed(3)}
                          </span>
                        ) : (
                          <span className="text-slate-600">—</span>
                        )}
                      </td>
                      <td className="p-4 text-center text-white">{metric.log_loss.toFixed(3)}</td>
                      <td className="p-4 text-center">
                        {metric.log_loss_delta_vs_elo !== 0 ? (
                          <span className={metric.log_loss_delta_vs_elo < 0 ? 'text-green-400 font-semibold' : 'text-red-400'}>
                            {metric.log_loss_delta_vs_elo.toFixed(3)}
                          </span>
                        ) : (
                          <span className="text-slate-600">—</span>
                        )}
                      </td>
                      <td className="p-4 text-center text-slate-400">{metric.sample_size.toLocaleString()}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="mt-6 bg-blue-950/30 border border-blue-800/50 rounded-lg p-4">
            <p className="text-sm text-slate-300">
              <strong className="text-blue-400">Claim:</strong> Across NBA/NHL/NCAAB, Max EV Boost models show{' '}
              <strong className="text-white">lower Brier score and log-loss</strong> than ELO/power baselines in out-of-sample tests.
            </p>
          </div>
        </div>
      </section>

      {/* Evidence Section 2: CLV */}
      <section className="py-16 px-4 bg-slate-950">
        <div className="max-w-6xl mx-auto">
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-white mb-3">
              2. Pricing Efficiency (Beat the Close / CLV)
            </h2>
            <p className="text-slate-400">
              Closing prices are the market's best consensus. Beating them indicates true edge even before outcomes.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-800 border-b-2 border-slate-700">
                <tr>
                  <th className="text-left p-4 text-slate-300 font-semibold">Strategy</th>
                  <th className="text-center p-4 text-slate-300 font-semibold">% Beats Close</th>
                  <th className="text-center p-4 text-slate-300 font-semibold">Median CLV</th>
                  <th className="text-center p-4 text-slate-300 font-semibold">N</th>
                  <th className="text-center p-4 text-slate-300 font-semibold">Window</th>
                </tr>
              </thead>
              <tbody>
                {CLV_METRICS.map((metric, idx) => (
                  <tr key={idx} className="border-b border-slate-800">
                    <td className="p-4 text-white">{metric.strategy}</td>
                    <td className="p-4 text-center">
                      <span className={metric.beats_close_pct > 0.55 ? 'text-green-400 font-semibold' : 'text-yellow-400'}>
                        {(metric.beats_close_pct * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="p-4 text-center">
                      <span className={metric.median_clv_cents > 5 ? 'text-green-400 font-semibold' : 'text-slate-300'}>
                        {formatCLV(metric.median_clv_cents)}
                      </span>
                    </td>
                    <td className="p-4 text-center text-slate-400">{metric.sample_size}</td>
                    <td className="p-4 text-center text-slate-500 text-sm">{metric.data_window}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-6 bg-green-950/30 border border-green-800/50 rounded-lg p-4">
            <p className="text-sm text-slate-300">
              <strong className="text-green-400">Claim:</strong> Our live alerts{' '}
              <strong className="text-white">beat the close more often</strong> than baselines; median CLV is{' '}
              <strong className="text-white">positive</strong> across validated strategies.
            </p>
          </div>
        </div>
      </section>

      {/* Evidence Section 3: Timeliness */}
      <section className="py-16 px-4 bg-slate-900">
        <div className="max-w-6xl mx-auto">
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-white mb-3">
              3. Timeliness (Speed to Information)
            </h2>
            <p className="text-slate-400">
              Median lead time from information shock to our model's fair price vs. first market move.
            </p>
          </div>

          <div className="space-y-4">
            {TIMELINESS_METRICS.map((metric, idx) => (
              <div key={idx} className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-1">{metric.signal_type}</h3>
                    <p className="text-sm text-slate-400">{metric.description}</p>
                  </div>
                  <div className="text-right">
                    <div className="text-3xl font-bold text-purple-400">
                      {metric.median_lead_time_seconds.toFixed(1)}s
                    </div>
                    <div className="text-xs text-slate-500">median lead time</div>
                  </div>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-slate-500">Sample: {metric.sample_size} events</span>
                  <span className="text-purple-400 font-semibold">Faster than market</span>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 bg-purple-950/30 border border-purple-800/50 rounded-lg p-4">
            <p className="text-sm text-slate-300">
              <strong className="text-purple-400">Claim:</strong> Model fair price adjusts{' '}
              <strong className="text-white">faster than the market</strong> during live state changes—especially bonus-imminent (NBA), delayed penalties/goalie pulls (NHL).
            </p>
          </div>
        </div>
      </section>

      {/* Evidence Section 4: Realized Returns */}
      <section className="py-16 px-4 bg-slate-950">
        <div className="max-w-6xl mx-auto">
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-white mb-3">
              4. Realized Returns (After Costs)
            </h2>
            <p className="text-slate-400 mb-4">
              ROI after slippage & rejections, with 95% confidence intervals. Results vary by execution.
            </p>

            <label className="flex items-center gap-2 text-slate-400 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={showSmallSamples}
                onChange={(e) => setShowSmallSamples(e.target.checked)}
                className="rounded"
              />
              Show strategies with N &lt; 100 (potentially unreliable)
            </label>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-800 border-b-2 border-slate-700">
                <tr>
                  <th className="text-left p-4 text-slate-300 font-semibold">Strategy</th>
                  <th className="text-center p-4 text-slate-300 font-semibold">ROI (net)</th>
                  <th className="text-center p-4 text-slate-300 font-semibold">95% CI</th>
                  <th className="text-center p-4 text-slate-300 font-semibold">Sample</th>
                  <th className="text-center p-4 text-slate-300 font-semibold">Avg Odds</th>
                  <th className="text-center p-4 text-slate-300 font-semibold">Min Odds Rule</th>
                </tr>
              </thead>
              <tbody>
                {filteredReturns.map((metric, idx) => (
                  <tr key={idx} className="border-b border-slate-800">
                    <td className="p-4 text-white">{metric.strategy}</td>
                    <td className="p-4 text-center">
                      <span className={metric.roi_net > 0.03 ? 'text-green-400 font-semibold text-lg' :
                                       metric.roi_net > 0 ? 'text-green-300 font-semibold' :
                                       'text-red-400'}>
                        {formatROI(metric.roi_net)}
                      </span>
                    </td>
                    <td className="p-4 text-center text-slate-400 text-sm">
                      {formatConfidenceInterval(metric.confidence_interval_95)}
                    </td>
                    <td className="p-4 text-center">
                      <span className={metric.sample_size < 100 ? 'text-yellow-400' : 'text-slate-300'}>
                        {metric.sample_size}
                      </span>
                    </td>
                    <td className="p-4 text-center text-slate-400">{metric.avg_odds}</td>
                    <td className="p-4 text-center text-slate-500 text-sm">{metric.min_odds_rule}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-6 bg-orange-950/30 border border-orange-800/50 rounded-lg p-4">
            <p className="text-sm text-slate-300">
              <strong className="text-orange-400">Disclosure:</strong> Results vary by sport, season, and user execution. We publish{' '}
              <strong className="text-white">data windows, sample sizes, and assumptions</strong> (slippage curves, min-odds rules).
            </p>
          </div>
        </div>
      </section>

      {/* Example Strategy Card */}
      <section className="py-16 px-4 bg-slate-900">
        <div className="max-w-4xl mx-auto">
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-white mb-3">
              Example: How to Read a Strategy Card
            </h2>
          </div>

          <div className="bg-gradient-to-br from-blue-950 to-slate-900 rounded-xl p-8 border-2 border-blue-600 shadow-2xl">
            <div className="flex justify-between items-start mb-6">
              <div>
                <div className="text-sm text-blue-400 font-semibold mb-1">{EXAMPLE_ALERT.strategy}</div>
                <div className="text-2xl font-bold text-white">{EXAMPLE_ALERT.game}</div>
              </div>
              <div className="bg-green-600 text-white px-4 py-2 rounded-lg font-bold">
                RECOMMENDED
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div className="space-y-3">
                <div>
                  <div className="text-xs text-slate-400 mb-1">Calibrated P(Over)</div>
                  <div className="text-3xl font-bold text-white">{(EXAMPLE_ALERT.calibrated_prob_over * 100).toFixed(1)}%</div>
                  <div className="text-sm text-slate-400">Fair: {EXAMPLE_ALERT.fair_odds_american}</div>
                </div>
                <div>
                  <div className="text-xs text-slate-400 mb-1">Best Available</div>
                  <div className="text-3xl font-bold text-green-400">{EXAMPLE_ALERT.best_available_odds}</div>
                  <div className="text-sm text-slate-400">
                    {EXAMPLE_ALERT.books_with_price} books, {EXAMPLE_ALERT.quote_age_seconds}s ago
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <div>
                  <div className="text-xs text-slate-400 mb-1">Edge</div>
                  <div className="text-3xl font-bold text-blue-400">{EXAMPLE_ALERT.edge_cents}¢</div>
                  <div className="text-sm text-slate-400">After costs</div>
                </div>
                <div>
                  <div className="text-xs text-slate-400 mb-1">Bet Size (¼-Kelly)</div>
                  <div className="text-3xl font-bold text-white">{EXAMPLE_ALERT.kelly_pct.toFixed(1)}%</div>
                  <div className="text-sm text-slate-400">Capped at {EXAMPLE_ALERT.kelly_cap.toFixed(1)}%</div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                <div className="text-xs text-slate-400 mb-1">CLV (Last 30d)</div>
                <div className="text-xl font-bold text-green-400">{formatCLV(EXAMPLE_ALERT.clv_last_30d_median)} median</div>
                <div className="text-sm text-slate-500">N = {EXAMPLE_ALERT.clv_last_30d_sample}</div>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                <div className="text-xs text-slate-400 mb-1">ROI (Last 90d, net)</div>
                <div className="text-xl font-bold text-green-400">{formatROI(EXAMPLE_ALERT.roi_net_last_90d)}</div>
                <div className="text-sm text-slate-500">{formatConfidenceInterval(EXAMPLE_ALERT.roi_ci_95)}</div>
              </div>
            </div>

            <div className="border-t border-slate-700 pt-4">
              <div className="text-xs text-slate-400 mb-2">REASONING:</div>
              <ul className="space-y-1">
                {EXAMPLE_ALERT.reasoning.map((reason, idx) => (
                  <li key={idx} className="text-sm text-slate-300 flex items-start gap-2">
                    <span className="text-blue-400 mt-0.5">•</span>
                    <span>{reason}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="mt-6 text-center text-xs text-slate-500 italic">
              We trigger only when price ≥ fair + cushion after costs, with live guards enabled.
            </div>
          </div>
        </div>
      </section>

      {/* A/B Test Results */}
      <section className="py-16 px-4 bg-slate-950">
        <div className="max-w-6xl mx-auto">
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-white mb-3">
              5. A/B Test: Strategy-Only vs ML-Enhanced
            </h2>
            <p className="text-slate-400">
              10-20% canary testing shows ML-enhanced signals have higher CLV and better calibration.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-800 border-b-2 border-slate-700">
                <tr>
                  <th className="text-left p-4 text-slate-300 font-semibold">Strategy</th>
                  <th className="text-center p-4 text-slate-300 font-semibold">Variant</th>
                  <th className="text-center p-4 text-slate-300 font-semibold">ΔCLV (¢)</th>
                  <th className="text-center p-4 text-slate-300 font-semibold">ΔBrier</th>
                  <th className="text-center p-4 text-slate-300 font-semibold">ΔROI (net)</th>
                  <th className="text-center p-4 text-slate-300 font-semibold">p-value</th>
                </tr>
              </thead>
              <tbody>
                {AB_TEST_RESULTS.map((result, idx) => (
                  <tr
                    key={idx}
                    className={`border-b border-slate-800 ${result.variant === 'ML-Enhanced' ? 'bg-blue-950/20' : ''}`}
                  >
                    <td className="p-4 text-white">{result.strategy}</td>
                    <td className="p-4 text-center">
                      <span className={result.variant === 'ML-Enhanced' ? 'text-blue-400 font-semibold' : 'text-slate-400'}>
                        {result.variant}
                      </span>
                    </td>
                    <td className="p-4 text-center">
                      {result.delta_clv_cents !== 0 ? (
                        <span className="text-green-400 font-semibold">{formatCLV(result.delta_clv_cents)}</span>
                      ) : (
                        <span className="text-slate-600">—</span>
                      )}
                    </td>
                    <td className="p-4 text-center">
                      {result.delta_brier !== 0 ? (
                        <span className="text-green-400 font-semibold">{result.delta_brier.toFixed(3)}</span>
                      ) : (
                        <span className="text-slate-600">—</span>
                      )}
                    </td>
                    <td className="p-4 text-center">
                      {result.delta_roi_net !== 0 ? (
                        <span className="text-green-400 font-semibold">{formatROI(result.delta_roi_net)}</span>
                      ) : (
                        <span className="text-slate-600">—</span>
                      )}
                    </td>
                    <td className="p-4 text-center">
                      {result.p_value !== 1.0 ? (
                        <span className={result.significant ? 'text-green-400 font-semibold' : 'text-yellow-400'}>
                          {result.p_value.toFixed(3)}
                        </span>
                      ) : (
                        <span className="text-slate-600">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Methodology Drawer */}
      <section className="py-8 px-4 bg-slate-900 border-t border-slate-800">
        <div className="max-w-6xl mx-auto">
          <button
            onClick={() => setMethodologyOpen(!methodologyOpen)}
            className="w-full flex items-center justify-between p-4 bg-slate-800 hover:bg-slate-750 rounded-lg transition-colors"
          >
            <span className="text-lg font-semibold text-white">Methodology & Disclosures</span>
            <svg
              className={`w-6 h-6 text-slate-400 transform transition-transform ${methodologyOpen ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {methodologyOpen && (
            <div className="mt-4 bg-slate-800/50 rounded-lg p-6 border border-slate-700 space-y-4">
              <div>
                <h3 className="text-lg font-semibold text-white mb-2">Backtest Protocol</h3>
                <p className="text-slate-400 text-sm">
                  Walk-forward by date; grouped cross-validation by event; no tick leakage. Features versioned and timestamped.
                </p>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-white mb-2">Costs & Slippage</h3>
                <p className="text-slate-400 text-sm">
                  Slippage modeled by book and quote-age; realistic fill probabilities; cushion applied before alerts.
                </p>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-white mb-2">Guards</h3>
                <ul className="text-slate-400 text-sm space-y-1">
                  <li>• Quote-age ≤ 4 seconds (drop stale quotes)</li>
                  <li>• Two-book confirmation (optional)</li>
                  <li>• Dispersion check (block if cross-book spread suggests move in flight)</li>
                </ul>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-white mb-2">Calibration</h3>
                <p className="text-slate-400 text-sm">
                  Isotonic/Platt scaling per model_version; always report both raw and calibrated probabilities.
                </p>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-white mb-2">Uncertainty</h3>
                <p className="text-slate-400 text-sm">
                  Conformal prediction intervals for totals/spreads (80%/95% confidence bands).
                </p>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-white mb-2">Disclaimer</h3>
                <p className="text-slate-400 text-sm italic">
                  Past performance does not guarantee future results. Availability and fills vary by user, book, and jurisdiction.
                  We measure edge through standard market metrics (calibration, CLV, timeliness) but cannot guarantee profits.
                </p>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* What We Don't Claim */}
      <section className="py-16 px-4 bg-red-950/20 border-t border-red-900/50">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-6">What We Don't Claim</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-slate-900/50 rounded-lg p-6 border border-red-800/50">
              <div className="text-4xl mb-3">❌</div>
              <p className="text-white font-semibold mb-2">No Fixed ROI Guarantees</p>
              <p className="text-sm text-slate-400">Markets change. We show evidence, not promises.</p>
            </div>

            <div className="bg-slate-900/50 rounded-lg p-6 border border-red-800/50">
              <div className="text-4xl mb-3">❌</div>
              <p className="text-white font-semibold mb-2">No "Always Win"</p>
              <p className="text-sm text-slate-400">Edge means winning more often than losing, not every time.</p>
            </div>

            <div className="bg-slate-900/50 rounded-lg p-6 border border-red-800/50">
              <div className="text-4xl mb-3">✅</div>
              <p className="text-white font-semibold mb-2">Evidence & Controls</p>
              <p className="text-sm text-slate-400">We show proof so you can make informed decisions.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Latency Targets */}
      <section className="py-16 px-4 bg-slate-900">
        <div className="max-w-4xl mx-auto">
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-white mb-3">System Latency (P95)</h2>
            <p className="text-slate-400">End-to-end: odds tick → user alert in under 450ms</p>
          </div>

          <div className="space-y-3">
            {LATENCY_TARGETS.map((target, idx) => {
              const onTarget = target.actual_p95_ms ? target.actual_p95_ms <= target.budget_ms : null;
              return (
                <div key={idx} className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                  <div className="flex justify-between items-center">
                    <div>
                      <div className="text-white font-semibold">{target.stage}</div>
                      <div className="text-sm text-slate-400">Budget: {target.budget_ms}ms</div>
                    </div>
                    {target.actual_p95_ms && (
                      <div className="text-right">
                        <div className={`text-2xl font-bold ${onTarget ? 'text-green-400' : 'text-red-400'}`}>
                          {target.actual_p95_ms}ms
                        </div>
                        <div className="text-xs text-slate-500">actual P95</div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>
    </div>
  );
};
