from agents.models.state import ConversationState
from agents.identity.identity_router import IdentityRoute
from agents.appointment.appointment_router import AppointmentRoute

def route_start(state: ConversationState):
    if not state.get("user_verified"):
        return IdentityRoute.IDENTITY_COLLECTOR_NODE
    
    # user is verified, look at appointment state
    appointment_state = state.get("appointment_state") or []

    # supported direct appointment routes
    if appointment_state and len(appointment_state) > 0:
        last = appointment_state[-1]
        # auto-exit read-only ops 
        if last == "cancel_appointment":
            return "cancel_appointment"
        
        if last == "add_appointment":
            return "add_appointment"
        
        if last == "reschedule_appointment":
            return "reschedule_appointment"
    
    # default
    return AppointmentRoute.PRIMARY_APPOINTMENT_NODE