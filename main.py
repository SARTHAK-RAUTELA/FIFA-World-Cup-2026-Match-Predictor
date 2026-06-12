"""
FIFA 2026 Match Prediction Tool
================================
Usage:
  python main.py                          # Predict all today's matches
  python main.py --date 2026-06-15        # Predict matches on specific date
  python main.py --match "USA" "Paraguay" # Predict specific match
  python main.py --odds                   # Input bookmaker odds for value bet analysis
  python main.py --watch                  # Continuous monitoring with live lineup updates
  python main.py --threshold 80           # Lower confidence threshold (default: 93)
"""
import sys
import time
import threading
import argparse
from datetime import date, datetime
from typing import Optional, Dict, List
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text
from rich.panel import Panel
from rich import print as rprint

from prediction.engine import PredictionEngine
from collectors.live_monitor import LiveMonitor
from display.formatter import (
    print_header, print_no_matches, render_prediction_panel,
    render_match_list, render_lineup_update_alert, print_collection_status
)
from config import MIN_CONFIDENCE_THRESHOLD

console = Console()


def parse_bookmaker_odds() -> Dict:
    """Interactive prompt for entering bookmaker odds."""
    console.print("\n[cyan]Enter bookmaker odds (press Enter to skip):[/cyan]")
    odds = {}

    try:
        console.print("[dim]1x2 Home odds (e.g. 2.08):[/dim] ", end="")
        home_odds = input().strip()
        console.print("[dim]1x2 Draw odds (e.g. 3.15):[/dim] ", end="")
        draw_odds = input().strip()
        console.print("[dim]1x2 Away odds (e.g. 3.80):[/dim] ", end="")
        away_odds = input().strip()

        if home_odds or draw_odds or away_odds:
            odds["1x2"] = {}
            if home_odds:
                odds["1x2"]["home"] = float(home_odds)
            if draw_odds:
                odds["1x2"]["draw"] = float(draw_odds)
            if away_odds:
                odds["1x2"]["away"] = float(away_odds)

        console.print("[dim]BTTS Yes odds (e.g. 2.13):[/dim] ", end="")
        btts_yes = input().strip()
        console.print("[dim]BTTS No odds (e.g. 1.69):[/dim] ", end="")
        btts_no = input().strip()

        if btts_yes or btts_no:
            odds["btts"] = {}
            if btts_yes:
                odds["btts"]["yes"] = float(btts_yes)
            if btts_no:
                odds["btts"]["no"] = float(btts_no)

    except (ValueError, KeyboardInterrupt):
        pass

    return odds


def run_single_match(engine: PredictionEngine, home: str, away: str,
                     odds: Optional[Dict] = None, threshold: float = MIN_CONFIDENCE_THRESHOLD) -> None:
    """Predict and display a single match."""
    with console.status(f"[cyan]Collecting data for {home} vs {away}...[/cyan]", spinner="dots"):
        pred = engine.predict_match(
            home_team=home,
            away_team=away,
            bookmaker_odds=odds,
        )

    confidence = pred.get("confidence", {}).get("total", 0)

    if confidence < threshold:
        console.print(Panel(
            f"[yellow]Confidence {confidence:.1f}% is below threshold {threshold}%.\n"
            f"Predicted outcome: {pred['confidence']['predicted_outcome']} "
            f"({pred['confidence']['predicted_outcome_prob']}%)\n\n"
            f"[dim]Run with --threshold {int(confidence)-5} to see full prediction.[/dim][/yellow]",
            title=f"⚠ LOW CONFIDENCE: {home} vs {away}",
            border_style="yellow",
        ))
    else:
        render_prediction_panel(pred)


def run_today(engine: PredictionEngine, target_date: Optional[date] = None,
              odds_map: Optional[Dict] = None, threshold: float = MIN_CONFIDENCE_THRESHOLD) -> List[Dict]:
    """Predict all today's FIFA 2026 matches."""
    print_header()

    with console.status("[cyan]Fetching today's FIFA 2026 fixtures...[/cyan]", spinner="dots"):
        fixtures = engine.aggregator.get_today_matches(target_date)

    if not fixtures:
        print_no_matches()
        return []

    console.print(f"[green]Found {len(fixtures)} match(es) today[/green]\n")
    render_match_list(fixtures)

    predictions = []
    for i, fixture in enumerate(fixtures, 1):
        home = fixture.get("home_team", "")
        away = fixture.get("away_team", "")
        if not home or not away:
            continue

        console.print(f"\n[bold cyan]Predicting match {i}/{len(fixtures)}: {home} vs {away}[/bold cyan]")

        with console.status(f"[cyan]  Collecting data...[/cyan]", spinner="dots"):
            try:
                pred = engine.predict_match(
                    home_team=home,
                    away_team=away,
                    match_id=str(fixture.get("id", "")),
                    venue_city=fixture.get("city", "Dallas"),
                    match_date=fixture.get("date", "")[:10] if fixture.get("date") else None,
                    bookmaker_odds=odds_map.get(f"{home.lower()}_{away.lower()}") if odds_map else None,
                )
                pred["fixture"] = fixture
                predictions.append(pred)
            except Exception as e:
                console.print(f"  [red]Error: {e}[/red]")
                continue

        confidence = pred.get("confidence", {}).get("total", 0)
        if confidence < threshold:
            console.print(
                f"  [yellow]⚠ Confidence {confidence:.1f}% below threshold {threshold}% "
                f"— showing summary only[/yellow]"
            )
            console.print(
                f"  Predicted: [bold]{pred['confidence']['predicted_outcome']}[/bold] "
                f"({pred['confidence']['predicted_outcome_prob']}%)"
            )
        else:
            render_prediction_panel(pred)

    return predictions


