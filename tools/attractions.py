"""OpenTripMap wrapper — free tier, needs an email-signup API key.
Get your key at https://opentripmap.io/product
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()


def get_attractions(lat: float, lon: float, radius: int = 5000, limit: int = 10) -> list:
    """Fetch top attractions near a point, with descriptions.

    Escalates the search radius if the first attempt comes back empty or
    very sparse — this matters for destinations that are spread over a wide
    area (e.g. island chains like Andaman) where a tight 5km radius around
    the geocoded centroid can miss everything.
    """
    key = os.getenv("OPENTRIPMAP_API_KEY")
    if not key:
        raise EnvironmentError("OPENTRIPMAP_API_KEY missing from .env")

    url = "https://api.opentripmap.com/0.1/en/places/radius"

    places = []
    for try_radius in (radius, 20000, 60000):
        params = {"radius": try_radius, "lon": lon, "lat": lat, "limit": limit, "apikey": key}
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        places = r.json().get("features", [])
        if len(places) >= 3:
            break  # good enough, stop escalating

    results = []
    for place in places[:limit]:
        xid = place["properties"]["xid"]
        detail_url = f"https://api.opentripmap.com/0.1/en/places/xid/{xid}"
        detail = requests.get(detail_url, params={"apikey": key}, timeout=15).json()

        name = detail.get("name", "").strip()
        if not name:
            continue  # skip unnamed points — not useful for an itinerary or map

        point = detail.get("point", {}) or {}
        results.append(
            {
                "name": name,
                "kinds": detail.get("kinds", ""),
                "description": (detail.get("wikipedia_extracts", {}) or {}).get("text", "")[:300],
                "rating": detail.get("rate", 0),
                "lat": point.get("lat"),
                "lon": point.get("lon"),
                "image": (detail.get("preview", {}) or {}).get("source", ""),
            }
        )
    return results


if __name__ == "__main__":
    print(get_attractions(26.9124, 75.7873, limit=5))  # Jaipur
