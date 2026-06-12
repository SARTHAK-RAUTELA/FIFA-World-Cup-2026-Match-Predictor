"""Quick smoke-test for the prediction models."""
from models.poisson_model import build_score_matrix, home_win_prob, draw_prob, away_win_prob, btts_yes
from models.elo_model import win_probability, expected_goals_from_elo, get_team_elo
from models.form_analyzer import calculate_form_score
from prediction.markets import calculate_all_markets

def test_poisson():
    # USA vs Paraguay: USA slight favourite
    lam_home = 1.65  # USA
    lam_away = 1.05  # Paraguay

    m = build_score_matrix(lam_home, lam_away)
    hw = home_win_prob(m)
    dr = draw_prob(m)
    aw = away_win_prob(m)

    print(f"Poisson model (lam_home={lam_home}, lam_away={lam_away}):")
    print(f"  Home Win: {hw*100:.1f}%")
    print(f"  Draw:     {dr*100:.1f}%")
    print(f"  Away Win: {aw*100:.1f}%")
    print(f"  BTTS Yes: {btts_yes(m)*100:.1f}%")
    assert abs(hw + dr + aw - 1.0) < 0.001, "Probabilities must sum to 1"
    assert hw > aw, "Home team (higher λ) should have higher win probability"
    print("  [OK] Probabilities sum to 1")

def test_elo():
    usa_elo = get_team_elo("USA")
    par_elo = get_team_elo("Paraguay")
    print(f"\nELO ratings: USA={usa_elo}, Paraguay={par_elo}")
    hw, dr, aw = win_probability(usa_elo, par_elo, is_neutral=True)
    print(f"ELO 1x2: Home={hw*100:.1f}% Draw={dr*100:.1f}% Away={aw*100:.1f}%")
    assert hw > aw, "USA (higher ELO) should have higher win probability"
    lam_h, lam_a = expected_goals_from_elo(usa_elo, par_elo)
    print(f"ELO xG: USA={lam_h}, Paraguay={lam_a}")
    print("  [OK] ELO model working")

def test_markets():
    mkts = calculate_all_markets(1.65, 1.05)
    print("\nMarket calculations:")
    print(f"  1x2: H={mkts['1x2']['home']['odds']} D={mkts['1x2']['draw']['odds']} A={mkts['1x2']['away']['odds']}")
    print(f"  BTTS Yes odds: {mkts['btts']['yes']['odds']}")
    print(f"  Over 2.5: {mkts['asian_total'][2.5]['over']['odds']} | Under 2.5: {mkts['asian_total'][2.5]['under']['odds']}")
    print(f"  Top correct score: {mkts['correct_score'][0]['home']}-{mkts['correct_score'][0]['away']} ({mkts['correct_score'][0]['probability']*100:.1f}%)")
    # Asian handicap
    ah_0 = mkts["asian_handicap"][0.0]
    print(f"  AH 0 (level): H={ah_0['home']['odds']} A={ah_0['away']['odds']}")
    print("  [OK] All markets calculated")

def test_form():
    results = [
        {"home_team": "USA", "away_team": "Mexico", "home_goals": 2, "away_goals": 0, "winner": "HOME_TEAM"},
        {"home_team": "Canada", "away_team": "USA", "home_goals": 1, "away_goals": 1, "winner": "DRAW"},
        {"home_team": "USA", "away_team": "Brazil", "home_goals": 0, "away_goals": 2, "winner": "AWAY_TEAM"},
        {"home_team": "USA", "away_team": "Panama", "home_goals": 3, "away_goals": 0, "winner": "HOME_TEAM"},
        {"home_team": "Costa Rica", "away_team": "USA", "home_goals": 0, "away_goals": 1, "winner": "AWAY_TEAM"},
    ]
    score = calculate_form_score(results, "USA")
    print(f"\nForm score for USA (3W 1D 1L): {score:.3f} (expected ~0.65+)")
    assert score > 0.5, "USA with 3W should have form > 0.5"
    print("  [OK] Form analyzer working")

if __name__ == "__main__":
    print("=" * 60)
    print("FIFA 2026 Prediction Tool - Model Tests")
    print("=" * 60)
    test_poisson()
    test_elo()
    test_markets()
    test_form()
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
