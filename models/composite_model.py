"""
Composite model combining Poisson, ELO, form, player impact, sentiment, and weather.
Produces final expected goals (λ) used for all market calculations.
"""
from typing import Dict, Tuple, Optional, List
from config import MODEL_WEIGHTS, HOME_ADVANTAGE
from models.poisson_model import build_score_matrix
from models.elo_model import expected_goals_from_elo, win_probability, get_team_elo, load_elo_ratings
from models.form_analyzer import (
    calculate_expected_goals, calculate_form_score, form_multiplier, recent_goal_avg
)
from models.player_impact import calculate_player_impact


WC_LEAGUE_AVG_GOALS = 2.68  # Historical World Cup average


def compute_lambdas(
    home_team: str,
    away_team: str,
    home_form: List[Dict],
    away_form: List[Dict],
    home_lineup: List[Dict],
    away_lineup: List[Dict],
    home_news: Dict,
    away_news: Dict,
    weather_impact: float = 1.0,
    is_neutral: bool = True,
    elo_ratings: Optional[Dict] = None,
) -> Tuple[float, float, Dict]:
    """
    Compute composite λ_home and λ_away from all available signals.
    Returns (lam_home, lam_away, diagnostics_dict).
    """
    if elo_ratings is None:
        elo_ratings = load_elo_ratings()

    # --- ELO component ---
    elo_home = get_team_elo(home_team, elo_ratings)
    elo_away = get_team_elo(away_team, elo_ratings)
    elo_lam_h, elo_lam_a = expected_goals_from_elo(
        elo_home, elo_away, WC_LEAGUE_AVG_GOALS, is_neutral
    )
    elo_1x2 = win_probability(elo_home, elo_away, is_neutral)

    # --- Form component ---
    form_lam_h, form_lam_a = calculate_expected_goals(
        home_form, away_form, home_team, away_team,
        league_avg=WC_LEAGUE_AVG_GOALS, is_neutral=is_neutral
    )
    home_form_score = calculate_form_score(home_form, home_team)
    away_form_score = calculate_form_score(away_form, away_team)

    # Form quality multipliers
    home_form_mult = form_multiplier(home_form_score)
    away_form_mult = form_multiplier(away_form_score)

    # --- Player impact component ---
    home_player_impact = calculate_player_impact(
        home_team, home_lineup, home_news.get("injured_players", [])
    )
    away_player_impact = calculate_player_impact(
        away_team, away_lineup, away_news.get("injured_players", [])
    )

    # --- Sentiment component ---
    # Morale: 0.5 = neutral, >0.5 = positive, <0.5 = negative
    home_morale = home_news.get("morale", 0.5)
    away_morale = away_news.get("morale", 0.5)
    # Convert morale to small λ multiplier: [0.95, 1.05]
    home_sentiment_mult = 0.95 + (home_morale * 0.10)
    away_sentiment_mult = 0.95 + (away_morale * 0.10)

    # Injury risk reduces expected goals
    home_injury_risk = home_news.get("injury_risk", 0.0)
    away_injury_risk = away_news.get("injury_risk", 0.0)
    home_injury_mult = 1.0 - (home_injury_risk * 0.10)
    away_injury_mult = 1.0 - (away_injury_risk * 0.10)

    # --- Weighted composite λ ---
    w = MODEL_WEIGHTS

    # Determine how much to trust form data vs ELO
    # If form data is sparse (< 3 matches per team), rely almost entirely on ELO
    home_form_count = len([r for r in home_form if True])
    away_form_count = len([r for r in away_form if True])
    form_reliability = min(1.0, (home_form_count + away_form_count) / 12.0)

    # Dynamic weights: when form is sparse, boost ELO weight
    elo_weight = w["elo"] + w["poisson"] * (1.0 - form_reliability)
    form_weight = w["poisson"] * form_reliability

    # Clamp extreme form λ values toward ELO when form sample is small
    if form_reliability < 0.5:
        blend = 0.3 + 0.4 * form_reliability  # 0.3 to 0.5 form blend
        form_lam_h = form_lam_h * blend + elo_lam_h * (1 - blend)
        form_lam_a = form_lam_a * blend + elo_lam_a * (1 - blend)

    # Base λ: weighted average of ELO-based and form-based
    total_base_weight = elo_weight + form_weight
    lam_h = (form_weight * form_lam_h + elo_weight * elo_lam_h) / total_base_weight
    lam_a = (form_weight * form_lam_a + elo_weight * elo_lam_a) / total_base_weight

    # Apply form quality multiplier
    lam_h *= (1.0 + (home_form_mult - 1.0) * w["form"])
    lam_a *= (1.0 + (away_form_mult - 1.0) * w["form"])

    # Apply player impact
    lam_h *= home_player_impact["attack_multiplier"] ** w["player_impact"]
    lam_a *= away_player_impact["attack_multiplier"] ** w["player_impact"]

    # Opponent defense: if their key defenders are missing, opponent scores more
    lam_h /= away_player_impact["defense_multiplier"] ** w["player_impact"]
    lam_a /= home_player_impact["defense_multiplier"] ** w["player_impact"]

    # Apply sentiment & injury multipliers
    lam_h *= (home_sentiment_mult ** w["sentiment"]) * (home_injury_mult ** w["player_impact"])
    lam_a *= (away_sentiment_mult ** w["sentiment"]) * (away_injury_mult ** w["player_impact"])

    # Apply weather impact (reduces total goals in bad weather)
    lam_h *= weather_impact
    lam_a *= weather_impact

    # Clip to realistic range
    lam_h = round(max(0.30, min(4.50, lam_h)), 3)
    lam_a = round(max(0.30, min(4.50, lam_a)), 3)

    diagnostics = {
        "elo_home": elo_home,
        "elo_away": elo_away,
        "elo_lam_home": elo_lam_h,
        "elo_lam_away": elo_lam_a,
        "elo_1x2": elo_1x2,
        "form_lam_home": form_lam_h,
        "form_lam_away": form_lam_a,
        "home_form_score": home_form_score,
        "away_form_score": away_form_score,
        "home_form_mult": home_form_mult,
        "away_form_mult": away_form_mult,
        "home_player_impact": home_player_impact,
        "away_player_impact": away_player_impact,
        "home_sentiment": home_sentiment_mult,
        "away_sentiment": away_sentiment_mult,
        "weather_impact": weather_impact,
        "final_lam_home": lam_h,
        "final_lam_away": lam_a,
    }

    return lam_h, lam_a, diagnostics
