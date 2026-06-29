"""
Stakes analyzer — Kelly Criterion stake sizing, value bet portfolio, penalty probability.

Kelly Criterion: f* = (p*b - q) / b
  p = model probability of winning
  q = 1 - p
  b = decimal odds - 1
  f* = optimal fraction of bankroll

We use Fractional Kelly (1/4) for safety — betting experience shows full Kelly is too
aggressive; 25% Kelly reduces variance while retaining 75% of EV.

Penalty shootout probability for KO games:
Based on WC historical data, P(90min draw) * P(ET draw | 90min draw) estimates P(pens).
"""
import math
from typing import Dict, List, Optional, Tuple


FRACTIONAL_KELLY = 0.25  # 25% Kelly — conservative but profitable
MIN_EDGE_PCT = 3.0        # minimum edge % to recommend a bet
MAX_STAKE_PCT = 5.0       # never stake more than 5% of bankroll on a single market
MIN_STAKE_AMOUNT = 1.0    # minimum absolute stake ($)


def kelly_fraction(model_prob: float, decimal_odds: float) -> float:
    """
    Returns the optimal Kelly fraction (clamped to [0, MAX_STAKE_PCT%]).
    Returns 0 if no positive edge.
    """
    if decimal_odds <= 1.0 or model_prob <= 0 or model_prob >= 1:
        return 0.0
    b = decimal_odds - 1.0  # net odds
    q = 1.0 - model_prob
    kelly = (model_prob * b - q) / b
    if kelly <= 0:
        return 0.0
    # Apply fractional Kelly and cap
    fractional = kelly * FRACTIONAL_KELLY
    return min(fractional, MAX_STAKE_PCT / 100.0)


def stake_amount(kelly_frac: float, bankroll: float) -> float:
    """Dollar stake from Kelly fraction and bankroll, floored at MIN_STAKE_AMOUNT."""
    amount = kelly_frac * bankroll
    return max(MIN_STAKE_AMOUNT, round(amount, 2)) if amount >= MIN_STAKE_AMOUNT else 0.0


def expected_profit(model_prob: float, decimal_odds: float, stake: float) -> float:
    """Expected profit = stake * (prob * (odds - 1) - (1 - prob))."""
    if decimal_odds <= 1.0:
        return 0.0
    return round(stake * (model_prob * (decimal_odds - 1) - (1 - model_prob)), 3)


def penalty_shootout_probability(lam_home: float, lam_away: float) -> Dict:
    """
    Estimate probability of extra time and penalty shootout in a KO game.

    Method:
    - P(draw after 90min) from Poisson score matrix (already computed in markets)
    - Historical WC KO: ~35-40% of draws go to pens (roughly P(ET draw) ≈ 0.45)
    - P(pens) = P(90min draw) * 0.45 (approx. ET draw rate from WC history)
    - P(home wins in pens | goes to pens) ≈ 0.50 (roughly even)
    """
    from models.poisson_model import build_score_matrix, draw_prob
    from config import MAX_GOALS

    matrix = build_score_matrix(lam_home, lam_away, MAX_GOALS)
    p_draw_90 = draw_prob(matrix)

    # WC historical data: ~40% of KO draws reach pens (others end in ET)
    # From WC 2014-2022: about 35 KO games went to ET; ~15 to pens = 43%
    P_ET_ALSO_DRAW = 0.43
    p_pens = round(p_draw_90 * P_ET_ALSO_DRAW, 4)

    # Home/away penalty win rate: home slight edge on PKs (estimated)
    # Research: no consistent home advantage in penalty shootouts
    p_home_pens = 0.50
    p_away_pens = 0.50

    # P(home wins including pens) = P(home wins 90min) + P(draw 90min) * P(ET home wins)
    # Simplified: P(go to pens) contribution
    return {
        "p_draw_90min": round(p_draw_90, 4),
        "p_extra_time": round(p_draw_90, 4),
        "p_penalty_shootout": p_pens,
        "p_home_wins_penalties": round(p_pens * p_home_pens, 4),
        "p_away_wins_penalties": round(p_pens * p_away_pens, 4),
        "note": "KO game: draws go to 30min ET, then possibly pens. ~43% of ET games go to pens.",
    }


