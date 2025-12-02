from pydantic import BaseModel, Field
from agents.appointment.tools.appointments import get_appointment_details, list_appointments
from agents.llms import get_llm_gemini_flash_light_latest
from agents.appointment.prompts.appointment_prompts import list_appointments_prompt
from agents.appointment.complete_or_escalate import CompleteOrEscalate
from typing import Optional
from agents.models.state import ConversationState
from agents.appointment.util.helpers import appointment_template_params

class ToListAppointments(BaseModel):
    """
    Transfer control to the list appointments node.
    """
    request: Optional[str] = Field(
        description="Any additional information the appointment list assistant should know",
        examples=[
            {"request": "I would like to list my appointments for the next 30 days"},
            {"request": "Show my upcoming appointments"},
            {"request": "List my past appointments"},
            {"request": "I would like to see my past appointments"},
        ]
    )

llm = get_llm_gemini_flash_light_latest(temperature=0.0)

list_appointments_node_tools = [list_appointments, get_appointment_details]

def list_appointments_node(state: ConversationState) -> dict:
    """
    Node: list appointments node
    - Lists the user's appointments
    - If the user needs help, and none of your tools are appropriate for it then
    "CompleteOrEscalate" the request to the host assistant. Do not waste users time. Do not make up invalid tools or functions.
    """
    chain = list_appointments_prompt | llm.bind_tools(list_appointments_node_tools + [CompleteOrEscalate])

    prompts_template = appointment_template_params(state)
    response = chain.invoke(prompts_template)

    return {
        "messages": [response],
    }