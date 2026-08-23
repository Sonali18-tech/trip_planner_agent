"""Streamlit dashboard — talks to the FastAPI backend."""
import datetime
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# 👇 change this to your deployed Render URL once you deploy the backend
API_URL = "http://localhost:8000"

st.set_page_config(page_title="AI Trip Planner", page_icon=None, layout="wide")

# ---------- Color theme ----------
INK = "#1A2233"         # near-black text
NAVY = "#0B3B4B"         # primary — deep teal-navy (used for text/accents, not big fills)
NAVY_DARK = "#082C38"
GOLD = "#B8802E"         # accent
GOLD_LIGHT = "#F3E3C8"
PAPER = "#FAF8F4"        # warm off-white — main background
SIDEBAR_BG = "#F1ECE1"   # slightly deeper warm tone for the sidebar
CARD = "#FFFFFF"
BORDER = "#E2DACB"
MUTED = "#5B6472"
GOOD = "#2F6F4E"
WARN = "#B4562E"

PLOTLY_PALETTE = [NAVY, GOLD, "#5B8C6E", "#8E6C8A", "#A6763D", "#4A6FA5"]

st.markdown(f"""
<style>
    .stApp {{ background-color: {PAPER}; }}
    html, body, [class*="css"] {{ color: {INK}; }}

    /* Sidebar — light warm tone with a navy edge, NOT inverted colors.
       Inverting the sidebar to a dark fill fights Streamlit's own widget
       styling and produces invisible/overlapping text, so we keep every
       surface light and use navy/gold only for text, borders and fills. */
    section[data-testid="stSidebar"] {{
        background-color: {SIDEBAR_BG};
        border-right: 3px solid {NAVY};
    }}
    section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p {{
        color: {INK} !important;
    }}
    section[data-testid="stSidebar"] input, section[data-testid="stSidebar"] textarea {{
        background-color: #ffffff !important;
        color: {INK} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 6px !important;
    }}
    section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {{
        background-color: #ffffff !important;
        color: {INK} !important;
        border-radius: 6px !important;
    }}
    section[data-testid="stSidebar"] hr {{ border-color: {BORDER}; }}

    /* Headings */
    h1, h2, h3 {{ color: {NAVY}; font-weight: 700; letter-spacing: -0.01em; }}
    .app-title {{ font-size: 2.1rem; font-weight: 800; color: {NAVY}; margin-bottom: 0; }}
    .app-subtitle {{ color: {MUTED}; font-size: 0.95rem; margin-top: 0.1rem; margin-bottom: 1.4rem; }}
    .section-label {{
        text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.75rem;
        color: {NAVY}; font-weight: 800; margin-bottom: 0.4rem;
        border-bottom: 2px solid {GOLD}; display: inline-block; padding-bottom: 2px;
    }}

    /* Buttons — light fill, navy border/text everywhere by default, so
       nothing ever renders as light-text-on-light-background. */
    .stButton > button {{
        background-color: #ffffff;
        border-radius: 6px; border: 1.5px solid {NAVY}; color: {NAVY};
        font-weight: 600;
    }}
    .stButton > button:hover {{ background-color: {GOLD_LIGHT}; border-color: {GOLD}; color: {NAVY_DARK}; }}
    .stButton > button[kind="primary"] {{
        background-color: {GOLD}; border-color: {GOLD}; color: #ffffff;
    }}
    .stButton > button[kind="primary"]:hover {{ background-color: #A0721F; border-color: #A0721F; color: #ffffff; }}

    /* Cards */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: {CARD}; border-radius: 10px; border: 1px solid {BORDER} !important;
        box-shadow: 0 1px 3px rgba(11,59,75,0.06);
    }}

    /* Hero banner */
    .hero {{
        background: linear-gradient(120deg, {NAVY} 0%, #124F63 55%, {NAVY_DARK} 100%);
        border-radius: 14px; padding: 2.1rem 2.4rem; margin-bottom: 1.6rem;
        box-shadow: 0 6px 18px rgba(8,44,56,0.18);
    }}
    .hero-title {{ font-size: 2.3rem; font-weight: 800; color: #ffffff; margin-bottom: 0.3rem; letter-spacing: -0.01em; }}
    .hero-subtitle {{ color: #D9E6E9; font-size: 1rem; max-width: 640px; line-height: 1.5; }}
    .hero-tagline {{
        display: inline-block; margin-top: 0.9rem; background-color: rgba(255,255,255,0.12);
        color: {GOLD_LIGHT}; padding: 4px 12px; border-radius: 20px; font-size: 0.78rem;
        font-weight: 700; letter-spacing: 0.03em;
    }}

    /* Timeline (itinerary) */
    .timeline-day {{ position: relative; padding-left: 2.4rem; padding-bottom: 1.6rem; }}
    .timeline-day:before {{
        content: ""; position: absolute; left: 10px; top: 30px; bottom: -8px; width: 2px;
        background-color: {BORDER};
    }}
    .timeline-day:last-child:before {{ display: none; }}
    .timeline-dot {{
        position: absolute; left: 0; top: 2px; width: 22px; height: 22px; border-radius: 50%;
        background-color: {NAVY}; color: #ffffff; font-weight: 800; font-size: 0.78rem;
        display: flex; align-items: center; justify-content: center;
    }}
    .timeline-dot.failed {{ background-color: {WARN}; }}
    .timeline-card {{
        background-color: {CARD}; border: 1px solid {BORDER}; border-radius: 10px;
        padding: 1.1rem 1.3rem; box-shadow: 0 1px 3px rgba(11,59,75,0.06);
    }}
    .timeline-card.failed {{ border-color: {WARN}; background-color: #FBF1EA; }}
    .timeline-date {{ color: {MUTED}; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.5rem; }}
    .slot-row {{ display: flex; gap: 10px; margin-bottom: 5px; align-items: baseline; }}
    .slot-tag {{
        flex-shrink: 0; width: 78px; font-size: 0.72rem; font-weight: 800; text-transform: uppercase;
        color: {GOLD}; letter-spacing: 0.04em;
    }}
    .cost-pill {{
        display: inline-block; margin-top: 0.7rem; background-color: {GOLD_LIGHT}; color: {NAVY_DARK};
        padding: 3px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: 700;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{ gap: 4px; border-bottom: 1px solid {BORDER}; }}
    .stTabs [data-baseweb="tab"] {{
        color: {MUTED}; font-weight: 600; padding: 8px 16px;
    }}
    .stTabs [aria-selected="true"] {{
        color: {NAVY} !important; border-bottom: 3px solid {GOLD} !important;
    }}
    .stTabs [data-baseweb="tab"] p {{ color: inherit !important; }}

    /* Metrics */
    div[data-testid="stMetric"] {{
        background-color: {CARD}; border: 1px solid {BORDER}; border-radius: 10px; padding: 0.8rem 1rem;
    }}
    div[data-testid="stMetricLabel"] {{ color: {MUTED}; }}
    div[data-testid="stMetricValue"] {{ color: {NAVY}; }}

    /* Alerts */
    div[data-testid="stAlert"] {{ border-radius: 8px; }}

    /* Badge */
    .badge {{
        display: inline-block; background-color: {GOLD_LIGHT}; color: {NAVY_DARK};
        border-radius: 4px; padding: 1px 8px; font-size: 0.78rem; font-weight: 700;

    }}
    .muted {{ color: {MUTED}; }}
    .divider-thin {{ border: none; border-top: 1px solid {BORDER}; margin: 1.1rem 0; }}
</style>
""", unsafe_allow_html=True)

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

