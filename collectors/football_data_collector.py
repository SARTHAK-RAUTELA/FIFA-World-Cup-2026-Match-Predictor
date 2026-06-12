"""
football-data.org API collector.
Free tier covers World Cup (code: WC).
Register free at https://www.football-data.org/client/register
"""
from datetime import date, timedelta
from typing import Optional, List, Dict
from collectors.base_collector import BaseCollector
from config import FOOTBALL_DATA_BASE, FOOTBALL_DATA_API_KEY, CACHE_TTL, FIFA_WC_CODES


class FootballDataCollector(BaseCollector):
    def __init__(self):
        headers = {"X-Auth-Token": FOOTBALL_DATA_API_KEY} if FOOTBALL_DATA_API_KEY else {}
        super().__init__(base_url=FOOTBALL_DATA_BASE, headers=headers, rate_limit_delay=0.7)

    @property
    def is_configured(self) -> bool:
        return bool(FOOTBALL_DATA_API_KEY)

    def get_today_fixtures(self, target_date: Optional[date] = None) -> List[Dict]:
        if not self.is_configured:
            return []
        from datetime import timedelta
        d = target_date or date.today()
        # Query a 2-day window: matches scheduled UTC tonight may fall on tomorrow's UTC date
        date_from = d.strftime("%Y-%m-%d")
        date_to = (d + timedelta(days=1)).strftime("%Y-%m-%d")
        for code in FIFA_WC_CODES:
            cache_key = f"fd_fixtures_{code}_{date_from}"
            data = self.cached_get(
                cache_key,
                f"competitions/{code}/matches",
                params={"dateFrom": date_from, "dateTo": date_to},
                ttl=CACHE_TTL["fixtures"],
            )
            if data and data.get("matches"):
                return self._parse_fixtures(data["matches"])
        return []

    def get_team_form(self, team_id: int, limit: int = 10) -> List[Dict]:
        if not self.is_configured:
            return []
        cache_key = f"fd_form_{team_id}"
        data = self.cached_get(
            cache_key,
            f"teams/{team_id}/matches",
            params={"status": "FINISHED", "limit": limit},
            ttl=CACHE_TTL["form"],
        )
        if not data:
            return []
        return self._parse_form(data.get("matches", []))

    def get_h2h(self, match_id: int) -> Optional[Dict]:
        if not self.is_configured:
            return None
        cache_key = f"fd_h2h_{match_id}"
        data = self.cached_get(
            cache_key,
            f"matches/{match_id}/head2head",
            params={"limit": 10},
            ttl=CACHE_TTL["h2h"],
        )
        return data

    def get_standings(self, competition_code: str = "WC") -> Optional[Dict]:
        if not self.is_configured:
            return None
        cache_key = f"fd_standings_{competition_code}"
        return self.cached_get(
            cache_key,
            f"competitions/{competition_code}/standings",
            ttl=CACHE_TTL["standings"],
        )

    def get_top_scorers(self, competition_code: str = "WC") -> List[Dict]:
        if not self.is_configured:
            return []
        cache_key = f"fd_scorers_{competition_code}"
        data = self.cached_get(
            cache_key,
            f"competitions/{competition_code}/scorers",
            ttl=CACHE_TTL["player_stats"],
        )
        if not data:
            return []
        return data.get("scorers", [])

    def _parse_fixtures(self, matches: List[Dict]) -> List[Dict]:
        result = []
        for m in matches:
            try:
                result.append({
                    "id": m.get("id"),
                    "source": "football-data.org",
                    "date": m.get("utcDate"),
                    "status": m.get("status"),
                    "home_team": m.get("homeTeam", {}).get("name", ""),
                    "away_team": m.get("awayTeam", {}).get("name", ""),
                    "home_team_id": m.get("homeTeam", {}).get("id"),
                    "away_team_id": m.get("awayTeam", {}).get("id"),
                    "home_score": (m.get("score", {}).get("fullTime", {}) or {}).get("home", 0),
                    "away_score": (m.get("score", {}).get("fullTime", {}) or {}).get("away", 0),
                    "venue": m.get("venue", ""),
                    "group": m.get("group", ""),
                    "stage": m.get("stage", ""),
                    "referee": (m.get("referees") or [{}])[0].get("name", "") if m.get("referees") else "",
                })
            except Exception:
                continue
        return result

    def _parse_form(self, matches: List[Dict]) -> List[Dict]:
        result = []
        for m in matches:
            try:
                full_time = m.get("score", {}).get("fullTime", {}) or {}
                home_goals = full_time.get("home", 0) or 0
                away_goals = full_time.get("away", 0) or 0
                winner = (m.get("score", {}).get("winner") or "").upper()
                result.append({
                    "date": m.get("utcDate"),
                    "home_team": m.get("homeTeam", {}).get("name"),
                    "away_team": m.get("awayTeam", {}).get("name"),
                    "home_goals": home_goals,
                    "away_goals": away_goals,
                    "winner": winner,  # HOME_TEAM, AWAY_TEAM, DRAW
                    "competition": m.get("competition", {}).get("name", ""),
                })
            except Exception:
                continue
        return result
