"""
Poisson distribution model for football score prediction.
Uses Dixon-Coles correction for low-scoring outcomes.
"""
import math
import numpy as np
from scipy.stats import poisson
from config import MAX_GOALS, DIXON_COLES_RHO


def poisson_pmf(k: int, lam: float) -> float:
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return poisson.pmf(k, lam)


def dixon_coles_tau(home: int, away: int, lam_h: float, lam_a: float, rho: float = DIXON_COLES_RHO) -> float:
    """
    Correction factor for statistical dependency in low-scoring outcomes.
    Standard Poisson overestimates 0-0, under-estimates 1-0 and 0-1.
    """
    if home == 0 and away == 0:
        return 1 - lam_h * lam_a * rho
    elif home == 0 and away == 1:
        return 1 + lam_h * rho
    elif home == 1 and away == 0:
        return 1 + lam_a * rho
    elif home == 1 and away == 1:
        return 1 - rho
    return 1.0


def build_score_matrix(lam_home: float, lam_away: float,
                       max_goals: int = MAX_GOALS) -> np.ndarray:
    """
    Compute probability matrix P[i][j] = P(home scores i, away scores j).
    Rows = home goals, Columns = away goals.
    """
    matrix = np.zeros((max_goals + 1, max_goals + 1))
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            p_home = poisson_pmf(i, lam_home)
            p_away = poisson_pmf(j, lam_away)
            tau = dixon_coles_tau(i, j, lam_home, lam_away)
            matrix[i][j] = p_home * p_away * tau

    # Normalise to ensure probabilities sum to 1
    total = matrix.sum()
    if total > 0:
        matrix /= total
    return matrix


def home_win_prob(matrix: np.ndarray) -> float:
    """P(home goals > away goals)."""
    return float(np.sum(np.tril(matrix, -1)))


def draw_prob(matrix: np.ndarray) -> float:
    """P(home goals == away goals)."""
    return float(np.trace(matrix))


def away_win_prob(matrix: np.ndarray) -> float:
    """P(away goals > home goals)."""
    return float(np.sum(np.triu(matrix, 1)))


def btts_yes(matrix: np.ndarray) -> float:
    """P(both teams score >= 1 goal)."""
    # P(home > 0) AND P(away > 0) = 1 - P(home=0) - P(away=0) + P(home=0, away=0)
    return float(1 - matrix[0, :].sum() - matrix[:, 0].sum() + matrix[0, 0])


def btts_no(matrix: np.ndarray) -> float:
    return 1.0 - btts_yes(matrix)


def over_prob(matrix: np.ndarray, line: float) -> float:
    """P(total goals > line), handles Asian lines (e.g. 2.5, 2.75)."""
    n = matrix.shape[0]
    prob = 0.0
    for i in range(n):
        for j in range(n):
            total = i + j
            if total > line:
                prob += matrix[i, j]
            elif abs(total - line) < 1e-9:
                # Exactly on the line: push (half-line logic handled in markets.py)
                pass
    return float(prob)


def under_prob(matrix: np.ndarray, line: float) -> float:
    """P(total goals < line)."""
    n = matrix.shape[0]
    prob = 0.0
    for i in range(n):
        for j in range(n):
            total = i + j
            if total < line:
                prob += matrix[i, j]
    return float(prob)


def asian_handicap_probs(matrix: np.ndarray, handicap: float) -> tuple:
    """
    Calculate Asian Handicap probabilities.
    handicap: positive = home team advantage (e.g. +0.5 means away needs to win by 1+)
              negative = away team advantage

    Returns: (home_win, push, away_win) — push is non-zero only at integer handicaps
    """
    n = matrix.shape[0]
    home_p, push_p, away_p = 0.0, 0.0, 0.0

    for i in range(n):
        for j in range(n):
            adjusted_diff = (i - j) + handicap  # positive = home advantage after handicap
            if adjusted_diff > 0:
                home_p += matrix[i, j]
            elif adjusted_diff < 0:
                away_p += matrix[i, j]
            else:
                push_p += matrix[i, j]

    return float(home_p), float(push_p), float(away_p)


def correct_score_probs(matrix: np.ndarray, top_n: int = 12) -> list:
    """Return top N most likely scorelines with probabilities."""
    n = matrix.shape[0]
    scores = []
    for i in range(n):
        for j in range(n):
            scores.append({"home": i, "away": j, "probability": float(matrix[i, j])})
    scores.sort(key=lambda x: x["probability"], reverse=True)
    return scores[:top_n]


def first_goal_probs(lam_home: float, lam_away: float) -> dict:
    """P(home scores first), P(away scores first), P(no goal)."""
    # Assumes goals follow Poisson, first scorer ~ proportional to rates
    total_lambda = lam_home + lam_away
    p_no_goal = math.exp(-total_lambda)
    p_score = 1 - p_no_goal
    p_home_first = (lam_home / total_lambda) * p_score if total_lambda > 0 else 0
    p_away_first = (lam_away / total_lambda) * p_score if total_lambda > 0 else 0
    return {
        "home_first": round(p_home_first, 4),
        "away_first": round(p_away_first, 4),
        "no_goal": round(p_no_goal, 4),
    }


def halftime_probs(lam_home: float, lam_away: float) -> dict:
    """Approximate half-time 1x2 using 45-minute lambdas (roughly half full-match)."""
    lam_h_ht = lam_home * 0.45  # slight weighting: slightly less scoring in 1st half
    lam_a_ht = lam_away * 0.45
    matrix_ht = build_score_matrix(lam_h_ht, lam_a_ht, max_goals=4)
    return {
        "home": round(home_win_prob(matrix_ht), 4),
        "draw": round(draw_prob(matrix_ht), 4),
        "away": round(away_win_prob(matrix_ht), 4),
    }


