from services.user_service import UserService
from agents.models.state import ConversationState
from langgraph.types import Command
from typing import Literal
from enum import StrEnum
from langgraph.graph import END

user_service = UserService()

# 
class IdentityRoute(StrEnum):
    """
    Pydantic model for the identity routing path.
    """
    # "working" nodes
    IDENTITY_COLLECTOR_NODE = "identity_collector_node"
    IDENTITY_ROUTING_NODE = "identity_routing_node"
    IDENTITY_VERIFICATION_NODE = "identity_verification_node"

    # next step nodes
    PRIMARY_APPOINTMENT_NODE = "primary_appointment_node"
    REDIRECT_TO_NEW_PATIENT_HANDOFF = "redirect_to_new_patient_handoff"
    NEW_PATIENT_CONFIRMATION_REQUEST_NODE = "new_patient_confirmation_request_node"
    IDENTITY_FULLFILLMENT_HELPER_NODE = "identity_fullfillment_helper_node"
    VALIDATE_CORRECTED_INPUT = "validate_corrected_input"
    IDENTITY_ASK_USER_TO_CORRECT_INFORMATION = "identity_ask_user_to_correct_information"
    CLEANUP_MESSAGES_MIDDLEWARE_NODE = "cleanup_messages_middleware_node"

IdentityRoutingPath = Literal[
    IdentityRoute.IDENTITY_COLLECTOR_NODE,
    IdentityRoute.IDENTITY_ROUTING_NODE,
    IdentityRoute.IDENTITY_VERIFICATION_NODE,
    IdentityRoute.PRIMARY_APPOINTMENT_NODE,
    IdentityRoute.REDIRECT_TO_NEW_PATIENT_HANDOFF,
    IdentityRoute.NEW_PATIENT_CONFIRMATION_REQUEST_NODE,
    IdentityRoute.IDENTITY_FULLFILLMENT_HELPER_NODE,
    IdentityRoute.VALIDATE_CORRECTED_INPUT,
    IdentityRoute.IDENTITY_ASK_USER_TO_CORRECT_INFORMATION,
    IdentityRoute.CLEANUP_MESSAGES_MIDDLEWARE_NODE,
]

def identity_routing_node(state: ConversationState) -> Command[IdentityRoutingPath]:
    """
    Routes the user to the appropriate node based on the state.
    """
    user = state.get("user")
    if user is None:
        # short circuit for out initial node
        return Command(
            goto=END,
        )
    
    if state.get("is_new_patient"):
        return Command(
            goto=IdentityRoute.REDIRECT_TO_NEW_PATIENT_HANDOFF,
        )
   
    if state.get("user_verified") and not state.get("is_new_patient"):
        return Command(
            goto=IdentityRoute.CLEANUP_MESSAGES_MIDDLEWARE_NODE, # movin to hard context switch (removing all previous messages)
        )

    # if user not verified, and not new patient but has all the data, then ask if this is a new patient
    if not state.get("user_verified") and state.get("is_new_patient") == None and user.name and user.date_of_birth and (user.phone or user.ssn_last_4):
        return Command(
            goto=IdentityRoute.NEW_PATIENT_CONFIRMATION_REQUEST_NODE,
        )

    
    # if user is not verified, all data exists for identity, but user is not verified (user said they're existing user, but data doesn't match)
    if state.get("is_new_patient") == False and state.get("user_verified") == False:
        return Command(
            goto=IdentityRoute.IDENTITY_FULLFILLMENT_HELPER_NODE, # continue asking user for more information
        )

    if state.get("is_new_patient") == True and state.get("user_verified") == False:
        return Command(
            goto=IdentityRoute.REDIRECT_TO_NEW_PATIENT_HANDOFF,
        )

    # fallback (more info needed from user)
    return Command(
        goto=END,
    )