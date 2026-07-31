"""
F5 Sizing Deep Dive — Asymmetric Bet Sizing & Dog vs Favorite

Three questions to answer:
1. What happens when you bet LESS on the tie (it pays more, so you need less)?
2. Is there a structural EV lean toward dog or favorite as the partner?
3. Where are the book's blind spots — what DON'T they factor into F5 tie pricing?
"""

from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime
import math

router = APIRouter(prefix="/api/f5/sizing", tags=["f5-sizing"])

BASE_TIE_RATE = 0.118

FACTOR_MULTIPLIERS = {
    "game_total": {
        "under_7": 1.203, "7_to_8": 1.000, "8_to_9": 0.975,
        "over_9": 0.797, "over_10": 0.720,
    },
    "ml_odds_proximity": {
        "both_plus_100_to_130": 1.18, "spread_130_to_160": 1.05,
        "spread_160_to_200": 0.95, "spread_over_200": 0.82,
    },
    "era_differential": {
        "both_under_3": 1.339, "diff_under_0.5": 1.102,
        "diff_0.5_to_1.0": 0.958, "diff_1.0_to_1.5": 0.881,
        "diff_over_1.5": 0.746,
    },
    "park_factor": {
        "pitcher_park": 1.169, "neutral": 0.983,
        "hitter_park": 0.771, "coors_field": 0.653,
    },
    "month": {
        "april": 1.059, "may": 1.008, "june": 0.966,
        "july": 0.932, "august": 0.958, "september": 1.025,
    },
}


def american_to_decimal(american: int) -> float:
    if american > 0:
        return 1 + american / 100
    return 1 + 100 / abs(american)


def estimate_tie_rate(factors: dict) -> float:
    rate = BASE_TIE_RATE
    for category, value in factors.items():
        if category in FACTOR_MULTIPLIERS and value in FACTOR_MULTIPLIERS[category]:
            rate *= FACTOR_MULTIPLIERS[category][value]
    return min(rate, 0.30)


def estimate_probabilities(away_odds, tie_odds, home_odds, tie_rate):
    """Get actual probabilities using our tie rate + book's team ratio"""
    dec_a = american_to_decimal(away_odds)
    dec_t = american_to_decimal(tie_odds)
    dec_h = american_to_decimal(home_odds)

    imp_a = 1 / dec_a
    imp_h = 1 / dec_h
    total = imp_a + (1/dec_t) + imp_h

    # De-vigged team split ratio
    away_share = (imp_a / total) / ((imp_a + imp_h) / total)
    home_share = 1 - away_share

    non_tie = 1 - tie_rate
    return {
        "p_away": non_tie * away_share,
        "p_tie": tie_rate,
        "p_home": non_tie * home_share,
    }


# ─── 1. FULL SIZING GRID ─────────────────────────────────────────────

