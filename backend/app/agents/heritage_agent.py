"""Heritage Agent: selects curated heritage sites for the trip planner."""

from app.data_loader import HERITAGE, find_heritage


def select_heritage_for_trip(destination: str, interests: str) -> list:
    selected = find_heritage(destination)
    if selected:
        return [selected]
    interest = interests.lower()
    return [
        x
        for x in HERITAGE
        if interest and interest in (x["category"] + " " + x["description"]).lower()
    ][:3]
