from agents.appointment.cancel_appointment_node import ToCancelAppointment
from agents.models.state import ConversationState
from langchain_core.messages import AIMessage, HumanMessage
from agents.appointment.prompts.appointment_prompts import primary_appointment_prompt
from agents.llms import get_llm_mini_model
from logging_config import logger, llm_logger
from agents.appointment.add_appointment_node import ToAddAppointment
from agents.appointment.util.helpers import appointment_template_params
from agents.appointment.tools.appointments import list_appointments

llm = get_llm_mini_model(temperature=0.0)

primary_appointment_node_tools = [
    list_appointments,
]

def primary_appointment_node(state: ConversationState) -> dict:
    """
    Node: main appointment node
    - Reads the user info from the state
    - Hands off to a specialized assistant for the user's request (add, cancel, reschedule appointments)
    """
    chain = primary_appointment_prompt | llm.bind_tools(primary_appointment_node_tools + [
        ToCancelAppointment,
        ToAddAppointment,
        # ToRescheduleAppointment,
    ])

    prompts_template = appointment_template_params(state)
    
    response = chain.invoke(prompts_template)

    return {
        "messages": [response],
    }