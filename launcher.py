"""
FIFA 2026 Match Prediction Tool - Interactive Launcher
Double-click FIFA_Predictor.bat to run this.
"""
import os
import sys

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from datetime import date
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.columns import Columns
from rich.text import Text
from rich.rule import Rule
from rich import box

from prediction.engine import PredictionEngine
from display.formatter import render_prediction_panel, render_match_list, print_collection_status

console = Console()


BANNER = r"""
  ______ _____  ______           ___   ___ ___   ____
 |  ____|_   _||  ____/\        |__ \ / _ \__ \ / ___|
 | |__    | |  | |__ /  \          ) | | | | ) | |
 |  __|   | |  |  __/ /\ \        / /| | | |/ /| |
 | |     _| |_ | | / ____ \      / /_| |_| / /_| |___
 |_|    |_____||_|/_/    \_\    |____|\___/____|_____|

        MATCH PREDICTION TOOL  ~  FIFA WORLD CUP 2026
"""

KNOWN_TEAMS = sorted([
    "Argentina", "France", "Brazil", "England", "Spain", "Germany",
    "Portugal", "Netherlands", "Belgium", "Italy", "Croatia", "Uruguay",
    "Colombia", "Mexico", "USA", "Morocco", "Japan", "South Korea",
    "Australia", "Ecuador", "Canada", "Senegal", "Peru", "Chile",
    "Paraguay", "Costa Rica", "Honduras", "Bolivia", "El Salvador",
    "Jamaica", "Nigeria", "Ghana", "Cameroon", "Egypt", "Algeria",
    "Ivory Coast", "South Africa", "Mali", "Tunisia", "DR Congo",
    "Iran", "Saudi Arabia", "Qatar", "China", "Iraq", "Jordan",
    "UAE", "Uzbekistan", "Bahrain", "New Zealand", "Panama",
    "Guatemala", "Trinidad and Tobago", "Venezuela",
])


def clear():
    os.system("cls" if sys.platform == "win32" else "clear")


def print_banner():
    console.print(f"[bold cyan]{BANNER}[/bold cyan]")
    console.print(f"[dim]  Powered by: Poisson + ELO + Form + Player Impact + Sentiment | "
                  f"Date: {date.today().strftime('%d %B %Y')}[/dim]")
    console.print()


def print_menu():
    console.print(Rule("[bold white] MAIN MENU [/bold white]", style="cyan"))
    console.print()

    menu = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    menu.add_column("Key", style="bold cyan", width=4)
    menu.add_column("Action", style="white")

    menu.add_row("1", "Predict TODAY's FIFA 2026 matches (auto-detect)")
    menu.add_row("2", "Predict a SPECIFIC match (enter teams)")
    menu.add_row("3", "Predict with BOOKMAKER ODDS (find value bets)")
    menu.add_row("4", "LIVE WATCH mode (auto-refresh lineups before kickoff)")
    menu.add_row("5", "Predict a different DATE")
    menu.add_row("6", "View list of supported teams")
    menu.add_row("0", "Exit")

    console.print(menu)
    console.print()


def pick_team(prompt_text: str) -> str:
    """Prompt user for a team name with autocomplete hint."""
    while True:
        raw = Prompt.ask(f"  [cyan]{prompt_text}[/cyan]").strip()
        if not raw:
            continue

        # Exact match (case-insensitive)
        for t in KNOWN_TEAMS:
            if t.lower() == raw.lower():
                return t

        # Partial match
        matches = [t for t in KNOWN_TEAMS if raw.lower() in t.lower()]
        if len(matches) == 1:
            console.print(f"  [dim]Matched: {matches[0]}[/dim]")
            return matches[0]
        elif len(matches) > 1:
            console.print(f"  [yellow]Multiple matches:[/yellow] {', '.join(matches)}")
            console.print("  [dim]Please type the full name.[/dim]")
        else:
            console.print(f"  [yellow]'{raw}' not in known teams. Using as-is.[/yellow]")
            return raw


