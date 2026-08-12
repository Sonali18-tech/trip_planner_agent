"""Agent 3 — Attractions & food.

Fetches top tourist attractions near the destination from OpenTripMap.
"""
from tools.attractions import get_attractions


def attractions_node(state: dict) -> dict:
    dest = state["destination_info"]
    places = get_attractions(dest["lat"], dest["lon"], limit=15)

    # simple interest filter — keep everything if no interests given
    interests = state["preferences"].get("interests", [])
    if interests:
        filtered = [
            p for p in places
            if any(i.lower() in p["kinds"].lower() for i in interests)
        ]
        places = filtered or places  # fall back to full list if filter empties it

    return {**state, "attractions": places}
