"""LangGraph state machine wiring together all 5 agents in sequence."""
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

from agents.intake_agent import intake_node
from agents.research_agent import research_node
from agents.attractions_agent import attractions_node
from agents.itinerary_agent import itinerary_node
from agents.budget_agent import budget_node
from agents.logistics_agent import travel_logistics_node


class TripState(TypedDict):
    preferences: dict
    destination_info: dict
    weather_forecast: list
    attractions: list
    raw_itinerary: list
    final_itinerary: list
    budget_breakdown: dict
    budget_status: str
    suggestions: list
    hotel_suggestions: list
    transport_options: list
    local_recommendations: list


def build_graph():
    g = StateGraph(TripState)

    # Note: node names must not collide with TripState field names, or
    # LangGraph raises "already being used as a state key" — hence "_agent" suffix.
    g.add_node("intake_agent", intake_node)
    g.add_node("research_agent", research_node)
    g.add_node("attractions_agent", attractions_node)
    g.add_node("itinerary_agent", itinerary_node)
    g.add_node("budget_agent", budget_node)
    g.add_node("logistics_agent", travel_logistics_node)

    g.set_entry_point("intake_agent")
    g.add_edge("intake_agent", "research_agent")
    g.add_edge("research_agent", "attractions_agent")
    g.add_edge("attractions_agent", "itinerary_agent")
    g.add_edge("itinerary_agent", "budget_agent")
    g.add_edge("budget_agent", "logistics_agent")
    g.add_edge("logistics_agent", END)

    return g.compile()


trip_graph = build_graph()
