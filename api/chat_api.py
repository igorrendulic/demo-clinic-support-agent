from fastapi import APIRouter
from api.models.chat import ChatRequest, ChatResponse
from agents.graph import graph
from langchain_core.messages import HumanMessage
from langgraph.types import Command
import uuid
from langchain_core.messages import AIMessage

chat_router = APIRouter()

@chat_router.post("/chat")
async def chat(request: ChatRequest):
    tid = request.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": tid}}
    user_message = HumanMessage(content=request.message)

    snapshot = await graph.aget_state(config)
    
    # Check if there are active interrupts pending
    if snapshot.interrupts:
        result = await graph.ainvoke(
            Command(resume=request.message), 
            config=config
        )
    else:
         # normal mode
        result = await graph.ainvoke(
            {"messages": [user_message]},
            config=config,
        )

    snapshot = await graph.aget_state(config)
    if snapshot.interrupts:
        # OUTCOME X: INTERRUPT HIT
        # The graph ran for a bit, then hit a NEW interrupt() line.
        # We extract the value (the question) and return it.
        interrupt_value = snapshot.interrupts[0].value
        return ChatResponse(message=interrupt_value, thread_id=tid)
    else:
        # Prefer last AI message, not just "last message"
        messages = result["messages"]
        ai_messages = [m for m in messages if isinstance(m, AIMessage)]
        last_msg = ai_messages[-1] if ai_messages else messages[-1]

        content = last_msg.content
        if isinstance(content, list):
            text_chunks = [c.get("text", "") for c in content if isinstance(c, dict)]
            last_text = text_chunks[-1] if text_chunks else ""
        else:
            last_text = content

        return ChatResponse(message=last_text, thread_id=tid)