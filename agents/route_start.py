from agents.models.state import ConversationState
from agents.identity.identity_router import IdentityRoute
from agents.appointment.appointment_router import AppointmentRoute

def route_start(state: ConversationState):
    if not state.get("user_verified"):
        return IdentityRoute.IDENTITY_COLLECTOR_NODE
    
    # user is verified, look at appointment state
    appointment_state = state.get("appointment_state") or []

    if appointment_state and len(appointment_state) > 0:
        last = appointment_state[-1]
        # auto-exit read-only ops 
        if last == "list_appointments":
            return AppointmentRoute.PRIMARY_APPOINTMENT_NODE
        
        if last == "add_appointment":
            return "add_appointment"

        # if last == "cancel_appointment":
        #     return AppointmentRoute.ENTER_CANCEL_APPOINTMENT_NODE
    
    # default
    return AppointmentRoute.PRIMARY_APPOINTMENT_NODE

    if state.get("user_verified") is True:
        appointment_state = state.get("appointment_state")
        if appointment_state and len(appointment_state) > 0:
            if appointment_state[-1] == "list_appointments": # auto exit read-only ops
                return AppointmentRoute.PRIMARY_APPOINTMENT_NODE
            # check if the last state is a tool call
            return appointment_state[-1]
        # no appointment state or empty appointment state
        return AppointmentRoute.PRIMARY_APPOINTMENT_NODE
    else:
        return IdentityRoute.IDENTITY_COLLECTOR_NODE