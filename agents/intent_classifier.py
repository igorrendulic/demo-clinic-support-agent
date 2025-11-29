from agents.models.intent import Intent, BOOK_APPOINTMENT_INTENT, ID_VERIFICATION_INTENT
from agents.models.state import ConversationState
from langchain_core.messages import HumanMessage
from typing import Sequence
from langchain_core.messages import BaseMessage

def detect_intents_from_messages(messages: Sequence[BaseMessage]) -> list[Intent]:
    """
    Detect the intents from the messages.
    """
    last_user = next(
        (m for m in reversed(messages) if isinstance(m, HumanMessage)), None)
    

def classify_intent(state: ConversationState) -> list[Intent]:
    """
    Classify the intent of the message.
    """
    # TODO: Implement intent classification logic
    return [BOOK_APPOINTMENT_INTENT, ID_VERIFICATION_INTENT]