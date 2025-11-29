# Define the intent schema 
from pydantic import BaseModel
from typing import Any
from enum import Enum

class IntentType(str, Enum):
    ID_VERIFICATION = "id_verification" 
    BOOK_APPOINTMENT = "book_appointment"
    APPOINTMENT_CONFIRMATION = "appointment_confirmation"
    APPOINTMENT_CANCELLATION = "appointment_cancellation"
    APPOINTMENT_RESCHEDULING = "appointment_rescheduling"
    SMALLTALK = "smalltalk"


class Intent(BaseModel):
    name: IntentType
    completed: bool

class IntentMetadata(BaseModel):
    name: str
    description: str
    slots: dict[str, Any]
    completed: bool

# define slots for each intent
BOOK_APPOINTMENT_SLOTS = {
    "date": {
        "type": "date",
        "description": "The date of the appointment",
        "required": True,
    },
    "time": {
        "type": "time",
        "description": "The time of the appointment",
        "required": True,
    },
}

BOOK_APPOINTMENT_INTENT = IntentType.BOOK_APPOINTMENT

# Itents for ID Verification
ID_VERIFICATION_SLOTS = {
    "phone_number": {
        "type": "string",
        "description": "Phone number of the user",
        "required": True,
    },
    "date_of_birth": {
        "type": "date",
        "description": "Date of birth of the user",
        "required": True,
    },
    "ssn_last_4": {
        "type": "string",
        "description": "Last 4 digits of the user's SSN",
        "required": True,
    },
}

ID_VERIFICATION_INTENT = Intent(
    name="id_verification",
    description="Verify the user's ID",
    slots=ID_VERIFICATION_SLOTS,
    completed=False,
)