"""Agent 5 — Budget optimizer.

Sums itinerary costs, converts to the user's currency, compares against
budget, and asks the LLM for swap suggestions if over budget.
"""
import os
import json
from langchain_groq import ChatGroq
from dotenv import load_dotenv

from tools.currency import convert_currency

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1,
)


def budget_node(state: dict) -> dict:
    itinerary = state["raw_itinerary"]
    budget = state["preferences"]["budget"]
    currency = state["preferences"]["currency"]

    total_usd = sum(day.get("estimated_cost_usd", 0) for day in itinerary)

    if currency == "USD":
        total = total_usd
    else:
        total = convert_currency(total_usd, "USD", currency)

    over = total > budget
    diff = abs(round(total - budget, 2))

    suggestions = []
    if over:
        prompt = f"""Trip costs {total} {currency}. Budget is {budget} {currency}.
Need to cut {diff} {currency}. Itinerary: {json.dumps(itinerary)}

Suggest 3 specific cost-saving swaps. Return ONLY a JSON list of 3 strings,
no markdown fences, no explanation."""
        r = llm.invoke(prompt)
        raw = r.content.strip().strip("`")
        try:
            suggestions = json.loads(raw)
        except json.JSONDecodeError:
            suggestions = [raw]

    return {
        **state,
        "final_itinerary": itinerary,
        "budget_breakdown": {
            "total_estimated": total,
            "budget": budget,
            "currency": currency,
            "difference": diff,
        },
        "budget_status": "over" if over else "within",
        "suggestions": suggestions,
    }
