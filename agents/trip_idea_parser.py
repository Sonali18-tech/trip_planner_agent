"""Agent 0 — Trip idea parser.

Takes a single free-text sentence like "5 day trip to Goa in December for
2 people, 30k budget, love beaches and nightlife" and extracts structured
fields the rest of the app already understands. This runs standalone (not
part of the LangGraph pipeline) — it just pre-fills the form; the person
still reviews/edits before actually planning.
"""
import re
from datetime import date
from tools.llm_helpers import make_llm, ask_llm_json

llm = make_llm(temperature=0.1)


def parse_trip_idea(text: str) -> dict:
    today = date.today().isoformat()
    prompt = f"""Extract trip-planning fields from this free-text request. Today's
date is {today}.

Request: "{text}"

Return ONLY a JSON object, no markdown fences, exact shape (use null for
anything not mentioned or not confidently inferable):
{{
  "destination": "city or region name, or null",
  "origin": "departure city if mentioned, else null",
  "num_days": integer or null,
  "start_date": "YYYY-MM-DD or null (resolve relative terms like 'next month', 'in December' using today's date)",
  "budget": number or null (if given like '30k' convert to 30000),
  "currency": "3-letter code, default INR if an Indian rupee amount/symbol is implied, else null",
  "travel_style": "one of: cultural, adventure, relaxed, luxury, budget — best guess, else null",
  "group_size": integer or null,
  "interests": ["array of relevant tags from: museums, food, nature, nightlife, shopping, history — only ones actually implied"]
}}"""

    parsed = ask_llm_json(llm, prompt, fallback={}) or {}

    # normalize budget if the model left it as a string like "30k" or "30,000"
    budget = parsed.get("budget")
    if isinstance(budget, str):
        digits = re.sub(r"[^\d.]", "", budget)
        try:
            parsed["budget"] = float(digits) * (1000 if "k" in budget.lower() else 1)
        except ValueError:
            parsed["budget"] = None

    return parsed