def watch_mode(engine: PredictionEngine, predictions: List[Dict],
               threshold: float = MIN_CONFIDENCE_THRESHOLD) -> None:
    """Continuous monitoring for lineup changes."""
    if not predictions:
        console.print("[yellow]No predictions to monitor.[/yellow]")
        return

    def on_change(home, away, changes, updated_pred):
        render_lineup_update_alert(home, away, changes)
        conf = updated_pred.get("confidence", {}).get("total", 0)
        if conf >= threshold:
            console.print(f"\n[cyan]Updated prediction after lineup change:[/cyan]")
            render_prediction_panel(updated_pred)
        else:
            console.print(
                f"[yellow]Updated confidence: {conf:.1f}% (below threshold)[/yellow]"
            )

    monitor = LiveMonitor(engine, on_lineup_change=on_change)

    for pred in predictions:
        if pred.get("match_id") and not pred.get("error"):
            fixture = pred.get("fixture", {})
            kickoff = fixture.get("date")
            monitor.add_match(
                match_id=str(pred["match_id"]),
                home_team=pred["home_team"],
                away_team=pred["away_team"],
                kickoff_time=kickoff,
                latest_prediction=pred,
            )

    monitor.start()
    console.print(Panel(
        "[green]Monitoring active. Watching for lineup changes...\n"
        "Press [bold]Ctrl+C[/bold] to stop.[/green]",
        border_style="green",
        title="Live Monitor",
    ))

    try:
        while True:
            status = monitor.get_status()
            time.sleep(30)
            console.print(
                f"[dim]{datetime.now().strftime('%H:%M:%S')} — Monitoring "
                f"{status['active_matches']} match(es)...[/dim]"
            )
    except KeyboardInterrupt:
        monitor.stop()
        console.print("\n[yellow]Monitor stopped.[/yellow]")


def main():
    parser = argparse.ArgumentParser(
        description="FIFA 2026 Match Prediction Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--match", nargs=2, metavar=("HOME", "AWAY"),
        help='Predict specific match, e.g.: --match "USA" "Paraguay"',
    )
    parser.add_argument(
        "--date", metavar="YYYY-MM-DD", default=None,
        help="Date to predict (default: today)",
    )
    parser.add_argument(
        "--odds", action="store_true",
        help="Interactively enter bookmaker odds for value bet analysis",
    )
    parser.add_argument(
        "--threshold", type=float, default=MIN_CONFIDENCE_THRESHOLD,
        help=f"Minimum confidence %% to show full prediction (default: {MIN_CONFIDENCE_THRESHOLD})",
    )
    parser.add_argument(
        "--watch", action="store_true",
        help="After predicting, continuously monitor for lineup changes",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Show all predictions regardless of confidence threshold",
    )

    args = parser.parse_args()

    # Handle --all flag
    threshold = 0.0 if args.all else args.threshold

    print_header()

    # Parse date
    target_date = None
    if args.date:
        try:
            target_date = date.fromisoformat(args.date)
        except ValueError:
            console.print(f"[red]Invalid date format: {args.date}. Use YYYY-MM-DD.[/red]")
            sys.exit(1)

    # Parse bookmaker odds
    bookmaker_odds = None
    if args.odds:
        if args.match:
            bookmaker_odds = parse_bookmaker_odds()
        else:
            console.print("[yellow]--odds only works with --match for now. Skipping.[/yellow]")

    # Initialize engine
    with console.status("[cyan]Initializing prediction engine...[/cyan]", spinner="dots"):
        engine = PredictionEngine()

    console.print("[green]✓ Prediction engine ready[/green]")
    console.print(f"[dim]ELO ratings loaded for {len(engine.elo_ratings)} teams[/dim]\n")

    predictions = []

    if args.match:
        home, away = args.match
        console.print(f"[cyan]Predicting: [bold]{home}[/bold] vs [bold]{away}[/bold][/cyan]\n")
        with console.status("[cyan]Collecting data...[/cyan]", spinner="dots"):
            pred = engine.predict_match(
                home_team=home,
                away_team=away,
                bookmaker_odds=bookmaker_odds,
            )
        predictions = [pred]
        confidence = pred.get("confidence", {}).get("total", 0)
        if confidence < threshold:
            console.print(Panel(
                f"[yellow]Confidence: {confidence:.1f}% (threshold: {threshold}%)\n"
                f"Predicted outcome: [bold]{pred['confidence']['predicted_outcome']}[/bold] "
                f"@ {pred['confidence']['predicted_outcome_prob']}% probability\n\n"
                f"Use --all or --threshold {max(0, int(confidence)-5)} to see full details.[/yellow]",
                title=f"⚠ Below Confidence Threshold",
                border_style="yellow",
            ))
        else:
            render_prediction_panel(pred)
    else:
        predictions = run_today(engine, target_date=target_date,
                                odds_map=None, threshold=threshold)

    if args.watch and predictions:
        watch_mode(engine, [p for p in predictions if not p.get("error")], threshold)


if __name__ == "__main__":
    main()
