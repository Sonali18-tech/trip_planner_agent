"""Open-Meteo wrapper — free, no signup, no API key needed."""
import requests


def get_weather_forecast(lat: float, lon: float, days: int = 7) -> list:
    """Return a list of daily weather dicts for the given coordinates."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
        "forecast_days": days,
        "timezone": "auto",
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()["daily"]

    return [
        {
            "date": data["time"][i],
            "max_temp": data["temperature_2m_max"][i],
            "min_temp": data["temperature_2m_min"][i],
            "rain_mm": data["precipitation_sum"][i],
            "rainy": data["precipitation_sum"][i] > 5,
        }
        for i in range(len(data["time"]))
    ]


if __name__ == "__main__":
    # Quick manual test: python tools/weather.py
    forecast = get_weather_forecast(28.6139, 77.2090, days=3)  # Delhi
    for day in forecast:
        print(day)
