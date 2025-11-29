from typing import Annotated, Sequence, TypedDict, Any

from langgraph.graph.message import add_messages
from agents.models.intent import Intent, IntentType
from langchain_core.messages import BaseMessage
from agents.models.user import User
from pydantic import Field

def add_intents(left: list[Intent], right: list[Intent]) -> list[IntentType]:
    """
    Merge two lists of intents.
    - Keep original order of first appearance of an intent.
    - Enforce uniqueness (no duplicates, but count multiple occurrences and modify completed status)
    """

    for intent in right:
        if intent.name in [i.name for i in left]:
            left[left.index(intent)].completed = intent.completed
        else:
            left.append(intent)
    return left

def add_active_intent(left: Intent | None, right: Intent | None) -> Intent | None:
    """
    Add the active intent to the state.
    """
    if right:
        return right
    return left

class ConversationState(TypedDict):
    user: User = Field(default=None, description="The user's information")
    urgency_level: int = Field(default=1, description="The urgency level of the user's request")
    urgency_reason: str = Field(default="No urgency", description="The reason for the urgency")
    messages: Annotated[Sequence[BaseMessage], add_messages] # conversational messages so far
    intents: Annotated[list[Intent], add_intents] # intents detected so far with add_intent reducer
    active_intent: Annotated[Intent | None, add_active_intent] # the intent that is currently being processed
    user_verified: bool = False # whether the user's identity has been verified
    is_new_patient: bool | None = None # whether the user is a new patient