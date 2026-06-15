"""
Collector for worldcup26.ir — free, no-key-required WC 2026 fixture/standings API.
Community-built; covers all 104 FIFA 2026 matches, 48 teams, 12 groups.
"""
import requests
from typing import List, Dict, Optional
from config import WORLDCUP26_BASE


class WorldCup26Collector:
    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "FIFA2026Predictor/1.0"})

    def _get(self, endpoint: str, timeout: int = 8) -> Optional[object]:
        try:
            resp = self._session.get(f"{WORLDCUP26_BASE}/{endpoint}", timeout=timeout)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return None

    def get_fixtures(self) -> List[Dict]:
        """Return all WC 2026 matches. Returns normalised fixture dicts."""
        raw = self._get("games")
        if not raw:
            return []
        games = raw if isinstance(raw, list) else raw.get("games", raw.get("data", []))
        if not isinstance(games, list):
            return []

        matches = []
        for g in games:
            # API returns home_team_name_en / away_team_name_en directly
            home = (g.get("home_team_name_en") or g.get("home_team") or g.get("homeTeam") or "").strip()
            away = (g.get("away_team_name_en") or g.get("away_team") or g.get("awayTeam") or "").strip()
            if not home or not away:
                continue
            hg_raw = g.get("home_score") or g.get("homeScore")
            ag_raw = g.get("away_score") or g.get("awayScore")
            finished = str(g.get("finished", "")).upper() == "TRUE"
            try:
                hg = int(hg_raw) if hg_raw is not None else None
                ag = int(ag_raw) if ag_raw is not None else None
            except (TypeError, ValueError):
                hg = ag = None
            # Only include score if match is finished
            matches.append({
                "home_team": home,
                "away_team": away,
                "home_goals": hg if finished else None,
                "away_goals": ag if finished else None,
                "finished": finished,
                "status": "finished" if finished else g.get("time_elapsed", ""),
                "date": g.get("local_date") or g.get("date") or g.get("matchDate", ""),
                "group": g.get("group", ""),
                "matchday": g.get("matchday"),
                "source": "worldcup26.ir",
            })
        return matches

    def get_group_standings(self) -> Dict[str, List[Dict]]:
        """Return raw group standings dict keyed by group letter.
        API returns {"groups": [{name, teams:[{team_id, mp, w, l, d, pts, gf, ga, gd}]}]}
        """
        raw = self._get("groups")
        if not raw:
            return {}

        groups_list = raw.get("groups", raw) if isinstance(raw, dict) else raw
        if not isinstance(groups_list, list):
            return {}

        result = {}
        for grp in groups_list:
            name = (grp.get("name") or grp.get("group") or "").strip()
            if name:
                result[name] = grp.get("teams", [])
        return result

    def get_teams(self) -> List[Dict]:
        """Return list of all 48 WC 2026 teams. API returns {teams:[...]}."""
        raw = self._get("teams")
        if not raw:
            return []
        teams = raw.get("teams", raw) if isinstance(raw, dict) else raw
        return teams if isinstance(teams, list) else []

    def get_completed_results_as_form(self) -> List[Dict]:
        """Return completed fixtures in form_analyzer-compatible format."""
        form = []
        for f in self.get_fixtures():
            hg = f.get("home_goals")
            ag = f.get("away_goals")
            if hg is None or ag is None:
                continue
            if hg > ag:
                winner = "HOME_TEAM"
            elif ag > hg:
                winner = "AWAY_TEAM"
            else:
                winner = "DRAW"
            form.append({
                "home_team": f["home_team"],
                "away_team": f["away_team"],
                "home_goals": hg,
                "away_goals": ag,
                "winner": winner,
                "competition": "FIFA World Cup 2026",
                "date": f.get("date", ""),
            })
        return form
