"""Open-Meteo wrapper — free, no signup, no API key needed."""
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


def _describe(code: int) -> tuple:
    return WEATHER_CODE_MAP.get(code, ("Unknown", "❓"))


def get_weather_forecast(lat: float, lon: float, days: int = 7, start_date: str = None) -> dict:
    """Return {'forecast': [...], 'forecast_available': bool}.

    Open-Meteo only forecasts ~16 days ahead. If start_date falls further out,
    we can't get real numbers for those exact days, so we say so instead of
    silently showing today's weather mislabeled as the trip dates.
    """
    from datetime import date, timedelta

    forecast_available = True
    if start_date:
        try:
            trip_start = date.fromisoformat(start_date)
            if (trip_start - date.today()).days > 15:
                forecast_available = False
        except ValueError:
            pass

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": (
            "temperature_2m_max,temperature_2m_min,apparent_temperature_max,"
            "apparent_temperature_min,precipitation_sum,precipitation_probability_max,"
            "windspeed_10m_max,relative_humidity_2m_max,weathercode"
        ),
        "timezone": "auto",
    }
    if forecast_available and start_date:
        trip_start = date.fromisoformat(start_date)
        trip_end = trip_start + timedelta(days=days - 1)
        params["start_date"] = trip_start.isoformat()
        params["end_date"] = trip_end.isoformat()
    else:
        params["forecast_days"] = days

    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()["daily"]

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
    return {"forecast": results, "forecast_available": forecast_available}


if __name__ == "__main__":
    # Quick manual test: python tools/weather.py
    result = get_weather_forecast(28.6139, 77.2090, days=3)  # Delhi
    for day in result["forecast"]:
        print(day)
