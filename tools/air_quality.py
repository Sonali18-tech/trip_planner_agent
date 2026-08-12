"""Open-Meteo Air Quality wrapper — free, no signup, no API key needed."""
import requests


def _aqi_category(aqi: float) -> str:
    """US AQI breakpoints."""
    if aqi is None:
        return "Unknown"
    if aqi <= 50:
        return "Good"
    if aqi <= 100:
        return "Moderate"
    if aqi <= 150:
        return "Unhealthy for sensitive groups"
    if aqi <= 200:
        return "Unhealthy"
    if aqi <= 300:
        return "Very unhealthy"
    return "Hazardous"


def get_air_quality(lat: float, lon: float, days: int = 7) -> list:
    """Return a list of daily average US AQI values."""
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "us_aqi",
        "forecast_days": min(days, 7),  # this API caps at 7 days
        "timezone": "auto",
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    hourly = r.json().get("hourly", {})

    times = hourly.get("time", [])
    aqi_values = hourly.get("us_aqi", [])
    if not times:
        return []

    # bucket hourly readings into daily averages
    daily = {}
    for t, v in zip(times, aqi_values):
        date = t[:10]
        if v is None:
            continue
        daily.setdefault(date, []).append(v)

    return [
        {
            "date": date,
            "aqi": round(sum(vals) / len(vals)),
            "category": _aqi_category(sum(vals) / len(vals)),
        }
        for date, vals in daily.items()
    ]


if __name__ == "__main__":
    print(get_air_quality(28.6139, 77.2090, days=3))  # Delhi
