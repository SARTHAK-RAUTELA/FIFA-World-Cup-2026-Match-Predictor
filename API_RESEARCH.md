# API Research — Football Data & Predictions for FIFA 2026

> Researched: 2026-06-13. To be integrated in next session.

---

## Plan: What to Add

| Priority | API | Reason | Cost |
|----------|-----|--------|------|
| 1 | `worldcup26.ir` | Free WC 2026 fixture source, no quota, no key | Free |
| 2 | The Odds API | Real bookmaker odds → better value bet detection | Free trial → paid |
| 3 | API-Football `/predictions` endpoint | Built-in prediction as additional model signal | $39/mo Ultra tier |
| 4 | Sportmonks All-In | Best single source: fixtures + lineups + AI predictions + xG + 50+ bookmaker odds | €129/mo |

---

## Tier 1 — Free / No Key Required

### worldcup26.ir (Add this first)
- Community-built open-source API, no API key required
- Covers all 104 FIFA 2026 matches, 48 teams, 12 groups, 16 stadiums
- **Endpoints:**
  - `GET https://worldcup26.ir/get/games` — all matches
  - `GET https://worldcup26.ir/get/groups` — group standings
  - `GET https://worldcup26.ir/get/teams` — all teams
  - `GET https://worldcup26.ir/get/stadiums` — venues
- **GitHub:** https://github.com/rezarahiminia/worldcup2026
- **Use for:** fixture discovery, team lists, standings (can replace/supplement football-data.org)
- **Caveat:** volunteer-maintained, uptime not guaranteed

### OpenFootball World Cup JSON (GitHub)
- Static JSON of all WC 2026 fixtures, groups, squads
- No requests needed — fetch once at startup
- **GitHub:** https://github.com/openfootball/worldcup.json
- **Use for:** static fixture/squad seed data, offline fallback

### OpenLigaDB
- Free public API, no key required
- Covers Bundesliga, Champions League, UEFA Euros, FIFA World Cup
- **Use for:** supplementary WC fixture data

---

## Tier 2 — Freemium / Low Cost

### The Odds API (PRIORITY — add for bookmaker odds)
- Real bookmaker odds from Bet365, Pinnacle, William Hill, etc.
- **Markets:** 1x2, BTTS, Over/Under (2.5, 3.5), Asian Handicap, DNB, Double Chance, corners, half-time
- **Why:** Replaces manual `--odds` entry in CLI; enables automatic value bet detection across all markets
- **Free trial available**
- **Docs:** https://the-odds-api.com/
- **Env var to add:** `THE_ODDS_API_KEY`
- **Example endpoint:** `GET https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup/odds/?apiKey=KEY&markets=h2h,totals,btts`

### API-Football `/predictions` (already partially integrated)
- Returns AI win/draw/loss probabilities directly per match
- **Endpoint:** `GET https://api-football-v1.p.rapidapi.com/v3/predictions?fixture=FIXTURE_ID`
- **Returns:** winner prediction, win %, goals over/under, match advice, comparison stats
- **Current key:** already set as `API_FOOTBALL_KEY` in `.env`
- **Tier required:** Ultra ($39/mo) — free tier does NOT include predictions
- **Use as:** additional signal in composite model (can add as 6th weight alongside poisson/elo/form/player_impact/sentiment)

### live-score-api.com
- Live scores, group standings, lineups, pre-match 1x2 odds
- **Free trial:** 14 days
- **Use for:** live score polling during `--watch` mode
- **Docs:** https://live-score-api.com/world-cup-api/

### WC2026 API on RapidAPI
- FIFA 2026 specific, available on RapidAPI
- Has free and PRO tiers
- **RapidAPI link:** https://rapidapi.com/Emiledaou/api/wc26-live-football-api

---

## Tier 3 — Paid Prediction APIs

### Sportmonks (Best all-in-one if budget allows)
- **What it provides:**
  - Fixtures, live scores, standings, squads, bracket
  - **AI-powered win/draw/loss predictions with probabilities**
  - xG (expected goals) and Pressure Index (proprietary)
  - Pre-match and live odds from **50+ bookmakers, 150+ markets**
  - Player stats, injury status
