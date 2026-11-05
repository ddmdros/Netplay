from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..agents import game_agent

router = APIRouter()

MAX_HISTORY = 10  # últimas mensagens que o front manda: contexto suficiente sem inflar o prompt


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    input: str = Field(min_length=1, max_length=2000)
    user_id: str
    history: list[Message] = []


class ChatResponse(BaseModel):
    response: str


@router.post("/chat", response_model=ChatResponse)
def handle_chat_message(request: ChatRequest):
    try:
        agent = game_agent.build_agent(request.user_id)
        history = [m.model_dump() for m in request.history[-MAX_HISTORY:]]
        return ChatResponse(response=game_agent.answer(agent, request.input, history))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no agente: {e}") from e
