from re import I
from agents.llms import get_llm_mini_model
from agents.models.state import ConversationState
from agents.models.user import User
from typing import Optional
from pydantic import BaseModel, Field
from logging_config import llm_logger, logger
from langchain_core.messages import HumanMessage
from agents.identity.prompts.identity_assistant import identity_collector_prompt
from langgraph.types import interrupt
from agents.identity.prompts.intent_prompt import IntentResult, intent_prompt
from typing import Literal
import asyncio

llm = get_llm_mini_model(temperature=0.0)

class UpdateInfo(BaseModel):
    """
    Pydantic model for updating the user's information.
    This is used to update the user's information in the state by the identity_collector_node
    """
    name: Optional[str] = Field(default=None, description="The user's full name")
    date_of_birth: Optional[str] = Field(default=None, description="The user's date of birth")
    ssn_last_4: Optional[str] = Field(default=None, description="The user's last 4 digits of their SSN")
    phone_number: Optional[str] = Field(default=None, description="The user's phone number")
    urgency_level: int = Field(default=1, description="The urgency level of the user's request")
    urgency_reason: str = Field(default="No urgency", description="The reason for the urgency")


def init_state(state: ConversationState) -> ConversationState:
    """
    Initializes the state.
    If the user is None, creates a new user with default values.
    Sets the urgency level and reason to default values.
    """
    user = state.get("user")
    if user is None:
        user = User(
            name="",
            date_of_birth="",
            ssn_last_4="",
            phone="",
            urgency_level=1,
            urgency_reason="No urgency",
        )
    state["user"] = user
    state["urgency_level"] = 1
    state["urgency_reason"] = "No urgency"
    state["is_new_patient"] = False
    state["user_verified"] = False
    state["identity_fullfillment_number_of_corrections"] = 0
    return state

def missing_required_fields(user: User | dict | None) -> list[str]:
    """
    Checks if the user has all required fields for validator to check agains the database
    """
    if isinstance(user, User):
        u = user
    elif isinstance(user, dict):
        u = User(**user)
    else:
        return ["name", "date_of_birth"]

    missing = []
    if not u.name:
        missing.append("Full Name")
    if not u.date_of_birth:
        missing.append("Date of Birth")
    if not u.ssn_last_4 and not u.phone:
        missing.append("Last 4 digits of SSN or Phone Number")

    return missing


def user_to_prompt_vars(state: ConversationState):
    """
    Converts the user to a dictionary of variables for the identity_collector_prompt.
    """
    user = state.get("user")
    if not user:
        # If user is None, create a new user with default values
        return {
            "messages": state.get("messages", []),
            "name": "",
            "phone_number": "",
            "date_of_birth": "",
            "ssn_last_4": "",
            "urgency_level": 1,
            "urgency_reason": "No urgency",
            "missing_information": missing_required_fields(user),
        }

    # Use actual last user message if present, else synthetic one
    # If user is not None, use the actual user values
    return {
        "messages": state.get("messages", []),
        "name": user.name or "",
        "phone_number": user.phone or "",
        "date_of_birth": user.date_of_birth or "",
        "ssn_last_4": user.ssn_last_4 or "",
        "urgency_level": state.get("urgency_level", 1),
        "urgency_reason": state.get("urgency_reason", "No urgency"),
        "is_new_patient": state.get("is_new_patient", False),
        "missing_information": missing_required_fields(user),
    }


def merge_users(existing_user: User | None, new_user: UpdateInfo) -> User:
    """
    Merges two users together. If the existing user is None, creates a new user.
    """
    if existing_user is None:
        existing_user = User()
    return existing_user.model_copy(
        update={
            "name": new_user.name or existing_user.name,
            "date_of_birth": new_user.date_of_birth or existing_user.date_of_birth,
            "phone": new_user.phone_number or existing_user.phone,
            "ssn_last_4": new_user.ssn_last_4 or existing_user.ssn_last_4,
        }
    )

def validate_identity_completness(state: ConversationState) -> Literal["success", "retry", "urgency"]:
    """
    Validates the identity completeness (we require all the data to be present)
    We also don't allow endless loops of asking user for information (max 10 corrections)
    """
    user = state.get("user")

    if state.get("urgency_level", 0) >= 8:
        return "urgency"

    if not user:
        return "retry"
    
    if not user.name or not user.date_of_birth or not (user.phone or user.ssn_last_4):
        return "retry"
    
    return "success"

async def ask_user_to_complete_information(state: ConversationState):
    """
    Ask user to complete their information.
    """
    user = state.get("user")
    missing_info = missing_required_fields(user)

    missing_info_str = f"Please provide the following information: \n- {'\n- '.join(missing_info)}"
    user_input = interrupt(missing_info_str)

    return {
        "messages": [HumanMessage(content=user_input)],
        "user": user,
    }

async def identity_collector_node(state: ConversationState) -> dict:
    """
    Graph node: call the identity_collector_runnable_node (LLM)
    which returns a User, then merge into state["User"].
    """

    if "user" not in state or state["user"] is None:
        state = init_state(state)
    user: User = state.get("user")

    structured_llm = llm.with_structured_output(UpdateInfo)
    chain = identity_collector_prompt | structured_llm

    structured_intent_llm = llm.with_structured_output(IntentResult)
    intent_chain = intent_prompt | structured_intent_llm  # a separate prompt just for intent
    last_human_msg = next(
        (m for m in reversed(state["messages"]) if m.type == "human"), None
    )
    intent_task = None
    if last_human_msg:
        intent_task = intent_chain.ainvoke({"text": last_human_msg.content})


    # parallel invocation
    template_params = user_to_prompt_vars(state)

    identity_task = chain.ainvoke(template_params)
    identity_res, intent_res = await asyncio.gather(
        identity_task,
        intent_task,
        return_exceptions=True,
    )

    llm_logger.info(f"identity_collector_node response: {identity_res}")
    llm_logger.info(f"identity_collector_node intent response: {intent_res}")

    user = merge_users(user, identity_res)

    out = {
        "user": user,
        "urgency_level": identity_res.urgency_level,
        "urgency_reason": identity_res.urgency_reason,
    }

    # optimistic injection — only add if successful
    if intent_res is not None and isinstance(intent_res, IntentResult):
        out["intents"] = [intent_res]

    return out