from pydantic import BaseModel, Field
from typing import Optional
from agents.models.state import ConversationState
from agents.llms import get_llm_mini_model
from logging_config import logger, llm_logger
from agents.appointment.tools.appointment_tools import check_appointment, commit_appointment
from agents.appointment.complete_or_escalate import CompleteOrEscalate
from agents.appointment.prompts.appointment_prompts import add_appointment_prompt
from agents.appointment.util.helpers import appointment_template_params
from agents.appointment.tools.confirmation_tools import confirm_appointment_tool

llm = get_llm_mini_model(temperature=0.0)

add_appointment_node_tools = [check_appointment, commit_appointment, confirm_appointment_tool]

class ToAddAppointment(BaseModel):
    """
    Transfer control to the add appointment node.
    """
    request: Optional[str] = Field(
        description="Any additional information the appointment add assistant should know",
        examples=[
            {"request": "I would like to add an appointment for tomorrow at 10:00 AM"},
            {"request": "Add an appointment for next week at 11:00 AM"},
            {"request": "Add an appointment for next month at 12:00 PM with Dr. John Doe"},
            {"request": "I would like to add an appointment for next year at 1:00 PM with Dr. John Doe"},
        ]
    )

async def add_appointment_node(state: ConversationState) -> dict:
    """
    Node: add appointment node
    - Adds an appointment for the user
    """

    chain = add_appointment_prompt | llm.bind_tools(add_appointment_node_tools + [CompleteOrEscalate])
    prompts_template = appointment_template_params(state)
    response = await chain.ainvoke(prompts_template)

    llm_logger.info(f"add_appointment_node: response: {response}")

    return {"messages": [response]}