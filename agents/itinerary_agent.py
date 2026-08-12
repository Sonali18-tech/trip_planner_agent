"""Agent 4 — Itinerary builder.

Uses the LLM (Groq/Llama 3.3) to group attractions into a day-by-day plan,
accounting for rainy days from the weather forecast.
"""
import os
import json
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.3,
)


def itinerary_node(state: dict) -> dict:
    prefs = state["preferences"]
    attractions = state["attractions"]
    weather = state["weather_forecast"]

    prompt = f"""You are a trip planning assistant. Build a {prefs['num_days']}-day
itinerary for {prefs['destination']} in {prefs['travel_style']} style, for a group
of {prefs.get('group_size', 1)}.

Weather forecast (rainy=true means prefer indoor activities that day):
{json.dumps(weather)}

Available attractions to choose from:
{json.dumps(attractions)}

Return ONLY a valid JSON list, one object per day, with this exact shape:
[
  {{
    "day": 1,
    "date": "YYYY-MM-DD",
    "activities": ["Morning: ...", "Afternoon: ...", "Evening: ..."],
    "meals": ["Breakfast suggestion", "Lunch suggestion", "Dinner suggestion"],
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
