import React from "react";

/**
 * FractionalKellyArticle
 * - Self-contained educational component on Fractional (1/4) Kelly staking
 * - Uses semantic HTML and Tailwind utility classes (optional)
 * - No external UI libs required
 */
export default function FractionalKellyArticle() {
  return (
    <article className="prose prose-neutral max-w-none">
      <header>
        <h1>Fractional Kelly Staking: Why 1/4 Kelly Is a Smart Risk Tool</h1>
        <p className="lead">
          The Kelly Criterion sizes bets based on edge and odds. Full Kelly maximizes long-term
          growth, but it’s usually too aggressive for real-world sports betting. Fractional Kelly
          (like 1/4 Kelly) reduces volatility while still scaling with edge.
        </p>
      </header>

      <section>
        <h2>What is 1/4 Kelly?</h2>
        <p>
          <strong>1/4 Kelly</strong> means staking <strong>25%</strong> of the full Kelly
          recommendation for a given bet. If full Kelly suggests 8% of bankroll, 1/4 Kelly
          recommends 2% of bankroll. Kelly is not fixed; it changes with your estimated win
          probability and the odds.
        </p>
        <ul>
          <li>Dynamic: recalculates for each bet opportunity</li>
          <li>Scaled: 1/4 Kelly = 0.25 × (full Kelly %)</li>
          <li>Safer: substantially lower drawdowns vs full Kelly</li>
        </ul>
      </section>

      <section>
        <h2>Why Not Bet Full Kelly?</h2>
        <p>
          Full Kelly is optimal only if your edge is known precisely and you can tolerate large
          swings. In practice, model noise and estimation error make full Kelly too volatile. Most
          experienced bettors use fractional Kelly (1/2 or 1/4) to reduce risk of drawdowns and
          compounding errors.
        </p>
      </section>

      <section>
        <h2>Example: 1/4 Kelly at -110 with a 55% True Win Probability</h2>
        <p>
          Suppose your model estimates a true win probability of <strong>55%</strong> and the market
          offers <strong>-110</strong>.
        </p>
        <ul>
          <li>Implied probability at -110 is 52.38% (decimal payout ≈ 1.909, so b = 0.909).</li>
          <li>Edge (growth-based) ≈ p × (b + 1) − 1 = 0.55 × 1.909 − 1 = 0.050 (5.0%).</li>
          <li>Full Kelly fraction ≈ edge / b = 0.05 / 0.909 ≈ 5.5% of bankroll.</li>
          <li>Therefore, <strong>1/4 Kelly ≈ 1.4%</strong> of bankroll.</li>
        </ul>
      </section>

      <section>
        <h2>Practical Ranges</h2>
        <p>
          Realistic edges in mature markets are usually modest. Typical 1/4 Kelly stakes often land
          in low single-digit percentages:
        </p>
        <div className="overflow-x-auto">
          <table>
            <thead>
              <tr>
                <th>Estimated Edge</th>
                <th>Full Kelly %</th>
                <th>1/4 Kelly % (Typical)</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>~2–3%</td>
                <td>~2.5–4%</td>
                <td>~0.6–1%</td>
              </tr>
              <tr>
                <td>~4–5%</td>
                <td>~5–7%</td>
                <td>~1.2–1.8%</td>
              </tr>
              <tr>
                <td>~6–7%</td>
                <td>~7–10%</td>
                <td>~1.8–2.5%</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="text-sm">
          Note: These are illustrative. Actual Kelly fractions depend on the odds and your true win
          probability. Many sharp bettors stake roughly 0.5%–2% per play using 1/4 Kelly logic.
        </p>
      </section>

      <section>
        <h2>Key Takeaways</h2>
        <ul>
          <li>Kelly is a dynamic sizing model, not a fixed unit system.</li>
          <li>1/4 Kelly reduces variance while preserving growth advantages.</li>
          <li>Use Kelly only when you have a defensible estimate of your edge.</li>
        </ul>
      </section>
    </article>
  );
}
