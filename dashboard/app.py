"""Streamlit dashboard — talks to the FastAPI backend."""
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

# 👇 change this to your deployed Render URL once you deploy the backend
API_URL = "http://localhost:8000"

st.set_page_config(page_title="AI Trip Planner", page_icon="🧳", layout="wide")

if "token" not in st.session_state:
    st.session_state.token = None
if "email" not in st.session_state:
    st.session_state.email = None

st.title("🧳 AI Trip Planner")
st.caption("6-agent AI system · Llama 3.3 70B (Groq) · free APIs only")


# ---------- Sidebar: auth ----------
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
    st.header("Trip details")
    destination = st.text_input("Destination city", "Jaipur")
    num_days = st.slider("Number of days", 1, 14, 3)
    budget = st.number_input("Budget", min_value=1.0, value=15000.0)
    currency = st.selectbox("Currency", ["INR", "USD", "EUR", "GBP"])
    travel_style = st.selectbox("Travel style", ["cultural", "adventure", "relaxed", "luxury", "budget"])
    group_size = st.number_input("Group size", min_value=1, value=1)
    interests = st.multiselect("Interests", ["museums", "food", "nature", "nightlife", "shopping", "history"])
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
    "num_days": num_days,
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
                    headers={"Authorization": f"Bearer {st.session_state.token}"}, timeout=120,
                )
            else:
                resp = requests.post(f"{API_URL}/plan", json=trip_payload, timeout=120)
            resp.raise_for_status()
            st.session_state.last_plan = resp.json()
            st.session_state.last_payload = trip_payload
        except Exception as e:
            st.error(f"Could not reach the API: {e}")
            st.stop()

data = st.session_state.get("last_plan")

if data:
    st.success(f"Trip plan ready for {data['destination']}!")

    # --- PDF download ---
    if st.button("📄 Download as PDF"):
        with st.spinner("Generating PDF..."):
            pdf_resp = requests.post(f"{API_URL}/plan/pdf", json=st.session_state.last_payload, timeout=120)
            if pdf_resp.ok:
                st.download_button(
                    "Click to save PDF", pdf_resp.content,
                    file_name=f"{data['destination']}_trip_plan.pdf", mime="application/pdf",
                )

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🗓️ Itinerary", "🗺️ Map", "🌦️ Weather", "💰 Budget", "🏨 Hotels & Flights"])

    # --- Itinerary ---
    with tab1:
        for day in data["itinerary"]:
            with st.expander(f"Day {day.get('day', '?')} — {day.get('date', '')}", expanded=True):
                st.write("**Activities:**")
                for a in day.get("activities", []):
                    st.write(f"- {a}")
                st.write("**Meals:**")
                for m in day.get("meals", []):
                    st.write(f"- {m}")
                st.write(f"**Estimated cost:** ${day.get('estimated_cost_usd', 0)}")

    # --- Map + attraction photos ---
    with tab2:
        attractions = [a for a in data.get("attractions", []) if a.get("lat") and a.get("lon")]
        if attractions:
            dest_info = data.get("destination_info", {})
            center = [dest_info.get("lat", attractions[0]["lat"]), dest_info.get("lon", attractions[0]["lon"])]
            m = folium.Map(location=center, zoom_start=13)
            for a in attractions:
                popup_html = f"<b>{a['name']}</b><br>{a.get('kinds', '')}"
                if a.get("image"):
                    popup_html += f"<br><img src='{a['image']}' width='150'>"
                folium.Marker([a["lat"], a["lon"]], popup=folium.Popup(popup_html, max_width=200), tooltip=a["name"]).add_to(m)
            st_folium(m, width=None, height=500)

            st.subheader("Attraction highlights")
            cols = st.columns(3)
            for i, a in enumerate(attractions[:9]):
                with cols[i % 3]:
                    if a.get("image"):
                        st.image(a["image"], caption=a["name"], use_container_width=True)
                    else:
                        st.write(f"**{a['name']}**")
        else:
            st.info("No mapped attractions returned for this destination.")

    # --- Weather ---
    with tab3:
        weather_df = pd.DataFrame(data["weather_summary"])
        if not weather_df.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=weather_df["date"], y=weather_df["max_temp"], name="Max temp"))
            fig.add_trace(go.Scatter(x=weather_df["date"], y=weather_df["min_temp"], name="Min temp"))
            st.plotly_chart(fig, use_container_width=True)

    # --- Budget ---
    with tab4:
        bb = data["budget_breakdown"]
        col1, col2, col3 = st.columns(3)
        col1.metric("Estimated total", f"{bb.get('total_estimated', 0)} {bb.get('currency', '')}")
        col2.metric("Your budget", f"{bb.get('budget', 0)} {bb.get('currency', '')}")
        col3.metric("Status", data["budget_status"].upper())
        if data["budget_status"] == "over" and data["suggestions"]:
            st.warning("Over budget — here are some suggested swaps:")
            for s in data["suggestions"]:
                st.write(f"- {s}")

    # --- Hotels & Flights ---
    with tab5:
        st.subheader("🏨 Hotel suggestions")
        for h in data.get("hotel_suggestions", []):
            st.write(f"- {h}")
        st.subheader("✈️ Flight tips")
        for f in data.get("flight_suggestions", []):
            st.write(f"- {f}")
        st.caption("These are AI-summarized search results, not live prices — verify on a booking site before purchasing.")
