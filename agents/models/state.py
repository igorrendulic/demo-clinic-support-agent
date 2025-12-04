from typing import Annotated, Literal, Sequence, TypedDict, Any

from langgraph.graph.message import add_messages
from agents.identity.prompts.intent_prompt import IntentResult
from langchain_core.messages import BaseMessage
from agents.models.user import User
from pydantic import Field

def add_intents(left: list[IntentResult], right: list[IntentResult]) -> list[IntentResult]:
    """
    Merge two lists of intents.
    - Keep original order of first appearance of an intent.
    - Enforce uniqueness (no duplicates)
    """
    if len(right) == 0:
        return left
    for r in right:
        if r.intent not in [i.intent for i in left]:
            left.append(r)
    return left

def update_appointment_stack_reducer(left: list[str], right: list[str]) -> list[str]:
    """
    Update the appointment stack reducer.
    - Keep original order of first appearance of an item.
    """
    if right is None:
        return left
    if right == "pop":
        return left[:-1]
    return left + [right]

class ConversationState(TypedDict):
    user: User = Field(default=None, description="The user's information")
    urgency_level: int = Field(default=1, description="The urgency level of the user's request")
    urgency_reason: str = Field(default="No urgency", description="The reason for the urgency")
    messages: Annotated[Sequence[BaseMessage], add_messages] # conversational messages so far
    intents: Annotated[list[IntentResult], add_intents] # intents detected so far with add_intent reducer
    user_verified: bool = False # whether the user's identity has been verified
    is_new_patient: bool | None = None # whether the user is a new patient
    identity_fullfillment_number_of_corrections: int = -1 # number of corrections made to the user's identity information
    appointment_state: Annotated[
        list[
            Literal[
                "primary_appointment_node",
                "list_appointments",
            ]
        ],
        update_appointment_stack_reducer
    ] # the state of the appointment