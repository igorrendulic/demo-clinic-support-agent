from pydantic import BaseModel, Field
from langchain_core.tools import tool

class ConfirmAppointmentArgs(BaseModel):
    """Explicit confirmation from the user about booking the candidate appointment."""
    confirm: bool = Field(
        ...,
        description=(
            "True if the user clearly wants to book the appointment, "
            "False if they decline, want to change something, or are unsure."
        ),
    )


@tool
def confirm_appointment_tool(confirm: bool) -> dict:
    """
    Use this tool to explicitly decide whether the user confirmed the appointment.

    The LLM must set `confirm=True` ONLY when the user has clearly agreed to
    book the appointment (e.g., 'yes', 'please confirm it', 'book it').
    """
    return {"confirm": confirm}