- **Pricing:**
  - Advanced: €69/mo (or €55/mo yearly) — fixtures, lineups, standings
  - All-In: €129/mo (or €103/mo yearly) — adds predictions, xG, odds
- **Free trial available**
- **Why useful:** Single API that replaces ESPN + Sofascore + The Odds API + a prediction layer
- **Docs:** https://www.sportmonks.com/football-api/world-cup-api/

### OddAlerts (Prediction-focused)
- AI-generated match probabilities: win/draw/loss %
- Value bet detection with edge metrics across multiple markets
- Bookmakers: Bet365, 1xBet, Pinnacle, William Hill
- **Pricing:** £69.99/mo with API access
- **Free trial:** 48 hours, 60 AI analyses per day
- **Why useful:** Returns probabilities directly — could validate/cross-check our Poisson model
- **Docs:** https://www.oddalerts.com/football-data-api

### TheStatsAPI
- Live fixtures, real-time scores, lineups, xG
- Betting odds from Bet365, Pinnacle, Betfair Exchange, Kambi
- Full WC 2026 coverage (all 104 matches, 48 teams, 12 groups)
- Historical World Cup data since 1930
- **Pricing:**
  - Starter: $50/mo — 100k requests/mo
  - Growth: $129/mo — 500k requests/mo
  - Scale: $379/mo — 5M requests/mo
- **Free trial:** 7 days
- **Docs:** https://www.thestatsapi.com/world-cup

---

## Tier 4 — Enterprise (Not Self-Serve)

### Opta / Stats Perform
- Official FIFA World Cup 2026 data distributor (designated Jan 2026)
- Industry-standard stats, deepest data quality available
- **Pricing:** Enterprise only, requires direct sales contact
- **Contact:** https://www.statsperform.com/
- **Not relevant for personal/small project**

---

## Implementation Notes for Tomorrow

### New collector files to create:
1. `collectors/worldcup26_collector.py` — hits `worldcup26.ir` endpoints, no key needed
2. `collectors/odds_api_collector.py` — hits `api.the-odds-api.com`, needs `THE_ODDS_API_KEY`
3. `collectors/api_football_predictions.py` — calls `/v3/predictions`, uses existing `API_FOOTBALL_KEY`

### .env keys to add:
```
THE_ODDS_API_KEY=your_key_here
```

### config.py additions needed:
```python
THE_ODDS_API_BASE = "https://api.the-odds-api.com/v4"
WORLDCUP26_BASE = "https://worldcup26.ir/get"
```

### Composite model change (if API-Football predictions added):
```python
MODEL_WEIGHTS = {
    "poisson":           0.35,  # was 0.40
    "elo":               0.20,  # was 0.25
    "form":              0.18,  # was 0.20
    "player_impact":     0.10,  # unchanged
    "sentiment":         0.05,  # unchanged
    "api_prediction":    0.12,  # NEW — API-Football /predictions signal
}
```

---

## Quick Reference: What Each Existing API Already Covers

| API | Already in project | What it covers |
|-----|-------------------|----------------|
| ESPN (no key) | Yes | Fixtures, lineups, live scores, form |
| football-data.org | Yes | WC fixtures, standings, form |
| API-Football (RapidAPI) | Yes | Stats, H2H — predictions need Ultra tier |
| Sofascore (sportapi7 RapidAPI) | Yes | Confirmed lineups, bookmaker odds (5 markets) |
| TheSportsDB | Yes | Match details, player stats |
| NewsAPI | Yes | Injury/team news |
| GNews | Yes | Injury/team news |
| Open-Meteo (no key) | Yes | Weather at venue |
| worldcup26.ir | **Not yet** | WC 2026 fixtures, groups, teams |
| The Odds API | **Not yet** | Full bookmaker odds, all markets |
| API-Football /predictions | **Not yet** | Direct AI win probability |
