"""Agent 5 — Budget optimizer.

Sums itinerary costs, converts to the user's currency, compares against
budget, and asks the LLM for swap suggestions if over budget.
"""
import json
from tools.currency import get_exchange_rate
from tools.llm_helpers import make_llm, ask_llm_json

llm = make_llm(temperature=0.1)


def budget_node(state: dict) -> dict:
    itinerary = state["raw_itinerary"]
    budget = state["preferences"]["budget"]
    currency = state["preferences"]["currency"]
    group_size = state["preferences"].get("group_size", 1) or 1

    rate = 1.0 if currency == "USD" else get_exchange_rate("USD", currency)

    def to_local(usd_amount: float) -> float:
        return round(usd_amount * rate, 2)

    # Convert each day's cost into the user's chosen currency, so the
    # itinerary the user sees is never silently in USD.
    for day in itinerary:
        usd_cost = day.get("estimated_cost_usd", 0)
        day["estimated_cost_local"] = to_local(usd_cost)
        day["currency"] = currency

    total_usd = sum(day.get("estimated_cost_usd", 0) for day in itinerary)
    total = to_local(total_usd)

    over = total > budget
    diff = abs(round(total - budget, 2))
    pct_of_budget = round((total / budget) * 100, 1) if budget else 0
    pct_saved_or_over = round(abs(100 - pct_of_budget), 1)

    suggestions = []
    if over:
        prompt = f"""Trip costs {total} {currency}. Budget is {budget} {currency}.
Need to cut {diff} {currency}. Itinerary: {json.dumps(itinerary)}

Suggest 3 specific cost-saving swaps. Return ONLY a JSON list of 3 strings,
no markdown fences, no explanation."""
        suggestions = ask_llm_json(llm, prompt, fallback=[]) or []

    return {
        **state,
        "final_itinerary": itinerary,
        "budget_breakdown": {
            "total_estimated": total,
            "budget": budget,
            "currency": currency,
            "difference": diff,
            "percent_of_budget": pct_of_budget,
            "percent_saved": pct_saved_or_over if not over else 0,
            "percent_over": pct_saved_or_over if over else 0,
            "group_size": group_size,
            "per_person_cost": round(total / group_size, 2),
            "per_person_budget": round(budget / group_size, 2),
        },
        "budget_status": "over" if over else "within",
        "suggestions": suggestions,
    }
