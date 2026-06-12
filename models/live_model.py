"""
In-play (live) prediction model.

Given the current score and elapsed minute, updates all outcome probabilities
by modelling remaining goals as Poisson(λ_rem) where:
  λ_rem = λ_original × (remaining_minutes / 90)

The current score is fixed — we only predict remaining goals.

Also generates live bet recommendations focused on fast in-play markets:
  - Match result (updated)
  - Next goal scorer (team)
  - Will there be more goals?
  - Asian total remaining
"""
import math
from typing import Dict, List
from models.poisson_model import build_score_matrix
from config import MAX_GOALS


def _prob_to_odds(p: float) -> float:
    return round(1.0 / p, 2) if p > 0.005 else 200.0


def update_live(
    lam_home: float,
    lam_away: float,
    home_score: int,
    away_score: int,
    minute: int,
    is_halftime: bool = False,
) -> Dict:
    """
    Update all market probabilities based on current match state.

    Args:
        lam_home: pre-match expected goals for home team (full 90 min)
        lam_away: pre-match expected goals for away team (full 90 min)
        home_score: current home goals
        away_score: current away goals
        minute: elapsed minutes (0-90+)
        is_halftime: True if currently half-time break

    Returns:
        dict with updated 1X2, next-goal, over/under, and recommendation list
    """
    # Remaining time fraction
    if is_halftime:
        # Second half not yet started — ~55% of goals come in 2nd half
        remaining_frac = 0.55
    else:
        remaining_frac = max(0.0, min(1.0, (90.0 - minute) / 90.0))

    lam_h_rem = lam_home * remaining_frac
    lam_a_rem = lam_away * remaining_frac
    total_lam_rem = lam_h_rem + lam_a_rem

    # Score matrix for remaining goals
    rem_matrix = build_score_matrix(lam_h_rem, lam_a_rem, MAX_GOALS)
    MG = rem_matrix.shape[0] - 1

    # Aggregate final 1X2 outcomes from remaining goals
    hw = dr = aw = 0.0
    for dx in range(MG + 1):
        for dy in range(MG + 1):
            p = float(rem_matrix[dx, dy])
            if p < 1e-10:
                continue
            fh = home_score + dx
            fa = away_score + dy
            if fh > fa:
                hw += p
            elif fh == fa:
                dr += p
            else:
                aw += p

    total = hw + dr + aw
    if total > 0:
        hw /= total
        dr /= total
        aw /= total

    # Draw No Bet (live)
    dnb_total = hw + aw
    dnb_home = hw / dnb_total if dnb_total > 0 else 0.5
    dnb_away = aw / dnb_total if dnb_total > 0 else 0.5

    # Next goal (team-level)
    if total_lam_rem > 0:
        p_home_scores_next = lam_h_rem / total_lam_rem
        p_away_scores_next = lam_a_rem / total_lam_rem
    else:
        p_home_scores_next = p_away_scores_next = 0.5

    p_no_more_goals = math.exp(-total_lam_rem)
    p_more_goals    = 1.0 - p_no_more_goals

    # Next goal weighted by whether any more goals happen
    p_home_next = p_home_scores_next * p_more_goals
    p_away_next = p_away_scores_next * p_more_goals

    # Over/Under for remaining goals (Asian style)
    def _over_rem(line: float) -> float:
        """P(remaining goals > line)."""
        total_goals = 0.0
        for k in range(MG + 1):
            for l in range(MG + 1):
                if k + l > line:
                    total_goals += float(rem_matrix[k, l])
        return total_goals

    # Asian total for full match (current score + remaining)
    current_total = home_score + away_score
    over_lines = {}
    for line in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]:
        # We need total_goals > line, where total_goals = current_total + remaining
        # So remaining needs to be > line - current_total
        rem_needed = line - current_total
        if rem_needed < 0:
            over_lines[line] = 1.0  # already over this line
        else:
            over_lines[line] = round(_over_rem(rem_needed), 4)

    return {
        "minute":          minute,
        "home_score":      home_score,
        "away_score":      away_score,
        "remaining_frac":  round(remaining_frac, 3),
        "lam_home_rem":    round(lam_h_rem, 3),
        "lam_away_rem":    round(lam_a_rem, 3),
        "1x2": {
            "home": round(hw, 4),
            "draw": round(dr, 4),
            "away": round(aw, 4),
        },
        "dnb": {
            "home": round(dnb_home, 4),
            "away": round(dnb_away, 4),
        },
        "next_goal": {
            "home": round(p_home_next, 4),
            "away": round(p_away_next, 4),
            "no_goal": round(p_no_more_goals, 4),
        },
        "more_goals": {
            "yes": round(p_more_goals, 4),
            "no":  round(p_no_more_goals, 4),
        },
        "asian_total_live": {
            line: {
                "over":  v,
                "under": round(1 - v, 4),
                "over_odds":  _prob_to_odds(v),
                "under_odds": _prob_to_odds(1 - v),
            }
            for line, v in over_lines.items()
        },
    }


