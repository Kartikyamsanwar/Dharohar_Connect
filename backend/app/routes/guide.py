from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.agents.heritage_agent import answer_heritage_question
from app.ratelimit import limit

router = APIRouter(prefix="/chat", tags=["guide"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=600)


@router.post("", dependencies=[Depends(limit(20))])
def chat(req: ChatRequest):
    return answer_heritage_question(req.message)
