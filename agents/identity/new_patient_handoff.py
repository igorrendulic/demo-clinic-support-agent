from agents.models.state import ConversationState
from langchain_core.messages import AIMessage

def new_patient_handoff_node(state: ConversationState) -> dict:
    """
    Node: handoff to a doctor
    - Reads the user info from the state
    - Hands off to a doctor
    """
    # user = state.get("user")
    return {"messages": [AIMessage(content="For new patients please go to this website: https://www.acme.com/new-patient-form, fill out the form, and come back to me. I will then help you with your appointment.")]}