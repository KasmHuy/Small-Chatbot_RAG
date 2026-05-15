"""FastAPI wrapper for the local RAG chat pipeline."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

try:
    from chat import run_chat_turn
except ImportError:  # pragma: no cover - fallback for package-style imports
    from .chat import run_chat_turn

app = FastAPI()


class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    response: str


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest) -> ChatResponse:
    response = run_chat_turn(request.prompt, history=[])
    return ChatResponse(response=response)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
