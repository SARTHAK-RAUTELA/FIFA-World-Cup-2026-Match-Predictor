"""
Headless prediction script for Germany vs Curaçao — FIFA World Cup 2026
Injects confirmed lineups (4/7 confirmed) and runs the full prediction engine.
"""
import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Monkey-patch DataAggregator to inject confirmed lineups before engine boots
CONFIRMED_LINEUPS = {
    "home": [
        {"name": "Manuel Neuer",        "position": "GK", "number": 1},
        {"name": "Joshua Kimmich",       "position": "RB", "number": 6},
        {"name": "Jonathan Tah",         "position": "CB", "number": 4},
        {"name": "Nico Schlotterbeck",   "position": "CB", "number": 15},
        {"name": "Nathaniel Brown",      "position": "LB", "number": 18},
        {"name": "Aleksandar Pavlovic",  "position": "DM", "number": 5},
        {"name": "Felix Nmecha",         "position": "DM", "number": 23},
        {"name": "Leroy Sane",           "position": "RW", "number": 19},
        {"name": "Jamal Musiala",        "position": "AM", "number": 10},
        {"name": "Florian Wirtz",        "position": "LW", "number": 17},
        {"name": "Kai Havertz",          "position": "ST", "number": 7},
    ],
    "away": [
        {"name": "Eloy Room",            "position": "GK", "number": 1},
        {"name": "Deveron Fonville",     "position": "RB", "number": 24},
        {"name": "Riechedly Bazoer",     "position": "CB", "number": 23},
        {"name": "Armando Obispo",       "position": "CB", "number": 18},
        {"name": "Sherel Floranus",      "position": "LB", "number": 5},
        {"name": "Juninho Bacuna",       "position": "DM", "number": 7},
        {"name": "Livano Comenencia",    "position": "DM", "number": 8},
        {"name": "Tahith Chong",         "position": "RW", "number": 21},
        {"name": "Leandro Bacuna",       "position": "AM", "number": 10},
        {"name": "Sontje Hansen",        "position": "LW", "number": 12},
        {"name": "Juergen Locadia",      "position": "ST", "number": 9},
    ],
    "home_formation": "4-2-3-1",
    "away_formation": "4-2-3-1",
    "confirmed": True,
}

BOOKMAKER_ODDS = {
    "1x2": {"home": 1.04, "draw": 17.00, "away": 29.00},
    "btts": {"yes": 2.20, "no": 1.65},
    "asian_handicap": {"line": -3.5, "home": 1.90, "away": 1.95},
    "totals": {"line": 4.5, "over": 1.95, "under": 1.90},
}

from collectors.data_aggregator import DataAggregator
_orig_get_match_full_data = DataAggregator.get_match_full_data

def _patched_get_match_full_data(self, home_team, away_team, match_id=None, sofascore_id=None):
    data = _orig_get_match_full_data(self, home_team, away_team, match_id, sofascore_id=sofascore_id)
    # Inject confirmed lineups regardless of what API returned
    data["lineups"] = CONFIRMED_LINEUPS
    return data

DataAggregator.get_match_full_data = _patched_get_match_full_data

from prediction.engine import PredictionEngine
from display.formatter import render_prediction_panel
from rich.console import Console
from rich.rule import Rule

console = Console()

console.print()
console.print(Rule("[bold cyan]FIFA 2026  —  MATCH PREDICTION[/bold cyan]", style="cyan"))
console.print("[dim]Confirmed lineups injected (4/7 lineup status)[/dim]")
console.print("[dim]Date: 14 June 2026 | NRG Stadium, Houston[/dim]")
console.print()

with console.status("[cyan]Loading prediction engine...[/cyan]", spinner="dots"):
    engine = PredictionEngine()

console.print(f"[dim]ELO database: {len(engine.elo_ratings)} teams loaded[/dim]")
console.print()

with console.status("[cyan]Running models for Germany vs Curaçao...[/cyan]", spinner="dots"):
    pred = engine.predict_match(
        home_team="Germany",
        away_team="Curaçao",
        venue_city="Houston",
        match_date="2026-06-14",
        bookmaker_odds=BOOKMAKER_ODDS,
    )

render_prediction_panel(pred)
