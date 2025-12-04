import uuid
from typing import Tuple
import pathlib
import sys
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from langgraph.checkpoint.memory import InMemorySaver

GREEN = "\033[92m"
RESET = "\033[0m"

BLUE = "\033[38;2;0;140;255m"

root = pathlib.Path(__file__).resolve().parents[1]  # go up 1 directory
sys.path.append(str(root))

from agents.graph import workflow # graph instance
from agents.hooks.evaluator_callback import EvaluatorCallbackHandler

inmemory = InMemorySaver()
graph = workflow.compile(checkpointer=inmemory)

eval_callback = EvaluatorCallbackHandler()

async def run_graph_turn(message: str, thread_id: str | None = None) -> Tuple[str, str]:
    """
    Run a single turn of the graph, respecting interrupts.
    Returns (assistant_message, thread_id).
    """

    tid = thread_id or str(uuid.uuid4())
    config = {"configurable": 
        {"thread_id": tid},
        "callbacks": [eval_callback]
    }
    
    user_message = HumanMessage(content=message)

    # 1) Get current state for this thread
    snapshot = await graph.aget_state(config)
    # 2) Decide whether to resume an interrupt, or run normally
    if snapshot.interrupts and len(snapshot.interrupts) > 0:
        # we're resuming an interrupted task
        result = await graph.ainvoke(
            Command(resume=message),
            config=config,
        )
    else:
        # normal first-time / regular turn
        result = await graph.ainvoke(
            {"messages": [user_message]},
            config=config,
        
        )

    # 3) Check if we hit a new interrupt
    snapshot = await graph.aget_state(config)
    if snapshot.interrupts and len(snapshot.interrupts) > 0:
        interrupt_value = snapshot.interrupts[0].value
        return interrupt_value, tid

    # 4) Otherwise, return the latest assistant message
    latest_msg = result["messages"][-1].content
    if isinstance(latest_msg, list):
        last_text = latest_msg[-1].get("text", "")
    else:
        last_text = latest_msg

    return last_text, tid

def print_messages(message, color: str = GREEN):
    print(f"🧪 ➡️ {color}{message}{RESET}")