def _ko_1x2_with_pens(markets: Dict, stage: str) -> Dict:
    """
    For KO rounds, extend 1x2 with 'including extra time and pens' probabilities.
    In KO betting markets 'draw' is unusual — most books offer:
      Home to qualify, Away to qualify (including ET+pens)
    This models that.
    """
    if stage not in {"round_of_32","round_of_16","quarter_final","semi_final","final"}:
        return {}

    lam_h = markets.get("lam_home", 1.3)
    lam_a = markets.get("lam_away", 1.0)
    pen_stats = penalty_shootout_probability(lam_h, lam_a)

    hw = markets["1x2"]["home"]["prob"]
    dr = markets["1x2"]["draw"]["prob"]
    aw = markets["1x2"]["away"]["prob"]

    # P(home qualifies) = P(home wins 90min) + P(draw 90min) * 0.50 (50/50 in ET+pens)
    p_home_qualify = hw + dr * 0.50
    p_away_qualify = aw + dr * 0.50

    def prob_to_odds(p):
        return round(1.0 / p, 2) if p > 0 else 999.0

    return {
        "home_to_qualify": {"prob": round(p_home_qualify, 4), "odds": prob_to_odds(p_home_qualify)},
        "away_to_qualify": {"prob": round(p_away_qualify, 4), "odds": prob_to_odds(p_away_qualify)},
        "penalty_shootout": pen_stats,
    }


def analyze_stakes(
    markets: Dict,
    value_bets: List[Dict],
    bookmaker_odds: Optional[Dict],
    bankroll: float = 100.0,
    stage: str = "group_stage",
) -> Dict:
    """
    Full stakes analysis:
    1. Kelly Criterion stake for each value bet
    2. Penalty/ET markets for KO games
    3. Portfolio summary: total recommended stake, expected profit, ROI
    4. Ranked betting card (sorted by EV)
    """
    betting_card: List[Dict] = []

    # ── Process each value bet ────────────────────────────────────────────────
    for vb in value_bets:
        model_prob = vb.get("model_prob", 0)
        bookie_odds = vb.get("bookie_odds", 0)
        edge_pct = vb.get("edge_pct", 0)

        if edge_pct < MIN_EDGE_PCT or bookie_odds <= 1.0:
            continue

        kf = kelly_fraction(model_prob, bookie_odds)
        amount = stake_amount(kf, bankroll)
        if amount == 0:
            continue

        ev = expected_profit(model_prob, bookie_odds, amount)
        roi = round(ev / amount * 100, 1) if amount > 0 else 0

        betting_card.append({
            "market": vb["market"],
            "selection": vb["selection"],
            "model_prob": round(model_prob, 4),
            "model_odds": vb.get("model_odds", 0),
            "bookie_odds": bookie_odds,
            "edge_pct": edge_pct,
            "kelly_fraction": round(kf * 100, 2),
            "recommended_stake": amount,
            "expected_profit": ev,
            "roi_pct": roi,
            "confidence": "HIGH" if edge_pct >= 8 else ("MEDIUM" if edge_pct >= 5 else "LOW"),
        })

    # ── If no bookmaker odds, use model-only recommendations ──────────────────
    if not bookmaker_odds and markets:
        betting_card = _model_only_recommendations(markets, bankroll, stage)

    # ── KO-specific: penalty/ET markets ──────────────────────────────────────
    ko_markets = _ko_1x2_with_pens(markets, stage)

    # Sort by expected profit descending
    betting_card.sort(key=lambda x: x.get("expected_profit", 0), reverse=True)

    # ── Portfolio summary ─────────────────────────────────────────────────────
    total_stake = round(sum(b["recommended_stake"] for b in betting_card), 2)
    total_ev = round(sum(b["expected_profit"] for b in betting_card), 3)
    portfolio_roi = round(total_ev / total_stake * 100, 1) if total_stake > 0 else 0

    # ── Best single bet ───────────────────────────────────────────────────────
    best_bet = betting_card[0] if betting_card else None

    # ── Risk rating ───────────────────────────────────────────────────────────
    if len(betting_card) == 0:
        risk_rating = "NO_VALUE"
        risk_note = "No bets with sufficient edge found. Avoid betting or wait for better odds."
    elif portfolio_roi > 15:
        risk_rating = "HIGH_VALUE"
        risk_note = f"Strong value detected. Portfolio ROI {portfolio_roi}%. Proceed with fractional Kelly stakes."
    elif portfolio_roi > 8:
        risk_rating = "MODERATE_VALUE"
        risk_note = f"Decent value found. ROI {portfolio_roi}%. Standard fractional Kelly recommended."
    else:
        risk_rating = "MARGINAL_VALUE"
        risk_note = f"Marginal edge only. ROI {portfolio_roi}%. Consider unit betting (1 unit max) not Kelly."

    return {
        "stage": stage,
        "bankroll": bankroll,
        "betting_card": betting_card,
        "ko_markets": ko_markets,
        "portfolio": {
            "total_stake": total_stake,
            "total_expected_profit": total_ev,
            "portfolio_roi_pct": portfolio_roi,
            "num_bets": len(betting_card),
            "risk_rating": risk_rating,
            "risk_note": risk_note,
        },
        "best_bet": best_bet,
        "kelly_method": f"Fractional Kelly ({int(FRACTIONAL_KELLY*100)}% of full Kelly)",
    }


