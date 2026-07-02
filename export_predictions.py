"""
Non-interactive prediction runner.
Fetches today's FIFA 2026 fixtures, runs all models, and writes a complete
prediction card payload to docs/predictions_export.json.
"""
import json
import os
import sys
from datetime import date, datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from prediction.engine import PredictionEngine

WEBSITE_DIR = os.path.join(os.path.dirname(__file__), "docs")
OUTPUT_FILE = os.path.join(WEBSITE_DIR, "predictions_export.json")

# ── Teams present at FIFA WC 2026 ────────────────────────────────────────────
WC_2026_TEAMS = {
    "Argentina", "France", "Brazil", "England", "Spain", "Germany",
    "Portugal", "Netherlands", "Belgium", "Italy", "Croatia", "Uruguay",
    "Colombia", "Mexico", "USA", "Morocco", "Japan", "South Korea",
    "Australia", "Ecuador", "Canada", "Senegal", "Peru", "Chile",
    "Paraguay", "Nigeria", "Ghana", "Cameroon", "Egypt", "Algeria",
    "Ivory Coast", "South Africa", "Mali", "Tunisia", "DR Congo",
    "Iran", "Saudi Arabia", "Qatar", "Uzbekistan", "Bahrain",
    "New Zealand", "Sweden", "Norway", "Switzerland", "Serbia",
    "Poland", "Bolivia", "Panama", "Jamaica", "Honduras",
    "El Salvador", "Costa Rica", "Guatemala", "Trinidad and Tobago",
    "Venezuela", "China", "Iraq", "Jordan", "UAE",
}

FLAG_MAP = {
    "Argentina": "🇦🇷", "France": "🇫🇷", "Brazil": "🇧🇷",
    "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "Spain": "🇪🇸", "Germany": "🇩🇪",
    "Portugal": "🇵🇹", "Netherlands": "🇳🇱", "Belgium": "🇧🇪",
    "Italy": "🇮🇹", "Croatia": "🇭🇷", "Uruguay": "🇺🇾",
    "Colombia": "🇨🇴", "Mexico": "🇲🇽", "USA": "🇺🇸",
    "Morocco": "🇲🇦", "Japan": "🇯🇵", "South Korea": "🇰🇷",
    "Australia": "🇦🇺", "Ecuador": "🇪🇨", "Canada": "🇨🇦",
    "Senegal": "🇸🇳", "Peru": "🇵🇪", "Chile": "🇨🇱",
    "Paraguay": "🇵🇾", "Nigeria": "🇳🇬", "Ghana": "🇬🇭",
    "Cameroon": "🇨🇲", "Egypt": "🇪🇬", "Algeria": "🇩🇿",
    "Ivory Coast": "🇨🇮", "South Africa": "🇿🇦", "Mali": "🇲🇱",
    "Tunisia": "🇹🇳", "DR Congo": "🇨🇩", "Iran": "🇮🇷",
    "Saudi Arabia": "🇸🇦", "Qatar": "🇶🇦", "Uzbekistan": "🇺🇿",
    "Bahrain": "🇧🇭", "New Zealand": "🇳🇿", "Sweden": "🇸🇪",
    "Norway": "🇳🇴", "Switzerland": "🇨🇭", "Serbia": "🇷🇸",
    "Poland": "🇵🇱", "Bolivia": "🇧🇴", "Panama": "🇵🇦",
    "Jamaica": "🇯🇲", "Honduras": "🇭🇳", "El Salvador": "🇸🇻",
    "Costa Rica": "🇨🇷", "China": "🇨🇳", "Iraq": "🇮🇶",
    "Jordan": "🇯🇴", "UAE": "🇦🇪",
}

STAGE_SHORT = {
    "group_stage": "GROUP", "round_of_32": "R32", "round_of_16": "R16",
    "quarter_final": "QF", "semi_final": "SF", "final": "FINAL",
}


def _auto_stage(d: date) -> str:
    if d < date(2026, 6, 28):   return "group_stage"
    if d <= date(2026, 7, 3):   return "round_of_32"
    if d <= date(2026, 7, 7):   return "round_of_16"
    if d <= date(2026, 7, 12):  return "quarter_final"
    if d <= date(2026, 7, 16):  return "semi_final"
    return "final"


def _format_kickoff(iso_dt: str) -> str:
    """'2026-06-29T17:00' → '17:00 ET'"""
    if not iso_dt or len(iso_dt) < 16:
        return ""
    try:
        return iso_dt[11:16] + " ET"
    except Exception:
        return ""


def _conf_level(total: float) -> str:
    if total >= 65:  return "HIGH"
    if total >= 45:  return "MEDIUM"
    return "LOW"


def _kelly(model_prob: float, bookie_odds: float) -> float:
    """Fractional Kelly (25%) as a percentage."""
    b = bookie_odds - 1
    if b <= 0:
        return 0.0
    f = (model_prob * (b + 1) - 1) / b
    return round(max(0.0, f * 25.0), 1)


def _match_id(home: str, away: str) -> str:
    return (home[:3] + "-" + away[:3]).lower().replace(" ", "")


def _build_note(home: str, away: str, diag: dict, markets: dict,
                value_bets: list, confidence: dict) -> str:
    parts = []
    elo_h = int(diag.get("elo_home", 0))
    elo_a = int(diag.get("elo_away", 0))
    lh = markets.get("lam_home", 0)
    la = markets.get("lam_away", 0)
    outcome = confidence.get("predicted_outcome", "")
    outcome_prob = confidence.get("predicted_outcome_prob", 0)

    if elo_h and elo_a:
        parts.append(f"{home} ELO {elo_h} · {away} ELO {elo_a}")
    if lh and la:
        parts.append(f"λ {lh:.2f} vs {la:.2f}")
    if outcome and outcome_prob:
        parts.append(f"Model: {outcome_prob:.0f}% {outcome.lower()}")
    if value_bets:
        best = max(value_bets, key=lambda x: x.get("edge_pct", 0))
        sel = best.get("selection", "")
        mkt = best.get("market", "")
        edge = best.get("edge_pct", 0)
        odds = best.get("bookie_odds", 0)
        if sel and edge:
            parts.append(f"Best value: {sel} ({mkt}) +{edge:.1f}% @ {odds:.2f}")
    return ". ".join(parts) + "." if parts else ""


