"""Streamlit dashboard — talks to the FastAPI backend."""
import datetime
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# 👇 change this to your deployed Render URL once you deploy the backend
API_URL = "http://localhost:8000"

st.set_page_config(page_title="AI Trip Planner", page_icon="🧳", layout="wide")

if "token" not in st.session_state:
    st.session_state.token = None
if "email" not in st.session_state:
    st.session_state.email = None

# Defaults for form fields — a parsed "trip idea" or a destination quick-pick
# overwrites these in session_state *before* the widgets below are created,
# which is how Streamlit lets you programmatically pre-fill a widget.
FORM_DEFAULTS = {
    "destination": "Jaipur", "origin": "Delhi", "budget": 15000.0, "currency": "INR",
    "travel_style": "cultural", "group_size": 1, "interests": [],
}
for k, v in FORM_DEFAULTS.items():
    st.session_state.setdefault(k, v)

st.title("🧳 AI Trip Planner")
st.caption("6-agent AI system · Llama 3.3 70B (Groq) · free APIs only")

POPULAR_DESTINATIONS = {
    "India": ["Goa", "Manali", "Jaipur", "Kerala", "Ladakh", "Andaman"],
    "International (for Indian travelers)": ["Bali", "Bangkok", "Singapore", "Dubai", "Maldives", "Vietnam"],
}

# ---------- Quick trip-idea box ----------
st.subheader("✨ Or just describe your trip")
idea_col1, idea_col2 = st.columns([5, 1])
with idea_col1:
    trip_idea = st.text_input(
        "Type a trip idea", placeholder="e.g. 5 day trip to Goa in December for 2 people, ₹30k budget, love beaches and nightlife",
        label_visibility="collapsed",
    )
with idea_col2:
    parse_clicked = st.button("Generate", use_container_width=True)

if parse_clicked and trip_idea.strip():
    with st.spinner("Reading your trip idea..."):
        try:
            r = requests.post(f"{API_URL}/plan/parse-idea", json={"text": trip_idea}, timeout=60)
            r.raise_for_status()
            parsed = r.json()
        except Exception as e:
            st.error(f"Could not parse that: {e}")
            parsed = {}

    if parsed.get("destination"):
        st.session_state["destination"] = parsed["destination"]
    if parsed.get("origin"):
        st.session_state["origin"] = parsed["origin"]
    if parsed.get("budget"):
        st.session_state["budget"] = float(parsed["budget"])
    if parsed.get("currency"):
        st.session_state["currency"] = parsed["currency"]
    if parsed.get("travel_style"):
        st.session_state["travel_style"] = parsed["travel_style"]
    if parsed.get("group_size"):
        st.session_state["group_size"] = int(parsed["group_size"])
    if parsed.get("interests"):
        st.session_state["interests"] = parsed["interests"]
    if parsed.get("start_date"):
        try:
            sd = datetime.date.fromisoformat(parsed["start_date"])
            days = parsed.get("num_days") or 3
            st.session_state["trip_dates"] = (sd, sd + datetime.timedelta(days=days - 1))
        except ValueError:
            pass
    st.success("Filled in the form below from your trip idea — review and adjust before planning.")
    st.rerun()

st.divider()


