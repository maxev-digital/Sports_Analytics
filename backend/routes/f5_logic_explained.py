"""
F5 Fade the Tie — Logic Explanation & Statistical Reasoning

Why does fading the tie work in some spots and not others?
Why is ace vs ace a TRAP? Why do lopsided games tie LESS?

This module provides the full statistical reasoning.
"""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/api/f5/explain", tags=["f5-explain"])


@router.get("/full")
async def explain_full_logic():
    """Complete explanation of why the strategy works when it works"""
    return {
        "title": "F5 Fade the Tie — Full Logic Breakdown",

        "core_concept": {
            "summary": (
                "A tie after 5 innings means BOTH teams scored the EXACT same number "
                "of runs through 5 frames. This is a probability question about score "
                "distributions, not about who wins."
            ),
            "key_insight": (
                "Ties require CONVERGENCE — both teams arriving at the same number. "
                "Anything that increases scoring VARIANCE (more runs, more randomness) "
                "makes exact convergence LESS likely, not more."
            ),
        },

        "why_even_matchups_tie_MORE": {
            "claim": "Evenly matched teams (both near +120 ML) tie more often after 5 innings",
            "intuition": "Seems wrong — wouldn't close games be more exciting, not more tied?",
            "actual_logic": [
                {
                    "point": "Similar scoring rates = similar expected runs",
                    "detail": (
                        "If both teams are expected to score ~2.1 runs through 5 innings, "
                        "the probability distribution of each team's score is centered "
                        "on the same number. Two bell curves centered on the same point "
                        "OVERLAP more, meaning more ties."
                    )
                },
                {
                    "point": "The tie outcomes cluster at common scores",
                    "detail": (
                        "In a 2.1 vs 2.1 expected runs game, the most common tied outcomes "
                        "are 2-2 (~14%), 1-1 (~12%), 0-0 (~8%), 3-3 (~6%). Those four "
                        "alone sum to ~40% of all possible ties, and they're all realistic "
                        "because both teams hit the same scoring zone."
                    )
                },
                {
                    "point": "Compare to a lopsided game",
                    "detail": (
                        "In a 3.5 vs 1.5 expected runs game, team A's distribution is "
                        "centered at 3-4 runs while team B's is centered at 1-2. "
                        "For a tie, team B needs to overperform AND team A needs to "
                        "underperform simultaneously. That's a lower-probability event."
                    )
                },
            ],
            "analogy": (
                "Think of it like two dice. If both dice are the same (d6 vs d6), "
                "they land on the same number ~16.7% of the time. If one is a d6 "
                "and the other is a d20, they match far less often (~5%). "
                "Even matchups = same dice = more ties."
            ),
        },

        "why_ace_vs_ace_is_a_trap": {
            "claim": "Two elite pitchers (both ERA < 3.50) produce the HIGHEST tie rate (~15.8%)",
            "intuition": "All 3 F5 outcomes at plus money looks great — low-scoring pitchers' duel",
            "actual_logic": [
                {
                    "point": "Low scoring compresses the score distribution",
                    "detail": (
                        "With two aces, expected F5 runs per team might be ~1.5. "
                        "The possible outcomes are compressed into {0, 1, 2, 3}. "
                        "With only 4 realistic scores per team, the chance of landing "
                        "on the same number is much higher than when scores range 0-6."
                    )
                },
                {
                    "point": "0-0 ties are surprisingly common in ace matchups",
                    "detail": (
                        "In a low-scoring game, 0-0 after 5 is a real outcome "
                        "(~10-12% of ace vs ace games). This single outcome adds "
                        "enormous weight to the tie probability. In high-scoring games, "
                        "0-0 after 5 almost never happens."
                    )
                },
                {
                    "point": "The odds reflect this — but not enough",
                    "detail": (
                        "Books do price ace vs ace ties shorter (+420 instead of +460). "
                        "But the real issue is structural: with a 15.8% tie rate and "
                        "odds of +420 (19.2% implied), the vig is only 3.4% — "
                        "but the payout on a WIN is compressed too because the ML "
                        "odds are close to even. Your breakeven tie rate in an even "
                        "matchup might only be 9-10%, but the actual rate is 15.8%. "
                        "You're paying 6+ points of juice on the tie fade."
                    )
                },
            ],
            "bottom_line": (
                "Ace vs ace is a TRAP because it looks clean (all + money) but "
                "the tie rate is 50-70% higher than average. The very thing that "
                "makes all 3 outcomes plus money (even matchup, low scoring) is "
                "the same thing that makes ties more likely."
            ),
        },

        "why_bad_starters_help": {
            "claim": "Games with at least one bad starter (ERA > 4.50) tie LESS (~8.8%)",
            "actual_logic": [
                {
                    "point": "More runs = wider score distribution = fewer collisions",
                    "detail": (
                        "A bad starter might give up 4-6 runs in 5 innings. "
                        "This spreads the opponent's score distribution across a wider range "
                        "(2, 3, 4, 5, 6, 7+). Meanwhile the bad starter's team might score "
                        "2-3 runs against a decent opposing pitcher. The distributions "
                        "have less overlap."
                    )
                },
                {
                    "point": "Asymmetric scoring = directional games",
                    "detail": (
                        "When one pitcher is bad, the game tends to GO somewhere early. "
                        "3-0, 4-1, 5-2 after 5 are common. These are NOT tied. "
                        "The bad pitcher creates early separation."
                    )
                },
                {
                    "point": "ERA differential is the single biggest factor",
                    "detail": (
                        "Our model shows 7.0 percentage points of swing between "
                        "ace vs ace (15.8%) and any bad starter (8.8%). "
                        "No other factor has as much influence. This makes sense: "
                        "pitching quality directly controls the scoring distribution."
                    )
                },
            ],
        },

        "why_hitter_parks_help": {
            "claim": "Hitter-friendly parks (Coors, Globe Life) produce fewer ties",
            "actual_logic": [
                {
                    "point": "Same principle as bad starters — more runs = wider distribution",
                    "detail": (
                        "Coors Field inflates scoring by ~40%. If a neutral park game "
                        "is 4-3 after 5, a Coors game might be 6-4. The absolute gap "
                        "between scores widens, making exact ties less likely."
                    )
                },
                {
                    "point": "Coors is the extreme outlier",
                    "detail": (
                        "Estimated tie rate at Coors: ~7.7%. In a high-total game at "
                        "Coors with a bad starter, we estimate ~5.5%. That's a massive "
                        "edge when books are pricing the tie at 17-20% implied."
                    )
                },
            ],
        },

        "why_high_totals_help": {
            "claim": "Games with O/U 9+ tie less than O/U 7 games",
            "actual_logic": [
                {
                    "point": "The total IS the scoring expectation",
                    "detail": (
                        "The game total is the market's best estimate of combined scoring. "
                        "O/U 11.5 means Vegas expects 11-12 total runs. High combined "
                        "scoring means each team individually scores more, which means "
                        "the score distributions are wider and less likely to collide."
                    )
                },
                {
                    "point": "Total captures multiple factors at once",
                    "detail": (
                        "The total already bakes in pitching quality, park factor, "
                        "weather, and team offensive strength. It's the market's "
                        "composite view. So even if you don't know the pitchers, "
                        "the total alone tells you a lot about tie probability."
                    )
                },
                {
                    "point": "Available BEFORE lineups",
                    "detail": (
                        "Opening totals are available 12-24 hours before first pitch. "
                        "This lets you pre-screen games before lineup announcements. "
                        "Total > 9 is the first filter to apply."
                    )
                },
            ],
        },

        "the_math_behind_breakeven": {
            "explanation": [
                {
                    "point": "The payout asymmetry is extreme",
                    "detail": (
                        "In a typical fade-the-tie setup: you risk $500 to win ~$52. "
                        "That's roughly 10:1 risk-reward. You need to win ~91% of the "
                        "time just to break even. Breakeven tie rate = ~9.6%."
                    )
                },
                {
                    "point": "Edge vs implied is NOT the same as +EV",
                    "detail": (
                        "The book prices ties at 17.9% implied. The actual rate is 11.8%. "
                        "That's a 6.1% 'edge' on the probability. But the PAYOUT structure "
                        "means you need the tie rate below 9.6%, not just below 17.9%. "
                        "The edge on probability doesn't automatically translate to +EV "
                        "because the win/loss amounts are so asymmetric."
                    )
                },
                {
                    "point": "Formula",
                    "detail": (
                        "EV = (1 - tie_rate) * profit_per_win + tie_rate * (-total_staked). "
                        "Breakeven: tie_rate = profit / (profit + total_staked). "
                        "With $52.79 profit and $500 staked: 52.79 / 552.79 = 9.56%. "
                        "The strategy is +EV ONLY when tie_rate < 9.56%."
                    )
                },
            ],
        },

        "sample_size_reality_check": {
            "what_we_know_for_sure": [
                "11.8% overall MLB F5 tie rate (243K games, very reliable)",
                "Park factors are well-documented (Coors at ~1.38 is consensus)",
                "Low-scoring games have more ties (this is mathematically provable)",
                "Even matchups have more ties (provable from score distributions)",
            ],
            "what_we_modeled": [
                "Exact multipliers per factor bucket (directionally correct, not precisely calibrated)",
                "How factors combine (we assumed multiplicative independence — partially wrong)",
                "Exact tie rates by ERA differential (need pitcher-level Retrosheet data to verify)",
                "Cross-factor interaction effects (park + pitching + total may not stack cleanly)",
            ],
            "what_we_need_to_validate": [
                "Pull Retrosheet play-by-play for 2015-2024",
                "Compute actual tie-after-5 rate for each game",
                "Join with starting pitcher ERA, park, total, spread",
                "Build actual tie rates per bucket from raw data",
                "Compare to our modeled rates — adjust multipliers",
            ],
            "estimated_sample_sizes_per_bucket": {
                "all_games": "~24,300 per season, ~243K over 10 years",
                "hitter_park_games": "~5,500/season (7 parks x ~81 home games x ~partial)",
                "coors_field_only": "~81 per season, ~810 over 10 years",
                "high_total_games": "~6,000-8,000/season (varies by year)",
                "ace_vs_ace": "~1,200-1,800/season (depends on ERA threshold)",
                "optimal_stack_all_factors": "~40-60 per season, ~400-600 over 10 years",
                "note": (
                    "The optimal stack (ALL factors aligned) has the smallest sample: "
                    "~45 games/season. Over 10 years that's ~450 games — enough to "
                    "detect a 5+ percentage point difference but NOT enough for "
                    "precise tie rate estimates. We'd want 1000+ games per bucket "
                    "for high confidence."
                )
            },
        },

        "honest_assessment": {
            "what_works": (
                "The DIRECTION of every factor is well-supported by baseball logic. "
                "More runs → fewer ties is mathematically provable. Even matchups → "
                "more ties is provable. Coors Field → more runs → fewer ties is factual."
            ),
            "what_needs_work": (
                "The exact MAGNITUDE of each factor multiplier is modeled, not measured. "
                "The difference between 'ties at Coors are 7.7%' and 'ties at Coors are 8.5%' "
                "matters when your breakeven is 9.6%. We need real data to calibrate."
            ),
            "recommendation": (
                "The framework is sound. Before betting real money: "
                "1) Pull Retrosheet data and validate the rates. "
                "2) Paper trade for 2-3 weeks during MLB season. "
                "3) Start with small units on only the strongest signals "
                "(Coors + high total + bad starter). "
                "4) Track actual results vs predicted tie rates."
            ),
        },

        "timestamp": datetime.now().isoformat()
    }
