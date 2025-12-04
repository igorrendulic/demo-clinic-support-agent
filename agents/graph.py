from langgraph.graph import StateGraph
from agents.models.state import ConversationState
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from agents.identity.identity_collector_node import identity_collector_node
from agents.identity.identity_verification_node import identity_verification_node, new_patient_confirmation_request_node
from agents.identity.handoffs import new_patient_handoff_node, urgency_handoff_node
from agents.appointment.primary_appointment_node import primary_appointment_node
from agents.appointment.clear_history_node import cleanup_messages_middleware_node
from agents.identity.identity_collector_node import ask_user_to_complete_information, validate_identity_completness
from agents.identity.identity_fullfillment_helper_node import identity_fullfillment_helper_node, validate_corrected_input, ask_user_to_correct_information
from agents.models.user import User
from agents.identity.identity_router import IdentityRoute, identity_routing_node
from agents.appointment.cancel_appointment_node import cancel_appointment_node, cancel_appointment_node_tools
from agents.appointment.add_appointment_node import add_appointment_node, add_appointment_node_tools
from agents.appointment.util.helpers import create_entry_node, create_tool_node_with_fallback, pop_appointment_stack_state
from agents.appointment.appointment_router import AppointmentRoute, route_primary_appointment, route_add_appointment, route_cancel_appointment
from agents.appointment.primary_appointment_node import primary_appointment_node_tools
from agents.appointment.reschedule_appointment_node import reschedule_appointment_node, reschedule_appointment_node_tools
from agents.appointment.appointment_router import route_reschedule_appointment

import os
from agents.route_start import route_start

workflow = StateGraph(ConversationState)

# "worker" nodes
workflow.add_node(IdentityRoute.IDENTITY_ROUTING_NODE, identity_routing_node)
workflow.add_node(IdentityRoute.IDENTITY_COLLECTOR_NODE, identity_collector_node)
workflow.add_node(IdentityRoute.IDENTITY_VERIFICATION_NODE, identity_verification_node)

# next steps for identity
workflow.add_node(IdentityRoute.NEW_PATIENT_CONFIRMATION_REQUEST_NODE, new_patient_confirmation_request_node)
workflow.add_node(IdentityRoute.REDIRECT_TO_NEW_PATIENT_HANDOFF, new_patient_handoff_node)
workflow.add_node(IdentityRoute.REDIRECT_TO_URGENCY_HANDOFF, urgency_handoff_node)
workflow.add_node(IdentityRoute.IDENTITY_FULLFILLMENT_HELPER_NODE, identity_fullfillment_helper_node)
workflow.add_node(IdentityRoute.VALIDATE_CORRECTED_INPUT, validate_corrected_input)
workflow.add_node(IdentityRoute.IDENTITY_ASK_USER_TO_CORRECT_INFORMATION, ask_user_to_correct_information)
workflow.add_node(IdentityRoute.IDENTITY_ASK_USER_TO_COMPLETE_INFORMATION, ask_user_to_complete_information)
workflow.add_node(IdentityRoute.CLEANUP_MESSAGES_MIDDLEWARE_NODE, cleanup_messages_middleware_node)

# always to go to verification after collecting the data (collector -> verification -> router)
workflow.add_edge(IdentityRoute.IDENTITY_COLLECTOR_NODE, IdentityRoute.IDENTITY_VERIFICATION_NODE)
workflow.add_edge(IdentityRoute.IDENTITY_VERIFICATION_NODE, IdentityRoute.IDENTITY_ROUTING_NODE)
workflow.add_edge(IdentityRoute.NEW_PATIENT_CONFIRMATION_REQUEST_NODE, IdentityRoute.IDENTITY_ROUTING_NODE)
workflow.add_edge(IdentityRoute.IDENTITY_ASK_USER_TO_CORRECT_INFORMATION, IdentityRoute.IDENTITY_FULLFILLMENT_HELPER_NODE)
workflow.add_edge(IdentityRoute.CLEANUP_MESSAGES_MIDDLEWARE_NODE, IdentityRoute.PRIMARY_APPOINTMENT_NODE)

# Loop back into collector after the user responds
workflow.add_edge(
    IdentityRoute.IDENTITY_ASK_USER_TO_COMPLETE_INFORMATION,
    IdentityRoute.IDENTITY_COLLECTOR_NODE,
)

# asking user to complete the information (required name, DOB and SSN or phone number)
workflow.add_conditional_edges(IdentityRoute.IDENTITY_COLLECTOR_NODE, 
    validate_identity_completness,
    {
        "success": IdentityRoute.IDENTITY_VERIFICATION_NODE,
        "retry": IdentityRoute.IDENTITY_ASK_USER_TO_COMPLETE_INFORMATION,
        "urgency": IdentityRoute.REDIRECT_TO_URGENCY_HANDOFF,
    }
)

