"""Safety Agent — context-aware travel safety tips."""

SAFETY_DISCLAIMER = (
    "Safety features shown are prototype concepts and do not replace official emergency services."
)


def build_safety_tips(state: dict) -> list:
    weather = state.get("weather", {})
    req = state.get("request", {})

    tips = [
        "Carry identification and emergency contacts.",
        "Respect monument rules and local customs.",
        "Keep valuables secure and share your trip plan with a trusted contact.",
        "Save local emergency numbers; dial 112 for unified emergency response in India.",
    ]

    if req.get("travelers", 1) > 1:
        tips.append("For group travel: agree on meeting points and share live location with trusted contacts.")

    for item in weather.get("forecast", []) if weather.get("available") else []:
        if item.get("rain_probability", 0) >= 60:
            tips.append(
                "Rain expected on some trip dates: carry rain protection and avoid slippery or exposed areas."
            )
        if item.get("temp_max", item.get("temp", 0)) >= 36:
            tips.append(
                "High heat expected: prefer early morning/evening outdoor visits and stay hydrated."
            )
        if item.get("thunderstorm"):
            tips.append("Thunderstorm risk: avoid exposed hilltops, open ruins and tall isolated structures.")

    return list(dict.fromkeys(tips))
