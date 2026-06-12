"""Test all configured API keys."""
import os, sys
os.environ["PYTHONIOENCODING"] = "utf-8"

from datetime import date
from dotenv import load_dotenv
load_dotenv()

from collectors.football_data_collector import FootballDataCollector
from collectors.api_football_collector import APIFootballCollector
from collectors.news_collector import NewsCollector
from collectors.weather_collector import WeatherCollector

print("=" * 60)
print("API KEY CONNECTIVITY TEST")
print("=" * 60)

# 1. football-data.org
print("\n[1] football-data.org")
fd = FootballDataCollector()
print(f"    Configured: {fd.is_configured}")
if fd.is_configured:
    fixtures = fd.get_today_fixtures(date.today())
    print(f"    Today's WC fixtures: {len(fixtures)}")
    for f in fixtures:
        print(f"      - {f['home_team']} vs {f['away_team']}  [{f.get('status','?')}]  {f.get('date','')[:16]}")
    if not fixtures:
        print("    (no fixtures today or API returned empty)")

# 2. API-Football RapidAPI
print("\n[2] API-Football (RapidAPI)")
apif = APIFootballCollector()
print(f"    Configured: {apif.is_configured}")
if apif.is_configured:
    fixtures2 = apif.get_fixtures(date.today())
    print(f"    Today's fixtures: {len(fixtures2)}")
    for f in fixtures2[:5]:
        print(f"      - {f['home_team']} vs {f['away_team']}")

# 3. NewsAPI
print("\n[3] NewsAPI")
from config import NEWS_API_KEY
print(f"    Configured: {bool(NEWS_API_KEY)}")
if NEWS_API_KEY:
    nc = NewsCollector()
    arts = nc.get_team_news("USA FIFA World Cup", days_back=5)
    print(f"    Articles found: {len(arts)}")
    if arts:
        print(f"    Latest: {arts[0].get('title','')[:75]}...")
        sentiment = nc.analyze_sentiment(arts)
        print(f"    Sentiment score: {sentiment['score']}  Morale: {sentiment['morale']}  Injury risk: {sentiment['injury_risk']}")

# 4. GNews
print("\n[4] GNews")
from config import GNEWS_API_KEY
print(f"    Configured: {bool(GNEWS_API_KEY)}")

# 5. Weather (free, no key)
print("\n[5] Open-Meteo (weather - no key needed)")
wc = WeatherCollector()
w = wc.get_match_weather("Dallas", date.today().isoformat())
if w:
    print(f"    Dallas weather: {w['description']}, {w['temperature_c']}C, wind {w['wind_speed_kmh']}kmh")
    print(f"    Goals impact factor: {w['impact_factor']}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
