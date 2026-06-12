"""
Player availability and quality impact on expected goals.
Adjusts λ based on key players' presence/absence.
"""
from typing import List, Dict, Optional


# Key player impact weights (how much a player's absence reduces team strength)
# Values represent % reduction in team's attacking/defensive capability
KEY_PLAYER_ROLES = {
    "FW": {"attack_impact": 0.15, "defense_impact": 0.02},
    "MF": {"attack_impact": 0.08, "defense_impact": 0.06},
    "DF": {"attack_impact": 0.02, "defense_impact": 0.12},
    "GK": {"attack_impact": 0.00, "defense_impact": 0.15},
    "ST": {"attack_impact": 0.15, "defense_impact": 0.01},
    "CF": {"attack_impact": 0.14, "defense_impact": 0.01},
    "CAM": {"attack_impact": 0.10, "defense_impact": 0.04},
    "CM": {"attack_impact": 0.07, "defense_impact": 0.07},
    "CDM": {"attack_impact": 0.03, "defense_impact": 0.10},
    "RW": {"attack_impact": 0.10, "defense_impact": 0.02},
    "LW": {"attack_impact": 0.10, "defense_impact": 0.02},
    "RB": {"attack_impact": 0.04, "defense_impact": 0.08},
    "LB": {"attack_impact": 0.04, "defense_impact": 0.08},
    "CB": {"attack_impact": 0.01, "defense_impact": 0.10},
}

# Known key players for FIFA 2026 teams (goalscorers / key contributors)
TEAM_KEY_PLAYERS = {
    "USA": [
        {"name": "Christian Pulisic", "position": "CAM", "importance": 0.9},
        {"name": "Ricardo Pepi", "position": "ST", "importance": 0.8},
        {"name": "Folarin Balogun", "position": "ST", "importance": 0.8},
        {"name": "Gio Reyna", "position": "CAM", "importance": 0.7},
        {"name": "Weston McKennie", "position": "CM", "importance": 0.7},
        {"name": "Tyler Adams", "position": "CDM", "importance": 0.75},
        {"name": "Matt Turner", "position": "GK", "importance": 0.7},
    ],
    "Paraguay": [
        {"name": "Miguel Almiron", "position": "CAM", "importance": 0.9},
        {"name": "Julio Enciso", "position": "CAM", "importance": 0.8},
        {"name": "Antonio Sanabria", "position": "ST", "importance": 0.8},
        {"name": "Gustavo Gomez", "position": "CB", "importance": 0.75},
        {"name": "Omar Alderete", "position": "CB", "importance": 0.65},
    ],
    "France": [
        {"name": "Kylian Mbappe", "position": "ST", "importance": 1.0},
        {"name": "Antoine Griezmann", "position": "CAM", "importance": 0.85},
        {"name": "Ousmane Dembele", "position": "RW", "importance": 0.80},
        {"name": "Aurelien Tchouameni", "position": "CDM", "importance": 0.75},
        {"name": "Mike Maignan", "position": "GK", "importance": 0.80},
    ],
    "Brazil": [
        {"name": "Vinicius Junior", "position": "LW", "importance": 1.0},
        {"name": "Rodrygo", "position": "RW", "importance": 0.85},
        {"name": "Raphinha", "position": "RW", "importance": 0.80},
        {"name": "Bruno Guimaraes", "position": "CM", "importance": 0.75},
        {"name": "Alisson", "position": "GK", "importance": 0.85},
    ],
    "Argentina": [
        {"name": "Lionel Messi", "position": "CAM", "importance": 1.0},
        {"name": "Julian Alvarez", "position": "ST", "importance": 0.85},
        {"name": "Rodrigo De Paul", "position": "CM", "importance": 0.75},
        {"name": "Emiliano Martinez", "position": "GK", "importance": 0.85},
    ],
    "England": [
        {"name": "Harry Kane", "position": "ST", "importance": 1.0},
        {"name": "Jude Bellingham", "position": "CAM", "importance": 0.95},
        {"name": "Phil Foden", "position": "CAM", "importance": 0.85},
        {"name": "Bukayo Saka", "position": "RW", "importance": 0.85},
    ],
    "Germany": [
        {"name": "Florian Wirtz", "position": "CAM", "importance": 0.95},
        {"name": "Jamal Musiala", "position": "CAM", "importance": 0.90},
        {"name": "Kai Havertz", "position": "ST", "importance": 0.80},
        {"name": "Joshua Kimmich", "position": "CDM", "importance": 0.85},
    ],
    "Spain": [
        {"name": "Pedri", "position": "CM", "importance": 0.90},
        {"name": "Lamine Yamal", "position": "RW", "importance": 0.92},
        {"name": "Alvaro Morata", "position": "ST", "importance": 0.78},
        {"name": "Rodri", "position": "CDM", "importance": 0.88},
    ],
    "Portugal": [
        {"name": "Bruno Fernandes", "position": "CAM", "importance": 0.90},
        {"name": "Bernardo Silva", "position": "CM", "importance": 0.85},
        {"name": "Rafael Leao", "position": "LW", "importance": 0.82},
        {"name": "Joao Felix", "position": "CAM", "importance": 0.80},
    ],
}


