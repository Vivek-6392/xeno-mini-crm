"""
AI Agent API
============
Exposes a streaming SSE endpoint for the Copilot chat interface.
The LangGraph agent runs in a thread pool so the async event loop is not blocked.
"""
from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.agents.graph import run_agent
from app.schemas import AgentChatRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/chat")
async def agent_chat(request: AgentChatRequest):
    """
    Accepts the current user message + conversation history.
    Streams the agent response as Server-Sent Events (SSE).

    SSE event format:
        data: {"type": "token", "content": "..."}
        data: {"type": "done"}
        data: {"type": "error", "content": "..."}
    """

    async def event_stream():
        try:
            history = [m.model_dump() for m in request.history]
            # Run the synchronous LangGraph agent in a thread
            response = await asyncio.to_thread(run_agent, request.message, history)

            # Stream word-by-word for a live typing effect
            words = response.split(" ")
            for i, word in enumerate(words):
                chunk = word if i == len(words) - 1 else word + " "
                yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
                await asyncio.sleep(0.02)

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as exc:
            logger.exception("Agent error")
            yield f"data: {json.dumps({'type': 'error', 'content': str(exc)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat/sync", summary="Non-streaming fallback")
async def agent_chat_sync(request: AgentChatRequest):
    """Returns the full response as JSON — useful for testing."""
    history = [m.model_dump() for m in request.history]
    response = await asyncio.to_thread(run_agent, request.message, history)
    return {"response": response}
