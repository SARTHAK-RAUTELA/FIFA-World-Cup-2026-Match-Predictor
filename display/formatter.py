"""
Rich terminal display for match predictions.
Renders all betting markets, confidence scores, and diagnostics in a readable format.
"""
from datetime import datetime
from typing import Dict, List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich import box
from rich.rule import Rule
from rich.align import Align
from prediction.confidence import confidence_color


console = Console()


def format_prob(prob: float) -> str:
    return f"{prob * 100:.1f}%"


def format_odds(odds: float) -> str:
    return f"{odds:.2f}"


def print_header():
    console.print()
    console.print(Rule("[bold cyan]FIFA 2026 MATCH PREDICTION TOOL[/bold cyan]", style="cyan"))
    console.print(f"[dim]Powered by: Poisson + ELO + Form + Player Impact + Sentiment Models[/dim]")
    console.print(f"[dim]Data Sources: football-data.org | ESPN | TheSportsDB | NewsAPI | Open-Meteo[/dim]")
    console.print(f"[dim]Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
    console.print()


def print_no_matches():
    console.print(Panel(
        "[yellow]No FIFA 2026 matches found for today.\n"
        "Check your internet connection or try a specific date with --date YYYY-MM-DD[/yellow]",
        title="No Matches",
        border_style="yellow",
    ))


def render_confidence_badge(confidence: Dict) -> Text:
    total = confidence["total"]
    color = confidence_color(total)
    badge = Text()
    badge.append(f" {total:.1f}% CONFIDENCE ", style=f"bold white on {color.split()[1] if ' ' in color else color}")
    if confidence["meets_threshold"]:
        badge.append("  [OK] ABOVE THRESHOLD", style="bold green")
    else:
        badge.append(f"  [!!] Below {confidence['threshold']}% threshold", style="bold yellow")
    return badge


def render_prediction_panel(pred: Dict) -> None:
    home = pred["home_team"]
    away = pred["away_team"]
    markets = pred["markets"]
    confidence = pred["confidence"]
    diag = pred["diagnostics"]
    data = pred.get("data", {})

    if "error" in pred:
        console.print(Panel(
            f"[red]Error predicting {home} vs {away}: {pred['error']}[/red]",
            border_style="red",
        ))
        return

    # Title
    conf_color = confidence_color(confidence["total"])
    title_text = f"[bold white] {home} [dim]vs[/dim] {away} [/bold white]"
    console.print(Panel(title_text, style="bold", border_style="bright_blue", padding=(0, 2)))

    # Confidence badge
    console.print(Align.center(render_confidence_badge(confidence)))
    console.print()

    # Expected Goals
    lam_h = markets["lam_home"]
    lam_a = markets["lam_away"]
    console.print(f"  [cyan]Expected Goals:[/cyan]  "
                  f"[bold]{home}[/bold]: [green]{lam_h:.2f}[/green]  |  "
                  f"[bold]{away}[/bold]: [red]{lam_a:.2f}[/red]  "
                  f"  [dim](Total: {lam_h + lam_a:.2f})[/dim]")
    console.print()

    # ELO Ratings
    console.print(f"  [cyan]ELO Ratings:[/cyan]  "
                  f"{home}: [bold]{diag.get('elo_home', '?'):.0f}[/bold]  |  "
                  f"{away}: [bold]{diag.get('elo_away', '?'):.0f}[/bold]")

    # Form Scores
    home_form_score = diag.get("home_form_score", 0.5)
    away_form_score = diag.get("away_form_score", 0.5)
    console.print(f"  [cyan]Form (0-1):[/cyan]   "
                  f"{home}: [bold]{home_form_score:.2f}[/bold]  |  "
                  f"{away}: [bold]{away_form_score:.2f}[/bold]")
    console.print()

    # Lineups
    home_lineup = data.get("home_lineup", [])
    away_lineup = data.get("away_lineup", [])
    lineup_confirmed = data.get("lineup_confirmed", False)
    home_formation = data.get("home_formation", "")
    away_formation = data.get("away_formation", "")

    if home_lineup or away_lineup:
        if lineup_confirmed:
            lu_status = "[bold green][OK] CONFIRMED LINEUPS[/bold green]"
        else:
            lu_status = "[yellow]~ Expected Lineups (unconfirmed)[/yellow]"
        formation_str = ""
        if home_formation or away_formation:
            formation_str = f"  |  {home_formation or '?'} vs {away_formation or '?'}"
        console.print(f"  [cyan]Lineups:[/cyan] {lu_status}{formation_str}")
        if home_lineup:
            names = [p.get("name", str(p)) if isinstance(p, dict) else str(p) for p in home_lineup]
            console.print(f"    {home}: [dim]{', '.join(names[:11])}[/dim]")
        if away_lineup:
            names = [p.get("name", str(p)) if isinstance(p, dict) else str(p) for p in away_lineup]
            console.print(f"    {away}: [dim]{', '.join(names[:11])}[/dim]")
        console.print()

    # Odds source indicator
    odds_source = pred.get("bookmaker_odds_source")
    if odds_source == "sofascore":
        console.print("  [cyan]Odds:[/cyan] [green]Auto-fetched from Sofascore (live bookmaker odds)[/green]")
        console.print()
    elif odds_source == "manual":
        console.print("  [cyan]Odds:[/cyan] [dim]Manually entered[/dim]")
        console.print()

    # Missing players
    missing_home = data.get("missing_home_players", [])
    missing_away = data.get("missing_away_players", [])
    if missing_home:
        console.print(f"  [yellow]!! {home} missing:[/yellow] {', '.join(missing_home)}")
    if missing_away:
        console.print(f"  [yellow]!! {away} missing:[/yellow] {', '.join(missing_away)}")
    if missing_home or missing_away:
        console.print()

    # Weather
    weather = data.get("weather")
    if weather:
        wdesc = weather.get("description", "")
        wtemp = weather.get("temperature_c", "?")
        wwind = weather.get("wind_speed_kmh", "?")
        wrain = weather.get("precipitation_mm", 0)
        wimp = weather.get("impact_factor", 1.0)
        weather_color = "yellow" if wimp < 0.95 else "green"
        console.print(f"  [cyan]Weather:[/cyan] {wdesc} | {wtemp}°C | Wind: {wwind} km/h | "
                      f"Rain: {wrain}mm | Impact: [{weather_color}]{wimp:.2f}x[/{weather_color}]")
        console.print()

    # --- 1x2 Table ---
    t_1x2 = Table(title="1x2", box=box.ROUNDED, show_header=True, header_style="bold cyan")
    t_1x2.add_column("Outcome", style="bold")
    t_1x2.add_column("Probability", justify="right")
    t_1x2.add_column("Fair Odds", justify="right")

    hw_p = markets["1x2"]["home"]["prob"]
    dr_p = markets["1x2"]["draw"]["prob"]
    aw_p = markets["1x2"]["away"]["prob"]

    def outcome_style(p: float, others: list) -> str:
        return "bold green" if p == max(others) else ""

    probs_1x2 = [hw_p, dr_p, aw_p]
    t_1x2.add_row(f"[H] {home}", format_prob(hw_p), format_odds(markets["1x2"]["home"]["odds"]),
                  style=outcome_style(hw_p, probs_1x2))
    t_1x2.add_row("[-] Draw", format_prob(dr_p), format_odds(markets["1x2"]["draw"]["odds"]),
                  style=outcome_style(dr_p, probs_1x2))
    t_1x2.add_row(f"[A] {away}", format_prob(aw_p), format_odds(markets["1x2"]["away"]["odds"]),
                  style=outcome_style(aw_p, probs_1x2))

    # --- BTTS Table ---
    t_btts = Table(title="Both Teams Score", box=box.ROUNDED, show_header=True, header_style="bold cyan")
    t_btts.add_column("Outcome", style="bold")
    t_btts.add_column("Probability", justify="right")
    t_btts.add_column("Fair Odds", justify="right")

    btts_y_p = markets["btts"]["yes"]["prob"]
    btts_n_p = markets["btts"]["no"]["prob"]
    t_btts.add_row("[Y] Yes", format_prob(btts_y_p), format_odds(markets["btts"]["yes"]["odds"]),
                   style="bold green" if btts_y_p > btts_n_p else "")
    t_btts.add_row("[N] No", format_prob(btts_n_p), format_odds(markets["btts"]["no"]["odds"]),
                   style="bold green" if btts_n_p > btts_y_p else "")

    # --- DNB Table ---
    t_dnb = Table(title="Draw No Bet", box=box.ROUNDED, show_header=True, header_style="bold cyan")
    t_dnb.add_column("Outcome", style="bold")
    t_dnb.add_column("Probability", justify="right")
    t_dnb.add_column("Fair Odds", justify="right")
    dnb_h = markets["draw_no_bet"]["home"]
    dnb_a = markets["draw_no_bet"]["away"]
    t_dnb.add_row(f"[H] {home}", format_prob(dnb_h["prob"]), format_odds(dnb_h["odds"]),
                  style="bold green" if dnb_h["prob"] > dnb_a["prob"] else "")
    t_dnb.add_row(f"[A] {away}", format_prob(dnb_a["prob"]), format_odds(dnb_a["odds"]),
                  style="bold green" if dnb_a["prob"] > dnb_h["prob"] else "")

    console.print(Columns([t_1x2, t_btts, t_dnb], equal=False, expand=False))
    console.print()

    # --- Double Chance ---
    t_dc = Table(title="Double Chance", box=box.ROUNDED, header_style="bold cyan")
    t_dc.add_column("Outcome")
    t_dc.add_column("Probability", justify="right")
    t_dc.add_column("Fair Odds", justify="right")
    dc = markets["double_chance"]
    t_dc.add_row(f"{home} or Draw", format_prob(dc["home_draw"]["prob"]), format_odds(dc["home_draw"]["odds"]))
    t_dc.add_row(f"{away} or Draw", format_prob(dc["away_draw"]["prob"]), format_odds(dc["away_draw"]["odds"]))
    t_dc.add_row(f"{home} or {away}", format_prob(dc["home_away"]["prob"]), format_odds(dc["home_away"]["odds"]))

    # --- First Goal ---
    t_fg = Table(title="1st Goal", box=box.ROUNDED, header_style="bold cyan")
    t_fg.add_column("Team")
    t_fg.add_column("Probability", justify="right")
    t_fg.add_column("Fair Odds", justify="right")
    fg = markets["first_goal"]
    t_fg.add_row(f"[H] {home}", format_prob(fg["home"]["prob"]), format_odds(fg["home"]["odds"]))
    t_fg.add_row("[0] None", format_prob(fg["none"]["prob"]), format_odds(fg["none"]["odds"]))
    t_fg.add_row(f"[A] {away}", format_prob(fg["away"]["prob"]), format_odds(fg["away"]["odds"]))

    # --- Halftime ---
    t_ht = Table(title="Halftime 1x2", box=box.ROUNDED, header_style="bold cyan")
    t_ht.add_column("Outcome")
    t_ht.add_column("Probability", justify="right")
    t_ht.add_column("Fair Odds", justify="right")
    ht = markets["halftime"]
    t_ht.add_row(f"[H] {home}", format_prob(ht["home"]["prob"]), format_odds(ht["home"]["odds"]))
    t_ht.add_row("[-] Draw", format_prob(ht["draw"]["prob"]), format_odds(ht["draw"]["odds"]))
    t_ht.add_row(f"[A] {away}", format_prob(ht["away"]["prob"]), format_odds(ht["away"]["odds"]))

    console.print(Columns([t_dc, t_fg, t_ht], equal=False, expand=False))
    console.print()

    # --- Asian Total ---
    t_at = Table(title="Asian Total (Over/Under)", box=box.ROUNDED, header_style="bold cyan")
    t_at.add_column("Line", justify="center")
    t_at.add_column("Over %", justify="right")
    t_at.add_column("Over Odds", justify="right")
    t_at.add_column("Under %", justify="right")
    t_at.add_column("Under Odds", justify="right")
    for line, data_line in markets["asian_total"].items():
        over_p = data_line["over"]["prob"]
        under_p = data_line["under"]["prob"]
        over_style = "bold green" if over_p > under_p else ""
        under_style = "bold green" if under_p > over_p else ""
        t_at.add_row(
            str(line),
            format_prob(over_p),
            format_odds(data_line["over"]["odds"]),
            format_prob(under_p),
            format_odds(data_line["under"]["odds"]),
            style="",
        )

    # --- Asian Handicap ---
    t_ah = Table(title=f"Asian Handicap ({home})", box=box.ROUNDED, header_style="bold cyan")
    t_ah.add_column("Handicap", justify="center")
    t_ah.add_column(f"{home} %", justify="right")
    t_ah.add_column(f"{home} Odds", justify="right")
    t_ah.add_column(f"{away} %", justify="right")
    t_ah.add_column(f"{away} Odds", justify="right")
    for h_val, h_data in markets["asian_handicap"].items():
        hp = h_data["home"]["prob"]
        ap = h_data["away"]["prob"]
        t_ah.add_row(
            f"{h_val:+.2f}",
            format_prob(hp),
            format_odds(h_data["home"]["odds"]),
            format_prob(ap),
            format_odds(h_data["away"]["odds"]),
        )

    console.print(Columns([t_at, t_ah], equal=True, expand=False))
    console.print()

    # --- Correct Score Top 12 ---
    t_cs = Table(title="Most Likely Correct Scores", box=box.ROUNDED, header_style="bold cyan")
    t_cs.add_column("Score", justify="center", style="bold")
    t_cs.add_column("Probability", justify="right")
    t_cs.add_column("Fair Odds", justify="right")
    cs_list = markets["correct_score"][:12]
    for cs in cs_list:
        score_str = f"{cs['home']} - {cs['away']}"
        t_cs.add_row(score_str, format_prob(cs["probability"]), format_odds(1.0 / cs["probability"] if cs["probability"] > 0 else 999))

    console.print(t_cs)
    console.print()

    # --- Value Bets ---
    vbets = pred.get("value_bets", [])
    if vbets:
        t_vb = Table(title="[>>] VALUE BETS  (Model vs Bookmaker)", box=box.ROUNDED, header_style="bold yellow")
        t_vb.add_column("Market")
        t_vb.add_column("Selection")
        t_vb.add_column("Our Prob", justify="right")
        t_vb.add_column("Our Odds", justify="right")
        t_vb.add_column("Bookie Odds", justify="right")
        t_vb.add_column("Edge %", justify="right")
        t_vb.add_column("Exp Value", justify="right")
        for vb in vbets:
            t_vb.add_row(
                vb["market"], vb["selection"],
                format_prob(vb["model_prob"]), format_odds(vb["model_odds"]),
                format_odds(vb["bookie_odds"]),
                f"[bold green]+{vb['edge_pct']:.1f}%[/bold green]",
                f"[{'green' if vb['expected_value'] > 0 else 'red'}]{vb['expected_value']:+.3f}[/]",
            )
        console.print(t_vb)
        console.print()

    # --- Confidence Breakdown ---
    comp = confidence["components"]
    t_conf = Table(title="Confidence Breakdown", box=box.SIMPLE, header_style="bold cyan")
    t_conf.add_column("Component")
    t_conf.add_column("Score", justify="right")
    for label, val in comp.items():
        color = "green" if val >= 80 else "yellow" if val >= 60 else "red"
        t_conf.add_row(label.replace("_", " ").title(), f"[{color}]{val:.1f}%[/{color}]")
    t_conf.add_row("[bold]TOTAL CONFIDENCE[/bold]",
                   f"[{confidence_color(confidence['total'])}][bold]{confidence['total']:.1f}%[/bold][/{confidence_color(confidence['total'])}]")

    # Data sources
    sources_text = f"Data sources: {', '.join(data.get('data_sources', ['fallback/default']))}"
    console.print(Columns([t_conf, Panel(sources_text, title="Data Sources", border_style="dim")]))
    console.print()


def render_lineup_update_alert(home_team: str, away_team: str, changes: List[str]) -> None:
    console.print(Panel(
        "\n".join([f"  • {c}" for c in changes]),
        title=f"[bold yellow]** LINEUP UPDATE: {home_team} vs {away_team} **[/bold yellow]",
        border_style="yellow",
    ))


def render_match_list(fixtures: List[Dict]) -> None:
    if not fixtures:
        print_no_matches()
        return

    t = Table(title="Today's FIFA 2026 Matches", box=box.ROUNDED, header_style="bold cyan")
    t.add_column("#", justify="right", style="dim")
    t.add_column("Match")
    t.add_column("Time (UTC)", justify="center")
    t.add_column("Venue")
    t.add_column("Status")
    t.add_column("Odds", justify="center")

    for i, f in enumerate(fixtures, 1):
        home = f.get("home_team", "?")
        away = f.get("away_team", "?")
        dt_raw = f.get("date", "")
        time_str = dt_raw[11:16] if len(dt_raw) >= 16 else "TBD"
        venue = f.get("venue", f.get("city", ""))[:28]
        status = f.get("status", f.get("sofascore_status", "SCHEDULED"))
        odds_badge = "[green]AUTO[/green]" if f.get("sofascore_id") else "[dim]--[/dim]"
        t.add_row(str(i), f"{home} vs {away}", time_str, venue, status, odds_badge)

    console.print(t)
    console.print()


def print_collection_status(message: str, status: str = "info") -> None:
    colors = {"info": "cyan", "ok": "green", "warn": "yellow", "error": "red"}
    color = colors.get(status, "white")
    icons = {"info": "ℹ", "ok": "✓", "warn": "⚠", "error": "✗"}
    icon = icons.get(status, "·")
    console.print(f"  [{color}]{icon}[/{color}] {message}")
