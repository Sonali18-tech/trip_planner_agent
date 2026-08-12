"""Agent 2 — Destination research.

Geocodes the city, fetches the weather forecast, pulls country info,
and web-searches local tips via Tavily.
"""
import os
import requests
from dotenv import load_dotenv

from tools.geocoding import get_coordinates
from tools.weather import get_weather_forecast
from tools.search import tavily_search

load_dotenv()


def research_node(state: dict) -> dict:
    prefs = state["preferences"]
    city = prefs["destination"]

    coords = get_coordinates(city)
    weather = get_weather_forecast(coords["lat"], coords["lon"], days=prefs["num_days"])

    country_info = {}
    try:
        country_r = requests.get(f"https://restcountries.com/v3.1/capital/{city}", timeout=15)
        if country_r.ok:
            country_info = country_r.json()[0]
    except Exception:
        pass  # non-critical — trip still works without it

    try:
        search_tips = tavily_search(f"best things to do in {city} {prefs['travel_style']}")
    except Exception:
        search_tips = []  # non-critical if Tavily key is missing/limit hit

    return {
        **state,
        "destination_info": {**coords, "country": country_info, "search_tips": search_tips},
        "weather_forecast": weather,
    }
