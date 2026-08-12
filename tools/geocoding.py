"""Nominatim (OpenStreetMap) wrapper — free, no signup, no API key needed.
Rate limit: max 1 request per second (be a polite citizen of the free service).
"""
import requests


def get_coordinates(city: str) -> dict:
    """Convert a city name into latitude/longitude."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": city, "format": "json", "limit": 1}
    headers = {"User-Agent": "TripPlannerApp/1.0 student-project"}

    r = requests.get(url, params=params, headers=headers, timeout=15)
    r.raise_for_status()
    results = r.json()

    if not results:
        raise ValueError(f"Could not find coordinates for '{city}'. Check spelling.")

    result = results[0]
    return {
        "lat": float(result["lat"]),
        "lon": float(result["lon"]),
        "display_name": result["display_name"],
    }


if __name__ == "__main__":
    print(get_coordinates("Jaipur"))
