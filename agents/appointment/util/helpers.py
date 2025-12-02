from typing import Callable
from langchain_core.messages import HumanMessage, ToolMessage
from agents.models.state import ConversationState
from langchain_core.runnables import RunnableLambda
from langgraph.prebuilt import ToolNode
from langgraph.graph.state import RunnableConfig
from langchain_core.runnables import Runnable, RunnableLambda

class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable
    
    def __call__(self, state: ConversationState, config: RunnableConfig):
        while True:
            result = self.runnable.invoke(state)

            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}

def create_entry_node(assistant_name: str, new_appointment_state: str) -> Callable:
    def appointment_entry_node(state: ConversationState) -> dict:
        tool_call_id = state["messages"][-1].tool_calls[0]["id"]
        return {
            "messages": [
                ToolMessage(
                    content=f"The assistant is now the {assistant_name}. Reflect on the above conversation between the host assistant and the user."
                    f" The user's intent is unsatisfied. Use the provided tools to assist the user. Remember, you are {assistant_name},"
                    " and the booking, update, other other action is not complete until after you have successfully invoked the appropriate tool."
                    " If the user changes their mind or needs help for other tasks, call the CompleteOrEscalate function to let the primary host assistant take control."
                    " Do not mention who you are - just act as the proxy for the assistant.",
                    tool_call_id=tool_call_id,
                )
            ],
            "appointment_state": new_appointment_state,
        }

    return appointment_entry_node

def create_tool_node_with_fallback(tools: list) -> dict:
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )

def handle_tool_error(state) -> dict:
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }

def create_tool_node_with_fallback(tools: list) -> dict:
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )

def pop_appointment_stack_state(state: ConversationState) -> dict:
    """Pop the appointment stack and return to the main assistant.

    This lets the full graph explicitly track the appointment flow and delegate control
    to specific sub-graphs.
    """
    messages = []
    if state["messages"][-1].tool_calls:
        # Note: Doesn't currently handle the edge case where the llm performs parallel tool calls
        messages.append(
            ToolMessage(
                content="Resuming dialog with the host assistant. Please reflect on the past conversation and assist the user as needed.",
                tool_call_id=state["messages"][-1].tool_calls[0]["id"],
            )
        )
    return {
        "appointment_state": "pop",
        "messages": messages,
    }

def appointment_template_params(state: ConversationState):
    user = state.get("user")
    messages = state.get("messages", [])
    if len(messages) == 0:
        messages = [HumanMessage(content="Respond with a real output.")]
    
    name = getattr(user, "name", None) if user is not None else None

    return {
        "name": name,
        "messages": messages,
    }