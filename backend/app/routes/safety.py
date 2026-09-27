from fastapi import APIRouter
from app.agents.safety_agent import SAFETY_DISCLAIMER

router = APIRouter(prefix="/safety", tags=["safety"])


@router.get("")
def safety_info():
    return {
        "disclaimer": SAFETY_DISCLAIMER,
        "trip_safety": {
            "share_trip": "Share destination, dates and contact details with a trusted person.",
            "trusted_contact": "Designate someone who receives your live itinerary updates.",
            "emergency": "Dial 112 (India unified emergency). For medical: 108 in many states.",
            "weather_precautions": "Review live forecast before outdoor heritage visits.",
            "checklist": [
                "Government ID and copies",
                "Emergency contact card",
                "First-aid basics",
                "Monument entry permits if required",
                "Hydration and sun/rain protection",
            ],
        },
        "group_safety": {
            "report_user": "Prototype: report inappropriate behaviour to moderators.",
            "block_user": "Prototype: block users from group interactions.",
            "guidelines": [
                "Respect local communities and monument rules",
                "No harassment or discrimination",
                "Verify group details before meeting strangers",
            ],
            "verification_status": "Placeholder — verified badge indicates prototype trust indicator only.",
        },
        "women_safety": {
            "prefer_verified_groups": "Choose groups with verified organizer badge when available.",
            "trusted_contact": "Share live location and check-in times.",
            "share_trip": "Share full itinerary including accommodation areas.",
            "checklist": [
                "Travel in well-lit, populated areas at night",
                "Keep emergency numbers accessible",
                "Trust instincts — leave uncomfortable situations",
                "Use official monument guides where available",
            ],
        },
    }
