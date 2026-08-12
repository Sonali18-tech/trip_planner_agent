"""Agent 1 — Preference intake.

In this build, preferences arrive already-structured from the FastAPI request
body (see api/schemas.py). This node just validates/normalizes them and puts
them on the shared state so downstream agents can rely on consistent fields.
"""


def intake_node(state: dict) -> dict:
    prefs = state["preferences"]

    # normalize a couple of fields defensively
    prefs["destination"] = prefs["destination"].strip()
    prefs["currency"] = prefs.get("currency", "INR").upper()
    prefs["travel_style"] = prefs.get("travel_style", "cultural")
    prefs["interests"] = prefs.get("interests", [])

    return {**state, "preferences": prefs}
