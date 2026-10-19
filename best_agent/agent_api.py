from fastapi import APIRouter
from pydantic import BaseModel
from fastapi.responses import StreamingResponse

#from best_agent.agent_2 import check_ollama, agent_stream, OLLAMA_MODEL
from best_agent.keep_phantom_tool_registry import TOOLS
from agent.neo4_conn import NEO4J_AVAILABLE
from best_agent.agent_2 import check_ollama, agent_stream, OLLAMA_MODEL

# ─────────────────────────────────────────────────────────────
# FastAPI App
# ─────────────────────────────────────────────────────────────
sessions: dict[str, list[dict]] = {}


router = APIRouter(tags=["APT : chat"])



class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


@router.post("/chat")
async def chat(req: ChatRequest):
    """Main chat endpoint — returns SSE stream."""
    if req.session_id not in sessions:
        sessions[req.session_id] = []

    history = sessions[req.session_id][-20:]  # keep last 20 turns

    async def stream_wrapper():
        collected_content = ""
        async for chunk in agent_stream(req.message, history):
            yield chunk
            # collect done event
            if chunk.startswith("event: done"):
                pass

        # Update history
        sessions[req.session_id].append({"role": "user", "content": req.message})
        sessions[req.session_id].append({"role": "assistant", "content": "[streamed]"})

    return StreamingResponse(
        stream_wrapper(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    sessions.pop(session_id, None)
    return {"cleared": True}


@router.get("/health")
async def health():
    ollama_status = await check_ollama()
    return {
        "status": "ok" if ollama_status["available"] else "degraded",
        "ollama": ollama_status,
        "neo4j": NEO4J_AVAILABLE,
        "model": OLLAMA_MODEL,
        "tools": len(TOOLS),
        "active_sessions": len(sessions),
    }


@router.get("/models")
async def models():
    return await check_ollama()