def _model_only_recommendations(markets: Dict, bankroll: float, stage: str) -> List[Dict]:
    """
    When no bookmaker odds are available, recommend bets based on strong model signals.
    Uses model fair odds as a proxy — only recommend if confidence is very high (>70%).
    """
    recommendations = []
    hw = markets.get("1x2", {}).get("home", {}).get("prob", 0)
    dr = markets.get("1x2", {}).get("draw", {}).get("prob", 0)
    aw = markets.get("1x2", {}).get("away", {}).get("prob", 0)

    def prob_to_odds(p):
        return round(1.0 / p, 2) if p > 0.01 else 999.0

    # Only recommend clear favorites (>65% model probability)
    for outcome, prob in [("Home Win", hw), ("Draw", dr), ("Away Win", aw)]:
        if prob >= 0.65:
            fair_odds = prob_to_odds(prob)
            # Assume bookmaker adds ~10% margin = implied odds ~10% higher
            assumed_bookie_odds = round(fair_odds * 0.92, 2)  # conservative estimate
            edge = prob - (1.0 / assumed_bookie_odds)
            if edge > 0.03:
                kf = kelly_fraction(prob, assumed_bookie_odds)
                amount = stake_amount(kf, bankroll)
                if amount > 0:
                    ev = expected_profit(prob, assumed_bookie_odds, amount)
                    recommendations.append({
                        "market": "1X2",
                        "selection": outcome,
                        "model_prob": round(prob, 4),
                        "model_odds": fair_odds,
                        "bookie_odds": assumed_bookie_odds,
                        "edge_pct": round(edge * 100, 2),
                        "kelly_fraction": round(kf * 100, 2),
                        "recommended_stake": amount,
                        "expected_profit": ev,
                        "roi_pct": round(ev / amount * 100, 1) if amount > 0 else 0,
                        "confidence": "MODEL_ONLY",
                        "note": "No bookmaker odds — using model fair odds with assumed 8% margin",
                    })

    # BTTS recommendations
    btts_y = markets.get("btts", {}).get("yes", {}).get("prob", 0)
    btts_n = markets.get("btts", {}).get("no", {}).get("prob", 0)
    for label, prob in [("BTTS Yes", btts_y), ("BTTS No", btts_n)]:
        if prob >= 0.68:
            fair_odds = prob_to_odds(prob)
            assumed_bookie_odds = round(fair_odds * 0.91, 2)
            edge = prob - (1.0 / assumed_bookie_odds)
            if edge > 0.03:
                kf = kelly_fraction(prob, assumed_bookie_odds)
                amount = stake_amount(kf, bankroll)
                if amount > 0:
                    ev = expected_profit(prob, assumed_bookie_odds, amount)
                    recommendations.append({
                        "market": "BTTS",
                        "selection": label,
                        "model_prob": round(prob, 4),
                        "model_odds": fair_odds,
                        "bookie_odds": assumed_bookie_odds,
                        "edge_pct": round(edge * 100, 2),
                        "kelly_fraction": round(kf * 100, 2),
                        "recommended_stake": amount,
                        "expected_profit": ev,
                        "roi_pct": round(ev / amount * 100, 1) if amount > 0 else 0,
                        "confidence": "MODEL_ONLY",
                        "note": "No bookmaker odds — using model fair odds",
                    })

    return recommendations


