"""
ESPN unofficial API collector.
No API key required — uses ESPN's public JSON endpoints.
Covers FIFA 2026 World Cup fixtures, lineups, and live scores.
"""
import requests
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from collectors.base_collector import BaseCollector
from config import ESPN_BASE, ESPN_WORLD_CUP_SLUGS, CACHE_TTL


class ESPNCollector(BaseCollector):
    def __init__(self):
        super().__init__(base_url=ESPN_BASE, rate_limit_delay=0.3)
        self._working_slug: Optional[str] = None

    def _find_working_slug(self) -> Optional[str]:
        if self._working_slug:
            return self._working_slug
        for slug in ESPN_WORLD_CUP_SLUGS:
            url = f"{ESPN_BASE}/{slug}/scoreboard"
            try:
                resp = requests.get(url, timeout=8)
                if resp.status_code == 200:
                    data = resp.json()
                    if "events" in data or "leagues" in data:
                        self._working_slug = slug
                        return slug
            except Exception:
                continue
        return None

    def get_today_fixtures(self, target_date: Optional[date] = None) -> List[Dict]:
        slug = self._find_working_slug()
        if not slug:
            return []
        d = target_date or date.today()
        date_str = d.strftime("%Y%m%d")
        cache_key = f"espn_fixtures_{date_str}"
        data = self.cached_get(
            cache_key,
            f"{slug}/scoreboard",
            params={"dates": date_str},
            ttl=CACHE_TTL["fixtures"],
        )
        if not data:
            return []
        return self._parse_fixtures(data)

    def get_match_details(self, event_id: str, slug: Optional[str] = None) -> Optional[Dict]:
        slug = slug or self._find_working_slug()
        if not slug:
            return None
        cache_key = f"espn_match_{event_id}"
        data = self.cached_get(
            cache_key,
            f"{slug}/summary",
            params={"event": event_id},
            ttl=CACHE_TTL["lineups"],
        )
        if not data:
            return None
        return self._parse_match_details(data)

    def get_team_recent_form(self, team_id: str, slug: Optional[str] = None) -> List[Dict]:
        slug = slug or self._find_working_slug()
        if not slug:
            return []
        cache_key = f"espn_form_{team_id}"
        data = self.cached_get(
            cache_key,
            f"{slug}/teams/{team_id}/schedule",
            ttl=CACHE_TTL["form"],
        )
        if not data:
            return []
        return self._parse_form(data)

    def _parse_fixtures(self, data: Dict) -> List[Dict]:
        matches = []
        for event in data.get("events", []):
            try:
                competition = event.get("competitions", [{}])[0]
                competitors = competition.get("competitors", [])
                home = next((c for c in competitors if c.get("homeAway") == "home"), None)
                away = next((c for c in competitors if c.get("homeAway") == "away"), None)
                if not home or not away:
                    continue

                status_obj = event.get("status", {}).get("type", {})
                match = {
                    "id": event.get("id"),
                    "source": "espn",
                    "date": event.get("date"),
                    "status": status_obj.get("name", "unknown"),
                    "status_short": status_obj.get("shortDetail", ""),
                    "home_team": home.get("team", {}).get("displayName", ""),
                    "away_team": away.get("team", {}).get("displayName", ""),
                    "home_team_id": home.get("team", {}).get("id"),
                    "away_team_id": away.get("team", {}).get("id"),
                    "home_score": int(home.get("score", 0) or 0),
                    "away_score": int(away.get("score", 0) or 0),
                    "venue": event.get("competitions", [{}])[0].get("venue", {}).get("fullName", ""),
                    "city": event.get("competitions", [{}])[0].get("venue", {}).get("city", {}).get("displayName", ""),
                    "broadcast": ", ".join(
                        b.get("names", [""])[0]
                        for b in competition.get("broadcasts", [])
                        if b.get("names")
                    ),
                }
                matches.append(match)
            except (KeyError, IndexError, TypeError):
                continue
        return matches

    def _parse_match_details(self, data: Dict) -> Dict:
        details = {"lineups": {"home": [], "away": []}, "injuries": [], "stats": {}}
        try:
            rosters = data.get("rosters", [])
            for roster in rosters:
                side = "home" if roster.get("homeAway") == "home" else "away"
                for entry in roster.get("entries", []):
                    athlete = entry.get("athlete", {})
                    player = {
                        "id": athlete.get("id"),
                        "name": athlete.get("displayName", ""),
                        "position": athlete.get("position", {}).get("abbreviation", ""),
                        "jersey": athlete.get("jersey", ""),
                        "starter": entry.get("starter", False),
                        "active": entry.get("active", True),
                        "did_not_play": entry.get("didNotPlay", False),
                    }
                    details["lineups"][side].append(player)

            for team_stats in data.get("teamStats", []):
                side = "home" if team_stats.get("homeAway") == "home" else "away"
                details["stats"][side] = {
                    s.get("name"): s.get("displayValue")
                    for s in team_stats.get("stats", [])
                }
        except Exception:
            pass
        return details

    def _parse_form(self, data: Dict) -> List[Dict]:
        results = []
        for event in data.get("events", [])[-10:]:
            try:
                competition = event.get("competitions", [{}])[0]
                competitors = competition.get("competitors", [])
                result_entry = {"date": event.get("date"), "opponent": "", "result": "U",
                                "goals_for": 0, "goals_against": 0}
                for comp in competitors:
                    if comp.get("homeAway") == "away":
                        result_entry["opponent"] = comp.get("team", {}).get("displayName", "")
                    score = int(comp.get("score", 0) or 0)
                    if comp.get("winner"):
                        result_entry["result"] = "W"
                    if comp.get("homeAway") == "home":
                        result_entry["goals_for"] = score
                    else:
                        result_entry["goals_against"] = score
                if result_entry["result"] == "U":
                    comp = competitors[0] if competitors else {}
                    if not comp.get("winner"):
                        result_entry["result"] = "D"
                results.append(result_entry)
            except Exception:
                continue
        return results