# ---------- Sidebar: auth + trip form ----------
with st.sidebar:
    st.header("Account")
    if st.session_state.token:
        st.success(f"Logged in as {st.session_state.email}")
        if st.button("Log out"):
            st.session_state.token = None
            st.session_state.email = None
            st.rerun()
    else:
        auth_tab1, auth_tab2 = st.tabs(["Log in", "Sign up"])
        with auth_tab1:
            login_email = st.text_input("Email", key="login_email")
            login_pw = st.text_input("Password", type="password", key="login_pw")
            if st.button("Log in"):
                r = requests.post(f"{API_URL}/auth/login", json={"email": login_email, "password": login_pw})
                if r.ok:
                    st.session_state.token = r.json()["access_token"]
                    st.session_state.email = login_email
                    st.rerun()
                else:
                    st.error("Login failed — check your email/password.")
        with auth_tab2:
            signup_email = st.text_input("Email", key="signup_email")
            signup_pw = st.text_input("Password (min 6 chars)", type="password", key="signup_pw")
            if st.button("Sign up"):
                r = requests.post(f"{API_URL}/auth/signup", json={"email": signup_email, "password": signup_pw})
                if r.ok:
                    st.session_state.token = r.json()["access_token"]
                    st.session_state.email = signup_email
                    st.rerun()
                else:
                    st.error(r.json().get("detail", "Signup failed"))

    st.divider()
    st.header("Popular destinations")
    for region, cities in POPULAR_DESTINATIONS.items():
        st.caption(region)
        pick_cols = st.columns(3)
        for i, city in enumerate(cities):
            with pick_cols[i % 3]:
                if st.button(city, key=f"pick_{city}", use_container_width=True):
                    st.session_state["destination"] = city
                    st.rerun()

    st.divider()
    st.header("Trip details")
    origin = st.text_input("Flying/traveling from", key="origin")
    destination = st.text_input("Destination city", key="destination")

    default_dates = st.session_state.get(
        "trip_dates",
        (datetime.date.today() + datetime.timedelta(days=7), datetime.date.today() + datetime.timedelta(days=10)),
    )
    date_range = st.date_input("Trip dates", value=default_dates, min_value=datetime.date.today())
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        num_days = (end_date - start_date).days + 1
    else:
        start_date = date_range if isinstance(date_range, datetime.date) else datetime.date.today()
        num_days = 3
    num_days = max(1, min(num_days, 14))
    st.caption(f"{num_days} day{'s' if num_days != 1 else ''}" + (" — pick an end date too" if not isinstance(date_range, tuple) else ""))

    budget = st.number_input("Budget", min_value=1.0, key="budget")
    currency = st.selectbox("Currency", ["INR", "USD", "EUR", "GBP"], key="currency")
    travel_style = st.selectbox("Travel style", ["cultural", "adventure", "relaxed", "luxury", "budget"], key="travel_style")
    group_size = st.number_input("Group size", min_value=1, key="group_size")
    interests = st.multiselect("Interests", ["museums", "food", "nature", "nightlife", "shopping", "history"], key="interests")
    save_trip = st.checkbox("Save this trip to my account", value=bool(st.session_state.token), disabled=not st.session_state.token)
    submit = st.button("Plan my trip", type="primary", use_container_width=True)

    if st.session_state.token:
        st.divider()
        st.header("My saved trips")
        r = requests.get(f"{API_URL}/trips", headers={"Authorization": f"Bearer {st.session_state.token}"})
        if r.ok:
            for t in r.json():
                st.write(f"📍 {t['destination']} — {t['created_at'][:10]}")


trip_payload = {
    "destination": destination,
    "origin": origin,
    "num_days": num_days,
    "start_date": start_date.isoformat(),
    "budget": budget,
    "currency": currency,
    "travel_style": travel_style,
    "group_size": group_size,
    "interests": interests,
}

if submit:
    with st.spinner("Agents are researching, planning, and budgeting your trip..."):
        try:
            if save_trip and st.session_state.token:
                resp = requests.post(
                    f"{API_URL}/plan/save", json=trip_payload,
                    headers={"Authorization": f"Bearer {st.session_state.token}"}, timeout=180,
                )
            else:
                resp = requests.post(f"{API_URL}/plan", json=trip_payload, timeout=180)
            resp.raise_for_status()
            st.session_state.last_plan = resp.json()
            st.session_state.last_payload = trip_payload
        except Exception as e:
            st.error(f"Could not reach the API: {e}")
            st.stop()

data = st.session_state.get("last_plan")

AQI_COLORS = {
    "Good": "🟢", "Moderate": "🟡", "Unhealthy for sensitive groups": "🟠",
    "Unhealthy": "🔴", "Very unhealthy": "🟣", "Hazardous": "⚫", "Unknown": "⚪",
}


def _money_field(d: dict, base_key: str, currency: str) -> str:
    """Look for a currency-specific field first (e.g. price_range_per_night_inr),
    falling back to the USD field, falling back to a raw dump of the dict."""
    for key in (f"{base_key}_{currency.lower()}", f"{base_key}_usd"):
        if key in d:
            symbol = currency if key.endswith(currency.lower()) else "USD"
            return f"{d[key]} {symbol}"
    return "—"