def calculate_player_impact(
    team_name: str,
    lineup: List[Dict],
    news_injured_players: Optional[List[str]] = None,
) -> Dict:
    """
    Calculate attack/defense impact multiplier based on:
    1. Confirmed lineup vs. key players list
    2. News-reported injuries

    Returns dict with attack_multiplier and defense_multiplier (both around 1.0).
    """
    news_injured_players = news_injured_players or []
    key_players = TEAM_KEY_PLAYERS.get(team_name, [])

    if not key_players:
        return {"attack_multiplier": 1.0, "defense_multiplier": 1.0, "missing_key_players": []}

    missing = []
    attack_reduction = 0.0
    defense_reduction = 0.0

    lineup_names = {p.get("name", "").lower() for p in lineup}
    news_names = {n.lower() for n in news_injured_players}

    for kp in key_players:
        kp_name = kp["name"].lower()
        kp_importance = kp.get("importance", 0.5)
        position = kp.get("position", "MF")
        role = KEY_PLAYER_ROLES.get(position, KEY_PLAYER_ROLES["MF"])

        # Check if confirmed absent
        in_lineup = any(kp_name in ln or ln in kp_name for ln in lineup_names)
        in_injured_news = any(kp_name in nn or nn in kp_name for nn in news_names)

        if not in_lineup and (in_injured_news or (lineup and not in_lineup)):
            missing.append(kp["name"])
            # Weight impact by player importance and role
            attack_reduction += role["attack_impact"] * kp_importance
            defense_reduction += role["defense_impact"] * kp_importance

    # Cap total reductions
    attack_reduction = min(0.35, attack_reduction)
    defense_reduction = min(0.30, defense_reduction)

    # Only apply reduction if we have lineup data (otherwise uncertainty = no change)
    if not lineup:
        attack_reduction *= 0.5  # partial reduction from news only
        defense_reduction *= 0.5

    return {
        "attack_multiplier": round(1.0 - attack_reduction, 3),
        "defense_multiplier": round(1.0 - defense_reduction, 3),
        "missing_key_players": missing,
        "attack_reduction_pct": round(attack_reduction * 100, 1),
        "defense_reduction_pct": round(defense_reduction * 100, 1),
    }


def squad_quality_rating(team_name: str) -> float:
    """
    Overall squad quality score 0-1 based on known key players.
    Used as a fallback when form data is unavailable.
    """
    from config import FIFA_2026_ELO_RATINGS
    elo = FIFA_2026_ELO_RATINGS.get(team_name, 1700.0)
    # Normalize ELO range [1600, 2100] to [0.2, 1.0]
    normalized = (elo - 1600) / (2100 - 1600)
    return round(max(0.2, min(1.0, normalized)), 3)