def input_odds() -> dict:
    """Walk the user through entering bookmaker odds."""
    console.print("\n  [bold cyan]Enter bookmaker odds[/bold cyan] [dim](press Enter to skip any)[/dim]\n")
    odds = {}

    def ask_odds(label: str) -> float:
        val = Prompt.ask(f"  [dim]{label}[/dim]", default="").strip()
        try:
            return float(val) if val else 0.0
        except ValueError:
            return 0.0

    h = ask_odds("1x2 Home odds (e.g. 2.08)")
    d = ask_odds("1x2 Draw odds (e.g. 3.15)")
    a = ask_odds("1x2 Away odds (e.g. 3.80)")
    if any([h, d, a]):
        odds["1x2"] = {}
        if h: odds["1x2"]["home"] = h
        if d: odds["1x2"]["draw"] = d
        if a: odds["1x2"]["away"] = a

    by = ask_odds("BTTS Yes odds (e.g. 2.13)")
    bn = ask_odds("BTTS No odds  (e.g. 1.69)")
    if by or bn:
        odds["btts"] = {}
        if by: odds["btts"]["yes"] = by
        if bn: odds["btts"]["no"] = bn

    return odds


def show_team_list():
    console.print()
    console.print(Rule("[bold white] SUPPORTED TEAMS [/bold white]", style="cyan"))
    cols = []
    chunk = 10
    for i in range(0, len(KNOWN_TEAMS), chunk):
        t = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
        t.add_column("", style="white", min_width=22)
        for name in KNOWN_TEAMS[i:i+chunk]:
            t.add_row(name)
        cols.append(t)
    console.print(Columns(cols))
    console.print()


def run_prediction(engine: PredictionEngine, home: str, away: str,
                   odds: dict = None, sofascore_id: int = None, threshold: float = 0.0):
    console.print()
    console.print(Rule(f"[bold white] {home}  vs  {away} [/bold white]", style="bright_blue"))

    with console.status("[cyan]  Collecting data and running models...[/cyan]", spinner="dots"):
        pred = engine.predict_match(
            home_team=home,
            away_team=away,
            sofascore_id=sofascore_id,
            bookmaker_odds=odds or None,
        )

    render_prediction_panel(pred)


def run_today_matches(engine: PredictionEngine, target_date=None):
    with console.status("[cyan]  Fetching today's FIFA 2026 fixtures...[/cyan]", spinner="dots"):
        fixtures = engine.aggregator.get_today_matches(target_date)

    if not fixtures:
        console.print(Panel(
            "[yellow]No FIFA 2026 matches found for today.\n\n"
            "  - Make sure your internet connection is active\n"
            "  - Try option 2 to predict a specific match\n"
            "  - Use option 5 to pick a different date[/yellow]",
            title="No Matches Found", border_style="yellow",
        ))
        return []

    console.print(f"\n  [green]Found {len(fixtures)} match(es)[/green]\n")
    render_match_list(fixtures)

    for i, f in enumerate(fixtures, 1):
        home = f.get("home_team", "")
        away = f.get("away_team", "")
        if not home or not away:
            continue
        odds_badge = " [green][AUTO-ODDS][/green]" if f.get("sofascore_id") else ""
        console.print(f"\n  [bold cyan]Predicting {i}/{len(fixtures)}: {home} vs {away}[/bold cyan]{odds_badge}")
        with console.status("  [cyan]Running models...[/cyan]", spinner="dots"):
            try:
                pred = engine.predict_match(
                    home_team=home, away_team=away,
                    match_id=str(f.get("id", "")),
                    sofascore_id=f.get("sofascore_id"),
                    venue_city=f.get("city", "Dallas"),
                    match_date=(f.get("date", "")[:10] if f.get("date") else None),
                )
                pred["fixture"] = f
            except Exception as e:
                console.print(f"  [red]Error: {e}[/red]")
                continue
        render_prediction_panel(pred)

    return fixtures


def run_watch_mode(engine: PredictionEngine, fixtures: list):
    if not fixtures:
        console.print("[yellow]No matches to monitor.[/yellow]")
        return

    from collectors.live_monitor import LiveMonitor

    def on_change(home, away, changes, updated):
        from display.formatter import render_lineup_update_alert
        render_lineup_update_alert(home, away, changes)
        render_prediction_panel(updated)

    monitor = LiveMonitor(engine, on_lineup_change=on_change)
    for f in fixtures:
        if f.get("id"):
            monitor.add_match(
                match_id=str(f["id"]),
                home_team=f.get("home_team", ""),
                away_team=f.get("away_team", ""),
                kickoff_time=f.get("date"),
            )

    monitor.start()
    console.print(Panel(
        "[green]Live monitor started. Checking for lineup changes...\n"
        "Press [bold]Ctrl+C[/bold] or [bold]Enter[/bold] to stop.[/green]",
        title="LIVE WATCH MODE", border_style="green",
    ))
    try:
        input()
    except KeyboardInterrupt:
        pass
    finally:
        monitor.stop()
        console.print("[dim]Monitor stopped.[/dim]")


