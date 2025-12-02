from enum import StrEnum
from langgraph.graph import END
from agents.models.state import ConversationState
from langgraph.prebuilt import tools_condition
from agents.appointment.list_appointment_node import ToListAppointments
from agents.appointment.add_appointment_node import ToAddAppointment

class AppointmentRoute(StrEnum):
    """
    Pydantic model for the appointment routing path.
    """
    ENTER_LIST_APPOINTMENTS_NODE = "enter_list_appointments_node"
    ENTER_ADD_APPOINTMENT_NODE = "enter_add_appointment_node"
    PRIMARY_APPOINTMENT_NODE = "primary_appointment_node"


def route_appointment_details(state: ConversationState):
    route = tools_condition(state)
    if route == END:
        return END
    
    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tool_call.get("name") == "CompleteOrEscalate" for tool_call in tool_calls)
    if did_cancel:
        return "leave_skill"
    # tool_names = [t.name for t in appointment_list_tools]
    # if all(tc["name"] in tool_names for tc in tool_calls):
    return "list_appointment_safe_tools"

def route_add_appointment(state: ConversationState):
    route = tools_condition(state)
    if route == END:
        return END
    
    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tool_call.get("name") == "CompleteOrEscalate" for tool_call in tool_calls)
    if did_cancel:
        return "leave_skill"
    # tool_names = [t.name for t in appointment_list_tools]
    # if all(tc["name"] in tool_names for tc in tool_calls):
    return "add_appointment_safe_tools"
    
def route_primary_appointment(state: ConversationState):
    route = tools_condition(state)
    if route == END:
        return END
    
    tool_calls = state["messages"][-1].tool_calls
    if tool_calls:
        if tool_calls[0].get("name") == ToListAppointments.__name__:
            return AppointmentRoute.ENTER_LIST_APPOINTMENTS_NODE
        
        if tool_calls[0].get("name") == ToAddAppointment.__name__:
            return AppointmentRoute.ENTER_ADD_APPOINTMENT_NODE
        
    return AppointmentRoute.PRIMARY_APPOINTMENT_NODE # default route
