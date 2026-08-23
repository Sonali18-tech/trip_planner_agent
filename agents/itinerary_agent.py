"""Agent 4 — Itinerary builder.

Uses the LLM (Groq/GPT-OSS 120B) to group attractions into a day-by-day plan,
accounting for rainy days from the weather forecast. Pulls in extra web
search for named restaurants/cafes, shopping spots, nightlife, and "must-do"
experiences so the plan uses real specific names instead of generic
placeholders like "a local restaurant".
"""
import json
from tools.search import tavily_search
from tools.llm_helpers import make_llm, extract_json

llm = make_llm(temperature=0.3)


def _search_safe(query: str, max_results: int = 3) -> list:
    try:
        return tavily_search(query, max_results=max_results)
    except Exception:
        return []


def _build_prompt(prefs, destination, currency, lean_weather, lean_attractions,
                   food_spots, shopping_spots, nightlife_spots, must_dos) -> str:
    return f"""You are an expert local trip planner. Build a {prefs['num_days']}-day
itinerary for {destination} in {prefs['travel_style']} style, for a group of
{prefs.get('group_size', 1)}. Prices should be given in USD (they'll be
converted to {currency} downstream) — just estimate honestly.

Weather forecast (rainy=true means prefer indoor activities that day):
{json.dumps(lean_weather)}

Attractions to draw from (mix historic sites, museums, viewpoints — don't use
every single one, pick variety). This list may be empty for remote/less
mapped destinations — if so, rely on your own knowledge of the destination
plus the search context below instead:
{json.dumps(lean_attractions)}

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
  "Must-do: " in the activity string.
- Each day should feel distinct — don't reuse the same restaurant, market, or
  attraction across multiple days.
- Never leave activities or meals empty. Every day must have real content
  even if you have to rely on general knowledge of the destination.

Return ONLY a valid JSON array, one object per day, no markdown fences, no
commentary before or after it — the response must start with [ and end with
], exact shape:
[
  {{
    "day": 1,
    "date": "YYYY-MM-DD",
    "activities": ["Morning: ...", "Afternoon: ...", "Evening: ..."],
    "meals": ["Breakfast at [specific place name]: short reason", "Lunch at [specific place name]: short reason", "Dinner at [specific place name]: short reason"],
    "estimated_cost_usd": 50
  }}
]"""


def _placeholder_day(day_num: int, date: str) -> dict:
    """Used only if the LLM output genuinely can't be parsed after a retry —
    visibly flags the problem instead of silently rendering a blank card."""
    return {
        "day": day_num,
        "date": date,
        "activities": ["Could not generate this day automatically — try clicking Plan my trip again."],
        "meals": ["Not available — please regenerate."],
        "estimated_cost_usd": 0,
        "generation_failed": True,
    }


def itinerary_node(state: dict) -> dict:
    prefs = state["preferences"]
    attractions = state["attractions"]
    weather = state["weather_forecast"]
    destination = prefs["destination"]
    currency = prefs["currency"]

    # Extra context so the LLM has real named places to draw from, not just
    # the OpenTripMap attraction list (which skews toward monuments/temples,
    # and can be sparse or empty for remote destinations like island chains).
    # Kept small (3 results, ~280 chars each, 4 searches) to stay well within
    # Groq's free-tier tokens-per-minute limit for gpt-oss-120b.
    food_spots = _search_safe(f"best local restaurants and cafes to eat in {destination}")
    shopping_spots = _search_safe(f"best markets shopping streets bazaars in {destination}")
    nightlife_spots = _search_safe(f"nightlife bars rooftop lounges evening spots in {destination}")
    must_dos = _search_safe(f"must do things unmissable experiences in {destination}")

    lean_attractions = [{"name": a.get("name"), "kinds": a.get("kinds")} for a in attractions[:10]]
    lean_weather = [
        {"date": w.get("date"), "condition": w.get("condition"), "rainy": w.get("rainy"),
         "max_temp": w.get("max_temp"), "min_temp": w.get("min_temp")}
        for w in weather
    ]

    prompt = _build_prompt(prefs, destination, currency, lean_weather, lean_attractions,
                            food_spots, shopping_spots, nightlife_spots, must_dos)

    raw_itinerary = None
    for attempt in range(2):  # one retry if the first response doesn't parse
        response = llm.invoke(prompt)
        parsed = extract_json(response.content)
        if isinstance(parsed, list) and parsed:
            raw_itinerary = parsed
            break

    if raw_itinerary is None:
        # Genuinely failed twice — build a visibly-flagged placeholder per day
        # rather than a single blank "Day 1" card with everything empty.
        raw_itinerary = [
            _placeholder_day(i + 1, lean_weather[i]["date"] if i < len(lean_weather) else "")
            for i in range(prefs["num_days"])
        ]

    return {**state, "raw_itinerary": raw_itinerary}
