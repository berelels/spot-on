"""
model.py — Poisson + Dixon-Coles football prediction model
"""

import numpy as np
from scipy.stats import poisson
from data_service import compute_team_stats

MAX_GOALS = 9   # considers scores from 0 to 8 goals per team

# League-wide average goals (used when we cannot derive them from data)
# These are empirical averages across top European leagues
FALLBACK_LEAGUE_AVG_HOME = 1.55
FALLBACK_LEAGUE_AVG_AWAY = 1.10


# ---------------------------------------------------------------------------
# Dixon-Coles correction
# ---------------------------------------------------------------------------

def dixon_coles_correction(
    matrix: np.ndarray,
    lh: float,
    la: float,
    rho: float = -0.06,
) -> np.ndarray:
    """
    Apply Dixon-Coles adjustment to the 4 low-scoring outcomes that the
    independent Poisson model systematically over/under-estimates.

    tau factors:
      (0,0) → 1 − λ_h · λ_a · ρ
      (1,0) → 1 + λ_a · ρ
      (0,1) → 1 + λ_h · ρ
      (1,1) → 1 − ρ
    """
    corrected = matrix.copy().astype(float)
    corrections = {
        (0, 0): 1.0 - lh * la * rho,
        (1, 0): 1.0 + la * rho,
        (0, 1): 1.0 + lh * rho,
        (1, 1): 1.0 - rho,
    }
    for (i, j), factor in corrections.items():
        corrected[i, j] *= factor
    total = corrected.sum()
    if total > 0:
        corrected /= total
    return corrected


# ---------------------------------------------------------------------------
# Score probability matrix
# ---------------------------------------------------------------------------

def score_matrix(lh: float, la: float) -> np.ndarray:
    """Build a MAX_GOALS × MAX_GOALS probability matrix for all scorelines."""
    home_probs = np.array([poisson.pmf(i, lh) for i in range(MAX_GOALS)])
    away_probs = np.array([poisson.pmf(j, la) for j in range(MAX_GOALS)])
    matrix = np.outer(home_probs, away_probs)
    return dixon_coles_correction(matrix, lh, la)


# ---------------------------------------------------------------------------
# Main prediction function
# ---------------------------------------------------------------------------

def predict(
    home_team_id: int,
    away_team_id: int,
    league_id: str,
    home_team_name: str,
    away_team_name: str,
) -> dict:
    """
    Run the full prediction pipeline and return a result dict.
    """
    home_stats = compute_team_stats(home_team_id, league_id)
    away_stats = compute_team_stats(away_team_id, league_id)

    # --- League averages ---
    # We must use a global baseline. If we calculate it just from the two teams playing,
    # the lambda formula reduces to the harmonic mean of (scored, conceded), which mathematically
    # squashes variance and artificially caps lambdas < 1.5, causing 1-1 to always dominate.
    if league_id in ["WC", "EC", "CA", "CAN", "WCQ"]:
        # National/Neutral matches have balanced baseline
        league_avg_home = 1.35
        league_avg_away = 1.35
    else:
        # Club matches have home advantage baseline
        league_avg_home = FALLBACK_LEAGUE_AVG_HOME
        league_avg_away = FALLBACK_LEAGUE_AVG_AWAY

    # --- Strength factors ---
    att_home = home_stats["home_scored"]  / league_avg_home
    def_home = home_stats["home_concede"] / league_avg_away
    att_away = away_stats["away_scored"]  / league_avg_away
    def_away = away_stats["away_concede"] / league_avg_home

    # Guard against zeros
    for val in (att_home, def_home, att_away, def_away):
        if val == 0:
            val = 0.5

    # --- Expected goals ---
    lambda_home = att_home * def_away * league_avg_home
    lambda_away = att_away * def_home * league_avg_away

    # Clamp to sensible range
    lambda_home = max(0.2, min(lambda_home, 6.0))
    lambda_away = max(0.2, min(lambda_away, 6.0))

    # --- Score matrix ---
    matrix = score_matrix(lambda_home, lambda_away)

    # --- Outcome probabilities ---
    home_win = float(np.sum(np.tril(matrix, -1)))
    draw     = float(np.sum(np.diag(matrix)))
    away_win = float(np.sum(np.triu(matrix, 1)))

    # Renormalise in case of floating-point drift
    total = home_win + draw + away_win
    home_win /= total
    draw     /= total
    away_win /= total

    # --- Top 10 scorelines ---
    flat = matrix.flatten()
    top_indices = np.argsort(flat)[::-1][:10]
    top_scores = []
    for idx in top_indices:
        i, j = divmod(int(idx), MAX_GOALS)
        top_scores.append({
            "score": f"{i}-{j}",
            "probability": round(float(flat[idx]), 4),
        })

    # --- Confidence ---
    matches_used = min(home_stats["matches_used"], away_stats["matches_used"])
    if matches_used >= 30:
        confidence = "high"
    elif matches_used >= 15:
        confidence = "medium"
    else:
        confidence = "low"

    # Dynamic explanatory text
    if league_id in ["WC", "EC", "CA", "CAN", "WCQ"]:
        data_text = f"Últimas {matches_used} partidas de cada seleção (todas as competições)"
    else:
        data_text = f"Últimas {matches_used} partidas de cada time nesta liga"

    return {
        "home_team":    home_team_name,
        "away_team":    away_team_name,
        "lambda_home":  round(lambda_home, 2),
        "lambda_away":  round(lambda_away, 2),
        "home_win":     round(home_win, 4),
        "draw":         round(draw, 4),
        "away_win":     round(away_win, 4),
        "top_scores":   top_scores,
        "data_based_on": data_text,
        "confidence":   confidence,
        "matches_used": matches_used,
    }
