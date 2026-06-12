"""
Sofascore/SportAPI collector via RapidAPI.
Endpoint: sportapi7.p.rapidapi.com
Provides: today's fixtures, confirmed lineups, bookmaker odds (16 markets),
          team statistics, live incidents.
Uses the same RapidAPI key as the API-Football collector.
"""
from datetime import date
from typing import Optional, List, Dict
from collectors.base_collector import BaseCollector
from config import SOFASCORE_BASE, API_FOOTBALL_KEY, CACHE_TTL


# Map Sofascore team names → canonical names used throughout this tool
SOFA_TEAM_MAP = {
    "united states": "USA",
    "bosnia & herzegovina": "Bosnia-Herzegovina",
    "bosnia and herzegovina": "Bosnia-Herzegovina",
    "czechia": "Czech Republic",
    "republic of ireland": "Ireland",
    "ivory coast": "Ivory Coast",
    "cote d'ivoire": "Ivory Coast",
    "dr congo": "DR Congo",
    "congo dr": "DR Congo",
    "drc": "DR Congo",
    "korea republic": "South Korea",
    "republic of korea": "South Korea",
    "north korea": "North Korea",
    "korea dpr": "North Korea",
    "saudi arabia": "Saudi Arabia",
    "trinidad & tobago": "Trinidad and Tobago",
}


def _sofa_team_name(raw: str) -> str:
    if not raw:
        return raw
    return SOFA_TEAM_MAP.get(raw.lower().strip(), raw.strip())


def _frac_to_decimal(frac: str) -> float:
    """Convert fractional odds string '7/2' to decimal 4.5."""
    try:
        if "/" in frac:
            num, den = frac.split("/")
            return round(int(num) / int(den) + 1, 3)
        return round(float(frac), 3)
    except (ValueError, ZeroDivisionError):
        return 0.0


