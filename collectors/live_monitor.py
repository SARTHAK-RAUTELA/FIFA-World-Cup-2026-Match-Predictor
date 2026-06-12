"""
Live match monitor.
Polls APIs for lineup changes and re-runs predictions when changes detected.
"""
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Callable
from config import LINEUP_REFRESH_INTERVAL, PRE_MATCH_REFRESH_INTERVAL


class LiveMonitor:
    def __init__(self, engine, on_lineup_change: Optional[Callable] = None):
        self.engine = engine
        self.on_lineup_change = on_lineup_change
        self._active_matches: Dict[str, Dict] = {}
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None

    def add_match(self, match_id: str, home_team: str, away_team: str,
                  kickoff_time: Optional[datetime] = None,
                  latest_prediction: Optional[Dict] = None) -> None:
        with self._lock:
            self._active_matches[match_id] = {
                "match_id": match_id,
                "home_team": home_team,
                "away_team": away_team,
                "kickoff_time": kickoff_time,
                "latest_prediction": latest_prediction,
                "last_checked": 0,
                "lineup_confirmed": False,
            }

    def remove_match(self, match_id: str) -> None:
        with self._lock:
            self._active_matches.pop(match_id, None)

    def start(self) -> None:
        """Start background monitoring thread."""
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop, daemon=True
        )
        self._monitor_thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)

    def _monitor_loop(self) -> None:
        while not self._stop_event.is_set():
            now = time.time()
            with self._lock:
                matches = list(self._active_matches.items())

            for match_id, match_data in matches:
                interval = self._get_refresh_interval(match_data)
                if now - match_data["last_checked"] >= interval:
                    self._check_match(match_id, match_data)

            time.sleep(10)  # Check every 10 seconds

    def _get_refresh_interval(self, match_data: Dict) -> int:
        """Determine how often to refresh based on time to kickoff."""
        kickoff = match_data.get("kickoff_time")
        if not kickoff:
            return LINEUP_REFRESH_INTERVAL

        now = datetime.utcnow()
        if isinstance(kickoff, str):
            try:
                kickoff = datetime.fromisoformat(kickoff.replace("Z", "+00:00"))
            except ValueError:
                return LINEUP_REFRESH_INTERVAL

        mins_to_kickoff = (kickoff.replace(tzinfo=None) - now).total_seconds() / 60

        if mins_to_kickoff < 0:
            return 300  # Match started/finished
        elif mins_to_kickoff < 30:
            return 30   # Poll every 30 seconds in final 30 min
        elif mins_to_kickoff < 60:
            return 60   # Every minute in final hour
        elif mins_to_kickoff < 120:
            return PRE_MATCH_REFRESH_INTERVAL
        else:
            return LINEUP_REFRESH_INTERVAL

    def _check_match(self, match_id: str, match_data: Dict) -> None:
        try:
            previous = match_data.get("latest_prediction")
            updated = self.engine.monitor_lineup_changes(
                match_id=match_id,
                home_team=match_data["home_team"],
                away_team=match_data["away_team"],
                previous_prediction=previous or {},
            )

            with self._lock:
                if match_id in self._active_matches:
                    self._active_matches[match_id]["last_checked"] = time.time()

            if updated:
                with self._lock:
                    if match_id in self._active_matches:
                        self._active_matches[match_id]["latest_prediction"] = updated

                # Detect what changed
                changes = self._detect_changes(previous, updated)
                if changes and self.on_lineup_change:
                    self.on_lineup_change(
                        match_data["home_team"],
                        match_data["away_team"],
                        changes,
                        updated,
                    )

        except Exception:
            pass

    def _detect_changes(self, old_pred: Optional[Dict], new_pred: Dict) -> List[str]:
        """Return list of human-readable lineup change descriptions."""
        if not old_pred:
            return ["Initial lineup confirmed"]

        changes = []
        old_data = old_pred.get("data", {})
        new_data = new_pred.get("data", {})

        def _names(lineup): return {p.get("name", "") for p in lineup if p.get("name")}

        old_home = _names(old_data.get("home_lineup", []))
        new_home = _names(new_data.get("home_lineup", []))
        old_away = _names(old_data.get("away_lineup", []))
        new_away = _names(new_data.get("away_lineup", []))

        home_team = new_pred.get("home_team", "Home")
        away_team = new_pred.get("away_team", "Away")

        for removed in (old_home - new_home):
            changes.append(f"{home_team}: {removed} removed from lineup")
        for added in (new_home - old_home):
            changes.append(f"{home_team}: {added} added to lineup")
        for removed in (old_away - new_away):
            changes.append(f"{away_team}: {removed} removed from lineup")
        for added in (new_away - old_away):
            changes.append(f"{away_team}: {added} added to lineup")

        # Confidence change
        old_conf = old_pred.get("confidence", {}).get("total", 0)
        new_conf = new_pred.get("confidence", {}).get("total", 0)
        if abs(old_conf - new_conf) > 2:
            direction = "up" if new_conf > old_conf else "down"
            changes.append(f"Confidence changed {direction}: {old_conf:.1f}% → {new_conf:.1f}%")

        return changes

    def get_status(self) -> Dict:
        with self._lock:
            return {
                "active_matches": len(self._active_matches),
                "matches": [
                    {
                        "id": mid,
                        "teams": f"{m['home_team']} vs {m['away_team']}",
                        "last_checked": datetime.fromtimestamp(m["last_checked"]).strftime("%H:%M:%S")
                        if m["last_checked"] > 0 else "never",
                    }
                    for mid, m in self._active_matches.items()
                ],
            }
