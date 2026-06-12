"""
API-Football via RapidAPI collector.
Free tier: 100 requests/day.
Provides fixtures, lineups, injuries, player stats, and live scores.
"""
from datetime import date
from typing import Optional, List, Dict
from collectors.base_collector import BaseCollector
from config import API_FOOTBALL_BASE, API_FOOTBALL_KEY, CACHE_TTL


class APIFootballCollector(BaseCollector):
    def __init__(self):
        headers = {
            "X-RapidAPI-Key": API_FOOTBALL_KEY,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com",
        } if API_FOOTBALL_KEY else {}
        super().__init__(base_url=API_FOOTBALL_BASE, headers=headers, rate_limit_delay=1.2)

    @property
    def is_configured(self) -> bool:
        return bool(API_FOOTBALL_KEY)

    def get_fixtures(self, target_date: Optional[date] = None, league_id: int = 1) -> List[Dict]:
        """
        Get fixtures for a date. FIFA World Cup 2026 league_id = 1 (standard WC league).
        Also tries league_id=9 for older World Cup editions.
        """
        if not self.is_configured:
            return []
        d = target_date or date.today()
        date_str = d.strftime("%Y-%m-%d")

        # Try different World Cup league IDs
        for lid in [1, 9, 4]:
            cache_key = f"apif_fixtures_{lid}_{date_str}"
            data = self.cached_get(
                cache_key,
                "fixtures",
                params={"league": lid, "date": date_str, "season": 2026},
                ttl=CACHE_TTL["fixtures"],
            )
            if data and data.get("response"):
                return self._parse_fixtures(data["response"])
        return []

    def get_lineups(self, fixture_id: int) -> Optional[Dict]:
        if not self.is_configured:
            return None
        cache_key = f"apif_lineup_{fixture_id}"
        data = self.cached_get(
            cache_key,
            "fixtures/lineups",
            params={"fixture": fixture_id},
            ttl=CACHE_TTL["lineups"],
        )
        if not data or not data.get("response"):
            return None
        return self._parse_lineups(data["response"])

    def get_injuries(self, league_id: int = 1, season: int = 2026) -> List[Dict]:
        if not self.is_configured:
            return []
        cache_key = f"apif_injuries_{league_id}_{season}"
        data = self.cached_get(
            cache_key,
            "injuries",
            params={"league": league_id, "season": season},
            ttl=CACHE_TTL["player_stats"],
        )
        if not data:
            return []
        return data.get("response", [])

    def get_team_statistics(self, team_id: int, league_id: int = 1, season: int = 2026) -> Optional[Dict]:
        if not self.is_configured:
            return None
        cache_key = f"apif_stats_{team_id}_{league_id}_{season}"
        data = self.cached_get(
            cache_key,
            "teams/statistics",
            params={"team": team_id, "league": league_id, "season": season},
            ttl=CACHE_TTL["form"],
        )
        if not data:
            return None
        return data.get("response")

    def get_team_recent_fixtures(self, team_id: int, last: int = 10) -> List[Dict]:
        if not self.is_configured:
            return []
        cache_key = f"apif_recent_{team_id}_{last}"
        data = self.cached_get(
            cache_key,
            "fixtures",
            params={"team": team_id, "last": last, "status": "FT"},
            ttl=CACHE_TTL["form"],
        )
        if not data or not data.get("response"):
            return []
        return self._parse_fixtures(data["response"])

    def search_team(self, name: str) -> Optional[Dict]:
        if not self.is_configured:
            return None
        cache_key = f"apif_team_search_{name.lower().replace(' ', '_')}"
        data = self.cached_get(
            cache_key,
            "teams",
            params={"search": name},
            ttl=86400,
        )
        if data and data.get("response"):
            return data["response"][0].get("team")
        return None

    def _parse_fixtures(self, fixtures: List[Dict]) -> List[Dict]:
        result = []
        for f in fixtures:
            try:
                fixture = f.get("fixture", {})
                teams = f.get("teams", {})
                goals = f.get("goals", {})
                venue = fixture.get("venue", {})
                result.append({
                    "id": fixture.get("id"),
                    "source": "api-football",
                    "date": fixture.get("date", ""),
                    "status": fixture.get("status", {}).get("short", ""),
                    "home_team": teams.get("home", {}).get("name", ""),
                    "away_team": teams.get("away", {}).get("name", ""),
                    "home_team_id": teams.get("home", {}).get("id"),
                    "away_team_id": teams.get("away", {}).get("id"),
                    "home_score": goals.get("home", 0) or 0,
                    "away_score": goals.get("away", 0) or 0,
                    "venue": venue.get("name", ""),
                    "city": venue.get("city", ""),
                })
            except Exception:
                continue
        return result

    def _parse_lineups(self, lineups: List[Dict]) -> Dict:
        result = {"home": [], "away": []}
        for side_data in lineups:
            team = side_data.get("team", {})
            is_home = side_data.get("team", {}).get("id") == lineups[0].get("team", {}).get("id")
            key = "home" if lineups.index(side_data) == 0 else "away"
            for player in side_data.get("startXI", []):
                p = player.get("player", {})
                result[key].append({
                    "id": p.get("id"),
                    "name": p.get("name", ""),
                    "position": p.get("pos", ""),
                    "number": p.get("number"),
                    "starter": True,
                })
            for player in side_data.get("substitutes", []):
                p = player.get("player", {})
                result[key].append({
                    "id": p.get("id"),
                    "name": p.get("name", ""),
                    "position": p.get("pos", ""),
                    "number": p.get("number"),
                    "starter": False,
                })
        return result
