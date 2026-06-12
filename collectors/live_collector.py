"""
Live match data collector — Sofascore via SportAPI7 (RapidAPI).
Provides: live score, incidents (goals/cards/subs), statistics, commentary.
Short-lived cache (30s) so predictions stay current during live matches.

Uses the same api/v1/event/{id} path pattern as SofascoreCollector.
"""
import time
import requests
from typing import Dict, List, Optional
from config import API_FOOTBALL_KEY

_ICON = {
    "goal":           "⚽",
    "goalpenalty":    "🎯",
    "penaltyscored":  "🎯",
    "missedpenalty":  "❌",
    "yellowcard":     "🟡",
    "yellowredcard":  "🟠",
    "redcard":        "🔴",
    "substitution":   "🔄",
    "vardecision":    "📺",
    "owngoal":        "🏳",
}

# Key statistics to display in the UI (in order)
_STAT_ORDER = [
    "Ball possession",
    "Total shots",
    "Shots on target",
    "Big chances",
    "Corner kicks",
    "Fouls",
    "Offsides",
    "Yellow cards",
    "Red cards",
    "Passes",
    "Accurate passes",
]


class LiveMatchCollector:
    BASE = "https://sportapi7.p.rapidapi.com"
    LIVE_TTL = 30  # seconds

    def __init__(self):
        self._headers = {
            "x-rapidapi-key": API_FOOTBALL_KEY or "",
            "x-rapidapi-host": "sportapi7.p.rapidapi.com",
        }
        self._cache: Dict[str, Dict] = {}
        self._ts:    Dict[str, float] = {}

    # ── Internal helpers ──────────────────────────────────────────────

    def _get(self, path: str, ttl: int = 30) -> Optional[Dict]:
        now = time.time()
        if path in self._cache and now - self._ts.get(path, 0) < ttl:
            return self._cache[path]
        try:
            r = requests.get(
                f"{self.BASE}/{path}",
                headers=self._headers,
                timeout=10,
            )
            if r.status_code == 200:
                data = r.json()
                self._cache[path] = data
                self._ts[path] = now
                return data
        except Exception:
            pass
        return self._cache.get(path)  # return stale on failure

    def clear_cache(self, event_id: int = None):
        if event_id:
            keys = [k for k in self._cache if str(event_id) in k]
            for k in keys:
                self._cache.pop(k, None)
                self._ts.pop(k, None)
        else:
            self._cache.clear()
            self._ts.clear()

    # ── Public API ────────────────────────────────────────────────────

    def get_live_data(self, event_id: int) -> Dict:
        """
        Fetch all live match data in one call.
        Returns: score, status, minute, incidents, statistics.
        """
        result = {
            "event_id": event_id,
            "home_team": "",
            "away_team": "",
            "home_score": 0,
            "away_score": 0,
            "ht_home_score": None,
            "ht_away_score": None,
            "minute": 0,
            "status": "Unknown",
            "status_code": "",
            "is_live": False,
            "is_halftime": False,
            "is_finished": False,
            "incidents": [],
            "statistics": {},
            "error": None,
        }

        if not API_FOOTBALL_KEY:
            result["error"] = "RapidAPI key not configured"
            return result

        # ── Match details + score ─────────────────────────────────────
        raw = self._get(f"api/v1/event/{event_id}")
        if raw and raw.get("event"):
            ev = raw["event"]
            result["home_team"] = ev.get("homeTeam", {}).get("name", "")
            result["away_team"] = ev.get("awayTeam", {}).get("name", "")

            hs = ev.get("homeScore", {}) or {}
            as_ = ev.get("awayScore", {}) or {}
            result["home_score"] = hs.get("current", 0) or 0
            result["away_score"] = as_.get("current", 0) or 0
            result["ht_home_score"] = hs.get("period1")
            result["ht_away_score"] = as_.get("period1")

            st = ev.get("status", {}) or {}
            st_type = (st.get("type") or "").lower()
            result["status"] = st.get("description", "Unknown")
            result["status_code"] = st_type
            result["minute"] = (st.get("liveTime", {}) or {}).get("minute", 0) or 0
            result["is_live"]     = st_type in ("inprogress",)
            result["is_halftime"] = st_type in ("halftime", "pause")
            result["is_finished"] = st_type in ("finished", "ended", "postponed",
                                                  "canceled", "abandoned")
        elif raw and raw.get("error"):
            result["error"] = str(raw["error"])

        # ── Incidents ─────────────────────────────────────────────────
        inc_raw = self._get(f"api/v1/event/{event_id}/incidents", ttl=self.LIVE_TTL)
        if inc_raw and inc_raw.get("incidents"):
            result["incidents"] = self._parse_incidents(
                inc_raw["incidents"],
                result["home_team"],
                result["away_team"],
            )

        # ── Statistics ────────────────────────────────────────────────
        stat_raw = self._get(f"api/v1/event/{event_id}/statistics", ttl=self.LIVE_TTL)
        if stat_raw and stat_raw.get("statistics"):
            result["statistics"] = self._parse_statistics(stat_raw["statistics"])

        return result

    def get_commentary(self, event_id: int) -> List[Dict]:
        """
        Fetch text commentary if available.
        Falls back to empty list if endpoint doesn't exist.
        """
        raw = self._get(f"api/v1/event/{event_id}/comments", ttl=60)
        if not raw:
            return []
        lines = raw.get("commentary") or raw.get("comments") or []
        result = []
        for line in lines:
            text = line.get("text") or line.get("comment") or ""
            minute = line.get("minute") or line.get("time") or ""
            if text:
                result.append({
                    "minute": str(minute),
                    "text": text,
                    "important": bool(line.get("important") or line.get("isImportant")),
                })
        # Most recent first
        return list(reversed(result))

    # ── Parsers ───────────────────────────────────────────────────────

    def _parse_incidents(self, raw: List[Dict], home_name: str, away_name: str) -> List[Dict]:
        parsed = []
        for inc in raw:
            inc_type = (inc.get("incidentType") or "").lower().replace("_", "")
            if inc_type in ("periodstart", "periodend", "inningstart", "period"):
                continue

            minute     = int(inc.get("minute") or 0)
            added_time = int(inc.get("addedTime") or 0)
            is_home    = bool(inc.get("isHome", True))
            team_name  = home_name if is_home else away_name

            icon = _ICON.get(inc_type, "•")

            # Player names
            player     = (inc.get("player")    or {}).get("name", "")
            player_in  = (inc.get("playerIn")  or {}).get("name", "")
            player_out = (inc.get("playerOut") or {}).get("name", "")

            # Score snapshot for goals
            h_sc = inc.get("homeScore", "")
            a_sc = inc.get("awayScore", "")
            score_snap = (f" → {h_sc}–{a_sc}") if inc_type in ("goal", "goalpenalty", "penaltyscored", "owngoal") and h_sc != "" else ""

            # Build description
            if inc_type == "substitution":
                desc = f"{player_in} on / {player_out} off"
            elif inc_type in ("goal", "goalpenalty", "penaltyscored"):
                assist = (inc.get("assist1", {}) or {}).get("name", "")
                desc = player + (f"  (assist: {assist})" if assist else "") + score_snap
            elif inc_type == "owngoal":
                desc = f"{player} (OG){score_snap}"
            elif inc_type == "vardecision":
                desc = inc.get("varDecision", "") or player
            else:
                desc = player

            minute_str = f"{minute}'" if not added_time else f"{minute}+{added_time}'"

            parsed.append({
                "minute":     minute,
                "minute_str": minute_str,
                "icon":       icon,
                "type":       inc_type,
                "is_home":    is_home,
                "team":       team_name,
                "desc":       desc,
                "is_goal":    inc_type in ("goal", "goalpenalty", "penaltyscored"),
                "is_red":     inc_type in ("redcard", "yellowredcard"),
            })

        parsed.sort(key=lambda x: x["minute"])
        return parsed

    def _parse_statistics(self, raw: List[Dict]) -> Dict:
        """Return flat {stat_name: {home, away}} for the full match."""
        stats = {}
        for period_block in raw:
            if (period_block.get("period") or "").upper() != "ALL":
                continue
            for group in period_block.get("groups", []):
                for item in group.get("statisticsItems", []):
                    name = item.get("name", "").strip()
                    if name:
                        stats[name] = {
                            "home": item.get("home", "0"),
                            "away": item.get("away", "0"),
                        }
        return stats