# asking user to fix existing information (limited try amounts)
workflow.add_conditional_edges(IdentityRoute.IDENTITY_FULLFILLMENT_HELPER_NODE, 
    validate_corrected_input,
    {
        "success": IdentityRoute.CLEANUP_MESSAGES_MIDDLEWARE_NODE,
        "failure": IdentityRoute.REDIRECT_TO_NEW_PATIENT_HANDOFF,
        "retry": IdentityRoute.IDENTITY_ASK_USER_TO_CORRECT_INFORMATION,
    }
)

# Entry/Start Router
workflow.add_conditional_edges(START, 
    route_start,
    {
        AppointmentRoute.PRIMARY_APPOINTMENT_NODE: AppointmentRoute.PRIMARY_APPOINTMENT_NODE,
        IdentityRoute.IDENTITY_COLLECTOR_NODE: IdentityRoute.IDENTITY_COLLECTOR_NODE,
        "add_appointment": "add_appointment",
        "cancel_appointment": "cancel_appointment",
        "reschedule_appointment": "reschedule_appointment",
    }
)

# adding primary appointment node
workflow.add_node(IdentityRoute.PRIMARY_APPOINTMENT_NODE, primary_appointment_node) # main appointment node

# Appontment part of the graph
# Book appointments assistant
workflow.add_node(AppointmentRoute.ENTER_ADD_APPOINTMENT_NODE, create_entry_node("Appointment Add Assistant", "add_appointment"))
workflow.add_node("add_appointment", add_appointment_node)
workflow.add_edge(AppointmentRoute.ENTER_ADD_APPOINTMENT_NODE, "add_appointment")
workflow.add_node("add_appointment_safe_tools", create_tool_node_with_fallback(add_appointment_node_tools))
workflow.add_edge("add_appointment_safe_tools", "add_appointment")
workflow.add_conditional_edges("add_appointment",
    route_add_appointment,
    {
        "leave_skill": "leave_skill",
        "add_appointment_safe_tools": "add_appointment_safe_tools",
        END: END,
    }
)

# cancel appointment assistant
workflow.add_node(AppointmentRoute.ENTER_CANCEL_APPOINTMENT_NODE, create_entry_node("Appointment Cancel Assistant", "cancel_appointment"))
workflow.add_node("cancel_appointment", cancel_appointment_node)
workflow.add_edge(AppointmentRoute.ENTER_CANCEL_APPOINTMENT_NODE, "cancel_appointment")
workflow.add_node("cancel_appointment_safe_tools", create_tool_node_with_fallback(cancel_appointment_node_tools))
workflow.add_edge("cancel_appointment_safe_tools", "cancel_appointment")
workflow.add_conditional_edges("cancel_appointment",
    route_cancel_appointment,
    {
        "leave_skill": "leave_skill",
        "cancel_appointment_safe_tools": "cancel_appointment_safe_tools",
        END: END,
    }
)

# reschedule appointment assistant
# cancel appointment assistant
workflow.add_node(AppointmentRoute.ENTER_RESCHEDULE_APPOINTMENT_NODE, create_entry_node("Appointment Reschedule Assistant", "reschedule_appointment"))
workflow.add_node("reschedule_appointment", reschedule_appointment_node)
workflow.add_edge(AppointmentRoute.ENTER_RESCHEDULE_APPOINTMENT_NODE, "reschedule_appointment")
workflow.add_node("reschedule_appointment_safe_tools", create_tool_node_with_fallback(reschedule_appointment_node_tools))
workflow.add_edge("reschedule_appointment_safe_tools", "reschedule_appointment")
workflow.add_conditional_edges("reschedule_appointment",
    route_reschedule_appointment,
    {
        "leave_skill": "leave_skill",
        "reschedule_appointment_safe_tools": "reschedule_appointment_safe_tools",
        END: END,
    }
)

# primary assistant
# The assistant can route to one of the delegated assistants,
# directly use a tool, or directly respond to the use
workflow.add_node("primary_appointment_node_tools", create_tool_node_with_fallback(primary_appointment_node_tools))
workflow.add_conditional_edges(AppointmentRoute.PRIMARY_APPOINTMENT_NODE,
    route_primary_appointment,
    [
        AppointmentRoute.ENTER_CANCEL_APPOINTMENT_NODE,
        AppointmentRoute.ENTER_ADD_APPOINTMENT_NODE,
        AppointmentRoute.ENTER_RESCHEDULE_APPOINTMENT_NODE,
        "primary_appointment_node_tools",
        END
    ]
)
workflow.add_edge("primary_appointment_node_tools", AppointmentRoute.PRIMARY_APPOINTMENT_NODE)
# return back to primary appointment node
workflow.add_node("leave_skill", pop_appointment_stack_state)
workflow.add_edge("leave_skill", AppointmentRoute.PRIMARY_APPOINTMENT_NODE)

is_api_mode = os.getenv("RUN_MODE") == "api"
print(f"is_api_mode: {is_api_mode}")
if is_api_mode:
    memory = InMemorySaver()
    graph = workflow.compile(checkpointer=memory)
else:
    graph = workflow.compile()

# os.makedirs("assets", exist_ok=True)
# png_bytes = graph.get_graph().draw_mermaid_png()
# with open("assets/graph.png", "wb") as f:
#     f.write(png_bytes)