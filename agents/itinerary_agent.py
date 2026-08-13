"""Agent 4 — Itinerary builder.

Uses the LLM (Groq/Llama 3.3) to group attractions into a day-by-day plan,
accounting for rainy days from the weather forecast. Pulls in extra web
search for named restaurants/cafes, shopping spots, nightlife, and "must-do"
experiences so the plan uses real specific names instead of generic
placeholders like "a local restaurant".
"""
import os
import json
from langchain_groq import ChatGroq
from dotenv import load_dotenv

from tools.search import tavily_search

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.3,
)


def _search_safe(query: str, max_results: int = 5) -> list:
    try:
        return tavily_search(query, max_results=max_results)
    except Exception:
        return []


def itinerary_node(state: dict) -> dict:
    prefs = state["preferences"]
    attractions = state["attractions"]
    weather = state["weather_forecast"]
    destination = prefs["destination"]
    currency = prefs["currency"]

    # Extra context so the LLM has real named places to draw from, not just
    # the OpenTripMap attraction list (which skews toward monuments/temples).
    food_spots = _search_safe(f"best local restaurants and cafes to eat in {destination}")
    shopping_spots = _search_safe(f"best markets shopping streets bazaars in {destination}")
    nightlife_spots = _search_safe(f"nightlife bars rooftop lounges evening spots in {destination}")
    must_dos = _search_safe(f"must do things unmissable experiences in {destination}")

    prompt = f"""You are an expert local trip planner. Build a {prefs['num_days']}-day
itinerary for {destination} in {prefs['travel_style']} style, for a group of
{prefs.get('group_size', 1)}. Prices should be given in USD (they'll be
converted to {currency} downstream) — just estimate honestly.

Weather forecast (rainy=true means prefer indoor activities that day):
{json.dumps(weather)}

Attractions to draw from (mix historic sites, museums, viewpoints — don't use
every single one, pick variety):
{json.dumps(attractions)}

Real restaurant/cafe names found via search (use these instead of generic
phrases like "a local restaurant" wherever a good match exists):
{json.dumps(food_spots)}

Real shopping markets/streets/bazaars found via search:
{json.dumps(shopping_spots)}

Real nightlife/evening spots found via search:
{json.dumps(nightlife_spots)}

Widely-recommended "must-do" experiences for this destination:
{json.dumps(must_dos)}

Rules for a GOOD itinerary (avoid generic output):
- Use REAL, SPECIFIC names for meals — actual restaurant/cafe/street-food-stall
  names pulled from the search context above, not "a local restaurant".
- Give the plan variety across days: mix historic/cultural sites, at least one
  shopping outlet or market, at least one nightlife/evening-specific
  experience (if the travel style and local culture support it), and don't
  repeat the same category of activity every single day.
- Mark any activity that's a genuine can't-miss must-do by prefixing it with
  "⭐ Must-do: " in the activity string.
- Each day should feel distinct — don't reuse the same restaurant, market, or
  attraction across multiple days.

Return ONLY a valid JSON list, one object per day, with this exact shape:
[
  {{
    "day": 1,
    "date": "YYYY-MM-DD",
    "activities": ["Morning: ...", "Afternoon: ...", "Evening: ..."],
    "meals": ["Breakfast at [specific place name]: short reason", "Lunch at [specific place name]: short reason", "Dinner at [specific place name]: short reason"],
    "estimated_cost_usd": 50
  }}
]
No explanation text, no markdown fences — JSON only."""

    response = llm.invoke(prompt)
    raw = response.content.strip()

    # strip markdown fences if the model adds them anyway
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw.replace("json\n", "", 1) if raw.startswith("json") else raw

    try:
        raw_itinerary = json.loads(raw)
    except json.JSONDecodeError:
        raw_itinerary = [{"day": 1, "error": "Could not parse LLM output", "raw": raw}]

    return {**state, "raw_itinerary": raw_itinerary}
