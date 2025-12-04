from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import Literal, Optional

class IntentResult(BaseModel):
    """
    Pydantic model for the intent result.
    """
    intent: Literal[
        "add_appointment",
        "reschedule_appointment",
        "cancel_appointment",
        "list_appointments",
        "other",
    ]
    confidence: float = Field(default=0.0, description="The confidence in the intent")
    original_message: Optional[str] = Field(default=None, description="The original message from the user")

intent_prompt = ChatPromptTemplate.from_messages([
    ("system",
        """Classify the user's intent based only on the given message.

        Return exactly one intent label from this set:
        - add_appointment
        - cancel_appointment
        - reschedule_appointment
        - list_appointments
        - other

        If you are not sure about the intent, return "other".

        Also include a confidence score between 0 and 1 for the intent.

        Example:
        - Intent: add_appointment
        - Confidence: 0.95
        - Response: "add_appointment"
        - Example: "I want to add an appointment for tomorrow at 10am."
        - Example: "I need to see a doctor for a headache."

        Example:
        - Intent: other
        - Confidence: 0.5
        - Response: "other"
        - Example: "I'm not sure what I want to do."
        - Example: "My name is Patrick"
        - Example: "My date of birth is Jan 1st 2000."
        - Example: "My last 4 digits of my SSN are 1234."
        - Example: "My phone number is 123-456-7890."

        Example:
        - Intent: cancel_appointment
        - Confidence: 0.85
        - Response: "cancel_appointment"
        - Example: "I want to cancel my appointment for tomorrow."

        Example:
        - Intent: reschedule_appointment
        - Confidence: 0.75
        - Response: "reschedule_appointment"
        - Example: "I want to reschedule my appointment for next week."

        Example:
        - Intent: list_appointments
        - Confidence: 0.65
        - Response: "list_appointments"
        - Example: "show me my upcoming appointments."
"""),
    ("human", "{text}")
])