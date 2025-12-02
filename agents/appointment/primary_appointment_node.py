from agents.appointment.list_appointment_node import ToListAppointments
from agents.models.state import ConversationState
from langchain_core.messages import AIMessage, HumanMessage
from agents.appointment.prompts.appointment_prompts import primary_appointment_prompt
from agents.llms import get_llm_gemini_flash_light_latest
from logging_config import logger, llm_logger
from agents.appointment.add_appointment_node import ToAddAppointment
from agents.appointment.util.helpers import appointment_template_params

llm = get_llm_gemini_flash_light_latest(temperature=0.0)

def primary_appointment_node(state: ConversationState) -> dict:
    """
    Node: main appointment node
    - Reads the user info from the state
    - Hands off to a doctor
    """
    user = state.get("user")
    messages = state.get("messages", [])
    logger.info(f"primary_appointment_node: user: {user}, messages: {messages}")

    # TODO! clear any old messages from user messages
    chain = primary_appointment_prompt | llm.bind_tools([
        ToListAppointments,
        ToAddAppointment,
    ])

    prompts_template = appointment_template_params(state)
    
    response = chain.invoke(prompts_template)

    llm_logger.info(f"primary_appointment_node: response: {response}")

    return {
        "messages": [response],
    }