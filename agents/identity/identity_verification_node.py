
from agents.models.state import ConversationState
from typing import Literal
from services.user_service import UserService
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from agents.llms import get_llm_mini_model
from langchain_core.messages import SystemMessage
from langgraph.types import interrupt
from logging_config import llm_logger

user_service = UserService()

llm = get_llm_mini_model(temperature=0.0)

class NewPatientIntent(BaseModel):
    """Classify the user's intent regarding their patient status."""
    is_new_patient: bool = Field(
        description="True if the user confirms they are a new patient. False if they say they are an existing patient, made a mistake, or want to retry."
    )
    reasoning: str = Field(
        description="A brief explanation of why you classified the intent this way."
    )

def new_patient_confirmation_request_node(state: ConversationState):
    """
    Asks the user if they are a new patient.
    """
    msg = "Based on the information provided, it appears you are a new patient. If you're a new patient, please say 'Yes'. In case you wish to correct your information, please say 'No' and correct your information."
    user_response_text = interrupt(msg)

    new_human_message = HumanMessage(content=user_response_text)
    structured_llm = llm.with_structured_output(NewPatientIntent)
    messages_to_send = [
        SystemMessage(content="The user was asked if they are a new patient. Classify their response."),
        new_human_message,
    ]
    classification = structured_llm.invoke(messages_to_send)
    
    llm_logger.info(classification)

    return {
        "messages": [new_human_message],
        "is_new_patient": classification.is_new_patient,
        "user_verified": False,
    }


def identity_verification_node(state: ConversationState) -> dict:
    """
        Decides the next step:
        1. If tool calls exist -> update state.
        2. If all info is collected -> handoff to set_user_info.
        3. Otherwise -> respond to user (ask more questions).
    """
    user = state.get("user")

    # simple check if user provided all details and if found in the database
    if user.name and user.date_of_birth and (user.phone or user.ssn_last_4):
        user = user_service.get_user(user.name, user.date_of_birth, user.phone, user.ssn_last_4)
        if user is not None:
            return {
                "user_verified": True,
                "is_new_patient": False,
                "user": user,
            }
        else:
            number_of_corrections = state.get("identity_fullfillment_number_of_corrections", 0)
            # exit the identity data correction loop
            if number_of_corrections >= 3:
                return {
                    "user_verified": False,
                    "is_new_patient": True,
                }
            return {
                "user_verified": False,
            }

    return {
        "user_verified": False,
    }