"""Open-Meteo wrapper — free, no signup, no API key needed."""
from datetime import date, timedelta
import requests

# WMO weather codes -> short human label + emoji
WEATHER_CODE_MAP = {
    0: ("Clear sky", "☀️"), 1: ("Mainly clear", "🌤️"), 2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"), 45: ("Fog", "🌫️"), 48: ("Fog", "🌫️"),
    51: ("Light drizzle", "🌦️"), 53: ("Drizzle", "🌦️"), 55: ("Dense drizzle", "🌧️"),
    61: ("Light rain", "🌦️"), 63: ("Rain", "🌧️"), 65: ("Heavy rain", "🌧️"),
    71: ("Light snow", "🌨️"), 73: ("Snow", "🌨️"), 75: ("Heavy snow", "❄️"),
    80: ("Rain showers", "🌦️"), 81: ("Rain showers", "🌧️"), 82: ("Violent showers", "⛈️"),
    95: ("Thunderstorm", "⛈️"), 96: ("Thunderstorm w/ hail", "⛈️"), 99: ("Severe thunderstorm", "⛈️"),
}

DAILY_FIELDS = (
    "temperature_2m_max,temperature_2m_min,apparent_temperature_max,"
    "apparent_temperature_min,precipitation_sum,precipitation_probability_max,"
    "windspeed_10m_max,relative_humidity_2m_max,weathercode"
)


def _describe(code: int) -> tuple:
    return WEATHER_CODE_MAP.get(code, ("Unknown", "❓"))


def _fetch(params: dict) -> dict:
    r = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=15)
    r.raise_for_status()
    return r.json()["daily"]


def _parse(data: dict, days: int) -> list:
    results = []
    for i in range(len(data["time"])):
        code = data["weathercode"][i]
        label, icon = _describe(code)
        results.append(
            {
                "date": data["time"][i],
                "max_temp": data["temperature_2m_max"][i],
                "min_temp": data["temperature_2m_min"][i],
                "feels_like_max": data["apparent_temperature_max"][i],
                "feels_like_min": data["apparent_temperature_min"][i],
                "rain_mm": data["precipitation_sum"][i],
                "rain_chance_pct": data.get("precipitation_probability_max", [None] * days)[i],
                "humidity_pct": data.get("relative_humidity_2m_max", [None] * days)[i],
                "wind_kmh": data.get("windspeed_10m_max", [None] * days)[i],
                "condition": label,
                "icon": icon,
                "rainy": data["precipitation_sum"][i] > 5,
            }
        )
    return results


def get_weather_forecast(lat: float, lon: float, days: int = 7, start_date: str = None) -> dict:
    """Return {'forecast': [...], 'forecast_available': bool}.

    Tries to fetch weather for the exact trip dates first. If that request
    fails for any reason (Open-Meteo rejects the date range, dates too far
    out, transient error, etc.) it falls back to a plain N-day forecast
    starting today rather than crashing the whole trip-planning pipeline.
    """
    base_params = {"latitude": lat, "longitude": lon, "daily": DAILY_FIELDS, "timezone": "auto"}

    forecast_available = True
    if start_date:
        try:
            trip_start = date.fromisoformat(start_date)
            if (trip_start - date.today()).days > 15:
                forecast_available = False
        except ValueError:
            start_date = None

    if forecast_available and start_date:
        trip_start = date.fromisoformat(start_date)
        trip_end = trip_start + timedelta(days=days - 1)
        try:
            data = _fetch({**base_params, "start_date": trip_start.isoformat(), "end_date": trip_end.isoformat()})
            return {"forecast": _parse(data, days), "forecast_available": True}
        except requests.exceptions.HTTPError:
            # Open-Meteo rejected the date-range request (e.g. dates outside
            # what it'll serve right now) — fall back below instead of failing.
            forecast_available = False

    data = _fetch({**base_params, "forecast_days": days})
    return {"forecast": _parse(data, days), "forecast_available": forecast_available}


if __name__ == "__main__":
    # Quick manual test: python tools/weather.py
    result = get_weather_forecast(28.6139, 77.2090, days=3)  # Delhi
    for day in result["forecast"]:
        print(day)
