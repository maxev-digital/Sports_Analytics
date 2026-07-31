"""
F5 Two-of-Three Strategy — Tie + One Team

Cover 2 of the 3 F5 outcomes:
  A) Tie + Underdog  → lose only if favorite leads after 5
  B) Tie + Favorite  → lose only if underdog leads after 5

The key question: can we size these two bets so that the combined
win rate (covering 2 outcomes) overcomes the combined risk?

This changes the breakeven math entirely vs single-outcome bets.
"""

from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime
import math

router = APIRouter(prefix="/api/f5/two-of-three", tags=["f5-two-of-three"])

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


def devig_probabilities(away_odds: int, tie_odds: int, home_odds: int) -> dict:
    """Remove vig to get true implied probabilities for team win split"""
    dec_a = american_to_decimal(away_odds)
    dec_t = american_to_decimal(tie_odds)
    dec_h = american_to_decimal(home_odds)

    imp_a = 1 / dec_a
    imp_t = 1 / dec_t
    imp_h = 1 / dec_h
    total = imp_a + imp_t + imp_h

    return {
        "away_devigged": imp_a / total,
        "tie_devigged": imp_t / total,
        "home_devigged": imp_h / total,
        "vig_pct": (total - 1) * 100,
    }


def estimate_actual_probabilities(
    away_odds: int, tie_odds: int, home_odds: int,
    estimated_tie_rate: float
) -> dict:
    """
    Estimate actual probabilities using our tie rate + book's team split.

    We trust our tie rate estimate but use the book's ratio of
    away vs home to split the remaining non-tie probability.
    """
    devigged = devig_probabilities(away_odds, tie_odds, home_odds)

    # The book's view of the team split (excluding tie)
    away_share = devigged["away_devigged"] / (devigged["away_devigged"] + devigged["home_devigged"])
    home_share = devigged["home_devigged"] / (devigged["away_devigged"] + devigged["home_devigged"])

    non_tie = 1 - estimated_tie_rate

    return {
        "p_away_leads": non_tie * away_share,
        "p_tie": estimated_tie_rate,
        "p_home_leads": non_tie * home_share,
        "away_share_of_non_tie": away_share,
        "home_share_of_non_tie": home_share,
    }