def main():
    # Initialise engine once
    with console.status("[cyan]Loading prediction engine...[/cyan]", spinner="dots"):
        engine = PredictionEngine()

    last_fixtures = []

    while True:
        print_banner()
        console.print(f"  [dim]ELO database: {len(engine.elo_ratings)} teams loaded[/dim]\n")
        print_menu()

        choice = Prompt.ask("  [bold cyan]Select option[/bold cyan]",
                            choices=["0", "1", "2", "3", "4", "5", "6"],
                            default="1")

        if choice == "0":
            console.print("\n[cyan]Goodbye! Good luck with your predictions.[/cyan]\n")
            break

        elif choice == "1":
            last_fixtures = run_today_matches(engine)

        elif choice == "2":
            console.print()
            console.print(Rule("[bold white] SPECIFIC MATCH [/bold white]", style="cyan"))
            home = pick_team("Home / Team 1 (e.g. USA)")
            away = pick_team("Away / Team 2 (e.g. Paraguay)")
            run_prediction(engine, home, away)

        elif choice == "3":
            console.print()
            console.print(Rule("[bold white] MATCH + BOOKMAKER ODDS [/bold white]", style="cyan"))
            home = pick_team("Home / Team 1")
            away = pick_team("Away / Team 2")

            # Try to auto-fetch Sofascore odds first
            auto_odds = None
            sofa_id = None
            with console.status("  [cyan]Checking for live bookmaker odds...[/cyan]", spinner="dots"):
                try:
                    sofa_id = engine.aggregator.sofa.find_event_id(home, away)
                    if sofa_id:
                        sf_data = engine.aggregator.sofa.get_match_data(sofa_id)
                        auto_odds = sf_data.get("odds") if sf_data else None
                except Exception:
                    pass

            if auto_odds:
                console.print("\n  [green]Auto-fetched bookmaker odds from Sofascore:[/green]")
                if "1x2" in auto_odds:
                    o = auto_odds["1x2"]
                    console.print(f"    1X2:  Home {o.get('home','?')}  Draw {o.get('draw','?')}  Away {o.get('away','?')}")
                if "btts" in auto_odds:
                    o = auto_odds["btts"]
                    console.print(f"    BTTS: Yes {o.get('yes','?')}  No {o.get('no','?')}")
                if "dnb" in auto_odds:
                    o = auto_odds["dnb"]
                    console.print(f"    DNB:  Home {o.get('home','?')}  Away {o.get('away','?')}")
                console.print()
                use_auto = Confirm.ask("  Use these auto-fetched odds?", default=True)
                if use_auto:
                    run_prediction(engine, home, away, odds=auto_odds, sofascore_id=sofa_id)
                else:
                    odds = input_odds()
                    run_prediction(engine, home, away, odds=odds, sofascore_id=sofa_id)
            else:
                console.print("  [dim]No auto-odds available. Enter manually:[/dim]")
                odds = input_odds()
                run_prediction(engine, home, away, odds=odds)

        elif choice == "4":
            if not last_fixtures:
                console.print("[yellow]Run option 1 first to load today's matches.[/yellow]")
                console.print("[dim]Or enter teams manually (option 2) then come back.[/dim]")
            else:
                run_watch_mode(engine, last_fixtures)

        elif choice == "5":
            console.print()
            raw_date = Prompt.ask("  [cyan]Enter date[/cyan]", default=date.today().isoformat())
            try:
                target = date.fromisoformat(raw_date)
            except ValueError:
                console.print("[red]Invalid date. Use YYYY-MM-DD format.[/red]")
                target = None
            if target:
                last_fixtures = run_today_matches(engine, target_date=target)

        elif choice == "6":
            show_team_list()

        # Pause before showing menu again
        console.print()
        try:
            Prompt.ask("  [dim]Press Enter to return to menu[/dim]", default="")
        except (KeyboardInterrupt, EOFError):
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted. Goodbye.[/dim]\n")
