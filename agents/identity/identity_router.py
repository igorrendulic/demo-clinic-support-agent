from services.user_service import UserService
from agents.models.state import ConversationState
from langgraph.types import Command
from typing import Literal
from enum import StrEnum
from langgraph.graph import END

user_service = UserService()

class IdentityRoute(StrEnum):
    """
    Pydantic model for the identity routing path.
    """
    # "working" nodes
    IDENTITY_COLLECTOR_NODE = "identity_collector_node"
    IDENTITY_ROUTING_NODE = "identity_routing_node"
    IDENTITY_VERIFICATION_NODE = "identity_verification_node"

    # next step nodes
    MAIN_APPOINTMENT_NODE = "main_appointment_node"
    REDIRECT_TO_NEW_PATIENT_HANDOFF = "redirect_to_new_patient_handoff"
    NEW_PATIENT_CONFIRMATION_REQUEST_NODE = "new_patient_confirmation_request_node"
    # ASK_FOR_MISSING_IDENTITY_INFO = "ask_for_missing_identity_info"

IdentityRoutingPath = Literal[
    IdentityRoute.IDENTITY_COLLECTOR_NODE,
    IdentityRoute.IDENTITY_ROUTING_NODE,
    IdentityRoute.IDENTITY_VERIFICATION_NODE,
    IdentityRoute.MAIN_APPOINTMENT_NODE,
    IdentityRoute.REDIRECT_TO_NEW_PATIENT_HANDOFF,
    IdentityRoute.NEW_PATIENT_CONFIRMATION_REQUEST_NODE,
    # IdentityRoute.ASK_FOR_MISSING_IDENTITY_INFO,
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
            goto=IdentityRoute.MAIN_APPOINTMENT_NODE,
        )

    # if user not verified, and not new patient but has all the data, then ask if this is a new patient
    if not state.get("user_verified") and state.get("is_new_patient") == None and user.name and user.date_of_birth and (user.phone or user.ssn_last_4):
        return Command(
            goto=IdentityRoute.NEW_PATIENT_CONFIRMATION_REQUEST_NODE,
        )

    if state.get("is_new_patient") == False and state.get("user_verified") == False:
        return Command(
            goto=END, # continue asking user for more information
            # TODO! maybe a node for information fixing? with user confirmation saying...ok..it's correct
        )

    if state.get("is_new_patient") == True and state.get("user_verified") == False:
        return Command(
            goto=IdentityRoute.REDIRECT_TO_NEW_PATIENT_HANDOFF,
        )

    # fallback (more info needed from user)
    return Command(
        goto=END,
    )