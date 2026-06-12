"""
Weather data collector using Open-Meteo API.
100% free, no API key required.
Weather impacts match play: rain reduces goals, wind affects passing.
"""
from typing import Optional, Dict
from collectors.base_collector import BaseCollector
from config import OPEN_METEO_BASE, CACHE_TTL


# FIFA 2026 host city coordinates
HOST_CITY_COORDS = {
    "New York": (40.7128, -74.0060),
    "Los Angeles": (34.0522, -118.2437),
    "Dallas": (32.7767, -96.7970),
    "San Francisco": (37.7749, -122.4194),
    "Seattle": (47.6062, -122.3321),
    "Boston": (42.3601, -71.0589),
    "Miami": (25.7617, -80.1918),
    "Atlanta": (33.7490, -84.3880),
    "Kansas City": (39.0997, -94.5786),
    "Philadelphia": (39.9526, -75.1652),
    "Houston": (29.7604, -95.3698),
    "Toronto": (43.6532, -79.3832),
    "Vancouver": (49.2827, -123.1207),
    "Guadalajara": (20.6597, -103.3496),
    "Mexico City": (19.4326, -99.1332),
    "Monterrey": (25.6866, -100.3161),
}

# Default to Dallas (main venue)
DEFAULT_CITY = "Dallas"


class WeatherCollector(BaseCollector):
    def __init__(self):
        super().__init__(base_url=OPEN_METEO_BASE, rate_limit_delay=0.2)

    def get_match_weather(self, city: str, match_date: str, match_hour: int = 20) -> Optional[Dict]:
        """Get weather forecast for a match location and time."""
        coords = self._get_coords(city)
        if not coords:
            coords = HOST_CITY_COORDS[DEFAULT_CITY]

        lat, lon = coords
        cache_key = f"weather_{city.lower().replace(' ', '_')}_{match_date}"
        data = self.cached_get(
            cache_key,
            "forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "hourly": "temperature_2m,precipitation,wind_speed_10m,relative_humidity_2m,weather_code",
                "start_date": match_date,
                "end_date": match_date,
                "timezone": "America/New_York",
                "wind_speed_unit": "kmh",
            },
            ttl=CACHE_TTL["weather"],
        )
        if not data:
            return None
        return self._parse_weather(data, match_hour)

    def _get_coords(self, city: str) -> Optional[tuple]:
        # Fuzzy match city name
        city_lower = city.lower()
        for known_city, coords in HOST_CITY_COORDS.items():
            if known_city.lower() in city_lower or city_lower in known_city.lower():
                return coords
        return None

    def _parse_weather(self, data: Dict, target_hour: int) -> Dict:
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        precip = hourly.get("precipitation", [])
        wind = hourly.get("wind_speed_10m", [])
        humidity = hourly.get("relative_humidity_2m", [])
        codes = hourly.get("weather_code", [])

        # Find the hour closest to match time
        idx = 0
        for i, t in enumerate(times):
            try:
                hour = int(t.split("T")[1][:2])
                if hour == target_hour:
                    idx = i
                    break
            except (IndexError, ValueError):
                continue

        temp = temps[idx] if idx < len(temps) else 22.0
        rain = precip[idx] if idx < len(precip) else 0.0
        wind_speed = wind[idx] if idx < len(wind) else 10.0
        hum = humidity[idx] if idx < len(humidity) else 50.0
        code = codes[idx] if idx < len(codes) else 0

        return {
            "temperature_c": temp,
            "precipitation_mm": rain,
            "wind_speed_kmh": wind_speed,
            "humidity_pct": hum,
            "weather_code": code,
            "description": self._weather_description(code),
            "impact_factor": self._calculate_impact(rain, wind_speed, temp),
        }

    def _weather_description(self, code: int) -> str:
        if code == 0:
            return "Clear sky"
        elif code <= 3:
            return "Partly cloudy"
        elif code <= 9:
            return "Fog"
        elif code <= 19:
            return "Drizzle"
        elif code <= 29:
            return "Rain"
        elif code <= 39:
            return "Snow"
        elif code <= 49:
            return "Freezing rain"
        elif code <= 59:
            return "Heavy drizzle"
        elif code <= 69:
            return "Heavy rain"
        elif code <= 79:
            return "Heavy snow"
        elif code <= 84:
            return "Rain showers"
        elif code <= 94:
            return "Thunderstorm"
        else:
            return "Heavy thunderstorm"

    def _calculate_impact(self, rain_mm: float, wind_kmh: float, temp_c: float) -> float:
        """
        Returns a multiplier for expected goals.
        Heavy rain/wind = fewer goals (lower λ).
        Range: 0.75 to 1.05
        """
        factor = 1.0

        # Rain impact (heavy rain significantly reduces goal-scoring)
        if rain_mm > 10:
            factor -= 0.20
        elif rain_mm > 5:
            factor -= 0.10
        elif rain_mm > 2:
            factor -= 0.05

        # Wind impact (strong wind reduces passing accuracy)
        if wind_kmh > 50:
            factor -= 0.10
        elif wind_kmh > 35:
            factor -= 0.05

        # Extreme temperature impact
        if temp_c > 38 or temp_c < 5:
            factor -= 0.05

        return round(max(0.75, min(1.05, factor)), 3)
