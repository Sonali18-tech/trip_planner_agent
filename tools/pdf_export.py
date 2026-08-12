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


def _clean(text: str) -> str:
    """fpdf2's core fonts only support latin-1 — strip anything outside that range."""
    return text.encode("latin-1", "ignore").decode("latin-1")


def build_trip_pdf(destination: str, itinerary: list, budget_breakdown: dict,
                    suggestions: list, hotels: list, flights: list, out_path: str) -> str:
    pdf = TripPDF()
    pdf.title_text = _clean(f"Trip Plan: {destination}")
    pdf.add_page()

    # Itinerary
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, "Day-by-day itinerary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)

    for day in itinerary:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, _clean(f"Day {day.get('day', '?')} - {day.get('date', '')}"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        for act in day.get("activities", []):
            pdf.multi_cell(0, 6, _clean(f"  - {act}"), new_x="LMARGIN", new_y="NEXT")
        for meal in day.get("meals", []):
            pdf.multi_cell(0, 6, _clean(f"  - {meal}"), new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, _clean(f"  Estimated cost: ${day.get('estimated_cost_usd', 0)}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    # Budget
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, "Budget breakdown", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, _clean(f"Estimated total: {budget_breakdown.get('total_estimated')} {budget_breakdown.get('currency')}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, _clean(f"Your budget: {budget_breakdown.get('budget')} {budget_breakdown.get('currency')}"), new_x="LMARGIN", new_y="NEXT")
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
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 10, "Hotel suggestions", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        for h in hotels:
            pdf.multi_cell(0, 6, _clean(f"  - {h}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

    # Flights
    if flights:
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 10, "Flight suggestions", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        for f in flights:
            pdf.multi_cell(0, 6, _clean(f"  - {f}"), new_x="LMARGIN", new_y="NEXT")

    pdf.output(out_path)
    return out_path
