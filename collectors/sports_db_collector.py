"""
TheSportsDB API collector.
Free tier available with API key '3'.
Provides team/player data, schedules, and event details.
"""
from typing import Optional, List, Dict
from collectors.base_collector import BaseCollector
from config import SPORTS_DB_BASE, SPORTS_DB_API_KEY, SPORTS_DB_WC_LEAGUE_IDS, CACHE_TTL


class SportsDBCollector(BaseCollector):
    def __init__(self):
        super().__init__(base_url=SPORTS_DB_BASE, rate_limit_delay=0.5)
        self._api_key = SPORTS_DB_API_KEY or "3"

    def search_team(self, team_name: str) -> Optional[Dict]:
        cache_key = f"sdb_team_{team_name.lower().replace(' ', '_')}"
        data = self.cached_get(
            cache_key,
            f"{self._api_key}/searchteams.php",
            params={"t": team_name},
            ttl=CACHE_TTL["player_stats"],
        )
        if data and data.get("teams"):
            return data["teams"][0]
        return None

    def get_team_players(self, team_id: str) -> List[Dict]:
        cache_key = f"sdb_players_{team_id}"
        data = self.cached_get(
            cache_key,
            f"{self._api_key}/lookup_all_players.php",
            params={"id": team_id},
            ttl=CACHE_TTL["player_stats"],
        )
        if not data:
            return []
        return data.get("player", []) or []

    def get_player_details(self, player_name: str) -> Optional[Dict]:
        cache_key = f"sdb_player_{player_name.lower().replace(' ', '_')}"
        data = self.cached_get(
            cache_key,
            f"{self._api_key}/searchplayers.php",
            params={"p": player_name},
            ttl=CACHE_TTL["player_stats"],
        )
        if data and data.get("player"):
            return data["player"][0]
        return None

    def get_next_wc_fixtures(self) -> List[Dict]:
        matches = []
        for league_id in SPORTS_DB_WC_LEAGUE_IDS:
            cache_key = f"sdb_next_{league_id}"
            data = self.cached_get(
                cache_key,
                f"{self._api_key}/eventsnextleague.php",
                params={"id": league_id},
                ttl=CACHE_TTL["fixtures"],
            )
            if data and data.get("events"):
                matches.extend(self._parse_fixtures(data["events"]))
                if matches:
                    break
        return matches

    def get_last_wc_results(self, limit: int = 10) -> List[Dict]:
        results = []
        for league_id in SPORTS_DB_WC_LEAGUE_IDS:
            cache_key = f"sdb_last_{league_id}"
            data = self.cached_get(
                cache_key,
                f"{self._api_key}/eventspastleague.php",
                params={"id": league_id},
                ttl=CACHE_TTL["form"],
            )
            if data and data.get("events"):
                results.extend(self._parse_results(data["events"]))
                if results:
                    break
        return results[:limit]

    def get_team_recent_results(self, team_id: str) -> List[Dict]:
        cache_key = f"sdb_team_results_{team_id}"
        data = self.cached_get(
            cache_key,
            f"{self._api_key}/eventslast.php",
            params={"id": team_id},
            ttl=CACHE_TTL["form"],
        )
        if not data:
            return []
        return self._parse_results(data.get("results", []) or [])

    def _parse_fixtures(self, events: List[Dict]) -> List[Dict]:
        result = []
        for e in events:
            try:
                result.append({
                    "id": e.get("idEvent"),
                    "source": "thesportsdb",
                    "date": e.get("dateEvent"),
                    "time": e.get("strTime"),
                    "home_team": e.get("strHomeTeam", ""),
                    "away_team": e.get("strAwayTeam", ""),
                    "home_team_id": e.get("idHomeTeam"),
                    "away_team_id": e.get("idAwayTeam"),
                    "venue": e.get("strVenue", ""),
                    "round": e.get("intRound"),
                    "status": "TIMED",
                })
            except Exception:
                continue
        return result

    def _parse_results(self, events: List[Dict]) -> List[Dict]:
        result = []
        for e in events:
            try:
                home_score = int(e.get("intHomeScore") or 0)
                away_score = int(e.get("intAwayScore") or 0)
                result.append({
                    "date": e.get("dateEvent"),
                    "home_team": e.get("strHomeTeam", ""),
                    "away_team": e.get("strAwayTeam", ""),
                    "home_goals": home_score,
                    "away_goals": away_score,
                    "winner": (
                        "HOME_TEAM" if home_score > away_score
                        else "AWAY_TEAM" if away_score > home_score
                        else "DRAW"
                    ),
                    "competition": e.get("strLeague", ""),
                    "source": "thesportsdb",
                })
            except Exception:
                continue
        return result