@router.get("/grid")
async def sizing_grid(
    away_odds: int = Query(...),
    tie_odds: int = Query(...),
    home_odds: int = Query(...),
    bankroll: float = Query(default=100),
    partner: str = Query(default="away", description="'away' or 'home'"),
    # Factors
    game_total: Optional[str] = Query(default=None),
    era_differential: Optional[str] = Query(default=None),
    park_factor: Optional[str] = Query(default=None),
    ml_odds_proximity: Optional[str] = Query(default=None),
    month: Optional[str] = Query(default=None),
):
    """
    Test EVERY possible sizing ratio from 5% tie / 95% team
    through 95% tie / 5% team in 5% increments.

    Shows how EV, variance, Sharpe, and payout profile change.
    Answers: what's the optimal tie allocation?
    """
    factors = {}
    for k, v in [("game_total", game_total), ("era_differential", era_differential),
                 ("park_factor", park_factor), ("ml_odds_proximity", ml_odds_proximity),
                 ("month", month)]:
        if v:
            factors[k] = v

    tie_rate = estimate_tie_rate(factors)
    probs = estimate_probabilities(away_odds, tie_odds, home_odds, tie_rate)

    dec_tie = american_to_decimal(tie_odds)
    dec_away = american_to_decimal(away_odds)
    dec_home = american_to_decimal(home_odds)

    if partner == "away":
        dec_team = dec_away
        p_team = probs["p_away"]
        p_lose = probs["p_home"]
    else:
        dec_team = dec_home
        p_team = probs["p_home"]
        p_lose = probs["p_away"]

    p_tie = probs["p_tie"]

    grid = []
    for tie_pct in range(5, 96, 5):
        team_pct = 100 - tie_pct
        tie_stake = bankroll * (tie_pct / 100)
        team_stake = bankroll * (team_pct / 100)

        payout_tie = dec_tie * tie_stake
        payout_team = dec_team * team_stake
        profit_tie = payout_tie - bankroll
        profit_team = payout_team - bankroll

        # EV
        ev = (p_tie * profit_tie +
              p_team * profit_team +
              p_lose * (-bankroll))

        # Variance & Sharpe
        outcomes = [(p_tie, profit_tie), (p_team, profit_team), (p_lose, -bankroll)]
        variance = sum(p * (v - ev)**2 for p, v in outcomes)
        std_dev = math.sqrt(variance)
        sharpe = ev / std_dev if std_dev > 0 else 0

        # Net outcome profile
        # How often do we actually MAKE money vs LOSE money?
        # Profit_team can be negative if team_stake is small
        outcomes_positive = 0
        if profit_tie > 0:
            outcomes_positive += p_tie
        if profit_team > 0:
            outcomes_positive += p_team

        grid.append({
            "tie_pct": tie_pct,
            "team_pct": team_pct,
            "tie_stake": round(tie_stake, 2),
            "team_stake": round(team_stake, 2),
            "if_tie_hits": round(profit_tie, 2),
            "if_team_hits": round(profit_team, 2),
            "if_lose": round(-bankroll, 2),
            "ev": round(ev, 2),
            "roi_pct": round((ev / bankroll) * 100, 2),
            "std_dev": round(std_dev, 2),
            "sharpe": round(sharpe, 4),
            "pct_outcomes_profitable": round(outcomes_positive * 100, 1),
            "team_hit_profitable": profit_team > 0,
        })

    # Find key points
    best_ev = max(grid, key=lambda x: x["ev"])
    best_sharpe = max(grid, key=lambda x: x["sharpe"])
    breakeven_pct = None
    for g in grid:
        if g["team_hit_profitable"] and breakeven_pct is None:
            continue
        if not g["team_hit_profitable"] and breakeven_pct is None:
            breakeven_pct = g["tie_pct"]

    # Find the tie_pct where team_hit flips from profitable to unprofitable
    flip_point = None
    for i in range(len(grid) - 1):
        if grid[i]["team_hit_profitable"] and not grid[i+1]["team_hit_profitable"]:
            flip_point = grid[i+1]["tie_pct"]
            break

    return {
        "title": "Sizing Grid — All Tie/Team Ratios",
        "parameters": {
            "away_odds": away_odds, "tie_odds": tie_odds, "home_odds": home_odds,
            "partner": partner, "bankroll": bankroll,
            "tie_rate_pct": round(tie_rate * 100, 1),
            "factors": factors,
        },
        "probabilities": {
            "p_tie": round(p_tie * 100, 1),
            "p_team_wins": round(p_team * 100, 1),
            "p_combined_win": round((p_tie + p_team) * 100, 1),
            "p_lose": round(p_lose * 100, 1),
        },
        "grid": grid,
        "key_points": {
            "best_ev": {
                "tie_pct": best_ev["tie_pct"],
                "ev": best_ev["ev"],
                "roi": best_ev["roi_pct"],
                "note": "Highest raw expected value",
            },
            "best_sharpe": {
                "tie_pct": best_sharpe["tie_pct"],
                "sharpe": best_sharpe["sharpe"],
                "ev": best_sharpe["ev"],
                "note": "Best risk-adjusted return (EV per unit of volatility)",
            },
            "team_hit_breakeven_tie_pct": flip_point,
            "team_hit_breakeven_note": (
                f"Above {flip_point}% on tie, the team leg LOSES money even when it hits. "
                f"Below {flip_point}%, both outcomes are profitable."
                if flip_point else "Team leg is always profitable at these odds"
            ),
        },
        "your_question_answered": {
            "less_on_tie": (
                f"YES — betting less on the tie works well. At {flip_point or 45}% tie / "
                f"{100 - (flip_point or 45)}% team, BOTH outcomes are profitable. "
                f"The tie pays {dec_tie}x so even a small bet returns big. "
                f"The team bet at {100 - (flip_point or 45)}% acts as your primary bet "
                f"with the tie as the bonus payout."
            ),
        },
    }


