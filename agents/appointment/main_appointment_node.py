from agents.models.state import ConversationState
from langchain_core.messages import AIMessage

def main_appointment_node(state: ConversationState) -> dict:
    """
    Node: main appointment node
    - Reads the user info from the state
    - Hands off to a doctor
    """
    user = state.get("User")
    return {"messages": [AIMessage(content="Hi. This is your appointment assistant. How can I help you today?")]}