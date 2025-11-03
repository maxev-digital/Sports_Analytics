import { Navigation } from '../components/Navigation';
import { Footer } from '../components/Footer';

export function Disclaimer() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white flex flex-col">
      <Navigation />

      <main className="flex-1 container mx-auto px-4 py-12 max-w-5xl">
        <h1 className="text-4xl font-bold text-red-400 mb-2">Full Disclaimer</h1>
        <p className="text-slate-400 mb-8">Last Updated: January 2, 2025</p>

        <div className="bg-slate-900/50 border border-red-900/50 rounded-lg p-8 space-y-6 text-slate-300 leading-relaxed">

          <div className="bg-red-900/20 border-2 border-red-500 rounded-lg p-6">
            <h2 className="text-2xl font-bold text-red-400 mb-3">⚠️ IMPORTANT: READ CAREFULLY</h2>
            <p className="text-lg">
              <strong>Max EV Sports is an informational and educational platform ONLY.</strong> We provide sports betting analytics,
              alerts, and tools but <strong className="text-red-400">WE DO NOT ACCEPT, PLACE, OR FACILITATE BETS.</strong> All betting
              is conducted through licensed third-party sportsbooks.
            </p>
          </div>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">1. Not Financial or Gambling Advice</h2>
            <p className="text-lg mb-3">
              <strong className="text-red-400">NOTHING ON THIS PLATFORM CONSTITUTES FINANCIAL, INVESTMENT, OR GAMBLING ADVICE.</strong>
            </p>
            <p className="mb-3">
              All content, including alerts, predictions, analytics, strategies, articles, and performance metrics are provided for
              <strong> informational and entertainment purposes only</strong>. You should not rely on any information from this Platform
              as a substitute for professional advice.
            </p>
            <p>
              <strong>You are solely responsible for your betting decisions and any resulting financial losses.</strong>
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">2. No Guarantees of Profitability</h2>
            <p className="mb-3">
              <strong className="text-yellow-400">WE MAKE NO GUARANTEES REGARDING PROFITABILITY, ACCURACY, OR SUCCESS OF ANY ALERTS, STRATEGIES, OR PREDICTIONS.</strong>
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Past performance does NOT guarantee future results</li>
              <li>Historical win rates do NOT predict future outcomes</li>
              <li>Alerts may become stale, inaccurate, or unprofitable before you can act on them</li>
              <li>Odds change rapidly and may differ from displayed values</li>
              <li>System alerts and strategies can and will experience losing periods</li>
              <li>Individual results will vary significantly</li>
            </ul>
            <p className="mt-3 text-lg">
              <strong className="text-red-400">You can and likely will lose money betting on sports.</strong>
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">3. Inherent Risks of Sports Betting</h2>
            <p className="mb-3">Sports betting involves substantial risk. You should be aware that:</p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li><strong>Loss of Capital:</strong> You can lose all money you wager</li>
              <li><strong>Addiction Risk:</strong> Gambling can be addictive and lead to financial ruin</li>
              <li><strong>Emotional Impact:</strong> Losses can cause stress, anxiety, and relationship problems</li>
              <li><strong>No Skill Guarantee:</strong> Even skilled analysis does not eliminate variance and luck</li>
              <li><strong>House Edge:</strong> Sportsbooks have built-in advantages (vig/juice) that favor them long-term</li>
              <li><strong>Unpredictable Events:</strong> Injuries, weather, referee decisions, and random events affect outcomes</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">4. Accuracy and Timeliness of Information</h2>
            <p className="mb-3">
              While we strive to provide accurate and timely information, we cannot guarantee:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li><strong>Odds Accuracy:</strong> Odds are sourced from third parties and may be delayed or incorrect</li>
              <li><strong>Alert Timeliness:</strong> Arbitrage and middle opportunities can close within seconds</li>
              <li><strong>Data Accuracy:</strong> Statistics, team information, and predictions may contain errors</li>
              <li><strong>System Availability:</strong> Platform outages or technical issues may prevent access to alerts</li>
              <li><strong>API Limitations:</strong> Third-party data providers may experience downtime or rate limits</li>
            </ul>
            <p className="mt-3 text-yellow-400 font-semibold">
              Always verify odds and information directly with the sportsbook before placing bets.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">5. Alert Types and Limitations</h2>

            <h3 className="text-xl font-semibold text-white mb-2">5.1 Arbitrage Alerts</h3>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Arbitrage opportunities may close within seconds</li>
              <li>Sportsbooks may limit or ban accounts that consistently exploit arbitrage</li>
              <li>Minimum profit margins may be too small to cover transaction costs</li>
              <li>Odds may change before you can place both sides of the bet</li>
            </ul>

            <h3 className="text-xl font-semibold text-white mt-4 mb-2">5.2 Steam Moves and Line Movement</h3>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Line movement does not guarantee sharp money or winning bets</li>
              <li>Reverse line movement can occur</li>
              <li>Public money can drive lines in the wrong direction</li>
            </ul>

            <h3 className="text-xl font-semibold text-white mt-4 mb-2">5.3 Middle Alerts</h3>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Middles are low-probability events</li>
              <li>Most middles result in one win and one loss (break-even minus vig)</li>
              <li>True middles (both bets winning) are rare</li>
            </ul>

            <h3 className="text-xl font-semibold text-white mt-4 mb-2">5.4 Live Betting Strategies</h3>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Live odds change extremely rapidly</li>
              <li>Increased variance and unpredictability</li>
              <li>Emotional decision-making risk</li>
              <li>Limited time to analyze</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">6. Performance Metrics and Backtesting</h2>
            <p className="mb-3">
              Historical performance metrics, win rates, and backtesting results displayed on the Platform:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Are based on historical data and theoretical assumptions</li>
              <li>Do not account for real-world limitations (bet limits, account restrictions, delays)</li>
              <li>May suffer from data mining bias or curve-fitting</li>
              <li>Do not reflect actual user results</li>
              <li>Cannot predict future performance</li>
              <li>May not include all costs (transaction fees, vig, taxes)</li>
            </ul>
            <p className="mt-3 text-yellow-400 font-semibold">
              Past performance is not indicative of future results.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">7. User Responsibility</h2>
            <p className="mb-3">By using Max EV Sports, you acknowledge that:</p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>You are solely responsible for all betting decisions</li>
              <li>You will only bet money you can afford to lose</li>
              <li>You will comply with all applicable laws in your jurisdiction</li>
              <li>You are of legal gambling age (21+ or applicable age in your area)</li>
              <li>You will not hold Max EV Holdings, LLC liable for any losses</li>
              <li>You will conduct your own due diligence before placing bets</li>
              <li>You understand the risks of gambling and will gamble responsibly</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">8. Third-Party Sportsbooks</h2>
            <p className="mb-3">
              We provide links to third-party sportsbooks for convenience only. We are not responsible for:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>The actions, terms, or policies of third-party sportsbooks</li>
              <li>Deposit or withdrawal issues with sportsbooks</li>
              <li>Disputes between you and sportsbooks</li>
              <li>Account limitations, closures, or restrictions</li>
              <li>Payout delays or denials</li>
              <li>Security or privacy practices of third parties</li>
            </ul>
            <p className="mt-3">
              Your relationship with sportsbooks is governed by their respective terms and conditions.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">9. No Professional Relationship</h2>
            <p>
              Use of this Platform does not create any professional relationship (financial advisor, investment advisor, gambling
              counselor, etc.) between you and Max EV Holdings, LLC or its employees. We are an informational service only.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">10. Legal and Regulatory Compliance</h2>
            <p className="mb-3">
              <strong className="text-yellow-400">You are solely responsible for ensuring your use of this Platform and all betting
              activities comply with laws in your jurisdiction.</strong>
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Sports betting laws vary by state, country, and jurisdiction</li>
              <li>Some jurisdictions prohibit online sports betting entirely</li>
              <li>Age requirements vary by location</li>
              <li>Tax obligations on gambling winnings vary by jurisdiction</li>
            </ul>
            <p className="mt-3">
              <strong>You must not use this Platform if doing so would violate laws in your area.</strong>
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">11. Limitation of Liability</h2>
            <p className="mb-3">
              <strong className="text-red-400">TO THE MAXIMUM EXTENT PERMITTED BY LAW, MAX EV HOLDINGS, LLC AND ITS OFFICERS,
              DIRECTORS, EMPLOYEES, AND AGENTS SHALL NOT BE LIABLE FOR ANY LOSSES OR DAMAGES ARISING FROM:</strong>
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Betting losses based on alerts, analytics, or information from the Platform</li>
              <li>Inaccurate, delayed, or missing data</li>
              <li>Technical errors, system outages, or service interruptions</li>
              <li>Unauthorized access to your account</li>
              <li>Actions of third-party sportsbooks</li>
              <li>Changes in odds or line movements</li>
              <li>Any consequential, indirect, incidental, or punitive damages</li>
            </ul>
            <p className="mt-3 text-lg">
              <strong>YOUR USE OF THIS PLATFORM IS AT YOUR OWN RISK.</strong>
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">12. Responsible Gambling Resources</h2>
            <div className="bg-blue-900/20 border-2 border-blue-500 rounded-lg p-6">
              <p className="text-lg mb-3">
                <strong>If you or someone you know has a gambling problem, help is available:</strong>
              </p>
              <ul className="space-y-2">
                <li>
                  <strong>National Council on Problem Gambling:</strong><br/>
                  <a href="tel:1-800-522-4700" className="text-blue-400 underline hover:text-blue-300">1-800-GAMBLER (1-800-522-4700)</a>
                </li>
                <li>
                  <strong>Website:</strong><br/>
                  <a href="https://www.ncpgambling.org" className="text-blue-400 underline hover:text-blue-300" target="_blank" rel="noopener noreferrer">ncpgambling.org</a>
                </li>
                <li>
                  <strong>Text Support:</strong><br/>
                  Text "GAMBLER" to 53342
                </li>
                <li>
                  <strong>Gamblers Anonymous:</strong><br/>
                  <a href="https://www.gamblersanonymous.org" className="text-blue-400 underline hover:text-blue-300" target="_blank" rel="noopener noreferrer">gamblersanonymous.org</a>
                </li>
              </ul>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">13. Educational Purpose</h2>
            <p>
              Content on this Platform, including articles, strategies, and educational material, is for educational purposes only.
              Educational content does not constitute advice or recommendations. Always conduct your own research and analysis.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">14. Changes to Disclaimer</h2>
            <p>
              We reserve the right to modify this Disclaimer at any time. Your continued use of the Platform after changes
              constitutes acceptance of the modified Disclaimer.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">15. Contact Information</h2>
            <p>
              If you have questions about this Disclaimer, please contact us:
            </p>
            <div className="mt-2 ml-4">
              <p><strong>Max EV Holdings, LLC</strong></p>
              <p>Email: <a href="mailto:support@max-ev-sports.com" className="text-yellow-400 underline hover:text-yellow-300">support@max-ev-sports.com</a></p>
              <p className="mt-2">Wyoming Limited Liability Company</p>
              <p>Filing ID: 2025-001800389</p>
            </div>
          </section>

          <div className="bg-red-900/20 border-2 border-red-500 rounded-lg p-6 mt-8">
            <p className="text-lg text-center">
              <strong className="text-red-400">BY USING MAX EV SPORTS, YOU ACKNOWLEDGE THAT YOU HAVE READ, UNDERSTOOD, AND AGREE
              TO THIS DISCLAIMER AND ACCEPT ALL RISKS ASSOCIATED WITH SPORTS BETTING.</strong>
            </p>
          </div>

        </div>
      </main>

      <Footer />
    </div>
  );
}
