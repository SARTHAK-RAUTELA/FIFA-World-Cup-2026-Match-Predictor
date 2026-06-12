"""
Aggregates data from all collectors and resolves team names
across different API naming conventions.
"""
import threading
from datetime import date
from typing import List, Dict, Optional
from collectors.espn_collector import ESPNCollector
from collectors.football_data_collector import FootballDataCollector
from collectors.api_football_collector import APIFootballCollector
from collectors.sports_db_collector import SportsDBCollector
from collectors.news_collector import NewsCollector
from collectors.weather_collector import WeatherCollector
from collectors.sofascore_collector import SofascoreCollector
from collectors.football_standings_collector import FootballStandingsCollector


# Normalise different API team name spellings to a canonical name
TEAM_NAME_MAP = {
    "united states": "USA", "united states of america": "USA",
    "us men's national team": "USA", "usmnt": "USA",
    "u.s.a.": "USA", "u.s.": "USA",
    "england": "England", "three lions": "England",
    "brasil": "Brazil", "brasil nacional": "Brazil",
    "deutschland": "Germany", "mannschaft": "Germany",
    "pays-bas": "Netherlands", "holland": "Netherlands",
    "espana": "Spain",
    "republic of ireland": "Ireland",
    "ivory coast": "Ivory Coast", "cote d'ivoire": "Ivory Coast",
    "drc": "DR Congo", "congo dr": "DR Congo",
    "south korea": "South Korea", "korea republic": "South Korea",
    "north korea": "North Korea", "korea dpr": "North Korea",
    "saudi arabia": "Saudi Arabia", "ksa": "Saudi Arabia",
    "bosnia & herzegovina": "Bosnia-Herzegovina",
    "bosnia and herzegovina": "Bosnia-Herzegovina",
    "czechia": "Czech Republic",
    "trinidad & tobago": "Trinidad and Tobago",
}


def normalise_team(name: str) -> str:
    if not name:
        return name
    lower = name.lower().strip()
    return TEAM_NAME_MAP.get(lower, name.strip())


def _names_overlap(a: str, b: str) -> bool:
    """Return True when two team name strings refer to the same team."""
    a_l = normalise_team(a).lower()
    b_l = normalise_team(b).lower()
    return a_l == b_l or a_l in b_l or b_l in a_l


