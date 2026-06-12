"""
Confidence scoring system.
Measures how reliable a prediction is, on a 0-100% scale.
Only output predictions when confidence >= threshold (default 93%).
"""
import math
from typing import Dict, List, Optional
from config import MIN_CONFIDENCE_THRESHOLD


def entropy(probs: List[float]) -> float:
    """Shannon entropy — lower = more predictable = higher confidence."""
    total = sum(p for p in probs if p > 0)
    if total == 0:
        return math.log(len(probs)) if probs else 0
    normed = [p / total for p in probs if p > 0]
    return -sum(p * math.log(p) for p in normed)


def max_entropy(n: int) -> float:
    """Maximum possible entropy for n outcomes (uniform distribution)."""
    return math.log(n) if n > 1 else 0


def prediction_clarity(probs: List[float]) -> float:
    """
    How dominant is the top outcome? (0=uniform, 1=certain)
    Based on relative entropy.
    """
    n = len(probs)
    if n <= 1:
        return 1.0
    e = entropy(probs)
    e_max = max_entropy(n)
    if e_max == 0:
        return 1.0
    return round(1.0 - (e / e_max), 4)


def data_quality_score(
    home_form_count: int,
    away_form_count: int,
    has_lineups: bool,
    has_news: bool,
    has_weather: bool,
    h2h_count: int,
) -> float:
    """
    Score data completeness/quality from 0.0 to 1.0.
    More data = higher quality score.
    """
    score = 0.0
    max_score = 0.0

    # Form data (up to 0.35)
    max_score += 0.35
    form_quality = min(10, (home_form_count + away_form_count) / 2)
    score += (form_quality / 10) * 0.35

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
    h2h_quality = min(10, h2h_count)
    score += (h2h_quality / 10) * 0.15

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
) -> Dict:
    """
    Calculate overall prediction confidence score.

    Components:
    1. Prediction clarity (how dominant is the predicted outcome)
    2. Data quality (amount and freshness of data)
    3. Model agreement (how consistent are sub-models)
    4. Lineup certainty (are we sure of the lineup?)

    Returns dict with total confidence and breakdown.
    """
    # 1. Prediction clarity from 1x2 probabilities
    p_1x2 = [
        markets["1x2"]["home"]["prob"],
        markets["1x2"]["draw"]["prob"],
        markets["1x2"]["away"]["prob"],
    ]
    clarity = prediction_clarity(p_1x2)

    # 2. Data quality
    # Confirmed lineups count as full data; unconfirmed expected lineups still help
    effective_lineups = bool(home_lineup and away_lineup)
    dq = data_quality_score(
        home_form_count=len(home_form),
        away_form_count=len(away_form),
        has_lineups=effective_lineups,
        has_news=has_news,
        has_weather=weather is not None,
        h2h_count=len(h2h),
    )
    # Small bonus for having auto-fetched bookmaker odds (better calibration)
    if has_bookmaker_odds:
        dq = min(1.0, dq + 0.03)

    # 3. Model agreement
    elo_hw, elo_dr, elo_aw = diagnostics.get("elo_1x2", (0.4, 0.3, 0.3))
    # Approximate form-based 1x2 from λ comparison
    lam_h = diagnostics.get("form_lam_home", 1.35)
    lam_a = diagnostics.get("form_lam_away", 1.35)
    total_lam = lam_h + lam_a
    form_hw = lam_h / total_lam * 0.85
    form_dr = 0.25 - abs(lam_h - lam_a) * 0.05
    form_dr = max(0.10, min(0.35, form_dr))
    form_aw = 1.0 - form_hw - form_dr

    poisson_hw = markets["1x2"]["home"]["prob"]
    poisson_dr = markets["1x2"]["draw"]["prob"]
    poisson_aw = markets["1x2"]["away"]["prob"]

    agreement = model_agreement_score(
        (elo_hw, elo_dr, elo_aw),
        (form_hw, form_dr, form_aw),
        (poisson_hw, poisson_dr, poisson_aw),
    )

    # 4. Lineup certainty
    if lineup_confirmed and home_lineup and away_lineup:
        lineup_certainty = 1.0          # Sofascore confirmed — we know exactly who's playing
    elif home_lineup and away_lineup:
        lineup_certainty = 0.88         # Both teams have data but not officially confirmed
    elif home_lineup or away_lineup:
        lineup_certainty = 0.78         # Only one team's lineup known
    else:
        lineup_certainty = 0.70         # No lineup data at all

    # Composite confidence (weighted)
    # When no data is available, use ELO as baseline and reflect lower certainty
    lineup_factor = (lineup_certainty - 0.70) / 0.30  # normalize 0.70-1.0 to 0.0-1.0

    raw_confidence = (
        clarity * 0.35 +
        dq * 0.30 +
        agreement * 0.25 +
        lineup_factor * 0.10
    )

    # Minimum floor when ELO baseline is used (no form/lineup data)
    # ELO alone gives ~50% reliable floor for strong favorites
    if dq < 0.10 and clarity > 0.20:
        raw_confidence = max(raw_confidence, clarity * 0.55)

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
            "prediction_clarity": round(clarity * 100, 1),
            "data_quality": round(dq * 100, 1),
            "model_agreement": round(agreement * 100, 1),
            "lineup_certainty": round(lineup_certainty * 100, 1),
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
