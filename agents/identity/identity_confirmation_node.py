from agents.models.state import ConversationState
from langgraph.types import Command
from typing import Literal
from services.user_service import UserService
from agents.llms import get_llm_gemini_flash_light_latest
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

# user_service = UserService()

# llm = get_llm_gemini_flash_light_latest(temperature=0.0)


# class NewPatientIntent(BaseModel):
#     """Classify the user's intent regarding their patient status."""
#     is_new_patient: bool = Field(
#         description="True if the user confirms they are a new patient. False if they say they are an existing patient, made a mistake, or want to retry."
#     )
#     reasoning: str = Field(
#         description="A brief explanation of why you classified the intent this way."
#     )

# def ask_for_existing_patient_confirmation_node(state: ConversationState) -> dict:
#     """
#     Asks the user if they are an existing patient.
#     """
#     last_human_message = None
#     for message in reversed(state.get("messages")):
#         if isinstance(message, HumanMessage):
#             last_human_message = message
#             break

#     structured_llm = llm.with_structured_output(NewPatientIntent)
#     messages_to_send = [
#         SystemMessage(content="The user was not found in the DB and was asked if they are a new patient. Classify their response."),
#         HumanMessage(content=last_human_message.content),
#     ]
#     classification = structured_llm.invoke(messages_to_send)
#     print(f"classification: {classification}")
#     return {
#         "is_new_patient": classification.is_new_patient,
#         "user_verified": False,
#     }