if data:
    st.success(f"Trip plan ready for {data['destination']}!")

    if not data.get("weather_forecast_available", True):
        st.info("Your trip dates are more than ~15 days out, so exact weather/AQI for those days isn't available yet — showing general seasonal data instead.")

    # --- PDF download ---
    if st.button("📄 Download as PDF"):
        with st.spinner("Generating PDF..."):
            pdf_resp = requests.post(f"{API_URL}/plan/pdf", json=st.session_state.last_payload, timeout=180)
            if pdf_resp.ok:
                st.download_button(
                    "Click to save PDF", pdf_resp.content,
                    file_name=f"{data['destination']}_trip_plan.pdf", mime="application/pdf",
                )

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["🗓️ Itinerary", "🗺️ Map", "🌦️ Weather & AQI", "💰 Budget", "🏨 Hotels, Transport & Local Gems"]
    )

    currency_symbol = data["budget_breakdown"].get("currency", "")
    trip_currency = st.session_state.last_payload.get("currency", "INR")

    # --- Itinerary ---
    with tab1:
        for day in data["itinerary"]:
            with st.expander(f"Day {day.get('day', '?')} — {day.get('date', '')}", expanded=True):
                st.write("**Activities:**")
                for a in day.get("activities", []):
                    if a.strip().startswith("⭐"):
                        st.markdown(f"- {a}")
                    else:
                        st.write(f"- {a}")
                st.write("**Meals:**")
                for m in day.get("meals", []):
                    st.write(f"- {m}")
                cost = day.get("estimated_cost_local", day.get("estimated_cost_usd", 0))
                st.write(f"**Estimated cost:** {cost} {currency_symbol}")

    # --- Map ---
    with tab2:
        attractions = [a for a in data.get("attractions", []) if a.get("lat") and a.get("lon")]
        if attractions:
            df = pd.DataFrame(attractions)
            dest_info = data.get("destination_info", {})
            fig = px.scatter_mapbox(
                df, lat="lat", lon="lon", hover_name="name",
                hover_data={"kinds": True, "lat": False, "lon": False},
                zoom=12, height=550,
                center={"lat": dest_info.get("lat", df["lat"].mean()), "lon": dest_info.get("lon", df["lon"].mean())},
            )
            fig.update_traces(marker=dict(size=14, color="#e8484e"))
            fig.update_layout(mapbox_style="open-street-map", margin={"r": 0, "t": 0, "l": 0, "b": 0})
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Attraction highlights")
            imgs = [a for a in attractions if a.get("image")]
            if imgs:
                cols = st.columns(3)
                for i, a in enumerate(imgs[:9]):
                    with cols[i % 3]:
                        st.image(a["image"], caption=a["name"])
            else:
                st.caption("No preview photos available from the attractions API for this destination.")
        else:
            st.info("No mapped attractions returned for this destination.")

    # --- Weather + AQI ---
    with tab3:
        weather_df = pd.DataFrame(data["weather_summary"])
        if not weather_df.empty:
            st.subheader("Daily overview")
            cols = st.columns(len(weather_df))
            for i, row in weather_df.iterrows():
                with cols[i]:
                    icon = row.get("icon", "")
                    st.markdown(f"**{row['date']}**")
                    st.markdown(f"### {icon} {row.get('condition', '')}")
                    st.metric("Max / Min temp", f"{row['max_temp']}° / {row['min_temp']}°")
                    if row.get("feels_like_max") is not None:
                        st.caption(f"Feels like {row['feels_like_max']}° / {row['feels_like_min']}°")
                    st.write(f"🌧️ Rain: {row['rain_mm']} mm" + (f" ({row['rain_chance_pct']}% chance)" if row.get("rain_chance_pct") is not None else ""))
                    if row.get("humidity_pct") is not None:
                        st.write(f"💧 Humidity: {row['humidity_pct']}%")
                    if row.get("wind_kmh") is not None:
                        st.write(f"💨 Wind: {row['wind_kmh']} km/h")
                    aqi = row.get("aqi")
                    if aqi is not None:
                        cat = row.get("aqi_category", "Unknown")
                        st.write(f"{AQI_COLORS.get(cat, '⚪')} AQI: {aqi} ({cat})")

            st.divider()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=weather_df["date"], y=weather_df["max_temp"], name="Max temp", mode="lines+markers"))
            fig.add_trace(go.Scatter(x=weather_df["date"], y=weather_df["min_temp"], name="Min temp", mode="lines+markers"))
            fig.update_layout(title="Temperature trend", yaxis_title="°C")
            st.plotly_chart(fig, use_container_width=True)

    # --- Budget ---
    with tab4:
        bb = data["budget_breakdown"]
        col1, col2, col3 = st.columns(3)
        col1.metric("Estimated total", f"{bb.get('total_estimated', 0)} {bb.get('currency', '')}")
        col2.metric("Your budget", f"{bb.get('budget', 0)} {bb.get('currency', '')}")
        if data["budget_status"] == "within":
            col3.metric("Status", "WITHIN BUDGET", delta=f"{bb.get('percent_saved', 0)}% saved")
        else:
            col3.metric("Status", "OVER BUDGET", delta=f"{bb.get('percent_over', 0)}% over", delta_color="inverse")
        st.progress(min(bb.get("percent_of_budget", 0) / 100, 1.0), text=f"{bb.get('percent_of_budget', 0)}% of budget used")

        if bb.get("group_size", 1) > 1:
            st.divider()
            st.subheader("👥 Split between the group")
            split_col1, split_col2, split_col3 = st.columns(3)
            split_col1.metric("Group size", bb.get("group_size", 1))
            split_col2.metric("Cost per person", f"{bb.get('per_person_cost', 0)} {bb.get('currency', '')}")
            split_col3.metric("Budget per person", f"{bb.get('per_person_budget', 0)} {bb.get('currency', '')}")

        budget_categories = data.get("budget_categories", [])
        if budget_categories:
            st.divider()
            st.subheader("📊 Where the money goes")
            cat_df = pd.DataFrame(budget_categories)
            pie = go.Figure(data=[go.Pie(
                labels=cat_df["category"], values=cat_df["amount"], hole=0.4,
                textinfo="label+percent",
            )])
            pie.update_layout(margin={"t": 10, "b": 10, "l": 10, "r": 10}, height=400)
            st.plotly_chart(pie, use_container_width=True)

        if data["budget_status"] == "over" and data["suggestions"]:
            st.warning("Over budget — here are some suggested swaps:")
            for s in data["suggestions"]:
                st.write(f"- {s}")

    # --- Hotels, Transport, Local gems ---
    with tab5:
        st.subheader("🏨 Hotel suggestions")
        hotels = data.get("hotel_suggestions", [])
        if hotels and isinstance(hotels[0], dict):
            for h in hotels:
                with st.container(border=True):
                    st.markdown(f"**{h.get('name', '')}** — {h.get('area', '')}")
                    price = _money_field(h, "price_range_per_night", trip_currency)
                    st.write(f"💵 ~{price}/night · {h.get('why', '')}")
        else:
            for h in hotels:
                st.write(f"- {h}")

        st.subheader("🚗 How to get there")
        transport = data.get("transport_options", [])
        if transport and isinstance(transport[0], dict):
            cols = st.columns(len(transport)) if len(transport) <= 4 else st.columns(4)
            for i, t in enumerate(transport):
                with cols[i % len(cols)]:
                    with st.container(border=True):
                        st.markdown(f"**{t.get('mode', '')}**")
                        st.write(f"⏱️ {t.get('typical_time', '?')}")
                        st.write(f"💵 ~{_money_field(t, 'typical_cost', trip_currency)}")
                        st.caption(t.get("tip", ""))
        else:
            for t in transport:
                st.write(f"- {t}")

        st.subheader("💎 Local hidden gems")
        local_recs = data.get("local_recommendations", [])
        if local_recs and isinstance(local_recs[0], dict):
            cols = st.columns(2)
            for i, r in enumerate(local_recs):
                with cols[i % 2]:
                    with st.container(border=True):
                        st.markdown(f"**{r.get('name', '')}** · _{r.get('type', '')}_")
                        if r.get("location"):
                            st.caption(f"📍 {r['location']}")
                        st.write(r.get("why", ""))
        else:
            for r in local_recs:
                st.write(f"- {r}")

        st.caption("Hotel/transport/local info is AI-summarized from web search, not live prices — verify before booking.")
