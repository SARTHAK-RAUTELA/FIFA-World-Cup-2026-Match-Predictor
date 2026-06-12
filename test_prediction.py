"""
End-to-end test: Predict USA vs Paraguay with bookmaker odds from the example.
"""
import sys
import os
os.environ["PYTHONIOENCODING"] = "utf-8"

from prediction.engine import PredictionEngine
from display.formatter import render_prediction_panel, print_header
from rich.console import Console

console = Console(force_terminal=True)

# Bookmaker odds from the user's example
BOOKIE_ODDS = {
    "1x2": {"home": 2.08, "draw": 3.15, "away": 3.80},
    "btts": {"yes": 2.13, "no": 1.69},
}

if __name__ == "__main__":
    print_header()
    console.print("[cyan]Testing: USA vs Paraguay (FIFA 2026)[/cyan]\n")
    console.print("[dim]Note: No API keys set - using ELO/mathematical baseline[/dim]\n")

    engine = PredictionEngine()

    with console.status("[cyan]Running prediction...[/cyan]", spinner="dots"):
        pred = engine.predict_match(
            home_team="USA",
            away_team="Paraguay",
            venue_city="Dallas",
            bookmaker_odds=BOOKIE_ODDS,
        )

    conf = pred["confidence"]
    console.print(f"[bold]Confidence: {conf['total']:.1f}% (threshold: {conf['threshold']}%)[/bold]")
    console.print(f"Predicted outcome: [bold green]{conf['predicted_outcome']}[/bold green] @ {conf['predicted_outcome_prob']}%\n")

    render_prediction_panel(pred)
