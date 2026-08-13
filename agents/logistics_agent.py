"""Agent 6 — Hotels, transport & local recommendations.

There's no good free flight/hotel-pricing API without a paid business account,
so this agent uses Tavily web search to pull current-ish info, then has the
LLM structure it into clean cards, priced directly in the user's chosen
currency (via a live USD exchange rate). Treat costs/times as ballpark
estimates to verify on a real booking site — not live prices.
"""
import os
import json
from langchain_groq import ChatGroq
from dotenv import load_dotenv

from tools.search import tavily_search
from tools.currency import get_exchange_rate

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.2,
)


def _search_safe(query: str, max_results: int = 5) -> list:
    try:
        return tavily_search(query, max_results=max_results)
    except Exception:
        return []


def _ask_llm_json(prompt: str, fallback: list) -> list:
    r = llm.invoke(prompt)
    raw = r.content.strip().strip("`")
    raw = raw[4:] if raw.startswith("json") else raw
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def travel_logistics_node(state: dict) -> dict:
    prefs = state["preferences"]
    destination = prefs["destination"]
    currency = prefs["currency"]
    budget_status = state.get("budget_status", "within")
    origin_hint = prefs.get("origin", "a major nearby city")

    try:
        rate = get_exchange_rate("USD", currency) if currency != "USD" else 1.0
    except Exception:
        rate = None  # if the currency API is down, fall back to USD in the prompt

    currency_instruction = (
        f"Give all prices directly in {currency} (1 USD ≈ {round(rate, 2)} {currency})."
        if rate else
        f"Give all prices in USD (could not fetch a live {currency} exchange rate)."
    )
    price_field = f"price_range_per_night_{currency.lower()}" if rate else "price_range_per_night_usd"
    cost_field = f"typical_cost_{currency.lower()}" if rate else "typical_cost_usd"

    # ---- Hotels ----
    hotel_results = _search_safe(
        f"best {prefs['travel_style']} hotels to stay in {destination} "
        f"{'budget friendly' if budget_status == 'over' else ''} price per night"
    )
    hotels = []
    if hotel_results:
        prompt = f"""Based on this search data about hotels/stays in {destination}:
{json.dumps(hotel_results)}

List 3-5 real accommodation names or areas mentioned. {currency_instruction}
Return ONLY a JSON list of objects, no markdown fences, exact shape:
[{{"name": "Hotel/area name", "area": "neighborhood if known, else destination name",
"{price_field}": "e.g. 3000-6000", "why": "one-line reason to pick it"}}]"""
        hotels = _ask_llm_json(prompt, [])

    # ---- Transport: multiple modes, each with time + cost + a tip ----
    transport_results = _search_safe(
        f"how to reach {destination} from {origin_hint} flight train bus cost time"
    )
    transport_options = []
    if transport_results:
        prompt = f"""Based on this search data about traveling to {destination}:
{json.dumps(transport_results)}

Describe realistic transport options to reach {destination} (flight, train, bus,
and car/taxi where relevant — skip a mode if genuinely not viable for this route).
{currency_instruction}
Return ONLY a JSON list of objects, no markdown fences, exact shape:
[{{"mode": "Flight", "typical_time": "e.g. 2h 30m", "{cost_field}": "e.g. 5000-9000",
"tip": "one practical booking tip for this mode"}}]"""
        transport_options = _ask_llm_json(prompt, [])

    # ---- Local hidden gems: cafes, street food, lesser-known spots ----
    local_results = _search_safe(
        f"hidden gems local cafes street food off the beaten path {destination} "
        f"where locals eat and hang out, exact location or area"
    )
    local_recommendations = []
    if local_results:
        prompt = f"""Based on this search data about {destination}:
{json.dumps(local_results)}

List 4-6 specific local cafes, eateries, street-food spots, or lesser-known
places (not the obvious tourist landmarks already in a typical itinerary).
Write each "why" as an inviting, vivid one-liner that makes someone want to go
(mention the signature dish/drink/vibe, not just "hidden gem"). Include the
actual neighborhood/street/area if the search data mentions it — if not
mentioned, write "check exact location on Google Maps" for location.
Return ONLY a JSON list of objects, no markdown fences, exact shape:
[{{"name": "Specific place name", "type": "e.g. cafe / street food / viewpoint",
"location": "neighborhood or street name", "why": "vivid one-line reason it's worth seeking out"}}]"""
        local_recommendations = _ask_llm_json(prompt, [])

    return {
        **state,
        "hotel_suggestions": hotels,
        "transport_options": transport_options,
        "local_recommendations": local_recommendations,
        "logistics_currency": currency if rate else "USD",
    }
