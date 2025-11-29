from langgraph.graph import StateGraph
from agents.models.state import ConversationState
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from agents.identity.identity_collector_node import identity_collector_node
from agents.identity.identity_verification_node import identity_verification_node, new_patient_confirmation_request_node
from agents.identity.new_patient_handoff import new_patient_handoff_node
from agents.appointment.main_appointment_node import main_appointment_node
from agents.models.user import User
from agents.identity.identity_router import IdentityRoute, identity_routing_node
import os

def initialize_state(state: ConversationState) -> ConversationState:
   return {
        # keep existing values if present, otherwise defaults
        "user": state.get("user", User()),
        "messages": state.get("messages", []),
        "intents": state.get("intents", []),
        "active_intent": state.get("active_intent"),  # can be None
        "user_verified": state.get("user_verified", False),
    }

workflow = StateGraph(ConversationState)

# "worker" nodes
workflow.add_node(IdentityRoute.IDENTITY_ROUTING_NODE, identity_routing_node)
workflow.add_node(IdentityRoute.IDENTITY_COLLECTOR_NODE, identity_collector_node)
workflow.add_node(IdentityRoute.IDENTITY_VERIFICATION_NODE, identity_verification_node)

# next steps for identity
workflow.add_node(IdentityRoute.NEW_PATIENT_CONFIRMATION_REQUEST_NODE, new_patient_confirmation_request_node)
workflow.add_node(IdentityRoute.REDIRECT_TO_NEW_PATIENT_HANDOFF, new_patient_handoff_node)
workflow.add_node(IdentityRoute.MAIN_APPOINTMENT_NODE, main_appointment_node) # main appointment node
# workflow.add_node(IdentityRoute.ASK_FOR_MISSING_IDENTITY_INFO, ask_for_missing_identity_info_node)

# always to go to verification after collecting the data (collector -> verification -> router)
workflow.add_edge(IdentityRoute.IDENTITY_COLLECTOR_NODE, IdentityRoute.IDENTITY_VERIFICATION_NODE)
workflow.add_edge(IdentityRoute.IDENTITY_VERIFICATION_NODE, IdentityRoute.IDENTITY_ROUTING_NODE)
workflow.add_edge(IdentityRoute.NEW_PATIENT_CONFIRMATION_REQUEST_NODE, IdentityRoute.IDENTITY_ROUTING_NODE)

workflow.add_edge(START, IdentityRoute.IDENTITY_COLLECTOR_NODE)

is_api_mode = os.getenv("RUN_MODE") == "api"
print(f"is_api_mode: {is_api_mode}")
if is_api_mode:
    memory = InMemorySaver()
    graph = workflow.compile(checkpointer=memory)
else:
    graph = workflow.compile()