class SofascoreCollector(BaseCollector):
    def __init__(self):
        headers = {
            "X-RapidAPI-Key": API_FOOTBALL_KEY,
            "X-RapidAPI-Host": "sportapi7.p.rapidapi.com",
        }
        super().__init__(base_url=SOFASCORE_BASE, headers=headers, rate_limit_delay=0.5)

    @property
    def is_configured(self) -> bool:
        return bool(API_FOOTBALL_KEY)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_today_wc_fixtures(self, target_date: Optional[date] = None) -> List[Dict]:
        """Return today's FIFA World Cup match stubs with event IDs."""
        if not self.is_configured:
            return []
        d = target_date or date.today()
        date_str = d.strftime("%Y-%m-%d")
        cache_key = f"sofa_wc_fixtures_{date_str}"
        data = self.cached_get(
            cache_key,
            f"api/v1/sport/football/scheduled-events/{date_str}",
            ttl=CACHE_TTL["fixtures"],
        )
        if not data:
            return []
        events = data.get("events", [])
        return [self._parse_fixture_stub(e) for e in events if self._is_world_cup(e)]

    def get_match_data(self, event_id: int) -> Dict:
        """
        Fetch lineups + odds for a Sofascore event.
        Returns combined dict:
          {
            event_id, confirmed_lineups, home_starters, away_starters,
            home_formation, away_formation, home_players, away_players,
            odds: {1x2: {...}, btts: {...}, dnb: {...}, double_chance: {...}, ht_1x2: {...}}
          }
        """
        if not self.is_configured:
            return {}
        result = {"event_id": event_id}
        lineups = self._get_lineups(event_id)
        result.update(lineups)
        odds = self._get_odds(event_id)
        if odds:
            result["odds"] = odds
        return result

    def find_event_id(self, home_team: str, away_team: str,
                      target_date: Optional[date] = None) -> Optional[int]:
        """Look up the Sofascore event ID for a match by team names."""
        fixtures = self.get_today_wc_fixtures(target_date)
        home_l = home_team.lower()
        away_l = away_team.lower()
        for f in fixtures:
            fh = f.get("home_team", "").lower()
            fa = f.get("away_team", "").lower()
            if (home_l in fh or fh in home_l) and (away_l in fa or fa in away_l):
                return f["event_id"]
        # Reverse order (team labelling can differ)
        for f in fixtures:
            fh = f.get("home_team", "").lower()
            fa = f.get("away_team", "").lower()
            if (away_l in fh or fh in away_l) and (home_l in fa or fa in home_l):
                return f["event_id"]
        return None

    def get_statistics(self, event_id: int) -> Dict:
        """Fetch in-match or post-match team statistics (shots, possession, xG)."""
        if not self.is_configured:
            return {}
        cache_key = f"sofa_stats_{event_id}"
        data = self.cached_get(
            cache_key,
            f"api/v1/event/{event_id}/statistics",
            ttl=60,  # 1 min for live stats
        )
        if not data:
            return {}
        return self._parse_statistics(data)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _is_world_cup(self, event: dict) -> bool:
        tour = event.get("tournament", {})
        unique = tour.get("uniqueTournament", {})
        name_lc = (unique.get("name", "") or tour.get("name", "")).lower()
        return "world cup" in name_lc or "fifa world" in name_lc

    def _parse_fixture_stub(self, event: dict) -> Dict:
        tour = event.get("tournament", {})
        unique = tour.get("uniqueTournament", {})
        eid = event.get("id")
        return {
            "event_id": eid,
            "sofascore_id": eid,   # also set sofascore_id for consistent access
            "home_team": _sofa_team_name(event.get("homeTeam", {}).get("name", "")),
            "away_team": _sofa_team_name(event.get("awayTeam", {}).get("name", "")),
            "status": event.get("status", {}).get("description", "Unknown"),
            "tournament": unique.get("name", tour.get("name", "")),
            "source": "sofascore",
        }

    def _get_lineups(self, event_id: int) -> Dict:
        cache_key = f"sofa_lineup_{event_id}"
        data = self.cached_get(
            cache_key,
            f"api/v1/event/{event_id}/lineups",
            ttl=CACHE_TTL["lineups"],
        )
        if not data:
            return {
                "confirmed_lineups": False,
                "home_starters": [],
                "away_starters": [],
                "home_formation": "",
                "away_formation": "",
                "home_players": [],
                "away_players": [],
            }

        confirmed = data.get("confirmed", False)
        home_data = data.get("home", {})
        away_data = data.get("away", {})

        home_players_raw = home_data.get("players", [])
        away_players_raw = away_data.get("players", [])

        def parse_players(raw_list):
            starters, subs = [], []
            for p in raw_list:
                pinfo = p.get("player", {})
                entry = {
                    "name": pinfo.get("name", pinfo.get("shortName", "")),
                    "position": p.get("position", ""),
                    "shirt_number": p.get("jerseyNumber", 0),
                    "substitute": p.get("substitute", True),
                    "rating": p.get("statistics", {}).get("rating", 0) if p.get("statistics") else 0,
                }
                if not entry["substitute"]:
                    starters.append(entry)
                else:
                    subs.append(entry)
            return starters, subs

        home_starters, home_subs = parse_players(home_players_raw)
        away_starters, away_subs = parse_players(away_players_raw)

        return {
            "confirmed_lineups": confirmed,
            "home_starters": home_starters,
            "away_starters": away_starters,
            "home_formation": home_data.get("formation", ""),
            "away_formation": away_data.get("formation", ""),
            "home_players": home_starters + home_subs,
            "away_players": away_starters + away_subs,
        }

    def _get_odds(self, event_id: int) -> Dict:
        cache_key = f"sofa_odds_{event_id}"
        data = self.cached_get(
            cache_key,
            f"api/v1/event/{event_id}/odds/1/all",
            ttl=CACHE_TTL["fixtures"],
        )
        if not data:
            return {}
        markets = data.get("markets", [])
        return self._parse_odds_markets(markets)

    def _parse_odds_markets(self, markets: list) -> Dict:
        """Convert all Sofascore odds markets to a standardized dict."""
        result = {}

        for market in markets:
            name = (market.get("marketName", "") or "").lower()
            choices = market.get("choices", [])
            if not choices:
                continue

            if name == "full time" or "1x2" in name:
                parsed = {}
                for c in choices:
                    cname = c.get("name", "")
                    odds = _frac_to_decimal(c.get("fractionalValue", ""))
                    if odds <= 0:
                        continue
                    if cname == "1":
                        parsed["home"] = odds
                    elif cname == "X":
                        parsed["draw"] = odds
                    elif cname == "2":
                        parsed["away"] = odds
                if parsed:
                    result["1x2"] = parsed

            elif "double chance" in name:
                parsed = {}
                for c in choices:
                    cname = c.get("name", "").upper()
                    odds = _frac_to_decimal(c.get("fractionalValue", ""))
                    if odds <= 0:
                        continue
                    if cname == "1X":
                        parsed["home_draw"] = odds
                    elif cname == "X2":
                        parsed["draw_away"] = odds
                    elif cname == "12":
                        parsed["home_away"] = odds
                if parsed:
                    result["double_chance"] = parsed

            elif "both teams" in name or name == "btts":
                parsed = {}
                for c in choices:
                    cname = c.get("name", "").lower()
                    odds = _frac_to_decimal(c.get("fractionalValue", ""))
                    if odds <= 0:
                        continue
                    if "yes" in cname:
                        parsed["yes"] = odds
                    elif "no" in cname:
                        parsed["no"] = odds
                if parsed:
                    result["btts"] = parsed

            elif "draw no bet" in name:
                parsed = {}
                for c in choices:
                    cname = c.get("name", "")
                    odds = _frac_to_decimal(c.get("fractionalValue", ""))
                    if odds <= 0:
                        continue
                    if cname == "1":
                        parsed["home"] = odds
                    elif cname == "2":
                        parsed["away"] = odds
                if parsed:
                    result["dnb"] = parsed

            elif "1st half" in name or "halftime" in name or "half time" in name:
                parsed = {}
                for c in choices:
                    cname = c.get("name", "")
                    odds = _frac_to_decimal(c.get("fractionalValue", ""))
                    if odds <= 0:
                        continue
                    if cname == "1":
                        parsed["home"] = odds
                    elif cname == "X":
                        parsed["draw"] = odds
                    elif cname == "2":
                        parsed["away"] = odds
                if parsed:
                    result["ht_1x2"] = parsed

            elif "over/under" in name or "total goals" in name:
                # Choices look like "Over (2.5)" / "Under (2.5)"
                for c in choices:
                    cname = (c.get("name", "") or "").lower()
                    odds = _frac_to_decimal(c.get("fractionalValue", ""))
                    if odds <= 0:
                        continue
                    if "over" in cname:
                        result.setdefault("over_under_over", {})[cname] = odds
                    elif "under" in cname:
                        result.setdefault("over_under_under", {})[cname] = odds

            elif "asian handicap" in name:
                result.setdefault("asian_handicap_raw", [])
                for c in choices:
                    cname = c.get("name", "")
                    odds = _frac_to_decimal(c.get("fractionalValue", ""))
                    if odds > 0:
                        result["asian_handicap_raw"].append({"name": cname, "odds": odds})

        return result

    def _parse_statistics(self, data: dict) -> Dict:
        """Extract key stats from Sofascore statistics response."""
        stats = {}
        groups = data.get("statistics", [])
        for group in groups:
            for item in group.get("statisticsItems", []):
                key = item.get("key", "")
                home_val = item.get("homeValue", item.get("home", 0))
                away_val = item.get("awayValue", item.get("away", 0))
                if key:
                    stats[key] = {"home": home_val, "away": away_val}
        return stats