st.markdown(
    '<div class="hero">'
    '<div class="hero-title">AI Trip Planner</div>'
    '<div class="hero-subtitle">A six-agent planning system that researches, budgets, and books logistics for your next trip in one pass — built on GPT-OSS 120B.</div>'
    '<div class="hero-tagline">Itinerary · Weather &amp; AQI · Budget · Hotels &amp; Transport · Local Guide</div>'
    '</div>',
    unsafe_allow_html=True,
)

POPULAR_DESTINATIONS = {
    "India": ["Goa", "Manali", "Jaipur", "Kerala", "Ladakh", "Andaman"],
    "International, for Indian travelers": ["Bali", "Bangkok", "Singapore", "Dubai", "Maldives", "Vietnam"],
}

# ---------- Quick trip-idea box ----------
st.markdown('<div class="section-label">Describe your trip</div>', unsafe_allow_html=True)
idea_col1, idea_col2 = st.columns([5, 1])
with idea_col1:
    trip_idea = st.text_input(
        "Type a trip idea",
        placeholder="5 day trip to Goa in December for 2 people, INR 30,000 budget, beaches and nightlife",
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
    st.success("Form updated from your trip idea below — review and adjust before planning.")
    st.rerun()

st.markdown('<hr class="divider-thin">', unsafe_allow_html=True)


# ---------- Sidebar: auth + trip form ----------
with st.sidebar:
    st.markdown('<div class="section-label">Account</div>', unsafe_allow_html=True)
    if st.session_state.token:
        st.success(f"Signed in as {st.session_state.email}")
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
                    st.error("Login failed — check your email and password.")
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
    st.markdown('<div class="section-label">Popular destinations</div>', unsafe_allow_html=True)
    for region, cities in POPULAR_DESTINATIONS.items():
        st.caption(region)
        pick_cols = st.columns(3)
        for i, city in enumerate(cities):
            with pick_cols[i % 3]:
                if st.button(city, key=f"pick_{city}", use_container_width=True):
                    st.session_state["destination"] = city
                    st.rerun()

    st.divider()
    st.markdown('<div class="section-label">Trip details</div>', unsafe_allow_html=True)
    origin = st.text_input("Traveling from", key="origin")
    destination = st.text_input("Destination", key="destination")

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
        st.markdown('<div class="section-label">Saved trips</div>', unsafe_allow_html=True)
        r = requests.get(f"{API_URL}/trips", headers={"Authorization": f"Bearer {st.session_state.token}"})
        if r.ok:
            for t in r.json():
                st.write(f"{t['destination']} — {t['created_at'][:10]}")


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

AQI_LABELS = {
    "Good": ("Good", GOOD), "Moderate": ("Moderate", GOLD),
    "Unhealthy for sensitive groups": ("Unhealthy — sensitive groups", WARN),
    "Unhealthy": ("Unhealthy", WARN), "Very unhealthy": ("Very unhealthy", "#8B2E2E"),
    "Hazardous": ("Hazardous", "#5C1A1A"), "Unknown": ("Unknown", MUTED),
}


def _money_field(d: dict, base_key: str, currency: str) -> str:
    """Look for a currency-specific field first (e.g. price_range_per_night_inr),
    falling back to the USD field, falling back to a raw dump of the dict."""
    for key in (f"{base_key}_{currency.lower()}", f"{base_key}_usd"):
        if key in d:
            symbol = currency if key.endswith(currency.lower()) else "USD"
            return f"{d[key]} {symbol}"
    return "not available"


def styled_fig(fig):
    fig.update_layout(
        colorway=PLOTLY_PALETTE, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=INK), legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    return fig


if data:
    st.success(f"Trip plan ready for {data['destination']}.")

    if not data.get("weather_forecast_available", True):
        st.info("Trip dates are more than about 15 days out, so exact weather and air-quality data for those days isn't available yet — general seasonal figures are shown instead.")

    if any(d.get("generation_failed") for d in data.get("itinerary", [])):
        st.warning("One or more days couldn't be generated automatically. Click Plan my trip again to retry those days.")

    # --- PDF download ---
    if st.button("Download as PDF"):
        with st.spinner("Generating PDF..."):
            pdf_resp = requests.post(f"{API_URL}/plan/pdf", json=st.session_state.last_payload, timeout=180)
            if pdf_resp.ok:
                st.download_button(
                    "Save PDF", pdf_resp.content,
                    file_name=f"{data['destination']}_trip_plan.pdf", mime="application/pdf",
                )

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Itinerary", "Map", "Weather and Air Quality", "Budget", "Hotels, Transport and Local Guide"]
    )

    currency_symbol = data["budget_breakdown"].get("currency", "")
    trip_currency = st.session_state.last_payload.get("currency", "INR")

    # --- Itinerary ---
    with tab1:
        for day in data["itinerary"]:
            failed = bool(day.get("generation_failed"))
            day_num = day.get("day", "?")
            date_str = day.get("date", "")
            dot_class = "timeline-dot failed" if failed else "timeline-dot"
            card_class = "timeline-card failed" if failed else "timeline-card"

            rows_html = ""
            if failed:
                rows_html += f"<div>{day.get('activities', [''])[0]}</div>"
            else:
                for a in day.get("activities", []):
                    text = a.strip()
                    slot = "Note"
                    for candidate in ("Morning", "Afternoon", "Evening"):
                        if text.lower().startswith(candidate.lower()):
                            slot = candidate
                            text = text.split(":", 1)[1].strip() if ":" in text else text
                            break
                    is_must_do = text.lower().startswith("must-do:")
                    if is_must_do:
                        text = text.split(":", 1)[1].strip() if ":" in text else text
                        text = f"<span class='badge'>Must-do</span>&nbsp; {text}"
                    rows_html += f"<div class='slot-row'><div class='slot-tag'>{slot}</div><div>{text}</div></div>"

                if day.get("meals"):
                    rows_html += "<div class='slot-row' style='margin-top:8px;'><div class='slot-tag'>Meals</div><div>" + "<br>".join(day["meals"]) + "</div></div>"

                cost = day.get("estimated_cost_local", day.get("estimated_cost_usd", 0))
                rows_html += f"<div class='cost-pill'>Estimated cost: {cost} {currency_symbol}</div>"

            st.markdown(f"""
            <div class="timeline-day">
                <div class="{dot_class}">{day_num}</div>
                <div class="{card_class}">
                    <div class="timeline-date">Day {day_num} — {date_str}</div>
                    {rows_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

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
            fig.update_traces(marker=dict(size=14, color=NAVY))
            fig.update_layout(mapbox_style="open-street-map", margin={"r": 0, "t": 0, "l": 0, "b": 0})
            st.plotly_chart(fig, use_container_width=True)

            st.markdown('<div class="section-label">Attraction highlights</div>', unsafe_allow_html=True)
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
            st.markdown('<div class="section-label">Daily overview</div>', unsafe_allow_html=True)
            cols = st.columns(len(weather_df))
            for i, row in weather_df.iterrows():
                with cols[i]:
                    with st.container(border=True):
                        st.markdown(f"**{row['date']}**")
                        st.markdown(f"###### {row.get('condition', '')}")
                        st.metric("Max / Min temp", f"{row['max_temp']}° / {row['min_temp']}°")
                        if row.get("feels_like_max") is not None:
                            st.caption(f"Feels like {row['feels_like_max']}° / {row['feels_like_min']}°")
                        rain_text = f"Rain: {row['rain_mm']} mm"
                        if row.get("rain_chance_pct") is not None:
                            rain_text += f" ({row['rain_chance_pct']}% chance)"
                        st.write(rain_text)
                        if row.get("humidity_pct") is not None:
                            st.write(f"Humidity: {row['humidity_pct']}%")
                        if row.get("wind_kmh") is not None:
                            st.write(f"Wind: {row['wind_kmh']} km/h")
                        aqi = row.get("aqi")
                        if aqi is not None:
                            label, color = AQI_LABELS.get(row.get("aqi_category", "Unknown"), ("Unknown", MUTED))
                            st.markdown(
                                f"<span style='color:{color}; font-weight:700;'>AQI {aqi} — {label}</span>",
                                unsafe_allow_html=True,
                            )

            st.markdown('<hr class="divider-thin">', unsafe_allow_html=True)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=weather_df["date"], y=weather_df["max_temp"], name="Max temp", mode="lines+markers"))
            fig.add_trace(go.Scatter(x=weather_df["date"], y=weather_df["min_temp"], name="Min temp", mode="lines+markers"))
            fig.update_layout(title="Temperature trend", yaxis_title="Degrees C")
            st.plotly_chart(styled_fig(fig), use_container_width=True)

    # --- Budget ---
    with tab4:
        bb = data["budget_breakdown"]
        col1, col2, col3 = st.columns(3)
        col1.metric("Estimated total", f"{bb.get('total_estimated', 0)} {bb.get('currency', '')}")
        col2.metric("Your budget", f"{bb.get('budget', 0)} {bb.get('currency', '')}")
        if data["budget_status"] == "within":
            col3.metric("Status", "Within budget", delta=f"{bb.get('percent_saved', 0)}% saved")
        else:
            col3.metric("Status", "Over budget", delta=f"{bb.get('percent_over', 0)}% over", delta_color="inverse")
        st.progress(min(bb.get("percent_of_budget", 0) / 100, 1.0), text=f"{bb.get('percent_of_budget', 0)}% of budget used")

        if bb.get("group_size", 1) > 1:
            st.markdown('<hr class="divider-thin">', unsafe_allow_html=True)
            st.markdown('<div class="section-label">Split between the group</div>', unsafe_allow_html=True)
            split_col1, split_col2, split_col3 = st.columns(3)
            split_col1.metric("Group size", bb.get("group_size", 1))
            split_col2.metric("Cost per person", f"{bb.get('per_person_cost', 0)} {bb.get('currency', '')}")
            split_col3.metric("Budget per person", f"{bb.get('per_person_budget', 0)} {bb.get('currency', '')}")

        budget_categories = data.get("budget_categories", [])
        if budget_categories:
            st.markdown('<hr class="divider-thin">', unsafe_allow_html=True)
            st.markdown('<div class="section-label">Cost breakdown</div>', unsafe_allow_html=True)
            cat_df = pd.DataFrame(budget_categories)
            pie = go.Figure(data=[go.Pie(
                labels=cat_df["category"], values=cat_df["amount"], hole=0.45,
                textinfo="label+percent", marker=dict(colors=PLOTLY_PALETTE),
            )])
            pie.update_layout(margin={"t": 10, "b": 10, "l": 10, "r": 10}, height=400)
            st.plotly_chart(styled_fig(pie), use_container_width=True)

        if data["budget_status"] == "over" and data["suggestions"]:
            st.warning("Over budget — consider these swaps:")
            for s in data["suggestions"]:
                st.write(f"- {s}")

    # --- Hotels, Transport, Local gems ---
    with tab5:
        st.markdown('<div class="section-label">Hotel suggestions</div>', unsafe_allow_html=True)
        hotels = data.get("hotel_suggestions", [])
        if hotels and isinstance(hotels[0], dict):
            for h in hotels:
                with st.container(border=True):
                    st.markdown(f"**{h.get('name', '')}** — {h.get('area', '')}")
                    price = _money_field(h, "price_range_per_night", trip_currency)
                    st.write(f"{price} per night · {h.get('why', '')}")
        else:
            for h in hotels:
                st.write(f"- {h}")

        st.markdown('<hr class="divider-thin">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">How to get there</div>', unsafe_allow_html=True)
        transport = data.get("transport_options", [])
        if transport and isinstance(transport[0], dict):
            cols = st.columns(len(transport)) if len(transport) <= 4 else st.columns(4)
            for i, t in enumerate(transport):
                with cols[i % len(cols)]:
                    with st.container(border=True):
                        st.markdown(f"**{t.get('mode', '')}**")
                        st.write(f"Time: {t.get('typical_time', 'n/a')}")
                        st.write(f"Cost: {_money_field(t, 'typical_cost', trip_currency)}")
                        st.caption(t.get("tip", ""))
        else:
            for t in transport:
                st.write(f"- {t}")

        st.markdown('<hr class="divider-thin">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Local guide — beyond the usual stops</div>', unsafe_allow_html=True)
        local_recs = data.get("local_recommendations", [])
        if local_recs and isinstance(local_recs[0], dict):
            cols = st.columns(2)
            for i, r in enumerate(local_recs):
                with cols[i % 2]:
                    with st.container(border=True):
                        st.markdown(f"**{r.get('name', '')}** &nbsp; <span class='muted'>{r.get('type', '')}</span>", unsafe_allow_html=True)
                        if r.get("location"):
                            st.caption(r["location"])
                        st.write(r.get("why", ""))
        else:
            for r in local_recs:
                st.write(f"- {r}")

        st.caption("Hotel, transport, and local information is AI-summarized from web search, not live prices — verify before booking.")