def _extract_prediction(pred: dict, fixture: dict, stage: str) -> dict:
    home = pred["home_team"]
    away = pred["away_team"]
    markets = pred.get("markets", {})
    diag = pred.get("diagnostics", {})
    confidence = pred.get("confidence", {})
    value_bets = pred.get("value_bets", [])

    # Lambdas (live inside the markets dict)
    lh = round(markets.get("lam_home", 0), 2)
    la = round(markets.get("lam_away", 0), 2)

    # 1x2 probabilities
    x12 = markets.get("1x2", {})
    ph = round(x12.get("home", {}).get("prob", 0) * 100)
    pd_ = round(x12.get("draw", {}).get("prob", 0) * 100)
    pa = round(x12.get("away", {}).get("prob", 0) * 100)
    # Keep percentages summing to 100
    if ph + pd_ + pa != 100:
        pa = 100 - ph - pd_

    # Predicted score: top correct-score entry
    cs_list = markets.get("correct_score", [])
    if cs_list:
        top_cs = cs_list[0]
        sh, sa = top_cs["home"], top_cs["away"]
    else:
        sh, sa = round(lh) if lh else 1, round(la) if la else 0

    # Confidence level
    conf_total = confidence.get("total", 0)
    conf = _conf_level(conf_total)

    # Best value bet
    if value_bets:
        best_vb = max(value_bets, key=lambda x: x.get("edge_pct", 0))
        bo = best_vb.get("bookie_odds")
        edge = round(best_vb.get("edge_pct", 0), 1)
        kelly = _kelly(best_vb.get("model_prob", 0), bo or 0)
        sel = best_vb.get("selection", "")
        mkt = best_vb.get("market", "")
        bet_label = f"{sel} — {mkt}" if mkt else sel
    else:
        outcome_map = {
            "Home Win": f"{home} Win",
            "Away Win": f"{away} Win",
            "Draw": "Draw",
        }
        outcome = confidence.get("predicted_outcome", "")
        bet_label = outcome_map.get(outcome, outcome or f"{home} Win")
        bo = None
        edge = 0.0
        kelly = 0.0

    kickoff_iso = fixture.get("date", "")
    time_str = _format_kickoff(kickoff_iso)
    venue = fixture.get("venue", fixture.get("city", ""))
    stage_short = STAGE_SHORT.get(stage, stage.upper())

    note = _build_note(home, away, diag, markets, value_bets, confidence)

    return {
        "id":            _match_id(home, away),
        "home":          home,
        "away":          away,
        "flag_home":     FLAG_MAP.get(home, "⚽"),
        "flag_away":     FLAG_MAP.get(away, "⚽"),
        "kickoff":       kickoff_iso[:16] if kickoff_iso else "",
        "time":          time_str,
        "venue":         venue,
        "stage":         stage_short,
        "lambda_home":   lh,
        "lambda_away":   la,
        "score_home":    sh,
        "score_away":    sa,
        "prob_home":     ph,
        "prob_draw":     pd_,
        "prob_away":     pa,
        "confidence":    conf,
        "confidence_total": round(conf_total, 1),
        "bet_label":     bet_label,
        "edge":          edge,
        "odds":          bo,
        "kelly":         kelly,
        "note":          note,
        "result":        None,
        "status":        "upcoming",
    }


def main():
    today = date.today()
    stage = _auto_stage(today)

    print(f"[export] Date: {today}  Stage: {stage}")
    print("[export] Loading prediction engine...")
    engine = PredictionEngine()

    print("[export] Fetching today's fixtures...")
    fixtures = engine.aggregator.get_today_matches()

    # Filter to WC 2026 teams only
    wc_fixtures = [
        f for f in fixtures
        if f.get("home_team") in WC_2026_TEAMS and f.get("away_team") in WC_2026_TEAMS
    ]
    skipped = len(fixtures) - len(wc_fixtures)
    if skipped:
        print(f"[export] Skipped {skipped} non-WC fixture(s)")

    predictions = []
    print(f"[export] {len(wc_fixtures)} WC fixture(s) — running models...")

    for f in wc_fixtures:
        home = f.get("home_team", "")
        away = f.get("away_team", "")
        print(f"  {home} vs {away}")
        try:
            pred = engine.predict_match(
                home_team=home,
                away_team=away,
                match_id=str(f.get("id", "")),
                sofascore_id=f.get("sofascore_id"),
                venue_city=f.get("city", "Dallas"),
                match_date=(f.get("date", "")[:10] if f.get("date") else None),
                stage=stage,
            )
            predictions.append(_extract_prediction(pred, f, stage))
        except Exception as e:
            print(f"  [ERROR] {home} vs {away}: {e}")

    export = {
        "prediction_date":  today.isoformat(),
        "stage":            stage,
        "generated_at":     today.strftime("%B %d, %Y"),
        "fixture_count":    len(predictions),
        "predictions":      predictions,
    }

    os.makedirs(WEBSITE_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as fh:
        json.dump(export, fh, indent=2, ensure_ascii=False)

    print(f"\n[export] Saved {len(predictions)} prediction(s) → {OUTPUT_FILE}")
    print(f"[export] prediction_date = {today.isoformat()}")


if __name__ == "__main__":
    main()
