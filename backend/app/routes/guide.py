from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.agents.guide_agent import answer_guide
from app.ratelimit import limit

router = APIRouter(prefix="/chat", tags=["guide"])


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=6000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=600)
    history: list[ChatTurn] = Field(default_factory=list, max_length=12)


@router.post("", dependencies=[Depends(limit(20))])
async def chat(req: ChatRequest):
    return await answer_guide(req.message, [t.model_dump() for t in req.history])
