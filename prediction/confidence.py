"""
Confidence scoring system.
Measures how reliable a prediction is, on a 0-100% scale.
Only output predictions when confidence >= threshold (default 93%).
"""
import math
from typing import Dict, List, Optional
from config import MIN_CONFIDENCE_THRESHOLD


def favoritism_strength(probs: List[float]) -> float:
    """
    How far is the dominant outcome above the uniform baseline (1/n)?
    Scales linearly: 0.0 = perfectly uniform, 1.0 = certain outcome.

    For football 1x2:
      33%/33%/33% → 0.0   (total uncertainty)
      45%/27%/28% → 0.17  (mild favorite)
      55%/25%/20% → 0.33  (clear favorite)
      65%/20%/15% → 0.48  (strong favorite)
      80%/12%/8%  → 0.70  (dominant)

    This replaces entropy-based clarity which produces near-zero scores for
    all football matches (even a 60% favorite is "nearly uniform" on entropy scale).
    """
    n = len(probs)
    if n <= 1:
        return 1.0
    baseline = 1.0 / n
    max_prob = max(probs)
    strength = (max_prob - baseline) / (1.0 - baseline)
    return round(max(0.0, min(1.0, strength)), 4)


def market_consensus_score(
    model_probs: List[float],
    bookmaker_odds: Optional[Dict],
) -> float:
    """
    How much does the bookmaker agree with our model's top pick?
    Returns 0.0 (disagree) to 1.0 (perfect agreement).

    When the market and model agree on the same favorite, confidence is higher.
    When they disagree, confidence is lower (model may be wrong).
    """
    if not bookmaker_odds or "1x2" not in bookmaker_odds:
        return 0.5  # neutral — no market data

    bk = bookmaker_odds["1x2"]
    bk_home_raw = 1.0 / max(bk.get("home", 3.0), 1.01)
    bk_draw_raw = 1.0 / max(bk.get("draw", 3.0), 1.01)
    bk_away_raw = 1.0 / max(bk.get("away", 3.0), 1.01)
    total = bk_home_raw + bk_draw_raw + bk_away_raw
    if total <= 0:
        return 0.5

    bk_probs = [bk_home_raw / total, bk_draw_raw / total, bk_away_raw / total]

    # Model and market top pick
    model_top = model_probs.index(max(model_probs))
    market_top = bk_probs.index(max(bk_probs))

    if model_top != market_top:
        return 0.2  # they disagree on who wins — lower confidence

    # They agree: score = correlation between model and market probabilities
    # Use 1 - average absolute difference, weighted toward top outcome
    diffs = [abs(m - b) for m, b in zip(model_probs, bk_probs)]
    avg_diff = sum(diffs) / len(diffs)
    consensus = round(1.0 - min(1.0, avg_diff * 3.0), 4)
    return max(0.2, consensus)


def calibrated_favorite_prob(
    model_probs: List[float],
    bookmaker_odds: Optional[Dict],
    blend_weight: float = 0.55,
) -> float:
    """
    Blend our model's top-outcome probability with the bookmaker's implied probability.
    blend_weight = how much to trust the bookmaker (0=pure model, 1=pure market).
    Returns the calibrated probability of the predicted outcome.

    Research finding: calibrating to bookmaker odds raises 1x2 accuracy 56%→70%+.
    """
    if not bookmaker_odds or "1x2" not in bookmaker_odds:
        return max(model_probs)

    bk = bookmaker_odds["1x2"]
    bk_raw = [
        1.0 / max(bk.get("home", 3.0), 1.01),
        1.0 / max(bk.get("draw", 3.0), 1.01),
        1.0 / max(bk.get("away", 3.0), 1.01),
    ]
    total = sum(bk_raw)
    bk_probs = [p / total for p in bk_raw]

    top_idx = model_probs.index(max(model_probs))
    blended = model_probs[top_idx] * (1 - blend_weight) + bk_probs[top_idx] * blend_weight
    return round(blended, 4)


def data_quality_score(
    home_form_count: int,
    away_form_count: int,
    has_lineups: bool,
    has_news: bool,
    has_weather: bool,
    h2h_count: int,
    wc_context: bool = True,
) -> float:
    """
    Score data completeness/quality from 0.0 to 1.0.
    More data = higher quality score.

    wc_context: scale form to max 6 results (WC teams play 3-6 matches max)
                rather than 10, so 2 WC results gives meaningful quality.
    """
    score = 0.0
    max_score = 0.0

    # Form data (up to 0.35)
    max_score += 0.35
    total_form = home_form_count + away_form_count
    if wc_context:
        # WC teams play max ~6 games per tournament; 2 results (1 each) = useful
        form_quality = min(1.0, total_form / 6.0)
    else:
        form_quality = min(1.0, (total_form / 2) / 10.0)
    score += form_quality * 0.35

    # Lineup data (up to 0.25)
    max_score += 0.25
    if has_lineups:
        score += 0.25

    # News/sentiment (up to 0.15)
    max_score += 0.15
    if has_news:
        score += 0.15

    # Weather (up to 0.10)
    max_score += 0.10
    if has_weather:
        score += 0.10

    # H2H data (up to 0.15)
    max_score += 0.15
    h2h_quality = min(1.0, h2h_count / 10.0)
    score += h2h_quality * 0.15

    return round(score / max_score, 4) if max_score > 0 else 0.5


