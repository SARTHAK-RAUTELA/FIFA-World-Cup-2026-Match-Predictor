"""
ELO rating model for FIFA 2026 match predictions.
Pre-seeded with ratings based on FIFA world rankings + recent WC qualifying.
Supports updating ELO from tournament results.
"""
import math
import json
import os
from typing import Dict, Tuple, Optional
from config import FIFA_2026_ELO_RATINGS, HOME_ADVANTAGE


ELO_K_FACTOR = {
    "group_stage": 40,
    "round_of_32": 45,
    "round_of_16": 50,
    "quarter_final": 55,
    "semi_final": 60,
    "final": 65,
    "default": 40,
}

ELO_STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "elo_state.json")


def load_elo_ratings() -> Dict[str, float]:
    """Load ELO ratings from state file (updated during tournament) or use defaults."""
    if os.path.exists(ELO_STATE_FILE):
        try:
            with open(ELO_STATE_FILE, "r") as f:
                saved = json.load(f)
            # Merge with defaults for any missing teams
            ratings = dict(FIFA_2026_ELO_RATINGS)
            ratings.update(saved)
            return ratings
        except Exception:
            pass
    return dict(FIFA_2026_ELO_RATINGS)


def save_elo_ratings(ratings: Dict[str, float]) -> None:
    """Persist updated ELO ratings."""
    os.makedirs(os.path.dirname(ELO_STATE_FILE), exist_ok=True)
    with open(ELO_STATE_FILE, "w") as f:
        json.dump(ratings, f, indent=2)


def expected_score(elo_a: float, elo_b: float, home_bonus: float = 0.0) -> float:
    """Expected score for team A vs team B (with optional home bonus in ELO points)."""
    return 1.0 / (1.0 + 10.0 ** ((elo_b - elo_a - home_bonus) / 400.0))


def win_probability(elo_home: float, elo_away: float, is_neutral: bool = False) -> Tuple[float, float, float]:
    """
    Calculate 1x2 probabilities using ELO difference.
    Returns (home_win, draw, away_win).
    Uses sigmoid-based draw model.
    """
    home_bonus = 0 if is_neutral else HOME_ADVANTAGE * 100  # convert factor to ELO points
    exp_home = expected_score(elo_home, elo_away, home_bonus)
    exp_away = 1.0 - exp_home

    # Draw probability increases when teams are closer in ELO
    # Heuristic: max draw probability at equal ELO ~ 0.25, decreases with difference
    elo_diff = abs(elo_home + (0 if is_neutral else HOME_ADVANTAGE * 100) - elo_away)
    draw_p = max(0.10, 0.28 * math.exp(-elo_diff / 600.0))

    home_win = exp_home * (1.0 - draw_p)
    away_win = exp_away * (1.0 - draw_p)

    # Normalise
    total = home_win + draw_p + away_win
    return (
        round(home_win / total, 4),
        round(draw_p / total, 4),
        round(away_win / total, 4),
    )


def expected_goals_from_elo(elo_home: float, elo_away: float,
                             league_avg_goals: float = 2.7,
                             is_neutral: bool = False) -> Tuple[float, float]:
    """
    Estimate expected goals (xG) using ELO difference.
    Based on the relationship between ELO difference and goal expectation.
    """
    home_bonus = 0 if is_neutral else HOME_ADVANTAGE * 100
    exp = expected_score(elo_home, elo_away, home_bonus)

    # Each team's share of total goals proportional to win expectation
    # Adjustment: winning probability translates to extra goals
    home_xg = league_avg_goals * (0.4 + 0.5 * exp)
    away_xg = league_avg_goals * (0.4 + 0.5 * (1 - exp))

    # Scale to realistic totals
    scaling = league_avg_goals / (home_xg + away_xg)
    home_xg *= scaling * 1.02
    away_xg *= scaling * 0.98

    return round(max(0.3, home_xg), 3), round(max(0.3, away_xg), 3)


def update_elo(ratings: Dict[str, float], home_team: str, away_team: str,
               home_goals: int, away_goals: int,
               stage: str = "group_stage",
               is_neutral: bool = True) -> Dict[str, float]:
    """Update ELO ratings after a match result."""
    ratings = dict(ratings)
    elo_h = ratings.get(home_team, 1700.0)
    elo_a = ratings.get(away_team, 1700.0)
    k = ELO_K_FACTOR.get(stage, ELO_K_FACTOR["default"])

    home_bonus = 0 if is_neutral else HOME_ADVANTAGE * 100
    exp_h = expected_score(elo_h, elo_a, home_bonus)

    # Actual result
    if home_goals > away_goals:
        result_h = 1.0
    elif home_goals == away_goals:
        result_h = 0.5
    else:
        result_h = 0.0

    # Goal difference multiplier (bigger wins get bigger ELO boosts)
    goal_diff = abs(home_goals - away_goals)
    if goal_diff == 1:
        gd_mult = 1.0
    elif goal_diff == 2:
        gd_mult = 1.5
    else:
        gd_mult = 1.75 + (goal_diff - 3) * 0.1

    delta = k * gd_mult * (result_h - exp_h)
    ratings[home_team] = round(elo_h + delta, 1)
    ratings[away_team] = round(elo_a - delta, 1)

    return ratings


def get_team_elo(team_name: str, ratings: Optional[Dict] = None) -> float:
    """Get ELO for a team, falling back to default."""
    if ratings is None:
        ratings = load_elo_ratings()

    # Try exact match
    if team_name in ratings:
        return ratings[team_name]

    # Fuzzy match
    lower = team_name.lower()
    for name, elo in ratings.items():
        if name.lower() == lower or lower in name.lower() or name.lower() in lower:
            return elo

    return 1700.0  # Default for unknown teams