def analyze_two_of_three(
    away_odds: int, tie_odds: int, home_odds: int,
    partner_team: str,  # "away" or "home"
    bankroll: float,
    factors: dict,
    sizing_mode: str = "equal_payout",  # or "max_tie", "balanced", "kelly"
) -> dict:
    """
    Full analysis of betting Tie + one team.

    Sizing modes:
      equal_payout — size so profit is same whether tie or team hits
      max_tie     — maximize tie bet, team bet is just insurance
      balanced    — 50/50 split between tie and team
      kelly       — kelly-optimal allocation between the two bets
    """
    tie_rate = estimate_tie_rate(factors)
    probs = estimate_actual_probabilities(away_odds, tie_odds, home_odds, tie_rate)

    dec_away = american_to_decimal(away_odds)
    dec_tie = american_to_decimal(tie_odds)
    dec_home = american_to_decimal(home_odds)

    # Determine which team we're partnering with the tie
    if partner_team == "away":
        team_odds = away_odds
        dec_team = dec_away
        team_label = "Away (Underdog)" if dec_away > dec_home else "Away (Favorite)"
        p_team_wins = probs["p_away_leads"]
        p_lose = probs["p_home_leads"]  # we lose if the OTHER team leads
        lose_label = "Home leads"
    else:
        team_odds = home_odds
        dec_team = dec_home
        team_label = "Home (Favorite)" if dec_home < dec_away else "Home (Underdog)"
        p_team_wins = probs["p_home_leads"]
        p_lose = probs["p_away_leads"]
        lose_label = "Away leads"

    p_win = probs["p_tie"] + p_team_wins  # combined win probability

    # ─── SIZING MODES ─────────────────────────────────────────────
    sizing_results = {}

    # 1. EQUAL PAYOUT: 5.60X = 2.36Y → Y = (dec_tie/dec_team) * X
    ratio = dec_tie / dec_team
    x_eq = bankroll / (1 + ratio)  # tie stake
    y_eq = bankroll - x_eq          # team stake
    payout_eq = dec_tie * x_eq
    profit_eq = payout_eq - bankroll

    sizing_results["equal_payout"] = {
        "tie_stake": round(x_eq, 2),
        "team_stake": round(y_eq, 2),
        "total_risked": round(bankroll, 2),
        "payout_if_tie": round(dec_tie * x_eq, 2),
        "payout_if_team": round(dec_team * y_eq, 2),
        "profit_if_tie": round(dec_tie * x_eq - bankroll, 2),
        "profit_if_team": round(dec_team * y_eq - bankroll, 2),
        "loss_if_other": round(-bankroll, 2),
    }

    # 2. MAX TIE: Put 70% on tie, 30% on team (insurance)
    x_mt = bankroll * 0.70
    y_mt = bankroll * 0.30

    sizing_results["max_tie"] = {
        "tie_stake": round(x_mt, 2),
        "team_stake": round(y_mt, 2),
        "total_risked": round(bankroll, 2),
        "payout_if_tie": round(dec_tie * x_mt, 2),
        "payout_if_team": round(dec_team * y_mt, 2),
        "profit_if_tie": round(dec_tie * x_mt - bankroll, 2),
        "profit_if_team": round(dec_team * y_mt - bankroll, 2),
        "loss_if_other": round(-bankroll, 2),
    }

    # 3. BALANCED: 50/50 split
    x_bal = bankroll * 0.50
    y_bal = bankroll * 0.50

    sizing_results["balanced"] = {
        "tie_stake": round(x_bal, 2),
        "team_stake": round(y_bal, 2),
        "total_risked": round(bankroll, 2),
        "payout_if_tie": round(dec_tie * x_bal, 2),
        "payout_if_team": round(dec_team * y_bal, 2),
        "profit_if_tie": round(dec_tie * x_bal - bankroll, 2),
        "profit_if_team": round(dec_team * y_bal - bankroll, 2),
        "loss_if_other": round(-bankroll, 2),
    }

    # 4. OPTIMAL: Find the split that maximizes EV
    # EV(x) = p_tie * (dec_tie * x - B) + p_team * (dec_team * (B-x) - B) + p_lose * (-B)
    # where B = bankroll, x = tie stake
    # dEV/dx = p_tie * dec_tie - p_team * dec_team = 0
    # Optimal x/B depends on whether tie or team has better individual EV
    # But since total is fixed at B, EV is linear in x — optimal is at boundary
    # unless we add a risk-adjustment

    # EV as a function of tie_fraction
    def ev_at_fraction(f):
        x = bankroll * f
        y = bankroll * (1 - f)
        ev = (probs["p_tie"] * (dec_tie * x - bankroll) +
              p_team_wins * (dec_team * y - bankroll) +
              p_lose * (-bankroll))
        return ev

    # Scan fractions
    best_f = 0
    best_ev = -999999
    ev_curve = []
    for pct in range(0, 101, 5):
        f = pct / 100
        ev = ev_at_fraction(f)
        ev_curve.append({"tie_pct": pct, "ev": round(ev, 2)})
        if ev > best_ev:
            best_ev = ev
            best_f = f

    x_opt = bankroll * best_f
    y_opt = bankroll * (1 - best_f)

    sizing_results["optimal"] = {
        "tie_stake": round(x_opt, 2),
        "team_stake": round(y_opt, 2),
        "tie_pct": round(best_f * 100, 1),
        "team_pct": round((1 - best_f) * 100, 1),
        "total_risked": round(bankroll, 2),
        "payout_if_tie": round(dec_tie * x_opt, 2),
        "payout_if_team": round(dec_team * y_opt, 2),
        "profit_if_tie": round(dec_tie * x_opt - bankroll, 2),
        "profit_if_team": round(dec_team * y_opt - bankroll, 2),
        "loss_if_other": round(-bankroll, 2),
        "ev_curve": ev_curve,
        "note": (
            "Since EV is linear in the split, the optimal is at a boundary. "
            "If tie EV > team EV per dollar, put 100% on tie. "
            "The team bet only adds value as variance reduction."
        ),
    }

    # ─── EV FOR EACH SIZING MODE ─────────────────────────────────
    ev_comparison = []
    for mode_name, mode_data in sizing_results.items():
        if mode_name == "optimal" and "ev_curve" in mode_data:
            continue  # skip curve data
        x = mode_data["tie_stake"]
        y = mode_data["team_stake"]

        ev = (probs["p_tie"] * (dec_tie * x - bankroll) +
              p_team_wins * (dec_team * y - bankroll) +
              p_lose * (-bankroll))

        # Variance
        outcomes = [
            (probs["p_tie"], dec_tie * x - bankroll),
            (p_team_wins, dec_team * y - bankroll),
            (p_lose, -bankroll),
        ]
        expected = sum(p * v for p, v in outcomes)
        variance = sum(p * (v - expected)**2 for p, v in outcomes)
        std_dev = math.sqrt(variance)
        sharpe = expected / std_dev if std_dev > 0 else 0

        ev_comparison.append({
            "mode": mode_name,
            "ev": round(ev, 2),
            "roi_pct": round((ev / bankroll) * 100, 2),
            "std_dev": round(std_dev, 2),
            "sharpe_ratio": round(sharpe, 4),
            "best_win": round(max(mode_data["profit_if_tie"], mode_data["profit_if_team"]), 2),
            "worst_win": round(min(mode_data["profit_if_tie"], mode_data["profit_if_team"]), 2),
            "loss": round(-bankroll, 2),
        })

    ev_comparison.sort(key=lambda x: x["ev"], reverse=True)

    # ─── BREAKEVEN ANALYSIS ──────────────────────────────────────
    # For equal payout: what win% do we need?
    # EV = p_win * profit - p_lose * bankroll = 0
    # p_win = bankroll / (profit + bankroll)
    breakeven_win_pct = bankroll / (profit_eq + bankroll) if (profit_eq + bankroll) > 0 else 1.0

    return {
        "strategy": f"Tie + {team_label}",
        "partner": partner_team,
        "probabilities": {
            "p_away_leads": round(probs["p_away_leads"] * 100, 1),
            "p_tie": round(probs["p_tie"] * 100, 1),
            "p_home_leads": round(probs["p_home_leads"] * 100, 1),
            "p_win_combined": round(p_win * 100, 1),
            "p_lose": round(p_lose * 100, 1),
            "lose_scenario": lose_label,
        },
        "odds": {
            "tie": {"american": tie_odds, "decimal": round(dec_tie, 3)},
            "team": {"american": team_odds, "decimal": round(dec_team, 3)},
        },
        "breakeven": {
            "win_pct_needed": round(breakeven_win_pct * 100, 1),
            "actual_win_pct": round(p_win * 100, 1),
            "margin": round((p_win - breakeven_win_pct) * 100, 1),
            "is_positive_ev": p_win > breakeven_win_pct,
        },
        "sizing_modes": sizing_results,
        "ev_comparison": ev_comparison,
        "factors": factors,
        "estimated_tie_rate": round(tie_rate * 100, 1),
    }


