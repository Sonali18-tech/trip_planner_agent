"""Agent 6 — Hotel & flight suggestions.

There's no good free flight/hotel-pricing API without a paid business account,
so this agent uses Tavily web search to pull current-ish options, then has the
LLM summarize them into clean, short suggestions. Treat these as a starting
point for the user to verify on a real booking site, not live prices.
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
    temperature=0.2,
)


def travel_logistics_node(state: dict) -> dict:
    prefs = state["preferences"]
    destination = prefs["destination"]
    budget_status = state.get("budget_status", "within")

    try:
        hotel_results = tavily_search(
            f"best {prefs['travel_style']} hotels to stay in {destination} "
            f"{'budget friendly' if budget_status == 'over' else ''}",
            max_results=5,
        )
    except Exception:
        hotel_results = []

    try:
        flight_results = tavily_search(
            f"how to book flights to {destination} tips cheapest time to fly",
            max_results=5,
        )
    except Exception:
        flight_results = []

    hotels, flights = [], []

    if hotel_results:
        prompt = f"""Based on this search data about hotels in {destination}:
{json.dumps(hotel_results)}

List 3-5 real hotel/accommodation names or areas mentioned, each with a one-line
reason to pick it. Return ONLY a JSON list of strings, no markdown fences."""
        r = llm.invoke(prompt)
        raw = r.content.strip().strip("`")
        raw = raw[4:] if raw.startswith("json") else raw
        try:
            hotels = json.loads(raw)
        except json.JSONDecodeError:
            hotels = [raw[:400]]

    if flight_results:
        prompt = f"""Based on this search data about flights to {destination}:
{json.dumps(flight_results)}

Give 3-5 short, practical flight-booking tips specific to this destination
(nearest airport, best time to book, budget airlines that fly there, etc).
Return ONLY a JSON list of strings, no markdown fences."""
        r = llm.invoke(prompt)
        raw = r.content.strip().strip("`")
        raw = raw[4:] if raw.startswith("json") else raw
        try:
            flights = json.loads(raw)
        except json.JSONDecodeError:
            flights = [raw[:400]]

    return {**state, "hotel_suggestions": hotels, "flight_suggestions": flights}
