"""Generates a shareable PDF of the trip itinerary using fpdf2 (pure Python, no system deps)."""
from fpdf import FPDF


class TripPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, self.title_text, new_x="LMARGIN", new_y="NEXT", align="C")
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def _clean(text) -> str:
    """fpdf2's core fonts only support latin-1 — strip anything outside that range."""
    return str(text).encode("latin-1", "ignore").decode("latin-1")


def _section_title(pdf, text):
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, _clean(text), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)


def _money_field(d: dict, base_key: str, currency: str) -> str:
    for key in (f"{base_key}_{currency.lower()}", f"{base_key}_usd"):
        if key in d:
            symbol = currency if key.endswith(currency.lower()) else "USD"
            return f"{d[key]} {symbol}"
    return "n/a"


def build_trip_pdf(destination: str, itinerary: list, budget_breakdown: dict,
                    suggestions: list, hotels: list, transport: list,
                    local_recs: list, out_path: str) -> str:
    pdf = TripPDF()
    pdf.title_text = _clean(f"Trip Plan: {destination}")
    pdf.add_page()
    currency = budget_breakdown.get("currency", "")

    # Itinerary
    _section_title(pdf, "Day-by-day itinerary")
    for day in itinerary:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, _clean(f"Day {day.get('day', '?')} - {day.get('date', '')}"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        for act in day.get("activities", []):
            pdf.multi_cell(0, 6, _clean(f"  - {act}"), new_x="LMARGIN", new_y="NEXT")
        for meal in day.get("meals", []):
            pdf.multi_cell(0, 6, _clean(f"  - {meal}"), new_x="LMARGIN", new_y="NEXT")
        cost = day.get("estimated_cost_local", day.get("estimated_cost_usd", 0))
        pdf.cell(0, 6, _clean(f"  Estimated cost: {cost} {currency}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    # Budget
    _section_title(pdf, "Budget breakdown")
    pdf.cell(0, 7, _clean(f"Estimated total: {budget_breakdown.get('total_estimated')} {currency}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, _clean(f"Your budget: {budget_breakdown.get('budget')} {currency}"), new_x="LMARGIN", new_y="NEXT")
    if budget_breakdown.get("percent_saved"):
        pdf.cell(0, 7, _clean(f"You're {budget_breakdown['percent_saved']}% under budget"), new_x="LMARGIN", new_y="NEXT")
    elif budget_breakdown.get("percent_over"):
        pdf.cell(0, 7, _clean(f"You're {budget_breakdown['percent_over']}% over budget"), new_x="LMARGIN", new_y="NEXT")
    if suggestions:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, "Cost-saving suggestions:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        for s in suggestions:
            pdf.multi_cell(0, 6, _clean(f"  - {s}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Hotels
    if hotels:
        _section_title(pdf, "Hotel suggestions")
        for h in hotels:
            if isinstance(h, dict):
                price = _money_field(h, "price_range_per_night", currency)
                line = f"  - {h.get('name', '')} ({h.get('area', '')}) - ~{price}/night - {h.get('why', '')}"
            else:
                line = f"  - {h}"
            pdf.multi_cell(0, 6, _clean(line), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

    # Transport
    if transport:
        _section_title(pdf, "How to get there")
        for t in transport:
            if isinstance(t, dict):
                cost = _money_field(t, "typical_cost", currency)
                line = f"  - {t.get('mode', '')}: ~{t.get('typical_time', '?')}, ~{cost} - {t.get('tip', '')}"
            else:
                line = f"  - {t}"
            pdf.multi_cell(0, 6, _clean(line), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

    # Local recommendations
    if local_recs:
        _section_title(pdf, "Local hidden gems")
        for r in local_recs:
            if isinstance(r, dict):
                loc = f" [{r.get('location', '')}]" if r.get("location") else ""
                line = f"  - {r.get('name', '')} ({r.get('type', '')}){loc} - {r.get('why', '')}"
            else:
                line = f"  - {r}"
            pdf.multi_cell(0, 6, _clean(line), new_x="LMARGIN", new_y="NEXT")

    pdf.output(out_path)
    return out_path
