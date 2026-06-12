"""Discover API-Football endpoints and today's matches."""
from dotenv import load_dotenv
load_dotenv()
from collectors.api_football_collector import APIFootballCollector
from datetime import date

apif = APIFootballCollector()
print("Configured:", apif.is_configured)

# Try getting today's fixtures without league filter to see what comes back
today = date.today().strftime("%Y-%m-%d")
print(f"Checking date: {today}")

# Try the status=live endpoint to see what's happening
data = apif.get("fixtures", params={"date": today})
if data:
    total = data.get("results", 0)
    print(f"Total fixtures today (all leagues): {total}")
    resp = data.get("response", [])
    # Find any football/soccer
    wc_matches = [f for f in resp if "World Cup" in str(f.get("league", {}).get("name", ""))
                  or "FIFA" in str(f.get("league", {}).get("name", ""))]
    print(f"World Cup matches: {len(wc_matches)}")
    for f in wc_matches[:5]:
        print(f"  ID={f['fixture']['id']}  {f['teams']['home']['name']} vs {f['teams']['away']['name']}  League={f['league']['name']}  LeagueID={f['league']['id']}")

    if not wc_matches and resp:
        print("Sample leagues found today:")
        seen = set()
        for f in resp[:50]:
            lid = f.get("league", {}).get("id")
            lname = f.get("league", {}).get("name", "")
            if lid not in seen:
                seen.add(lid)
                print(f"  League ID={lid}  {lname}")
else:
    print("No response from API")
    # Check headers
    import requests
    from config import API_FOOTBALL_KEY
    r = requests.get(
        "https://api-football-v1.p.rapidapi.com/v3/status",
        headers={"X-RapidAPI-Key": API_FOOTBALL_KEY, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"},
        timeout=10
    )
    print(f"Status check: HTTP {r.status_code}")
    if r.status_code == 200:
        j = r.json()
        print("Account:", j.get("response", {}).get("account", {}))
        print("Requests:", j.get("response", {}).get("requests", {}))
