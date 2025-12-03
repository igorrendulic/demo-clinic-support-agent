from agents.models.state import ConversationState
from langchain_core.messages import AIMessage

async def new_patient_handoff_node(state: ConversationState) -> dict:
    """
    Node: handoff to a doctor
    - Reads the user info from the state
    - Hands off to a doctor
    """
    return await {"messages": [AIMessage(content=
    """For new patients please go to this website: https://www.acme.com/new-patient-form, fill out the form, and come back to me. 
    If you're existing patient and you had trouble with verifying your identity please call our support line at 1-800-555-1234  . 
    Our support line is open 24/7 and is staffed by friendly and helpful representatives who will help you with your appointment.
    Thank you for using ACME Health clinic and have a great day!
    """)]}