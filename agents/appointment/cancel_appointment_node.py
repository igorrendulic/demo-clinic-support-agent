from pydantic import BaseModel, Field
from agents.llms import get_llm_mini_model
from agents.appointment.prompts.appointment_prompts import cancel_appointment_prompt
from agents.appointment.complete_or_escalate import CompleteOrEscalate
from typing import Optional
from agents.models.state import ConversationState
from agents.appointment.util.helpers import appointment_template_params
from agents.appointment.tools.appointment_tools import find_appointment_tool, commit_cancel_appointment
from agents.appointment.tools.confirmation_tools import confirm_appointment_tool

class ToCancelAppointment(BaseModel):
    """
    Transfer control to the cancel appointment node.
    """
    request: Optional[str] = Field(
        description="Any additional information the appointment cancel assistant should know",
        examples=[
            {"request": "I would like to cancel my appointment on 2025-12-02 at 14:00"},
            {"request": "I would like to cancel my appointment on 2025-12-02 at 15:00 with Dr. Igor Doe"},
            {"request": "I would like to cancel my appointment next week"},
            {"request": "I would like to cancel my appointment next week with Dr. Igor Doe"},
        ]
    )

llm = get_llm_mini_model(temperature=0.0)

cancel_appointment_node_tools = [find_appointment_tool, confirm_appointment_tool, commit_cancel_appointment]

async def cancel_appointment_node(state: ConversationState) -> dict:
    """
    Node: cancel appointment node
    - Cancels the user's appointment
    - If the user needs help, and none of your tools are appropriate for it then
    "CompleteOrEscalate" the request to the host assistant. Do not waste users time. Do not make up invalid tools or functions.
    """
    chain = cancel_appointment_prompt | llm.bind_tools(cancel_appointment_node_tools + [CompleteOrEscalate])

    prompts_template = appointment_template_params(state)
    response = await chain.ainvoke(prompts_template)

    return {"messages": [response]}