def live_recommendations(
    live_pred: Dict,
    original_pred: Dict,
    home: str,
    away: str,
) -> List[Dict]:
    """
    Generate ranked live bet recommendations.
    Focuses on high-probability in-play markets that change fast.
    """
    recs = []
    x      = live_pred["1x2"]
    ng     = live_pred["next_goal"]
    mg     = live_pred["more_goals"]
    minute = live_pred["minute"]
    h_sc   = live_pred["home_score"]
    a_sc   = live_pred["away_score"]

    def _add(market, selection, prob, why, urgency="MEDIUM"):
        recs.append({
            "market":    market,
            "selection": selection,
            "prob":      round(prob, 4),
            "fair_odds": _prob_to_odds(prob),
            "why":       why,
            "urgency":   urgency,
        })

    # ── Match result ─────────────────────────────────────────────────
    if x["home"] >= 0.65:
        _add("Match Result", f"{home} Win", x["home"],
             f"Leading {h_sc}-{a_sc} with {90-minute}' left.", "HIGH")
    elif x["away"] >= 0.65:
        _add("Match Result", f"{away} Win", x["away"],
             f"Leading {a_sc}-{h_sc} with {90-minute}' left.", "HIGH")
    elif x["draw"] >= 0.50 and minute > 70:
        _add("Match Result", "Draw", x["draw"],
             f"Score {h_sc}-{a_sc} at {minute}' — draw looking likely.", "HIGH")
    else:
        best_r = max([(x["home"], home), (x["draw"], "Draw"), (x["away"], away)],
                     key=lambda t: t[0])
        if best_r[0] > 0.48:
            _add("Match Result", best_r[1], best_r[0],
                 f"Current favourite at {minute}'.", "MEDIUM")

    # ── Next goal ────────────────────────────────────────────────────
    if mg["yes"] > 0.55:
        best_ng = max([(ng["home"], f"{home} to score next"),
                       (ng["away"], f"{away} to score next")], key=lambda t: t[0])
        _add("Next Goal (team)", best_ng[1], best_ng[0],
             "Remaining xG still active.", "MEDIUM" if best_ng[0] > 0.55 else "LOW")

    # ── More goals ───────────────────────────────────────────────────
    if minute < 75:
        if mg["yes"] > 0.65:
            _add("More Goals", "Yes — at least 1 more", mg["yes"],
                 f"Expected {live_pred['lam_home_rem'] + live_pred['lam_away_rem']:.1f} more goals.", "MEDIUM")
        elif mg["no"] > 0.55 and minute > 70:
            _add("More Goals", "No more goals", mg["no"],
                 f"Low xG remaining with only {90-minute}' left.", "LOW")

    # ── DNB if close game ────────────────────────────────────────────
    dnb = live_pred.get("dnb", {})
    if h_sc == a_sc and minute < 80:
        best_dnb = max([(dnb.get("home", 0.5), home), (dnb.get("away", 0.5), away)],
                       key=lambda t: t[0])
        if best_dnb[0] > 0.58:
            _add("Draw No Bet", best_dnb[1], best_dnb[0],
                 "Draw currently but one team is stronger — DNB removes draw risk.", "MEDIUM")

    # Sort: HIGH urgency first, then by probability
    recs.sort(key=lambda r: (r["urgency"] != "HIGH", -r["prob"]))
    return recs[:5]
