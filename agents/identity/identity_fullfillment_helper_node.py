from agents.models.state import ConversationState
from agents.llms import get_llm_gemini_flash_light_latest
from agents.identity.prompts.identity_assistant import identity_fullfillment_helper_prompt
from langchain_core.messages import AIMessage
from agents.identity.identity_collector_node import UpdateInfo, user_to_prompt_vars, handle_tool_calls
from logging_config import llm_logger
from services.user_service import UserService
from typing import Tuple, List, Literal
from agents.models.user import User
from langchain_core.messages import HumanMessage, BaseMessage
from langgraph.types import interrupt

llm = get_llm_gemini_flash_light_latest(temperature=0.0)

user_service = UserService()

def ask_user_to_correct_information(state: ConversationState):
    """
    Ask the user to correct their information.
    """
    user = state.get("user")
    number_of_corrections = state.get("identity_fullfillment_number_of_corrections", 0)
    current_info_str = f"""
        Current information:
        Name: {user.name}
        Date of Birth: {user.date_of_birth}
        Last 4 digits of SSN: {user.ssn_last_4}
        Phone number: {user.phone}
        \n\n
        Review the current information and provide the correct information.
        """

    user_input = interrupt(current_info_str)
    number_of_corrections = number_of_corrections + 1
    return {
        "messages": [HumanMessage(content=user_input)],
        "user": user,
        "identity_fullfillment_number_of_corrections": number_of_corrections,
    }

def validate_corrected_input(state: ConversationState) -> Literal["success", "failure", "retry"]:
    """
    Validate the corrected input from the user.
    """
    user = state.get("user")
    number_of_corrections = state.get("identity_fullfillment_number_of_corrections", 0)
    if number_of_corrections > 3:
        return "failure"
    
    u = user_service.get_user(user.name, user.date_of_birth, user.phone, user.ssn_last_4)
    if u is not None:
        # user has been verified, validation node should validate it also
        return "success"
    return "retry"

def identity_fullfillment_helper_node(state: ConversationState) -> dict:
    """
    Helper node to help the user with their identity information.
    If user has made too many corrections, finish the conversation and offer them either new patient form or support line
    This is in case they're trying to "hack" the system by trying to correct their identity information too many times (e.g. guessing the correct information)
    """
    user = state.get("user")

    number_of_corrections = state.get("identity_fullfillment_number_of_corrections", 0)
    chain = identity_fullfillment_helper_prompt | llm.bind_tools([UpdateInfo])

    template_params = user_to_prompt_vars(state)
    response = chain.invoke(template_params)
    llm_logger.info(f"identity_fullfillment_helper_node response: {response}")

    updated_user = handle_tool_calls(response, user)
    if updated_user is not None:
        number_of_corrections = number_of_corrections + 1
        user = updated_user
        
    u = user_service.get_user(user.name, user.date_of_birth, user.phone, user.ssn_last_4)
    if u is not None:
        # user has been verified, validation node should validate it also
        return {
            "user": u,
            "identity_fullfillment_number_of_corrections": number_of_corrections,
        }
  
    return {
        "messages": [response],
        "user": user,
        "identity_fullfillment_number_of_corrections": number_of_corrections,
    }