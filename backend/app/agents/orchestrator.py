from app.agents.graph import build_graph
from app.agents.safety_agent import SAFETY_DISCLAIMER

GRAPH = build_graph()

AGENT_ORDER = [
    "Orchestrator",
    "Heritage Agent",
    "Weather Agent",
    "Travel Agent",
    "Recommendation Agent",
    "Itinerary Agent",
    "Safety Agent",
]


async def plan_trip(request: dict) -> dict:
    initial_log = [{"agent": "Orchestrator", "status": "completed"}]
    result = await GRAPH.ainvoke({"request": request, "agent_log": initial_log})
    result.pop("request", None)

    log_map = {}
    for entry in result.get("agent_log", []):
        log_map[entry["agent"]] = entry["status"]

    agent_activity = []
    for name in AGENT_ORDER:
        if name == "Orchestrator":
            agent_activity.append({"name": name, "status": "completed", "icon": "🧠"})
        else:
            status = log_map.get(name, "completed")
            if name == "Weather Agent" and not result.get("weather", {}).get("available"):
                status = "unavailable"
            if name == "Travel Agent" and not result.get("travel", {}).get("available"):
                status = "unavailable"
            agent_activity.append({"name": name, "status": status, "icon": "✓"})

    result["agent_activity"] = agent_activity
    result["safety_disclaimer"] = SAFETY_DISCLAIMER
    return result