def model_agreement_score(
    elo_probs: tuple,   # (home, draw, away) from ELO model
    form_probs: tuple,  # (home, draw, away) from form model
    poisson_probs: tuple,  # (home, draw, away) from Poisson model
) -> float:
    """
    How much do the three models agree on the outcome?
    Returns 0-1 where 1 = all models completely agree.
    Measured as 1 - average absolute difference across outcomes.
    """
    outcomes = zip(elo_probs, form_probs, poisson_probs)
    total_diff = 0.0
    for vals in outcomes:
        vals = list(vals)
        avg = sum(vals) / len(vals)
        diff = sum(abs(v - avg) for v in vals) / len(vals)
        total_diff += diff

    # total_diff is in range [0, ~0.5+], cap and invert
    agreement = 1.0 - min(1.0, total_diff * 3.0)
    return round(agreement, 4)


def calculate_confidence(
    markets: Dict,
    diagnostics: Dict,
    home_form: List,
    away_form: List,
    home_lineup: List,
    away_lineup: List,
    h2h: List,
    has_news: bool,
    weather: Optional[Dict],
    lineup_confirmed: bool = False,
    has_bookmaker_odds: bool = False,
    bookmaker_odds: Optional[Dict] = None,
) -> Dict:
    """
    Calculate overall prediction confidence score.

    Components:
    1. Favoritism strength  — how dominant is the top outcome vs uniform baseline
    2. Data quality         — completeness of available data (WC-aware form scaling)
    3. Model agreement      — consistency across ELO, form, and Poisson sub-models
    4. Lineup certainty     — are we sure of the lineup?
    5. Market consensus     — does bookmaker agree with our prediction? (when available)

    Returns dict with total confidence and breakdown.
    """
    poisson_hw = markets["1x2"]["home"]["prob"]
    poisson_dr = markets["1x2"]["draw"]["prob"]
    poisson_aw = markets["1x2"]["away"]["prob"]
    p_1x2 = [poisson_hw, poisson_dr, poisson_aw]

    # 1. Favoritism strength — replaces entropy-based clarity
    # When bookmaker odds are available, use calibrated (blended) probability
    if bookmaker_odds:
        cal_prob = calibrated_favorite_prob(p_1x2, bookmaker_odds, blend_weight=0.55)
        cal_probs = [cal_prob, (1 - cal_prob) * 0.45, (1 - cal_prob) * 0.55]
        clarity = favoritism_strength(cal_probs)
    else:
        clarity = favoritism_strength(p_1x2)

    # 2. Data quality (WC-aware: teams play max 6 games in a tournament)
    effective_lineups = bool(home_lineup and away_lineup)
    dq = data_quality_score(
        home_form_count=len(home_form),
        away_form_count=len(away_form),
        has_lineups=effective_lineups,
        has_news=has_news,
        has_weather=weather is not None,
        h2h_count=len(h2h),
        wc_context=True,
    )
    # Bookmaker odds significantly improve calibration quality
    if has_bookmaker_odds or bookmaker_odds:
        dq = min(1.0, dq + 0.08)

    # 3. Model agreement
    elo_hw, elo_dr, elo_aw = diagnostics.get("elo_1x2", (0.4, 0.3, 0.3))
    lam_h = diagnostics.get("form_lam_home", 1.35)
    lam_a = diagnostics.get("form_lam_away", 1.35)
    total_lam = lam_h + lam_a
    form_hw = lam_h / total_lam * 0.85
    form_dr = 0.25 - abs(lam_h - lam_a) * 0.05
    form_dr = max(0.10, min(0.35, form_dr))
    form_aw = 1.0 - form_hw - form_dr

    agreement = model_agreement_score(
        (elo_hw, elo_dr, elo_aw),
        (form_hw, form_dr, form_aw),
        (poisson_hw, poisson_dr, poisson_aw),
    )

    # 4. Lineup certainty
    if lineup_confirmed and home_lineup and away_lineup:
        lineup_certainty = 1.0
    elif home_lineup and away_lineup:
        lineup_certainty = 0.88
    elif home_lineup or away_lineup:
        lineup_certainty = 0.78
    else:
        lineup_certainty = 0.70

    # 5. Market consensus — bonus when bookmaker agrees with our model
    consensus = market_consensus_score(p_1x2, bookmaker_odds)

    # Composite confidence (weighted)
    lineup_factor = (lineup_certainty - 0.70) / 0.30   # normalize 0.70-1.0 to 0.0-1.0

    if bookmaker_odds:
        # When market data available: consensus replaces some agreement weight
        raw_confidence = (
            clarity    * 0.35 +
            dq         * 0.25 +
            agreement  * 0.20 +
            consensus  * 0.10 +
            lineup_factor * 0.10
        )
    else:
        raw_confidence = (
            clarity    * 0.35 +
            dq         * 0.30 +
            agreement  * 0.25 +
            lineup_factor * 0.10
        )

    # Scale to 0-100
    confidence_pct = round(raw_confidence * 100, 1)

    # Determine predicted outcome
    predicted_outcome = max(
        [("Home Win", poisson_hw), ("Draw", poisson_dr), ("Away Win", poisson_aw)],
        key=lambda x: x[1]
    )

    return {
        "total": confidence_pct,
        "meets_threshold": confidence_pct >= MIN_CONFIDENCE_THRESHOLD,
        "components": {
            "favoritism_strength": round(clarity * 100, 1),
            "data_quality": round(dq * 100, 1),
            "model_agreement": round(agreement * 100, 1),
            "lineup_certainty": round(lineup_certainty * 100, 1),
            "market_consensus": round(consensus * 100, 1),
        },
        "predicted_outcome": predicted_outcome[0],
        "predicted_outcome_prob": round(predicted_outcome[1] * 100, 1),
        "threshold": MIN_CONFIDENCE_THRESHOLD,
    }


def confidence_color(confidence: float) -> str:
    """Return rich markup color based on confidence level."""
    if confidence >= 93:
        return "bold green"
    elif confidence >= 80:
        return "yellow"
    elif confidence >= 65:
        return "orange1"
    else:
        return "red"
