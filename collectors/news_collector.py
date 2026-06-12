"""
News collector for team/player sentiment analysis.
Uses NewsAPI (free tier) + GNews + web scraping fallback.
"""
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collectors.base_collector import BaseCollector
from config import NEWS_API_BASE, NEWS_API_KEY, GNEWS_BASE, GNEWS_API_KEY, CACHE_TTL


INJURY_KEYWORDS = [
    "injured", "injury", "fitness doubt", "doubt", "out", "ruled out",
    "miss", "absent", "suspended", "ban", "red card", "hamstring",
    "ankle", "knee", "groin", "calf", "thigh", "muscle", "strain",
    "illness", "ill", "sick", "unavailable", "withdrawn", "not training",
]

POSITIVE_KEYWORDS = [
    "fit", "returns", "back", "ready", "confident", "good form",
    "winning streak", "goals", "assists", "strong", "momentum", "fired up",
    "determined", "rested", "fully fit", "training", "sharp",
]

NEGATIVE_KEYWORDS = [
    "crisis", "row", "argument", "fire", "sacked", "chaos", "disarray",
    "struggling", "poor form", "losing", "booed", "pressure", "crisis",
    "slump", "defeated", "weak", "problems", "issues", "concern",
]


class NewsCollector(BaseCollector):
    def __init__(self):
        super().__init__(base_url=NEWS_API_BASE, rate_limit_delay=1.0)
        self._gnews = BaseCollector(base_url=GNEWS_BASE, rate_limit_delay=1.0)

    @property
    def is_configured(self) -> bool:
        return bool(NEWS_API_KEY or GNEWS_API_KEY)

    def get_team_news(self, team_name: str, days_back: int = 7) -> List[Dict]:
        articles = []

        if NEWS_API_KEY:
            articles.extend(self._fetch_newsapi(team_name, days_back))

        if not articles and GNEWS_API_KEY:
            articles.extend(self._fetch_gnews(team_name))

        # Fallback: try NewsAPI without auth for headlines (limited)
        if not articles:
            articles.extend(self._fetch_public_rss(team_name))

        return articles[:20]

    def get_player_news(self, player_name: str) -> List[Dict]:
        articles = []
        if NEWS_API_KEY:
            articles.extend(self._fetch_newsapi(player_name, days_back=5))
        return articles[:10]

    def get_match_news(self, home_team: str, away_team: str) -> List[Dict]:
        query = f"{home_team} vs {away_team} FIFA World Cup 2026"
        articles = []
        if NEWS_API_KEY:
            articles.extend(self._fetch_newsapi(query, days_back=3))
        if not articles and GNEWS_API_KEY:
            articles.extend(self._fetch_gnews(query))
        return articles[:15]

    def analyze_sentiment(self, articles: List[Dict]) -> Dict:
        """Return sentiment scores from -1 (very negative) to +1 (very positive)."""
        if not articles:
            return {"score": 0.0, "injury_risk": 0.0, "morale": 0.5, "article_count": 0}

        sentiment_scores = []
        injury_count = 0
        positive_count = 0

        for article in articles:
            text = f"{article.get('title', '')} {article.get('description', '')}".lower()

            # Injury detection: require at least 2 strong injury keywords OR 1 specific medical term
            strong_injury_kws = ["injured", "injury", "ruled out", "hamstring", "knee",
                                 "ankle", "groin", "calf", "fracture", "suspended", "ban"]
            weak_injury_kws = ["doubt", "miss", "absent", "unavailable", "withdrawn"]
            medical_terms = ["hamstring", "knee", "ankle", "groin", "calf", "fracture",
                             "surgery", "strain", "muscle", "illness"]

            strong_hits = sum(1 for kw in strong_injury_kws if kw in text)
            has_medical = any(kw in text for kw in medical_terms)
            is_injury = strong_hits >= 2 or (strong_hits >= 1 and has_medical)

            if is_injury:
                injury_count += 1
                sentiment_scores.append(-0.6)
            elif any(kw in text for kw in POSITIVE_KEYWORDS):
                positive_count += 1
                sentiment_scores.append(0.4)
            elif any(kw in text for kw in NEGATIVE_KEYWORDS):
                sentiment_scores.append(-0.3)
            else:
                sentiment_scores.append(0.0)

        avg_score = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
        injury_risk = min(1.0, injury_count / max(len(articles), 1) * 1.5)

        return {
            "score": round(avg_score, 3),
            "injury_risk": round(injury_risk, 3),
            "morale": round((avg_score + 1) / 2, 3),  # 0-1 scale
            "article_count": len(articles),
            "injury_articles": injury_count,
            "positive_articles": positive_count,
        }

    def extract_injured_players(self, articles: List[Dict]) -> List[str]:
        """Extract player names mentioned alongside injury keywords."""
        injured = set()
        injury_pattern = re.compile(
            r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)\s+(?:is\s+)?(?:' +
            '|'.join(re.escape(kw) for kw in INJURY_KEYWORDS[:8]) +
            ')',
            re.IGNORECASE,
        )
        for article in articles:
            text = f"{article.get('title', '')} {article.get('description', '')}"
            for match in injury_pattern.finditer(text):
                injured.add(match.group(1))
        return list(injured)

    def _fetch_newsapi(self, query: str, days_back: int = 7) -> List[Dict]:
        if not NEWS_API_KEY:
            return []
        from_date = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        cache_key = f"newsapi_{query[:30].replace(' ', '_')}_{from_date}"
        data = self.cached_get(
            cache_key,
            "everything",
            params={
                "q": query,
                "from": from_date,
                "sortBy": "publishedAt",
                "language": "en",
                "apiKey": NEWS_API_KEY,
                "pageSize": 20,
            },
            ttl=CACHE_TTL["news"],
        )
        if not data:
            return []
        return [
            {
                "title": a.get("title", ""),
                "description": a.get("description", ""),
                "url": a.get("url", ""),
                "published_at": a.get("publishedAt", ""),
                "source": a.get("source", {}).get("name", ""),
            }
            for a in data.get("articles", [])
        ]

    def _fetch_gnews(self, query: str) -> List[Dict]:
        if not GNEWS_API_KEY:
            return []
        cache_key = f"gnews_{query[:30].replace(' ', '_')}"
        data = self._gnews.cached_get(
            cache_key,
            "search",
            params={
                "q": query,
                "lang": "en",
                "max": 10,
                "token": GNEWS_API_KEY,
            },
            ttl=CACHE_TTL["news"],
        )
        if not data:
            return []
        return [
            {
                "title": a.get("title", ""),
                "description": a.get("description", ""),
                "url": a.get("url", ""),
                "published_at": a.get("publishedAt", ""),
                "source": a.get("source", {}).get("name", ""),
            }
            for a in data.get("articles", [])
        ]

    def _fetch_public_rss(self, query: str) -> List[Dict]:
        """Minimal fallback using a public news search without auth."""
        return []
