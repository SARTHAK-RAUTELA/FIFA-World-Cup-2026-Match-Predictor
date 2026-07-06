"""
Finds ALL_PREDS entries in docs/index.html with status "upcoming", checks
football-data.org for a finished result on that fixture's date, and if the
match is done, fills in the real score and grades the pick (correct/wrong).

Grading conventions:
- "{Team} Match Result" / "Draw" / "Draw (ET/Pens)": graded on the final
  outcome (score.winner), which already accounts for extra time/penalties.
- Asian Handicap / Over-Under Goals / BTTS: graded on the 90-minute score
  (score.fullTime) — standard bookmaker convention for these markets, which
  settle before extra time even in knockout rounds.
- A push (exact Asian Handicap line) or an unrecognised betLabel is marked
  "done" (grey FINAL badge) rather than guessed as correct/wrong.

Usage: python scripts/update_match_results.py
"""
import json
import os
import re
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

from collectors.football_data_collector import FootballDataCollector

INDEX_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "index.html")
ARRAY_MARKER = "const ALL_PREDS = "

# Site team name -> football-data.org team name, where they differ.
TEAM_ALIASES = {
    "USA": "United States",
    "Czech Republic": "Czechia",
    "DR Congo": "Congo DR",
    "Cabo Verde": "Cape Verde Islands",
}


def api_name(site_name):
    return TEAM_ALIASES.get(site_name, site_name)


def grade_bet(bet_label, home, away, home_goals, away_goals, winner):
    """Returns True (correct), False (wrong), or "push" (void/indeterminate)."""
    m = re.match(r"^(.+) Match Result$", bet_label)
    if m:
        picked = m.group(1)
        if winner == "HOME_TEAM":
            return picked == home
        if winner == "AWAY_TEAM":
            return picked == away
        return False  # picked a team but match drawn

    if bet_label == "Draw":
        return winner == "DRAW"

    m = re.match(r"^(.+) [-−]([\d.]+) Asian Handicap$", bet_label)
    if m:
        team, line = m.group(1), float(m.group(2))
        if team == home:
            diff = (home_goals - line) - away_goals
        elif team == away:
            diff = (away_goals - line) - home_goals
        else:
            return "push"
        if diff > 0:
            return True
        if diff == 0:
            return "push"
        return False

    m = re.match(r"^(Over|Under) ([\d.]+) Goals$", bet_label)
    if m:
        direction, threshold = m.group(1), float(m.group(2))
        total = home_goals + away_goals
        return total > threshold if direction == "Over" else total < threshold

    m = re.match(r"^BTTS [—-] (Yes|No)$", bet_label)
    if m:
        both_scored = home_goals > 0 and away_goals > 0
        return both_scored if m.group(1) == "Yes" else not both_scored

    return "push"  # unrecognised label — don't guess, mark FINAL instead


def result_display(score):
    duration = score.get("duration", "REGULAR")
    full = score.get("fullTime") or {}
    home_goals, away_goals = full.get("home", 0), full.get("away", 0)
    display = f"{home_goals}–{away_goals}"
    pens = score.get("penalties") or {}
    if duration == "PENALTY_SHOOTOUT" and pens.get("home") is not None:
        display += f" ({pens['home']}–{pens['away']} pens)"
    elif duration == "EXTRA_TIME":
        display += " (AET)"
    return display, home_goals, away_goals


def main():
    collector = FootballDataCollector()
    if not collector.is_configured:
        print("FOOTBALL_DATA_API_KEY not set — skipping result update.")
        sys.exit(1)

    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    marker_idx = text.find(ARRAY_MARKER)
    if marker_idx == -1:
        print("Could not find ALL_PREDS array in docs/index.html")
        sys.exit(1)

    array_start = marker_idx + len(ARRAY_MARKER)
    preds, end_idx = json.JSONDecoder().raw_decode(text, array_start)

    upcoming = [p for p in preds if p.get("status") == "upcoming"]
    if not upcoming:
        print("No upcoming fixtures to check.")
        return

    dates = sorted({p["date"] for p in upcoming})
    matches_by_date = {}
    for d in dates:
        date_from = d
        date_to = (date.fromisoformat(d) + timedelta(days=1)).isoformat()
        matches_by_date[d] = collector.get_matches(date_from, date_to)

    changed = 0
    for p in upcoming:
        home_api, away_api = api_name(p["home"]), api_name(p["away"])
        match = next(
            (
                m for m in matches_by_date.get(p["date"], [])
                if m.get("homeTeam", {}).get("name") == home_api
                and m.get("awayTeam", {}).get("name") == away_api
            ),
            None,
        )
        if not match or match.get("status") != "FINISHED":
            continue

        score = match.get("score", {})
        winner = score.get("winner")
        display, home_goals, away_goals = result_display(score)
        verdict = grade_bet(p["betLabel"], p["home"], p["away"], home_goals, away_goals, winner)

        p["time"] = "FT"
        p["result"] = display
        p["status"] = "done" if verdict == "push" else ("correct" if verdict else "wrong")
        p["note"] = f"{p['note']} Full-time: {p['home']} {display} {p['away']}."
        changed += 1
        print(f"Graded {p['id']}: {p['home']} {display} {p['away']} -> {p['status']}")

    if not changed:
        print("Checked all upcoming fixtures — nothing finished yet.")
        return

    new_array = json.dumps(preds, ensure_ascii=False)
    new_text = text[:array_start] + new_array + text[end_idx:]
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(new_text)
    print(f"Updated {changed} fixture(s) in {INDEX_PATH}")


if __name__ == "__main__":
    main()
