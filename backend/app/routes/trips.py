from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.agents.orchestrator import plan_trip
from app.ratelimit import limit

router = APIRouter(prefix="/plan", tags=["trips"])


class TripRequest(BaseModel):
    from_location: str = Field(min_length=2, max_length=120)
    destination: str = Field(min_length=2, max_length=120)
    date: str
    days: int = Field(ge=1, le=14)
    budget: float = Field(ge=0)
    interests: str = Field(default="", max_length=200)
    travelers: int = Field(default=1, ge=1, le=20)


@router.post("", dependencies=[Depends(limit(10))])
async def create_plan(req: TripRequest):
    return await plan_trip(
        {
            "from": req.from_location,
            "destination": req.destination,
            "date": req.date,
            "days": req.days,
            "budget": req.budget,
            "interests": req.interests,
            "travelers": req.travelers,
        }
    )
