"""
Recent form analyzer.
Calculates weighted form scores and attack/defense strength from recent matches.
"""
import math
from typing import List, Dict, Tuple, Optional
from config import HOME_ADVANTAGE

# Aliases for fuzzy team name matching
TEAM_ALIASES = {
    "usa": ["united states", "us men", "usmnt", "u.s.a", "u.s."],
    "england": ["three lions"],
    "brazil": ["brasil"],
    "germany": ["deutschland"],
    "south korea": ["korea republic", "korea"],
    "ivory coast": ["cote d'ivoire", "cote divoire"],
    "dr congo": ["congo dr", "drc"],
}

def _names_match(name_a: str, name_b: str) -> bool:
    """Check if two team names refer to the same team (handles aliases)."""
    a = name_a.lower().strip()
    b = name_b.lower().strip()
    if a == b or a in b or b in a:
        return True
    # Check aliases
    for canonical, aliases in TEAM_ALIASES.items():
        a_matches = (a == canonical or a in aliases)
        b_matches = (b == canonical or b in aliases)
        if a_matches and b_matches:
            return True
        if a_matches and canonical in b:
            return True
        if b_matches and canonical in a:
            return True
    return False


def exponential_weights(n: int, decay: float = 0.7) -> List[float]:
    """Most recent match gets weight 1, older matches decay exponentially."""
    weights = [decay ** i for i in range(n)]
    total = sum(weights)
    return [w / total for w in weights]


def calculate_form_score(results: List[Dict], team_name: str) -> float:
    """
    Calculate form score from 0 to 1 based on W/D/L in recent matches.
    Most recent match weighted highest.
    """
    if not results:
        return 0.5  # neutral baseline

    # Filter only results where this team actually played
    relevant = [
        r for r in results
        if _names_match(team_name, r.get("home_team", "")) or _names_match(team_name, r.get("away_team", ""))
    ]
    if not relevant:
        return 0.5

    outcomes = []
    for r in relevant[:10]:  # max last 10 matches
        home = r.get("home_team", "")
        away = r.get("away_team", "")
        winner = r.get("winner", "DRAW").upper()

        is_home = _names_match(team_name, home)
        is_away = _names_match(team_name, away)

        if not (is_home or is_away):
            continue

        if winner == "DRAW":
            outcomes.append(0.5)
        elif (winner == "HOME_TEAM" and is_home) or (winner == "AWAY_TEAM" and is_away):
            outcomes.append(1.0)  # Win
        else:
            outcomes.append(0.0)  # Loss

    if not outcomes:
        return 0.5

    weights = exponential_weights(len(outcomes))
    score = sum(o * w for o, w in zip(outcomes, weights))
    return round(score, 4)


def calculate_attack_strength(results: List[Dict], team_name: str,
                               league_avg_goals: float = 1.35) -> float:
    """
    Attack strength = (team's avg goals scored) / (league average)
    Returns multiplier (>1 = stronger than average attack)
    """
    goals_scored = []
    for r in results[:10]:
        home = r.get("home_team", "")
        away = r.get("away_team", "")

        if _names_match(team_name, home):
            goals_scored.append(r.get("home_goals", 0) or 0)
        elif _names_match(team_name, away):
            goals_scored.append(r.get("away_goals", 0) or 0)

    if not goals_scored:
        return 1.0

    avg = sum(goals_scored) / len(goals_scored)
    return round(max(0.3, avg / league_avg_goals), 3)


def calculate_defense_strength(results: List[Dict], team_name: str,
                                league_avg_goals: float = 1.35) -> float:
    """
    Defense strength = (league average) / (team's avg goals conceded)
    Returns multiplier (>1 = stronger than average defense, concedes fewer goals)
    Inverse: we multiply OPPONENT's λ by (league_avg / team_goals_conceded)
    """
    goals_conceded = []
    for r in results[:10]:
        home = r.get("home_team", "")
        away = r.get("away_team", "")

        if _names_match(team_name, home):
            goals_conceded.append(r.get("away_goals", 0) or 0)
        elif _names_match(team_name, away):
            goals_conceded.append(r.get("home_goals", 0) or 0)

    if not goals_conceded:
        return 1.0

    avg_conceded = sum(goals_conceded) / len(goals_conceded)
    if avg_conceded <= 0:
        return 2.0  # Very strong defense

    return round(league_avg_goals / avg_conceded, 3)


def calculate_expected_goals(
    home_form: List[Dict], away_form: List[Dict],
    home_team: str, away_team: str,
    league_avg: float = 2.75,
    is_neutral: bool = True,
    home_advantage: float = HOME_ADVANTAGE,
) -> Tuple[float, float]:
    """
    Calculate expected goals for both teams using attack/defense strengths.

    λ_home = league_avg/2 × home_attack × away_defense_weakness × home_advantage_factor
    λ_away = league_avg/2 × away_attack × home_defense_weakness
    """
    per_team_avg = league_avg / 2.0

    home_atk = calculate_attack_strength(home_form, home_team, per_team_avg)
    away_atk = calculate_attack_strength(away_form, away_team, per_team_avg)

    # Defense: how many goals does the team's OPPONENT typically score?
    # A good defense means opponent scores less, so their attack is weakened
    home_def = calculate_defense_strength(home_form, home_team, per_team_avg)
    away_def = calculate_defense_strength(away_form, away_team, per_team_avg)

    # λ = per_team_avg × attacker_strength × opponent_defense_weakness
    # defense_weakness = 1 / defense_strength
    home_def_weakness = 1.0 / home_def if home_def > 0 else 1.0
    away_def_weakness = 1.0 / away_def if away_def > 0 else 1.0

    lam_home = per_team_avg * home_atk * away_def_weakness
    lam_away = per_team_avg * away_atk * home_def_weakness

    # Home advantage for non-neutral venues (FIFA 2026 is at neutral+ hosts)
    if not is_neutral:
        lam_home *= home_advantage

    # Clip to realistic range
    lam_home = round(max(0.3, min(4.5, lam_home)), 3)
    lam_away = round(max(0.3, min(4.5, lam_away)), 3)

    return lam_home, lam_away


def form_multiplier(form_score: float) -> float:
    """
    Convert form score (0-1) to a λ multiplier.
    Perfect form (1.0) = +20% goals, poor form (0.0) = -20% goals.
    """
    # Linear interpolation: form=0 → 0.80, form=0.5 → 1.00, form=1.0 → 1.20
    return round(0.80 + 0.40 * form_score, 3)


def recent_goal_avg(results: List[Dict], team_name: str, n: int = 5) -> float:
    """Average goals scored in last N matches."""
    goals = []
    for r in results[:n]:
        home = r.get("home_team", "")
        away = r.get("away_team", "")
        if _names_match(team_name, home):
            goals.append(r.get("home_goals", 0) or 0)
        elif _names_match(team_name, away):
            goals.append(r.get("away_goals", 0) or 0)
    return round(sum(goals) / len(goals), 3) if goals else 1.35
