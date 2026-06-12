"""
Football Standings API collector.
Free, no API key needed. ESPN-backed.
Base URL: https://api-football-standings.azharimm.site
Provides group standings for FIFA World Cup 2026.
"""
from typing import Optional, List, Dict
from collectors.base_collector import BaseCollector
from config import FOOTBALL_STANDINGS_BASE, CACHE_TTL


# ESPN league IDs / slugs to try for FIFA World Cup 2026
WC_LEAGUE_SLUGS = ["fifa.world", "fifa.worldcup", "fifa.wc"]


class FootballStandingsCollector(BaseCollector):
    def __init__(self):
        super().__init__(base_url=FOOTBALL_STANDINGS_BASE, rate_limit_delay=0.3)
        self._wc_league_id: Optional[str] = None
        self._wc_season_id: Optional[str] = None

    def get_wc_standings(self) -> List[Dict]:
        """
        Return FIFA World Cup 2026 group standings.
        Each entry: {team, group, points, wins, draws, losses, gf, ga, gd, position}
        """
        league_id = self._find_wc_league_id()
        if not league_id:
            return []
        season_id = self._find_wc_season(league_id)
        if not season_id:
            return []
        return self._fetch_standings(league_id, season_id)

    def get_team_standing(self, team_name: str) -> Optional[Dict]:
        """Get a specific team's current standing in the WC group stage."""
        all_standings = self.get_wc_standings()
        team_l = team_name.lower()
        for entry in all_standings:
            if team_l in entry.get("team", "").lower() or \
               entry.get("team", "").lower() in team_l:
                return entry
        return None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _find_wc_league_id(self) -> Optional[str]:
        if self._wc_league_id:
            return self._wc_league_id

        data = self.cached_get("standings_leagues", "leagues", ttl=CACHE_TTL["standings"])
        if not data:
            return None

        leagues = data.get("data", []) if isinstance(data, dict) else data
        if not isinstance(leagues, list):
            return None

        # Look for FIFA World Cup entry
        for league in leagues:
            slug = (league.get("slug") or league.get("id") or "").lower()
            name = (league.get("name") or "").lower()
            if "world cup" in name or "fifa.world" in slug or slug in WC_LEAGUE_SLUGS:
                self._wc_league_id = league.get("id") or league.get("slug")
                return self._wc_league_id

        # Fallback: try known slugs directly
        for slug in WC_LEAGUE_SLUGS:
            test = self.cached_get(
                f"standings_league_test_{slug}",
                f"leagues/{slug}/seasons",
                ttl=CACHE_TTL["standings"],
            )
            if test and not (isinstance(test, dict) and test.get("error")):
                self._wc_league_id = slug
                return slug

        return None

    def _find_wc_season(self, league_id: str) -> Optional[str]:
        if self._wc_season_id:
            return self._wc_season_id

        data = self.cached_get(
            f"standings_seasons_{league_id}",
            f"leagues/{league_id}/seasons",
            ttl=CACHE_TTL["standings"],
        )
        if not data:
            return None

        seasons = data.get("data", []) if isinstance(data, dict) else data
        if not isinstance(seasons, list):
            return None

        # Prefer 2026 season; fall back to most recent
        target = None
        for s in seasons:
            year = str(s.get("year") or s.get("name") or "")
            if "2026" in year:
                target = s
                break
        if not target and seasons:
            target = seasons[0]

        if target:
            self._wc_season_id = str(target.get("id") or target.get("year") or "")
            return self._wc_season_id
        return None

    def _fetch_standings(self, league_id: str, season_id: str) -> List[Dict]:
        data = self.cached_get(
            f"standings_{league_id}_{season_id}",
            f"leagues/{league_id}/seasons/{season_id}/standings",
            params={"sort": "asc"},
            ttl=CACHE_TTL["standings"],
        )
        if not data:
            return []

        entries_raw = (
            data.get("data", {}).get("standings", {}).get("entries", [])
            if isinstance(data, dict)
            else []
        )
        if not entries_raw:
            # Alternative structure
            entries_raw = data.get("entries", []) if isinstance(data, dict) else []

        results = []
        for entry in entries_raw:
            team = entry.get("team", {}).get("displayName", "") or \
                   entry.get("team", {}).get("name", "")
            if not team:
                continue

            stats_list = entry.get("stats", [])
            stats = {s["name"]: s.get("value", 0) for s in stats_list if s.get("name")}

            results.append({
                "team": team,
                "group": entry.get("note", {}).get("abbreviation", ""),
                "position": entry.get("sortOrder") or entry.get("rank", 0),
                "points": stats.get("points", 0),
                "wins": stats.get("wins", 0),
                "draws": stats.get("ties", stats.get("draws", 0)),
                "losses": stats.get("losses", 0),
                "gf": stats.get("pointsFor", stats.get("goalsFor", 0)),
                "ga": stats.get("pointsAgainst", stats.get("goalsAgainst", 0)),
                "gd": stats.get("pointDifferential", 0),
                "played": stats.get("gamesPlayed", 0),
                "source": "football-standings",
            })

        return results