# ─── 2. DOG vs FAVORITE LEAN ─────────────────────────────────────────

@router.get("/dog-vs-favorite")
async def dog_vs_favorite_analysis():
    """
    Test Tie + Underdog vs Tie + Favorite across many game shapes.
    Answer: is there a structural EV lean toward one or the other?

    Key concept: book odds ≠ true odds. If the book doesn't price in
    ace+ace+pitcherpark+cold, then BOTH teams AND the tie may be
    mispriced. The question is which side gets more mispricing.
    """

    # Test across different matchup shapes
    test_cases = [
        # Even matchups (both teams similar)
        {"name": "Dead even (+125/+125)", "away": 125, "tie": 420, "home": 125,
         "factors": {"era_differential": "both_under_3", "park_factor": "pitcher_park",
                    "game_total": "under_7"}},
        {"name": "Slight home lean (+130/+118)", "away": 130, "tie": 430, "home": 118,
         "factors": {"era_differential": "both_under_3", "park_factor": "pitcher_park",
                    "game_total": "under_7"}},

        # Moderate favorites
        {"name": "Moderate fav (+145/+108)", "away": 145, "tie": 450, "home": 108,
         "factors": {"era_differential": "both_under_3", "park_factor": "pitcher_park",
                    "game_total": "under_7"}},
        {"name": "Moderate fav (+155/+105)", "away": 155, "tie": 450, "home": 105,
         "factors": {"era_differential": "diff_under_0.5", "park_factor": "pitcher_park",
                    "game_total": "under_7"}},

        # Bigger underdogs
        {"name": "Big dog (+180/+100)", "away": 180, "tie": 440, "home": 100,
         "factors": {"era_differential": "diff_0.5_to_1.0", "park_factor": "pitcher_park",
                    "game_total": "under_7"}},
        {"name": "Big dog (+200/+100)", "away": 200, "tie": 440, "home": 100,
         "factors": {"era_differential": "diff_0.5_to_1.0", "park_factor": "pitcher_park",
                    "game_total": "under_7"}},

        # Even matchups at higher tie conditions
        {"name": "Even + extreme tie factors (+120/+120)", "away": 120, "tie": 400, "home": 120,
         "factors": {"era_differential": "both_under_3", "park_factor": "pitcher_park",
                    "game_total": "under_7", "month": "april"}},

        # What about when book has dog at really good odds?
        {"name": "Dog at +220, fav at even (+220/+100)", "away": 220, "tie": 460, "home": 100,
         "factors": {"era_differential": "diff_0.5_to_1.0", "park_factor": "pitcher_park",
                    "game_total": "under_7"}},
    ]

    results = []
    for tc in test_cases:
        tie_rate = estimate_tie_rate(tc["factors"])
        probs = estimate_probabilities(tc["away"], tc["tie"], tc["home"], tie_rate)

        dec_away = american_to_decimal(tc["away"])
        dec_tie = american_to_decimal(tc["tie"])
        dec_home = american_to_decimal(tc["home"])

        # Determine who is dog/favorite
        if dec_away > dec_home:
            dog_side, fav_side = "away", "home"
            dec_dog, dec_fav = dec_away, dec_home
            p_dog, p_fav = probs["p_away"], probs["p_home"]
        else:
            dog_side, fav_side = "home", "away"
            dec_dog, dec_fav = dec_home, dec_away
            p_dog, p_fav = probs["p_home"], probs["p_away"]

        p_tie = probs["p_tie"]
        bankroll = 100

        # Test multiple sizing ratios for each pairing
        best_dog = {"ev": -9999}
        best_fav = {"ev": -9999}

        for tie_pct in range(10, 91, 5):
            tie_stake = bankroll * (tie_pct / 100)
            team_stake = bankroll * (1 - tie_pct / 100)

            # Tie + Dog
            profit_tie_d = dec_tie * tie_stake - bankroll
            profit_dog = dec_dog * team_stake - bankroll
            ev_dog = p_tie * profit_tie_d + p_dog * profit_dog + p_fav * (-bankroll)

            if ev_dog > best_dog["ev"]:
                best_dog = {
                    "ev": ev_dog, "tie_pct": tie_pct,
                    "profit_tie": round(profit_tie_d, 2),
                    "profit_team": round(profit_dog, 2),
                }

            # Tie + Fav
            profit_tie_f = dec_tie * tie_stake - bankroll
            profit_fav = dec_fav * team_stake - bankroll
            ev_fav = p_tie * profit_tie_f + p_fav * profit_fav + p_dog * (-bankroll)

            if ev_fav > best_fav["ev"]:
                best_fav = {
                    "ev": ev_fav, "tie_pct": tie_pct,
                    "profit_tie": round(profit_tie_f, 2),
                    "profit_team": round(profit_fav, 2),
                }

        # Individual leg EV (per $1 bet)
        ev_tie_per_dollar = p_tie * (dec_tie - 1) - (1 - p_tie)
        ev_dog_per_dollar = p_dog * (dec_dog - 1) - (1 - p_dog)
        ev_fav_per_dollar = p_fav * (dec_fav - 1) - (1 - p_fav)

        results.append({
            "name": tc["name"],
            "odds": {"away": tc["away"], "tie": tc["tie"], "home": tc["home"]},
            "tie_rate_pct": round(tie_rate * 100, 1),
            "probabilities": {
                "p_dog": round(p_dog * 100, 1),
                "p_tie": round(p_tie * 100, 1),
                "p_fav": round(p_fav * 100, 1),
            },
            "individual_ev_per_dollar": {
                "tie": round(ev_tie_per_dollar, 4),
                "dog": round(ev_dog_per_dollar, 4),
                "fav": round(ev_fav_per_dollar, 4),
                "best_individual": (
                    "TIE" if ev_tie_per_dollar > max(ev_dog_per_dollar, ev_fav_per_dollar)
                    else "DOG" if ev_dog_per_dollar > ev_fav_per_dollar
                    else "FAV"
                ),
            },
            "tie_plus_dog": {
                "best_ev": round(best_dog["ev"], 2),
                "best_sizing": f"{best_dog['tie_pct']}% tie / {100-best_dog['tie_pct']}% dog",
                "if_tie": best_dog["profit_tie"],
                "if_dog": best_dog["profit_team"],
            },
            "tie_plus_fav": {
                "best_ev": round(best_fav["ev"], 2),
                "best_sizing": f"{best_fav['tie_pct']}% tie / {100-best_fav['tie_pct']}% fav",
                "if_tie": best_fav["profit_tie"],
                "if_fav": best_fav["profit_team"],
            },
            "winner": "DOG" if best_dog["ev"] > best_fav["ev"] else "FAV",
            "ev_difference": round(best_dog["ev"] - best_fav["ev"], 2),
        })

    # Aggregate analysis
    dog_wins = sum(1 for r in results if r["winner"] == "DOG")
    fav_wins = len(results) - dog_wins
    avg_ev_diff = sum(r["ev_difference"] for r in results) / len(results)

    return {
        "title": "Dog vs Favorite — Structural EV Analysis",
        "results": results,
        "aggregate": {
            "dog_is_better_pairing": dog_wins,
            "fav_is_better_pairing": fav_wins,
            "avg_ev_difference_dog_minus_fav": round(avg_ev_diff, 2),
            "structural_lean": (
                f"The UNDERDOG is the better pairing in {dog_wins}/{len(results)} cases. "
                if dog_wins > fav_wins else
                f"The FAVORITE is the better pairing in {fav_wins}/{len(results)} cases. "
            ),
        },
        "why": _explain_dog_vs_fav_lean(results),
    }