class DataAggregator:
    def __init__(self):
        self.espn = ESPNCollector()
        self.fd = FootballDataCollector()
        self.apif = APIFootballCollector()
        self.sdb = SportsDBCollector()
        self.news = NewsCollector()
        self.weather = WeatherCollector()
        self.sofa = SofascoreCollector()
        self.standings_api = FootballStandingsCollector()
        self._lock = threading.RLock()

    def get_today_matches(self, target_date: Optional[date] = None) -> List[Dict]:
        """Fetch today's FIFA 2026 matches from all available sources, merged."""
        from datetime import timedelta
        d = target_date or date.today()
        d_next = d + timedelta(days=1)
        results = {}

        def fetch(name, fn, *args):
            try:
                results[name] = fn(*args)
            except Exception:
                results[name] = []

        # Also query Sofascore for tomorrow to catch 01:00 UTC games (evening US time)
        def fetch_sofa_combined():
            try:
                today_f = self.sofa.get_today_wc_fixtures(d)
                next_f  = self.sofa.get_today_wc_fixtures(d_next)
                results["sofa"] = today_f + next_f
            except Exception:
                results["sofa"] = []

        threads = [
            threading.Thread(target=fetch, args=("fd",    self.fd.get_today_fixtures, d)),
            threading.Thread(target=fetch, args=("espn",  self.espn.get_today_fixtures, d)),
            threading.Thread(target=fetch, args=("apif",  self.apif.get_fixtures, d)),
            threading.Thread(target=fetch, args=("sdb",   self.sdb.get_next_wc_fixtures)),
            threading.Thread(target=fetch_sofa_combined),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=15)

        # Merge: prioritise football-data.org > Sofascore > API-Football > ESPN > TheSportsDB
        seen_pairs = set()
        all_matches = []
        for source in ("fd", "sofa", "apif", "espn", "sdb"):
            for match in results.get(source, []):
                home = normalise_team(match.get("home_team", ""))
                away = normalise_team(match.get("away_team", ""))
                if not home or not away:
                    continue
                pair = tuple(sorted([home.lower(), away.lower()]))
                if pair not in seen_pairs:
                    seen_pairs.add(pair)
                    match["home_team"] = home
                    match["away_team"] = away
                    all_matches.append(match)

        # Attach sofascore_id to every fixture (for lineup/odds lookup later)
        sofa_fixtures = results.get("sofa", [])
        for match in all_matches:
            # Already has sofascore_id (came from Sofascore source or previously tagged)
            if match.get("sofascore_id"):
                continue
            for sf in sofa_fixtures:
                sh = sf.get("home_team", "")
                sa = sf.get("away_team", "")
                if _names_overlap(match["home_team"], sh) and _names_overlap(match["away_team"], sa):
                    match["sofascore_id"] = sf["sofascore_id"]
                    match["sofascore_status"] = sf.get("status", "")
                    break

        return all_matches

    def get_match_full_data(
        self,
        home_team: str,
        away_team: str,
        match_id: Optional[str] = None,
        sofascore_id: Optional[int] = None,
    ) -> Dict:
        """Collect all data needed for prediction for a specific match."""
        data = {
            "home_team": home_team,
            "away_team": away_team,
            "lineups": {"home": [], "away": [], "confirmed": False},
            "home_form": [],
            "away_form": [],
            "h2h": [],
            "home_news": {},
            "away_news": {},
            "match_news": {},
            "weather": None,
            "bookmaker_odds": None,
            "data_sources": [],
        }

        def _collect_form_fd():
            if not self.fd.is_configured:
                return
            for code in ["WC", "PL", "CL"]:
                try:
                    standings = self.fd.get_standings(code)
                    if not standings:
                        continue
                    for group in (standings.get("standings") or []):
                        for entry in (group.get("table") or []):
                            team_name = entry.get("team", {}).get("name", "")
                            team_id = entry.get("team", {}).get("id")
                            if team_id and _names_overlap(home_team, team_name):
                                form = self.fd.get_team_form(team_id, limit=10)
                                if form:
                                    data["home_form"] = form
                                    data["data_sources"].append("football-data:home_form")
                            if team_id and _names_overlap(away_team, team_name):
                                form = self.fd.get_team_form(team_id, limit=10)
                                if form:
                                    data["away_form"] = form
                                    data["data_sources"].append("football-data:away_form")
                    if data["home_form"] and data["away_form"]:
                        return
                except Exception:
                    continue

        def _collect_form_sdb():
            if data["home_form"] and data["away_form"]:
                return
            home_sdb = self.sdb.search_team(home_team)
            away_sdb = self.sdb.search_team(away_team)
            if home_sdb and not data["home_form"]:
                form = self.sdb.get_team_recent_results(home_sdb.get("idTeam", ""))
                if form:
                    data["home_form"] = form
                    data["data_sources"].append("thesportsdb:home_form")
            if away_sdb and not data["away_form"]:
                form = self.sdb.get_team_recent_results(away_sdb.get("idTeam", ""))
                if form:
                    data["away_form"] = form
                    data["data_sources"].append("thesportsdb:away_form")

        def _collect_news():
            home_articles = self.news.get_team_news(home_team)
            away_articles = self.news.get_team_news(away_team)
            match_articles = self.news.get_match_news(home_team, away_team)
            data["home_news"] = self.news.analyze_sentiment(home_articles)
            data["home_news"]["injured_players"] = self.news.extract_injured_players(home_articles)
            data["away_news"] = self.news.analyze_sentiment(away_articles)
            data["away_news"]["injured_players"] = self.news.extract_injured_players(away_articles)
            data["match_news"] = self.news.analyze_sentiment(match_articles)
            if home_articles or away_articles:
                data["data_sources"].append("news:sentiment")

        def _collect_lineups_legacy():
            """Old path: API-Football or ESPN lineups (fallback)."""
            if not match_id:
                return
            if self.apif.is_configured:
                try:
                    fixture_id = int(match_id)
                    lineup = self.apif.get_lineups(fixture_id)
                    if lineup and (lineup.get("home") or lineup.get("away")):
                        data["lineups"]["home"] = lineup.get("home", [])
                        data["lineups"]["away"] = lineup.get("away", [])
                        data["data_sources"].append("api-football:lineups")
                        return
                except (ValueError, TypeError):
                    pass
            details = self.espn.get_match_details(str(match_id))
            if details:
                lineups = details.get("lineups", {"home": [], "away": []})
                if lineups.get("home") or lineups.get("away"):
                    data["lineups"]["home"] = lineups.get("home", [])
                    data["lineups"]["away"] = lineups.get("away", [])
                    data["data_sources"].append("espn:lineups")

        def _collect_sofascore():
            """Sofascore: confirmed lineups + bookmaker odds."""
            # Determine event ID
            eid = sofascore_id
            if not eid:
                try:
                    eid = self.sofa.find_event_id(home_team, away_team)
                except Exception:
                    eid = None
            if not eid:
                return

            try:
                sf = self.sofa.get_match_data(eid)
            except Exception:
                return

            if not sf:
                return

            # Lineups (Sofascore is the most reliable source)
            home_starters = sf.get("home_starters", [])
            away_starters = sf.get("away_starters", [])
            confirmed = sf.get("confirmed_lineups", False)

            if home_starters or away_starters:
                # Convert Sofascore player dicts to name-list format for compat
                data["lineups"]["home"] = [
                    {"name": p["name"], "position": p.get("position", "")}
                    for p in home_starters
                ]
                data["lineups"]["away"] = [
                    {"name": p["name"], "position": p.get("position", "")}
                    for p in away_starters
                ]
                data["lineups"]["confirmed"] = confirmed
                data["lineups"]["home_formation"] = sf.get("home_formation", "")
                data["lineups"]["away_formation"] = sf.get("away_formation", "")
                label = "sofascore:lineups_confirmed" if confirmed else "sofascore:lineups_expected"
                data["data_sources"].append(label)

            # Bookmaker odds
            odds = sf.get("odds")
            if odds:
                data["bookmaker_odds"] = odds
                data["data_sources"].append("sofascore:odds")

        # Run all collectors in parallel threads
        threads = [
            threading.Thread(target=_collect_form_fd),
            threading.Thread(target=_collect_news),
            threading.Thread(target=_collect_sofascore),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=25)

        # SportsDB form as fallback (sequential — needs fd result first)
        _collect_form_sdb()

        # Legacy lineups fallback if Sofascore didn't provide them
        if not data["lineups"]["home"] and not data["lineups"]["away"]:
            _collect_lineups_legacy()

        return data

    def get_h2h_history(self, home_team: str, away_team: str, limit: int = 10) -> List[Dict]:
        """Get head-to-head history."""
        cache = self.sdb.cache
        cache_key = f"h2h_{home_team.lower()}_{away_team.lower()}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        all_results = self.sdb.get_last_wc_results(50)
        h2h = [
            r for r in all_results
            if (_names_overlap(home_team, r.get("home_team", "")) and
                _names_overlap(away_team, r.get("away_team", ""))) or
               (_names_overlap(away_team, r.get("home_team", "")) and
                _names_overlap(home_team, r.get("away_team", "")))
        ][:limit]

        cache.set(cache_key, h2h, ttl=86400)
        return h2h

    def refresh_lineups(self, match_id: str, sofascore_id: Optional[int] = None) -> Optional[Dict]:
        """Force-refresh lineups bypassing cache."""
        if sofascore_id:
            self.sofa.cache.delete(f"sofa_lineup_{sofascore_id}")
        self.espn.cache.delete(f"espn_match_{match_id}")
        try:
            self.apif.cache.delete(f"apif_lineup_{int(match_id)}")
        except (ValueError, TypeError):
            pass
        return self.espn.get_match_details(match_id)

    def get_wc_standings(self) -> List[Dict]:
        """Get current FIFA World Cup group standings."""
        try:
            return self.standings_api.get_wc_standings()
        except Exception:
            return []
