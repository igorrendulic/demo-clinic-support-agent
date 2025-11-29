from fastapi import APIRouter
from api.models.chat import ChatRequest, ChatResponse
from agents.graph import graph
from langchain_core.messages import HumanMessage
from langgraph.types import Command
import uuid

chat_router = APIRouter()

@chat_router.post("/chat")
async def chat(request: ChatRequest):
    tid = request.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": tid}}
    user_message = HumanMessage(content=request.message)

    snapshot = await graph.aget_state(config)
    
    # Check if there are active interrupts pending
    if snapshot.tasks and snapshot.tasks[0].interrupts:
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

    snapshot = graph.get_state(config)
    if snapshot.tasks and snapshot.tasks[0].interrupts:
        # OUTCOME X: INTERRUPT HIT
        # The graph ran for a bit, then hit a NEW interrupt() line.
        # We extract the value (the question) and return it.
        interrupt_value = snapshot.tasks[0].interrupts[0].value
        return ChatResponse(message=interrupt_value, thread_id=tid)
    else:
        latest_msg = result["messages"][-1].content
        if isinstance(latest_msg, list):
            last_text = latest_msg[-1].get("text", "")
        else:
            last_text = latest_msg
        return ChatResponse(message=last_text, thread_id=tid)