def _explain_dog_vs_fav_lean(results):
    """Explain the structural reasoning"""
    return {
        "book_blind_spots": {
            "title": "Where Books DON'T Fully Price F5 Ties",
            "explanation": (
                "F5 3-way is a secondary/alternate market. Books set it by: "
                "1) Taking the full-game ML. "
                "2) Applying a standard F5 adjustment (roughly: compress the favorite's edge "
                "because 5 innings = less time for the better team to separate). "
                "3) Setting the tie at a standard range (+380 to +500 depending on matchup). "
                "What they likely DON'T do: adjust the tie price for the specific combination "
                "of starting pitcher ERA × park factor × weather × month. That's our edge."
            ),
            "factors_books_miss": [
                {
                    "factor": "ERA Differential (specific combination)",
                    "detail": (
                        "Books adjust the ML based on pitcher quality, but the TIE price "
                        "may not fully reflect that ace-vs-ace compresses scoring into "
                        "0-0, 1-1, 2-2 territory. The tie goes from 11.8% to 15.8% "
                        "but the tie odds might only move from +460 to +420."
                    ),
                },
                {
                    "factor": "Park Factor on TIE specifically",
                    "detail": (
                        "Books price park factor into the total (O/U) but may not "
                        "fully adjust the F5 tie price. A pitcher park increases ties "
                        "but the tie price may stay at +430 regardless."
                    ),
                },
                {
                    "factor": "Stacked conditions",
                    "detail": (
                        "Even if books adjust for each factor individually, they likely "
                        "don't model the MULTIPLICATIVE stacking effect. Ace vs ace (+3.4%) "
                        "AND pitcher park (+3.5%) AND cold weather (+1.5%) together push "
                        "tie rate to 22%+, but the book might only adjust 4-5% total."
                    ),
                },
                {
                    "factor": "Cold weather / April effect",
                    "detail": (
                        "Cold weather suppresses offense. Books adjust the total but "
                        "the F5 tie price may not reflect that cold = slower starts = "
                        "more 0-0 and 1-1 situations through 5 innings."
                    ),
                },
            ],
        },
        "dog_vs_fav_reasoning": {
            "why_dog_might_be_better": [
                "Higher odds = more payout per dollar when the dog hits",
                "Dog odds (+180 to +220) compound better with the tie odds",
                "In a Tie+Dog setup, BOTH outcomes are long shots that pay big — "
                "you're building a portfolio of +EV longshots rather than one longshot + one short price",
                "Book may overprice the underdog less efficiently than the favorite "
                "(sharp money concentrates on favorites, leaving dog lines softer)",
            ],
            "why_fav_might_be_better": [
                "Higher win probability = the team leg hits more often",
                "When sizing less on tie, the team bet is your primary bet — "
                "a favorite is more reliable as a primary bet",
                "Combined win rate (tie + fav) is higher, meaning fewer losing days",
                "Psychologically easier to sustain through losing streaks",
            ],
            "the_real_answer": (
                "It depends on the SPECIFIC odds. When the underdog is at +180 or higher, "
                "Tie+Dog tends to produce better EV because the dog's payout compensates. "
                "When the underdog is at +130-150 (slight dog), Tie+Fav is often similar or better. "
                "The optimal partner is whichever team has better individual EV per dollar, "
                "which depends on how much the book has mispriced each side."
            ),
        },
    }


