# AI Trip Planner Agent

A 5-agent LangGraph system that plans a trip end-to-end using only free APIs
and a free LLM (GPT-OSS 120B via Groq).

## Agents
1. **Intake** — normalizes user preferences
2. **Research** — geocoding + weather + country info + local tips
3. **Attractions** — top POIs near the destination
4. **Itinerary builder** — day-by-day plan via the LLM
5. **Budget optimizer** — currency conversion + cost-saving suggestions

## Quick start

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # then fill in your real keys
```

Run the API:
```bash
uvicorn api.main:app --reload --port 8000
# docs at http://localhost:8000/docs
```

Run the dashboard (in a second terminal):
```bash
streamlit run dashboard/app.py
```

## Getting your free API keys
- Groq: console.groq.com → Create API Key
- OpenTripMap: opentripmap.io → Get API Key
- Tavily: tavily.com → Get Free API Key
- ExchangeRate-API: exchangerate-api.com → Get Free Key
- Open-Meteo, Nominatim, RestCountries: no key needed

## Deploy
- Backend → Render.com (Docker web service, free tier)
- Dashboard → Streamlit Community Cloud (free)
