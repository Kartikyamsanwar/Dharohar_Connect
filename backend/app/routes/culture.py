from fastapi import APIRouter
from app.data_loader import CULTURE, filter_culture

router = APIRouter(prefix="/culture", tags=["culture"])

CULTURE_CATEGORIES = [
    "Architecture",
    "Traditional Arts",
    "Yoga",
    "Ayurveda",
    "Indigenous Games",
    "Performing Arts",
    "Food Heritage",
    "Ancient Science & Engineering",
    "Festivals & Traditions",
]


@router.get("")
def list_culture(category: str = "", region: str = ""):
    return {"items": filter_culture(category, region), "categories": CULTURE_CATEGORIES}