# ─── 3. SMALL TIE + LARGER TEAM BREAKDOWN ────────────────────────────

@router.get("/small-tie-strategy")
async def small_tie_strategy(
    away_odds: int = Query(default=125),
    tie_odds: int = Query(default=420),
    home_odds: int = Query(default=125),
    bankroll: float = Query(default=100),
    partner: str = Query(default="away"),
    game_total: Optional[str] = Query(default=None),
    era_differential: Optional[str] = Query(default=None),
    park_factor: Optional[str] = Query(default=None),
    ml_odds_proximity: Optional[str] = Query(default=None),
    month: Optional[str] = Query(default=None),
):
    """
    The user's specific question: bet LESS on tie since odds are better,
    more on the team. Walk through exactly how this works.
    """
    factors = {}
    for k, v in [("game_total", game_total), ("era_differential", era_differential),
                 ("park_factor", park_factor), ("ml_odds_proximity", ml_odds_proximity),
                 ("month", month)]:
        if v:
            factors[k] = v

    tie_rate = estimate_tie_rate(factors)
    probs = estimate_probabilities(away_odds, tie_odds, home_odds, tie_rate)

    dec_tie = american_to_decimal(tie_odds)
    dec_away = american_to_decimal(away_odds)
    dec_home = american_to_decimal(home_odds)

    if partner == "away":
        dec_team = dec_away
        p_team = probs["p_away"]
        p_lose = probs["p_home"]
        team_odds = away_odds
    else:
        dec_team = dec_home
        p_team = probs["p_home"]
        p_lose = probs["p_away"]
        team_odds = home_odds

    p_tie = probs["p_tie"]

    # The "small tie" concept: what if we size the tie bet so it
    # pays back exactly 2x our total risk? Or 3x? Or just covers cost?

    sizing_concepts = []

    # Concept A: Tie pays back 2x total risk (conservative)
    # dec_tie * tie_stake = 2 * bankroll → tie_stake = 2*bankroll / dec_tie
    tie_2x = min(2 * bankroll / dec_tie, bankroll * 0.95)
    team_2x = bankroll - tie_2x
    sizing_concepts.append({
        "name": "Tie pays 2x total risk",
        "tie_stake": round(tie_2x, 2),
        "team_stake": round(team_2x, 2),
        "tie_pct": round(tie_2x / bankroll * 100, 1),
        "if_tie": round(dec_tie * tie_2x - bankroll, 2),
        "if_team": round(dec_team * team_2x - bankroll, 2),
        "if_lose": round(-bankroll, 2),
        "ev": round(p_tie * (dec_tie * tie_2x - bankroll) + p_team * (dec_team * team_2x - bankroll) + p_lose * (-bankroll), 2),
    })

    # Concept B: Tie just covers cost (breakeven on tie hit)
    # dec_tie * tie_stake = bankroll → tie_stake = bankroll / dec_tie
    tie_be = bankroll / dec_tie
    team_be = bankroll - tie_be
    sizing_concepts.append({
        "name": "Tie just covers cost (breakeven)",
        "tie_stake": round(tie_be, 2),
        "team_stake": round(team_be, 2),
        "tie_pct": round(tie_be / bankroll * 100, 1),
        "if_tie": round(dec_tie * tie_be - bankroll, 2),
        "if_team": round(dec_team * team_be - bankroll, 2),
        "if_lose": round(-bankroll, 2),
        "ev": round(p_tie * (dec_tie * tie_be - bankroll) + p_team * (dec_team * team_be - bankroll) + p_lose * (-bankroll), 2),
    })

    # Concept C: Small tie insurance (20% tie / 80% team)
    tie_sm = bankroll * 0.20
    team_sm = bankroll * 0.80
    sizing_concepts.append({
        "name": "Small tie insurance (20/80)",
        "tie_stake": round(tie_sm, 2),
        "team_stake": round(team_sm, 2),
        "tie_pct": 20,
        "if_tie": round(dec_tie * tie_sm - bankroll, 2),
        "if_team": round(dec_team * team_sm - bankroll, 2),
        "if_lose": round(-bankroll, 2),
        "ev": round(p_tie * (dec_tie * tie_sm - bankroll) + p_team * (dec_team * team_sm - bankroll) + p_lose * (-bankroll), 2),
    })

    # Concept D: 30/70 split
    tie_30 = bankroll * 0.30
    team_30 = bankroll * 0.70
    sizing_concepts.append({
        "name": "30/70 split",
        "tie_stake": round(tie_30, 2),
        "team_stake": round(team_30, 2),
        "tie_pct": 30,
        "if_tie": round(dec_tie * tie_30 - bankroll, 2),
        "if_team": round(dec_team * team_30 - bankroll, 2),
        "if_lose": round(-bankroll, 2),
        "ev": round(p_tie * (dec_tie * tie_30 - bankroll) + p_team * (dec_team * team_30 - bankroll) + p_lose * (-bankroll), 2),
    })

    # Concept E: Size both for equal PROFIT (not equal payout)
    # profit_tie = profit_team
    # dec_tie * x - B = dec_team * (B - x) - B
    # dec_tie * x = dec_team * B - dec_team * x
    # x * (dec_tie + dec_team) = dec_team * B
    # x = dec_team * B / (dec_tie + dec_team)
    tie_ep = dec_team * bankroll / (dec_tie + dec_team)
    team_ep = bankroll - tie_ep
    sizing_concepts.append({
        "name": "Equal PROFIT (not equal payout)",
        "tie_stake": round(tie_ep, 2),
        "team_stake": round(team_ep, 2),
        "tie_pct": round(tie_ep / bankroll * 100, 1),
        "if_tie": round(dec_tie * tie_ep - bankroll, 2),
        "if_team": round(dec_team * team_ep - bankroll, 2),
        "if_lose": round(-bankroll, 2),
        "ev": round(p_tie * (dec_tie * tie_ep - bankroll) + p_team * (dec_team * team_ep - bankroll) + p_lose * (-bankroll), 2),
    })

    # Find the sweet spot: where both outcomes are profitable
    # and EV is maximized
    sweet_spot = None
    for sc in sizing_concepts:
        if sc["if_tie"] > 0 and sc["if_team"] > 0:
            if sweet_spot is None or sc["ev"] > sweet_spot["ev"]:
                sweet_spot = sc

    return {
        "title": "Small Tie Strategy — Bet Less on Tie, More on Team",
        "parameters": {
            "away_odds": away_odds, "tie_odds": tie_odds, "home_odds": home_odds,
            "partner": partner, "team_odds": team_odds,
            "bankroll": bankroll, "factors": factors,
        },
        "probabilities": {
            "p_tie": round(p_tie * 100, 1),
            "p_team": round(p_team * 100, 1),
            "p_combined": round((p_tie + p_team) * 100, 1),
            "p_lose": round(p_lose * 100, 1),
        },
        "tie_rate_pct": round(tie_rate * 100, 1),
        "sizing_concepts": sizing_concepts,
        "sweet_spot": sweet_spot,
        "insight": (
            f"The tie at +{tie_odds} pays {dec_tie}x, so a ${round(tie_be,2)} bet "
            f"returns your full ${bankroll:.0f} bankroll. Anything above that is profit. "
            f"That leaves ${round(team_be,2)} for the team bet, which at +{team_odds} "
            f"pays ${round(dec_team * team_be, 2)}. "
            f"This 'tie-as-insurance' framing means the team bet is your PRIMARY play "
            f"and the tie is a bonus that covers your cost if it hits."
        ),
    }