# ─── Endpoints ────────────────────────────────────────────────────────

@router.get("/analyze")
async def analyze(
    away_odds: int = Query(..., description="Away F5 ML"),
    tie_odds: int = Query(..., description="Tie F5 ML"),
    home_odds: int = Query(..., description="Home F5 ML"),
    bankroll: float = Query(default=100, description="Amount to deploy"),
    # Factors
    game_total: Optional[str] = Query(default=None),
    era_differential: Optional[str] = Query(default=None),
    park_factor: Optional[str] = Query(default=None),
    ml_odds_proximity: Optional[str] = Query(default=None),
    month: Optional[str] = Query(default=None),
    # Teams
    away_team: Optional[str] = Query(default=None),
    home_team: Optional[str] = Query(default=None),
):
    """
    Analyze both 2-of-3 strategies for a game:
      - Tie + Away (underdog or favorite)
      - Tie + Home (favorite or underdog)
    Returns which pairing is optimal and why.
    """
    factors = {}
    if game_total:
        factors["game_total"] = game_total
    if era_differential:
        factors["era_differential"] = era_differential
    if park_factor:
        factors["park_factor"] = park_factor
    if ml_odds_proximity:
        factors["ml_odds_proximity"] = ml_odds_proximity
    if month:
        factors["month"] = month

    tie_plus_away = analyze_two_of_three(
        away_odds, tie_odds, home_odds, "away", bankroll, factors
    )
    tie_plus_home = analyze_two_of_three(
        away_odds, tie_odds, home_odds, "home", bankroll, factors
    )

    # Which is better?
    away_ev = next((e["ev"] for e in tie_plus_away["ev_comparison"] if e["mode"] == "equal_payout"), 0)
    home_ev = next((e["ev"] for e in tie_plus_home["ev_comparison"] if e["mode"] == "equal_payout"), 0)

    if away_ev > home_ev:
        recommended = "tie_plus_away"
        reason = "Better EV pairing tie with the away team"
    else:
        recommended = "tie_plus_home"
        reason = "Better EV pairing tie with the home team"

    # Identify the underdog and favorite
    dec_away = american_to_decimal(away_odds)
    dec_home = american_to_decimal(home_odds)
    if dec_away > dec_home:
        underdog = "away"
        favorite = "home"
    else:
        underdog = "home"
        favorite = "away"

    return {
        "game": {
            "away_team": away_team or "Away",
            "home_team": home_team or "Home",
            "away_odds": away_odds,
            "tie_odds": tie_odds,
            "home_odds": home_odds,
            "underdog": underdog,
            "favorite": favorite,
        },
        "tie_plus_away": tie_plus_away,
        "tie_plus_home": tie_plus_home,
        "recommendation": {
            "best_pairing": recommended,
            "reason": reason,
            "away_ev": round(away_ev, 2),
            "home_ev": round(home_ev, 2),
        },
        "strategic_logic": _build_strategic_logic(
            tie_plus_away, tie_plus_home, underdog, favorite, factors
        ),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/scenario-scan")
async def scenario_scan():
    """
    Test the 2-of-3 strategy across all our signal conditions.
    Find where Tie + Underdog or Tie + Favorite becomes +EV.
    """
    scenarios = [
        # HIGH TIE RATE — partner with the underdog
        {
            "name": "Ace vs Ace, Pitcher Park, Low Total (Peak Tie)",
            "away": 125, "tie": 420, "home": 125,
            "factors": {"era_differential": "both_under_3", "park_factor": "pitcher_park",
                       "game_total": "under_7", "ml_odds_proximity": "both_plus_100_to_130"},
            "expected_behavior": "Highest tie rate. Tie + either team should work if tie rate > 20%.",
        },
        {
            "name": "Ace vs Ace, Pitcher Park",
            "away": 120, "tie": 430, "home": 130,
            "factors": {"era_differential": "both_under_3", "park_factor": "pitcher_park"},
            "expected_behavior": "High tie rate but less extreme.",
        },
        {
            "name": "Ace vs Ace, Even Matchup",
            "away": 125, "tie": 420, "home": 125,
            "factors": {"era_differential": "both_under_3", "ml_odds_proximity": "both_plus_100_to_130"},
            "expected_behavior": "Even money + aces. Classic tie setup.",
        },
        {
            "name": "Even Matchup, Low Total, Pitcher Park, April",
            "away": 115, "tie": 400, "home": 120,
            "factors": {"ml_odds_proximity": "both_plus_100_to_130", "game_total": "under_7",
                       "park_factor": "pitcher_park", "month": "april"},
            "expected_behavior": "Maximum tie conditions without requiring ace pitchers.",
        },
        # MODERATE TIE RATE
        {
            "name": "Even Matchup, Neutral Park, Avg Total",
            "away": 120, "tie": 440, "home": 120,
            "factors": {"ml_odds_proximity": "both_plus_100_to_130", "game_total": "8_to_9"},
            "expected_behavior": "Baseline even game. Moderate tie rate.",
        },
        {
            "name": "Slight Favorite, Low Total",
            "away": 145, "tie": 450, "home": 108,
            "factors": {"game_total": "under_7", "ml_odds_proximity": "spread_130_to_160"},
            "expected_behavior": "Slight lean. Tie + underdog has better odds.",
        },
        # LOW TIE RATE — these should NOT work for 2-of-3
        {
            "name": "Bad Starter, High Total, Hitter Park",
            "away": 175, "tie": 480, "home": 105,
            "factors": {"era_differential": "diff_over_1.5", "game_total": "over_9",
                       "park_factor": "hitter_park"},
            "expected_behavior": "Low tie rate. 2-of-3 should be -EV here.",
        },
        {
            "name": "Coors Slugfest",
            "away": 130, "tie": 490, "home": 130,
            "factors": {"park_factor": "coors_field", "game_total": "over_10"},
            "expected_behavior": "Very low tie rate. 2-of-3 worst case.",
        },
        # UNDERDOG-HEAVY
        {
            "name": "Big Underdog + Ace, Pitcher Park",
            "away": 200, "tie": 440, "home": 100,
            "factors": {"era_differential": "diff_1.0_to_1.5", "park_factor": "pitcher_park",
                       "game_total": "under_7"},
            "expected_behavior": "Big dog at +200. Tie + Underdog has 2 high-payout outcomes.",
        },
        {
            "name": "Big Underdog + Even Pitching, Low Total",
            "away": 180, "tie": 430, "home": 105,
            "factors": {"era_differential": "diff_0.5_to_1.0", "game_total": "under_7",
                       "ml_odds_proximity": "spread_160_to_200"},
            "expected_behavior": "Dog at +180 with a low total. Interesting tie + dog spot.",
        },
    ]

    results = []
    for sc in scenarios:
        analysis_away = analyze_two_of_three(
            sc["away"], sc["tie"], sc["home"], "away", 100, sc["factors"]
        )
        analysis_home = analyze_two_of_three(
            sc["away"], sc["tie"], sc["home"], "home", 100, sc["factors"]
        )

        # Get equal_payout EVs
        ev_away = next((e for e in analysis_away["ev_comparison"] if e["mode"] == "equal_payout"), {})
        ev_home = next((e for e in analysis_home["ev_comparison"] if e["mode"] == "equal_payout"), {})

        # Get optimal EVs
        opt_away = next((e for e in analysis_away["ev_comparison"] if e["mode"] == "optimal"), ev_away)
        opt_home = next((e for e in analysis_home["ev_comparison"] if e["mode"] == "optimal"), ev_home)

        # Also get max_tie mode EVs
        mt_away = next((e for e in analysis_away["ev_comparison"] if e["mode"] == "max_tie"), ev_away)
        mt_home = next((e for e in analysis_home["ev_comparison"] if e["mode"] == "max_tie"), ev_home)

        tie_rate = estimate_tie_rate(sc["factors"])

        best_ev = max(ev_away.get("ev", -999), ev_home.get("ev", -999),
                      mt_away.get("ev", -999), mt_home.get("ev", -999))
        best_config = "N/A"
        if best_ev == ev_away.get("ev"):
            best_config = "Tie+Away equal_payout"
        elif best_ev == ev_home.get("ev"):
            best_config = "Tie+Home equal_payout"
        elif best_ev == mt_away.get("ev"):
            best_config = "Tie+Away max_tie"
        elif best_ev == mt_home.get("ev"):
            best_config = "Tie+Home max_tie"

        results.append({
            "scenario": sc["name"],
            "expected_behavior": sc["expected_behavior"],
            "tie_rate_pct": round(tie_rate * 100, 1),
            "odds": {"away": sc["away"], "tie": sc["tie"], "home": sc["home"]},
            "tie_plus_away": {
                "win_pct": analysis_away["probabilities"]["p_win_combined"],
                "breakeven_pct": analysis_away["breakeven"]["win_pct_needed"],
                "margin": analysis_away["breakeven"]["margin"],
                "equal_payout_ev": ev_away.get("ev", 0),
                "equal_payout_roi": ev_away.get("roi_pct", 0),
                "max_tie_ev": mt_away.get("ev", 0),
                "max_tie_roi": mt_away.get("roi_pct", 0),
                "is_positive_ev": analysis_away["breakeven"]["is_positive_ev"],
            },
            "tie_plus_home": {
                "win_pct": analysis_home["probabilities"]["p_win_combined"],
                "breakeven_pct": analysis_home["breakeven"]["win_pct_needed"],
                "margin": analysis_home["breakeven"]["margin"],
                "equal_payout_ev": ev_home.get("ev", 0),
                "equal_payout_roi": ev_home.get("roi_pct", 0),
                "max_tie_ev": mt_home.get("ev", 0),
                "max_tie_roi": mt_home.get("roi_pct", 0),
                "is_positive_ev": analysis_home["breakeven"]["is_positive_ev"],
            },
            "best_configuration": best_config,
            "best_ev": round(best_ev, 2),
            "verdict": "PLAY" if best_ev > 0 else "PASS",
        })

    # Summary
    plays = [r for r in results if r["verdict"] == "PLAY"]
    passes = [r for r in results if r["verdict"] == "PASS"]

    return {
        "title": "F5 Two-of-Three Scenario Scan",
        "summary": {
            "total_scenarios": len(results),
            "positive_ev": len(plays),
            "negative_ev": len(passes),
            "best_scenario": plays[0]["scenario"] if plays else None,
            "best_ev": plays[0]["best_ev"] if plays else None,
        },
        "scenarios": results,
        "key_findings": _build_findings(results),
        "timestamp": datetime.now().isoformat(),
    }


def _build_strategic_logic(tie_away, tie_home, underdog, favorite, factors):
    """Build explanation of why one pairing is better"""
    tie_rate = estimate_tie_rate(factors)

    sections = []

    # Tie + Underdog logic
    sections.append({
        "pairing": "Tie + Underdog",
        "logic": (
            "You win when EITHER the underdog leads OR it's tied after 5. "
            "The underdog pays more per dollar bet, so when the team leg hits, "
            "the payout is larger. The combined probability of tie + underdog winning "
            "is smaller (underdog wins less often), but each win pays more."
        ),
        "best_when": [
            "Tie rate is HIGH (ace vs ace, pitcher park, low total)",
            "Underdog is at long odds (+180 or higher) — big payoff when they lead",
            "You want ASYMMETRIC payouts — small bets, big wins",
        ],
        "risk": "You lose when the favorite leads — which is the MOST LIKELY single outcome",
    })

    sections.append({
        "pairing": "Tie + Favorite",
        "logic": (
            "You win when EITHER the favorite leads OR it's tied after 5. "
            "The favorite wins more often, so the team leg hits more frequently. "
            "But the payout per hit is smaller (favorite odds are shorter). "
            "The combined win probability is HIGHER than tie + underdog."
        ),
        "best_when": [
            "You want HIGHER win rate (favorite wins most often)",
            "Favorite is not too short (still + money or close to it)",
            "You want more consistent returns, lower variance",
        ],
        "risk": "You lose when the underdog leads — less likely but still ~35-45%",
    })

    sections.append({
        "key_insight": (
            f"With estimated tie rate of {tie_rate*100:.1f}%, the tie bet carries "
            f"the edge (or not) regardless of which team you pair it with. "
            f"The team bet is INSURANCE — it recovers your money when the tie doesn't hit. "
            f"The question is: which insurance is cheaper? "
            f"Pairing with the underdog gives bigger individual payouts. "
            f"Pairing with the favorite gives higher combined win probability. "
            f"The optimal choice depends on the specific odds and your bankroll."
        ),
    })

    return sections


def _build_findings(results):
    plays = [r for r in results if r["verdict"] == "PLAY"]
    passes = [r for r in results if r["verdict"] == "PASS"]

    findings = []

    if plays:
        findings.append({
            "finding": "2-of-3 IS viable in high-tie-rate conditions",
            "detail": (
                f"{len(plays)} of {len(results)} scenarios are +EV. "
                f"The strategy works when tie rate exceeds ~20% AND "
                f"odds are structured favorably (all outcomes near +100 or higher)."
            ),
            "qualifying_scenarios": [p["scenario"] for p in plays],
        })

    # Check if underdog or favorite pairing is consistently better
    dog_better = sum(1 for r in results
                     if r["tie_plus_away"]["equal_payout_ev"] > r["tie_plus_home"]["equal_payout_ev"])
    fav_better = len(results) - dog_better

    findings.append({
        "finding": f"Tie + {'Away' if dog_better > fav_better else 'Home'} is usually the better pairing",
        "detail": (
            f"Tie + Away was better in {dog_better}/{len(results)} scenarios. "
            f"Tie + Home was better in {fav_better}/{len(results)} scenarios. "
            f"The pairing choice matters less than the game selection — "
            f"picking the RIGHT game is 80% of the edge."
        ),
    })

    # Tie rate threshold
    for r in sorted(results, key=lambda x: x["tie_rate_pct"], reverse=True):
        if r["verdict"] == "PASS":
            threshold = r["tie_rate_pct"]
            findings.append({
                "finding": f"Tie rate threshold is approximately {threshold+1}%+",
                "detail": (
                    f"The highest tie rate that still produced -EV was {threshold}% "
                    f"({r['scenario']}). Scenarios with tie rates above this were +EV. "
                    f"This gives us a clear screening threshold."
                ),
            })
            break

    findings.append({
        "finding": "Sizing mode matters less than game selection",
        "detail": (
            "Equal payout, max_tie, and balanced sizing all produce similar EV "
            "because EV is linear in the allocation split. The GAME you pick "
            "determines whether you have edge. Sizing determines the payout shape."
        ),
    })

    return findings
