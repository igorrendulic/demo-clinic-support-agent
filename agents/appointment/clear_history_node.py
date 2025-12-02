from langgraph.graph.message import RemoveMessage
from agents.models.state import ConversationState

def cleanup_messages_middleware_node(state: ConversationState) -> dict:
    """
    Node: clear the history of the conversation
    """
    removal_instructions = [
        RemoveMessage(id = m.id) for m in state.get("messages", [])
    ]
    return {
        "messages": removal_instructions,
    }