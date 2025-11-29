from agents.llms import get_llm_gemini_flash_light_latest
from agents.models.state import ConversationState
from agents.models.user import User
from langgraph.graph import END
from typing import Optional
from pydantic import BaseModel, Field
from services.user_service import UserService
from logging_config import llm_logger, logger
from langchain_core.messages import AIMessage
from agents.identity.prompts.identity_assistant import identity_collector_prompt

user_service = UserService()

llm = get_llm_gemini_flash_light_latest(temperature=0.0)

class UpdateInfo(BaseModel):
    """
    Pydantic model for updating the user's information.
    This is used to update the user's information in the state by the identity_collector_node
    """
    name: Optional[str] = Field(default=None, description="The user's full name")
    date_of_birth: Optional[str] = Field(default=None, description="The user's date of birth")
    ssn_last_4: Optional[str] = Field(default=None, description="The user's last 4 digits of their SSN")
    phone_number: Optional[str] = Field(default=None, description="The user's phone number")
    urgency_level: int = Field(default=1, description="The urgency level of the user's request")
    urgency_reason: str = Field(default="No urgency", description="The reason for the urgency")

def init_state(state: ConversationState) -> ConversationState:
    """
    Initializes the state.
    If the user is None, creates a new user with default values.
    Sets the urgency level and reason to default values.
    """
    user = state.get("user")
    if user is None:
        user = User(
            name="",
            date_of_birth="",
            ssn_last_4="",
            phone="",
            urgency_level=1,
            urgency_reason="No urgency",
        )
    state["user"] = user
    state["urgency_level"] = 1
    state["urgency_reason"] = "No urgency"
    state["is_new_patient"] = False
    state["user_verified"] = False
    return state

def missing_required_fields(user: User | dict | None) -> list[str]:
    """
    Checks if the user has all required fields for validator to check agains the database
    """
    if isinstance(user, User):
        u = user
    elif isinstance(user, dict):
        u = User(**user)
    else:
        return ["name", "date_of_birth"]

    missing = []
    if not u.name:
        missing.append("Full Name")
    if not u.date_of_birth:
        missing.append("Date of Birth")
    if not u.ssn_last_4 and not u.phone:
        missing.append("Last 4 digits of SSN or Phone Number")

    return missing


def user_to_prompt_vars(state: ConversationState):
    """
    Converts the user to a dictionary of variables for the identity_collector_prompt.
    """
    user = state.get("user")
    if not user:
        # If user is None, create a new user with default values
        return {
            "messages": state.get("messages", []),
            "name": "",
            "phone_number": "",
            "date_of_birth": "",
            "ssn_last_4": "",
            "urgency_level": 1,
            "urgency_reason": "No urgency",
            "missing_information": missing_required_fields(user),
        }

    # Use actual last user message if present, else synthetic one
    # If user is not None, use the actual user values
    return {
        "messages": state.get("messages", []),
        "name": user.name or "",
        "phone_number": user.phone or "",
        "date_of_birth": user.date_of_birth or "",
        "ssn_last_4": user.ssn_last_4 or "",
        "urgency_level": state.get("urgency_level", 1),
        "urgency_reason": state.get("urgency_reason", "No urgency"),
        "is_new_patient": state.get("is_new_patient", False),
        "missing_information": missing_required_fields(user),
    }


def merge_users(existing_user: User | None, new_user: UpdateInfo) -> User:
    """
    Merges two users together. If the existing user is None, creates a new user.
    """
    if existing_user is None:
        existing_user = User()
    return existing_user.model_copy(
        update={
            "name": new_user.name or existing_user.name,
            "date_of_birth": new_user.date_of_birth or existing_user.date_of_birth,
            "phone": new_user.phone_number or existing_user.phone,
            "ssn_last_4": new_user.ssn_last_4 or existing_user.ssn_last_4,
        }
    )

def handle_tool_calls(response, user: User) -> User | None:
    """
    Handles the tool calls from the response.
    """
    if response and response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call["name"] == "UpdateInfo":
                

                raw_args = tool_call["args"]
                actual_data = raw_args.get("BaseModel", raw_args)
                try:
                    update_info_obj = UpdateInfo.model_validate(actual_data)
                    updated_user = merge_users(user, update_info_obj)
                    return updated_user
                except Exception as e:
                    logger.error(f"Error validating tool call: {e}")
            else:
                logger.error(f"Unknown tool call: {tool_call}. Ignoring...")
    return None

# def ask_for_missing_identity_info_node(state: ConversationState) -> dict:
#     """
#     Asks the user for the missing identity information.
#     """
#     user = state.get("user")
#     if user is None:
#         user = init_state(state)
    
#     chain = identity_collector_missing_info_prompt | llm.bind_tools([UpdateInfo])

#     template_params = user_to_prompt_vars(state)
#     response = chain.invoke(template_params)
    
#     llm_logger.info(f"{response}")
    
#     updated_user = handle_tool_calls(response, user)
#     if updated_user is not None:
#         user = updated_user    

#     return {
#         "messages": [response],
#         "user": user,
#     }

def identity_collector_node(state: ConversationState) -> dict:
    """
    Graph node: call the identity_collector_runnable_node (LLM)
    which returns a User, then merge into state["User"].
    """
    messages = state.get("messages", [])
    logger.info(f"current messages: {messages}")
    
    # Create the chain: Prompt -> LLM (with tools bound)
    chain = identity_collector_prompt | llm.bind_tools([UpdateInfo])

    if "user" not in state or state["user"] is None:
        state = init_state(state)

    # 3. Invoke the chain
    template_params = user_to_prompt_vars(state)
    response = chain.invoke(template_params)
    
    llm_logger.info(f"{response}")

    user = state.get("user")
    if user is None:
        user = init_state(state)

    updated_user = handle_tool_calls(response, user)
    if updated_user is not None:
        user = updated_user

    # additional check if response from the LLM is empty (sometimes is, sometimes it asks user for additional info), but we don't have all data yet 
    # (possible due to smaller LLM, i should test larger one)
    additional_messages = []
    if response.content is None or response.content == "":
        missing_info = missing_required_fields(user)
        if len(missing_info) > 0:
            missing_info_str = ", ".join(missing_info)
            additional_messages.append(AIMessage(content=f"Please provide the following information: {missing_info_str}"))

    return {
        "messages": [response] + additional_messages,
        "user": user,
    }