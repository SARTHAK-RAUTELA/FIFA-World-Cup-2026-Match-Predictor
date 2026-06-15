"""
Local WC 2026 results collector — reads data/fifa_2026_results.json.
Provides form data for all WC 2026 teams using actual tournament results,
and applies pending ELO updates from those results to elo_state.json.
"""
import json
import os
from typing import List, Dict

_RESULTS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "fifa_2026_results.json")


def _load_data() -> Dict:
    with open(_RESULTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_data(data: Dict) -> None:
    with open(_RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _names_overlap(a: str, b: str) -> bool:
    a_l = a.lower().strip()
    b_l = b.lower().strip()
    return a_l == b_l or a_l in b_l or b_l in a_l


def _result_to_form_dict(r: Dict) -> Dict:
    hg = r.get("home_goals", 0)
    ag = r.get("away_goals", 0)
    if hg > ag:
        winner = "HOME_TEAM"
    elif ag > hg:
        winner = "AWAY_TEAM"
    else:
        winner = "DRAW"
    return {
        "home_team": r.get("home_team", ""),
        "away_team": r.get("away_team", ""),
        "home_goals": hg,
        "away_goals": ag,
        "winner": winner,
        "competition": "FIFA World Cup 2026",
        "date": r.get("date", ""),
    }


def get_team_wc_form(team_name: str, n: int = 10) -> List[Dict]:
    """
    Return a team's WC 2026 results as form dicts compatible with form_analyzer.
    Most recent results first.
    """
    try:
        data = _load_data()
    except Exception:
        return []

    form = []
    for r in data.get("results", []):
        home = r.get("home_team", "")
        away = r.get("away_team", "")
        if _names_overlap(team_name, home) or _names_overlap(team_name, away):
            form.append(_result_to_form_dict(r))

    form.sort(key=lambda x: x.get("date", ""), reverse=True)
    return form[:n]


def get_all_results_as_form() -> List[Dict]:
    """Return all WC 2026 results in form-compatible format (for H2H lookups)."""
    try:
        data = _load_data()
    except Exception:
        return []
    return [_result_to_form_dict(r) for r in data.get("results", [])]


def apply_pending_elo_updates() -> int:
    """
    Apply any un-applied ELO updates from elo_updates_needed list.
    Updates data/elo_state.json and marks entries as applied in the JSON file.
    Returns the number of updates applied.
    """
    from models.elo_model import load_elo_ratings, save_elo_ratings, update_elo
    try:
        data = _load_data()
    except Exception:
        return 0

    pending = [u for u in data.get("elo_updates_needed", []) if not u.get("applied", False)]
    if not pending:
        return 0

    ratings = load_elo_ratings()
    applied_count = 0

    for upd in pending:
        home = upd.get("home", "")
        away = upd.get("away", "")
        hg = upd.get("hg", 0)
        ag = upd.get("ag", 0)
        if home and away:
            ratings = update_elo(ratings, home, away, hg, ag, stage="group_stage", is_neutral=True)
            upd["applied"] = True
            applied_count += 1

    if applied_count > 0:
        save_elo_ratings(ratings)
        _save_data(data)

    return applied_count


def record_result(
    home_team: str,
    away_team: str,
    home_goals: int,
    away_goals: int,
    match_id: str = None,
    date: str = None,
    group: str = None,
    venue: str = None,
    stage: str = "group_stage",
) -> None:
    """
    Append a new finished match result to the local results file,
    and immediately apply its ELO update.
    """
    from models.elo_model import load_elo_ratings, save_elo_ratings, update_elo
    try:
        data = _load_data()
    except Exception:
        return

    # Deduplicate: skip if already recorded (fuzzy name match + same score)
    for r in data.get("results", []):
        if (_names_overlap(r.get("home_team", ""), home_team) and
                _names_overlap(r.get("away_team", ""), away_team) and
                r.get("home_goals") == home_goals and r.get("away_goals") == away_goals):
            return

    hg = home_goals
    ag = away_goals
    result_code = "H" if hg > ag else ("A" if ag > hg else "D")

    new_result = {
        "match_id": match_id or f"WC2026_{home_team[:3].upper()}_{away_team[:3].upper()}",
        "date": date or "",
        "stage": stage,
        "home_team": home_team,
        "away_team": away_team,
        "home_goals": hg,
        "away_goals": ag,
        "result": result_code,
    }
    if venue:
        new_result["venue"] = venue
    if group:
        new_result["group"] = group

    data.setdefault("results", []).append(new_result)
    data["_meta"]["matches_played"] = len(data["results"])
    if date:
        data["_meta"]["last_updated"] = date

    # Apply ELO update immediately
    ratings = load_elo_ratings()
    ratings = update_elo(ratings, home_team, away_team, hg, ag, stage=stage, is_neutral=True)
    save_elo_ratings(ratings)

    _save_data(data)
