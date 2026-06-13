# FIFA 2026 Match Prediction Tool

A Python CLI tool that predicts betting market outcomes for FIFA 2026 World Cup matches using a composite mathematical model combining ELO ratings, Poisson goal distribution, Dixon-Coles correction, recent form analysis, player impact scoring, and live lineup data from multiple sports APIs.

---

## Table of Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
  - [Data Collection Layer](#data-collection-layer)
  - [Mathematical Models](#mathematical-models)
  - [Prediction Markets](#prediction-markets)
  - [Confidence Scoring](#confidence-scoring)
  - [Live Monitoring](#live-monitoring)
- [Project Structure](#project-structure)
- [Setup](#setup)
  - [Requirements](#requirements)
  - [Installation](#installation)
  - [API Keys](#api-keys)
- [Usage](#usage)
  - [Quick Start (Windows)](#quick-start-windows)
  - [CLI Commands](#cli-commands)
- [Configuration](#configuration)
- [Model Weights](#model-weights)
- [ELO Ratings](#elo-ratings)
- [Confidence Levels](#confidence-levels)
- [Caching](#caching)

---

## Overview

This tool predicts the following betting markets for any FIFA 2026 World Cup match:

| Market | Description |
|--------|-------------|
| **1x2** | Home win / Draw / Away win probabilities |
| **BTTS** | Both Teams to Score (Yes/No) |
| **Asian Handicap** | Spread-adjusted win probability |
| **Asian Total** | Over/Under goal totals (2.5, 3.5) |
| **Draw No Bet (DNB)** | 1x2 with draw refunded |
| **Double Chance** | Home/Draw, Away/Draw combinations |
| **Correct Score** | Most probable exact scorelines |
| **First Goal** | Which team scores first |
| **Half-Time Result** | 1x2 at half time |

It also detects **value bets** by comparing model probabilities against bookmaker odds (when provided), highlighting markets where the implied probability is lower than the model's estimate.

---

## How It Works

### Data Collection Layer

The tool aggregates data from multiple free and RapidAPI sources. Each collector inherits from `BaseCollector` (`collectors/base_collector.py`) which provides:

- **Rate limiting** — configurable per-collector delay between requests
- **Automatic retry** — exponential back-off on 5xx errors, respects `Retry-After` on 429
- **Thread-safe TTL cache** — all responses cached in memory via `DataCache` (`data/cache.py`)

**Active collectors:**

| Collector | Source | Data provided |
|-----------|--------|---------------|
| `ESPNCollector` | ESPN public API (no key) | Fixtures, lineups, live scores, team form |
| `SportsDbCollector` | TheSportsDB (free key `"3"`) | Match details, player stats |
| `SofascoreCollector` | sportapi7.p.rapidapi.com | Confirmed starting XIs, formations, 5-market bookmaker odds |
| `FootballDataCollector` | api.football-data.org | WC fixtures, standings, form for tracked leagues |
| `APIFootballCollector` | api-football-v1.p.rapidapi.com | Team stats, H2H records |
| `NewsCollector` | NewsAPI + GNews | Injury news, team sentiment analysis |
| `WeatherCollector` | Open-Meteo (no key) | Match-day weather at venue city |

All collectors are orchestrated by a `DataAggregator` that fans out requests, merges results, and resolves conflicts (e.g., ESPN fixture IDs mapped to Sofascore IDs for lineup lookup).

---

### Mathematical Models

#### 1. ELO Rating Model (`models/elo_model.py`)

Pre-seeded ratings for all 72+ FIFA 2026 qualified teams, calibrated from FIFA world rankings and WC qualifying results.

**Win probability** uses the standard ELO formula with a sigmoid-based draw model:

```
expected_score(A, B) = 1 / (1 + 10^((ELO_B - ELO_A - home_bonus) / 400))

draw_probability = max(0.10, 0.28 × exp(-|ELO_diff| / 600))
```

Home advantage adds **+100 ELO points** (configurable via `HOME_ADVANTAGE_FACTOR`). All FIFA 2026 venues are treated as neutral-site (USA/Canada/Mexico), so this bonus is suppressed.

**Expected goals from ELO:**

```
home_xG = avg_goals × (0.4 + 0.5 × expected_score)
away_xG = avg_goals × (0.4 + 0.5 × (1 - expected_score))
```

**ELO updates** after each match use goal-difference multipliers (1.0 for 1-goal wins, 1.5 for 2-goal wins, 1.75+ for 3+ goals) and stage-based K-factors (40 for group stage, up to 65 for the final). Updated ratings persist to `data/elo_state.json` so predictions improve throughout the tournament.

#### 2. Poisson Goal Distribution

Given home λ and away λ (expected goals) from the ELO/form composite:

```
P(home scores h goals) = e^(-λ_home) × λ_home^h / h!
P(away scores a goals) = e^(-λ_away) × λ_away^a / a!
```

The full score matrix is computed up to `MAX_GOALS` (default 8) goals per team, giving exact probabilities for every possible scoreline.

#### 3. Dixon-Coles Correction

Low-scoring outcomes (0-0, 1-0, 0-1, 1-1) are adjusted using the Dixon-Coles correlation parameter `ρ = -0.13`:

```
P(0,0) ×= 1 - λ_home × λ_away × ρ
P(1,0) ×= 1 + λ_away × ρ
P(0,1) ×= 1 + λ_home × ρ
P(1,1) ×= 1 - ρ
```

This corrects for the empirical observation that 1-1 draws are less likely and 1-0/0-1 results more likely than pure Poisson predicts.

#### 4. Form Analyzer

Pulls the last 5–10 results for each team from ESPN/football-data.org and computes a weighted form score where recent results count more. The form delta is used to adjust the base ELO-derived λ values before Poisson is applied.

#### 5. Player Impact Model (`models/player_impact.py`)

Adjusts λ values based on lineup confirmation:

- Each team has a known key-player list with position and importance score (0–1)
- Position roles define attack/defense impact weights (e.g., a GK absence reduces `defense_multiplier` by up to 15%)
- If a key player is missing from the confirmed lineup (or named in injury news), attack and/or defense multipliers are reduced
- Caps: max 35% attack reduction, max 30% defense reduction

Example: If Mbappe is confirmed absent for France, `attack_multiplier` drops ~0.15 × 1.0 (his importance) = 15%, reducing France's λ_home proportionally.

#### 6. Composite Model

The five signals are blended with configurable weights:

| Signal | Default weight |
|--------|---------------|
| Poisson xG | 40% |
| ELO win probability | 25% |
| Recent form | 20% |
| Player impact | 10% |
| News sentiment | 5% |

---

### Prediction Markets

All markets are derived from the score matrix:

**1x2**
```
P(home win) = sum of P(h,a) where h > a
P(draw)     = sum of P(h,a) where h == a
P(away win) = sum of P(h,a) where h < a
```

**BTTS Yes** = `P(home ≥ 1) × P(away ≥ 1)`

**Asian Total 2.5 Over** = `sum of P(h,a) where h+a > 2`

**Asian Handicap** — the home team's handicap line is set from the ELO difference; the probability is the adjusted 1x2 after applying the goal offset to the score matrix.

**Correct Score** — top 5 most probable exact scorelines from the full matrix.

**Draw No Bet** — home_win / (home_win + away_win) and away_win / (home_win + away_win).

**Value bet detection** — for each market where bookmaker odds are provided, the model computes implied probability and flags value if:
```
model_probability > (1 / bookmaker_odds) × 1.03
```
(3% edge threshold to account for bookmaker margin)

---

### Confidence Scoring

The overall prediction confidence is a weighted combination of:

| Factor | Contributes when |
|--------|-----------------|
| ELO gap between teams | Larger gap → higher base confidence |
| Lineup confirmation status | Confirmed XIs add ~15–25% |
| Form data availability | Recent matches available |
| Data source agreement | ESPN + football-data.org agree on same fixture |
| News sentiment signal | Injury/suspension news present |

Typical ranges:
- **~29%** — no lineup data, only ELO + form
- **~45%** — unconfirmed lineup from Sofascore
- **~50–55%** — confirmed lineup (released ~1 hour before kickoff)
- **93%+** — extreme favorites with confirmed lineups (threshold for auto-display)

The default `MIN_CONFIDENCE_THRESHOLD` is **93%**. Predictions below this threshold show a summary line only; use `--all` or `--threshold N` to override.

---

### Live Monitoring

`LiveMonitor` (`collectors/live_monitor.py`) runs a background thread that polls APIs for lineup changes and re-runs predictions when the starting XI changes.

Polling interval adapts to time until kickoff:

| Time to kickoff | Poll interval |
|-----------------|--------------|
| > 2 hours | 120 seconds |
| 1–2 hours | 60 seconds |
| 30–60 minutes | 60 seconds |
| < 30 minutes | 30 seconds |
| Match started | 300 seconds |

When a change is detected (player added/removed from lineup, confidence delta > 2%), the terminal displays an alert and re-renders the full prediction panel if confidence crosses the threshold.

---

## Project Structure

```
prediction-Testing/
├── main.py                   # CLI entry point (argparse)
├── launcher.py               # Interactive double-click launcher
├── FIFA_Predictor.bat        # Windows launcher (sets UTF-8, opens terminal)
├── config.py                 # All settings, API URLs, ELO ratings, weights
├── requirements.txt
├── .env                      # API keys (not committed)
├── .env.example              # Key names and registration links
│
├── collectors/
│   ├── base_collector.py     # Rate limiting, retry, cached_get
│   ├── espn_collector.py     # ESPN public API — fixtures, lineups, form
│   ├── sports_db_collector.py# TheSportsDB — match details, player stats
│   └── live_monitor.py       # Background lineup polling thread
│
├── models/
│   ├── elo_model.py          # ELO ratings, win probability, xG from ELO
│   └── player_impact.py      # Key-player absence → λ adjustment
│
├── prediction/
│   └── engine.py             # PredictionEngine — orchestrates all models
│
├── display/
│   └── formatter.py          # Rich terminal tables, panels, alerts
│
└── data/
    ├── cache.py              # Thread-safe in-memory TTL cache (DataCache)
    └── elo_state.json        # Persisted ELO ratings (auto-updated)
```

---

## Setup

### Requirements

- Python 3.11+
- Windows (for `.bat` launcher; `main.py` works on any OS)

### Installation

```bash
# Clone the repo
git clone <repo-url>
cd prediction-Testing

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy env template and fill in API keys
copy .env.example .env
```

### API Keys

Edit `.env` and set the following keys. All have free tiers sufficient for daily use.

| Variable | Source | Free tier |
|----------|--------|-----------|
| `FOOTBALL_DATA_API_KEY` | [football-data.org](https://www.football-data.org/client/register) | Unlimited WC access |
| `API_FOOTBALL_KEY` | [RapidAPI — api-football](https://rapidapi.com/api-sports/api/api-football) | 100 req/day |
| `NEWS_API_KEY` | [newsapi.org](https://newsapi.org/register) | 100 req/day |
| `GNEWS_API_KEY` | [gnews.io](https://gnews.io/) | 100 req/day |
| `SPORTS_DB_API_KEY` | TheSportsDB | Use `3` for free tier |

The `API_FOOTBALL_KEY` (RapidAPI key) is shared between `api-football-v1.p.rapidapi.com` and `sportapi7.p.rapidapi.com` (Sofascore). Both services are accessed via the same key.

ESPN and Open-Meteo require no API key.

---

## Usage

### Quick Start (Windows)

Double-click **`FIFA_Predictor.bat`** — opens a 180×50 terminal, sets UTF-8 encoding, and launches the interactive `launcher.py` menu.

### CLI Commands

```bash
# Predict all of today's FIFA 2026 matches
python main.py

# Predict matches on a specific date
python main.py --date 2026-06-15

# Predict a specific match
python main.py --match "USA" "Paraguay"

# Enter bookmaker odds for value bet detection
python main.py --match "France" "Brazil" --odds

# Show all predictions regardless of confidence threshold
python main.py --all

# Lower the confidence threshold to 40%
python main.py --threshold 40

# Predict today's matches then watch for lineup changes
python main.py --watch
```

**`--watch` mode** keeps the process alive, polls for lineup changes every 30–120 seconds, and re-renders predictions when lineups change. Press `Ctrl+C` to exit.

---

## Configuration

All tunable parameters live in `.env` (overrides) and `config.py` (defaults):

| Setting | Default | Description |
|---------|---------|-------------|
| `MIN_CONFIDENCE_THRESHOLD` | `93.0` | Below this %, show summary only |
| `DATA_REFRESH_INTERVAL` | `300` s | General data refresh interval |
| `PRE_MATCH_REFRESH_INTERVAL` | `60` s | Refresh interval 1–2 hrs before kickoff |
| `LINEUP_REFRESH_INTERVAL` | `120` s | Default lineup poll interval |
| `MAX_GOALS_PREDICTION` | `8` | Score matrix size (h,a each 0–8) |
| `HOME_ADVANTAGE_FACTOR` | `1.15` | ELO home bonus (suppressed for neutral WC venues) |
| `DIXON_COLES_RHO` | `-0.13` | Low-score correction parameter |

---

## Model Weights

```python
MODEL_WEIGHTS = {
    "poisson":        0.40,   # Poisson score matrix
    "elo":            0.25,   # ELO win probability
    "form":           0.20,   # Recent 5–10 match form
    "player_impact":  0.10,   # Key player availability
    "sentiment":      0.05,   # News/injury sentiment
}
```

Weights can be adjusted in `config.py` without changing any model code.

---

## ELO Ratings

All 72+ teams are pre-seeded in `config.py` under `FIFA_2026_ELO_RATINGS`. Selected ratings:

| Team | ELO | Region |
|------|-----|--------|
| Argentina | 2095 | CONMEBOL |
| France | 2065 | UEFA |
| Brazil | 2045 | CONMEBOL |
| England | 2025 | UEFA |
| Spain | 2015 | UEFA |
| Germany | 2000 | UEFA |
| Portugal | 1980 | UEFA |
| USA | 1845 | CONCACAF |
| Morocco | 1840 | CAF |
| Japan | 1830 | AFC |
| Mexico | 1880 | CONCACAF |

Ratings update automatically after each predicted match (if `--watch` is running or results are fed in) and persist to `data/elo_state.json`.

---

## Caching

`DataCache` (`data/cache.py`) is an in-memory, thread-safe TTL cache shared across all collectors. TTLs:

| Data type | TTL |
|-----------|-----|
| Fixtures | 1 hour |
| Lineups | 2 minutes |
| Form | 2 hours |
| H2H records | 24 hours |
| News | 30 minutes |
| Weather | 1 hour |
| Standings | 2 hours |
| Player stats | 4 hours |

Cache is per-session (not persisted to disk). Restarting the tool clears all cached data.