def format_betting_card(stakes: Dict, home_team: str, away_team: str) -> str:
    """Format stakes analysis as a clean text card for display (ASCII-safe)."""
    SEP = "=" * 62
    lines = []
    lines.append(f"\n{SEP}")
    lines.append(f"  BETTING CARD: {home_team} vs {away_team}")
    lines.append(f"  Stage: {stakes.get('stage','?').upper().replace('_',' ')}")
    lines.append(f"  Method: {stakes.get('kelly_method','Fractional Kelly')}")
    lines.append(SEP)

    card = stakes.get("betting_card", [])
    if not card:
        lines.append("  No value bets detected. Await bookmaker odds or skip match.")
    else:
        lines.append(f"  {'Market':<12} {'Selection':<16} {'Edge':>6} {'Odds':>6} {'Stake':>7} {'EV':>7}")
        lines.append(f"  {'-'*12} {'-'*16} {'-'*6} {'-'*6} {'-'*7} {'-'*7}")
        for b in card:
            conf = "[H]" if b.get("confidence") == "HIGH" else ("[M]" if b.get("confidence") == "MEDIUM" else "[L]")
            lines.append(
                f"  {b['market']:<12} {b['selection']:<16} "
                f"{b['edge_pct']:>5.1f}% {b['bookie_odds']:>5.2f} "
                f"${b['recommended_stake']:>6.2f} ${b['expected_profit']:>6.3f} {conf}"
            )

    p = stakes.get("portfolio", {})
    lines.append(SEP)
    lines.append(f"  Total stake: ${p.get('total_stake',0):.2f}  |  "
                 f"Expected profit: ${p.get('total_expected_profit',0):.3f}  |  "
                 f"ROI: {p.get('portfolio_roi_pct',0)}%")
    lines.append(f"  Risk: {p.get('risk_rating','?')}")
    lines.append(f"  {p.get('risk_note','')}")

    ko = stakes.get("ko_markets", {})
    if ko and ko.get("penalty_shootout"):
        ps = ko["penalty_shootout"]
        lines.append(f"\n  [KO MARKETS]")
        lines.append(f"  P(90min draw): {ps.get('p_draw_90min',0)*100:.1f}%  |  "
                     f"P(penalty shootout): {ps.get('p_penalty_shootout',0)*100:.1f}%")
        if ko.get("home_to_qualify"):
            hq = ko["home_to_qualify"]
            aq = ko["away_to_qualify"]
            lines.append(f"  Home to qualify: {hq['prob']*100:.1f}% (odds {hq['odds']})  |  "
                         f"Away to qualify: {aq['prob']*100:.1f}% (odds {aq['odds']})")

    lines.append(SEP)
    return "\n".join(lines)
