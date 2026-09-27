import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END

from app.agents.heritage_agent import select_heritage_for_trip
from app.agents.recommendation_agent import build_recommendations
from app.agents.itinerary_agent import build_itinerary
from app.agents.safety_agent import build_safety_tips, SAFETY_DISCLAIMER
from app.services.weather_service import get_weather
from app.services.travel_service import get_route


class TripState(TypedDict, total=False):
    request: dict
    heritage: list
    weather: dict
    travel: dict
    recommendations: dict
    itinerary: list
    safety: list
    agent_log: Annotated[list, operator.add]


async def heritage_node(state: TripState):
    req = state["request"]
    heritage = select_heritage_for_trip(req.get("destination", ""), req.get("interests", ""))
    return {
        "heritage": heritage,
        "agent_log": [{"agent": "Heritage Agent", "status": "completed"}],
    }


async def weather_node(state: TripState):
    req = state["request"]
    result = await get_weather(req.get("destination", ""), req.get("date", ""), int(req.get("days", 1)))
    return {
        "weather": result,
        "agent_log": [{"agent": "Weather Agent", "status": "completed" if result.get("available") else "unavailable"}],
    }


async def travel_node(state: TripState):
    req = state["request"]
    travel = await get_route(req.get("from", ""), req.get("destination", ""))
    return {
        "travel": travel,
        "agent_log": [{"agent": "Travel Agent", "status": "completed" if travel.get("available") else "unavailable"}],
    }


async def recommendation_node(state: TripState):
    rec = build_recommendations(state)
    return {
        "recommendations": rec,
        "agent_log": [{"agent": "Recommendation Agent", "status": "completed"}],
    }


async def itinerary_node(state: TripState):
    itinerary = build_itinerary(state)
    return {
        "itinerary": itinerary,
        "agent_log": [{"agent": "Itinerary Agent", "status": "completed"}],
    }


async def safety_node(state: TripState):
    tips = build_safety_tips(state)
    return {
        "safety": tips,
        "agent_log": [{"agent": "Safety Agent", "status": "completed"}],
    }


def build_graph():
    graph = StateGraph(TripState)
    graph.add_node("heritage", heritage_node)
    graph.add_node("weather", weather_node)
    graph.add_node("travel", travel_node)
    graph.add_node("recommendation", recommendation_node)
    graph.add_node("itinerary", itinerary_node)
    graph.add_node("safety", safety_node)

    graph.add_edge(START, "heritage")
    graph.add_edge(START, "weather")
    graph.add_edge(START, "travel")
    graph.add_edge("heritage", "recommendation")
    graph.add_edge("weather", "recommendation")
    graph.add_edge("travel", "recommendation")
    graph.add_edge("recommendation", "itinerary")
    graph.add_edge("itinerary", "safety")
    graph.add_edge("safety", END)
    return graph.compile()
