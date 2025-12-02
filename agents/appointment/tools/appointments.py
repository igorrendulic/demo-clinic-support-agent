from langchain_core.tools import tool
from typing import Annotated
from agents.models.user import User
from langgraph.prebuilt import InjectedState
from services.appointment_service import AppointmentService, Appointment, AppointmentConflictError, AppointmentNotFoundError
import re
from datetime import datetime

appointment_service = AppointmentService()

def normalize(s: str) -> str:
    s = s.lower() # lowercase
    s = re.sub(r"[^\w\s]", "", s) # remove all non-alphanumeric characters
    return re.sub(r"\s+", " ", s).strip() # replace multiple spaces with a single space

@tool
def list_appointments(user: Annotated[User, InjectedState("user")]) -> list[dict]:
    """
    List the user's appointments.s
    Returns: 
    - A list of the user's appointments
    """
    if not user or not user.id:
        return [{"error": "User not found"}]

    appointments = appointment_service.get_appointments(user.id)
    return [appointment.model_dump() for appointment in appointments]

@tool
def check_appointment(user: Annotated[User, InjectedState("user")],appointment: Appointment) -> dict:
    """
    Validate and normalize an appointment request for the user, but DO NOT save it.
    Returns:
    - {"ok": True, "appointment": {...}, "message": "..."} when ready to book
    - {"ok": False, "error": "..."} on validation/format errors
    - richer structures on ambiguity or conflicts
    """
    if not user or not user.id:
        return {"ok": False, "error": "User not found"}

    # 1) Validate required fields
    missing = []
    if not appointment.date:
        missing.append("date")
    if not appointment.provider:
        missing.append("provider")

    if missing:
        return {
            "ok": False,
            "error": f"Please provide all of the missing information: {', '.join(missing)}."
        }

    # 2) Validate / normalize doctor
    all_doctors = appointment_service.list_all_doctors_for_user(user.id)
    if not all_doctors:
        return {"ok": False, "error": "No doctors found for the user"}

    query = normalize(appointment.provider)
    matches = []
    for d in all_doctors:
        nd = normalize(d)
        if nd == query:
            matches.append(d)
            break
        if query in nd.split():
            matches.append(d)
        if query in nd:
            matches.append(d)

    if len(matches) == 0:
        return {
            "ok": False,
            "error": (
                f"Doctor {appointment.provider} not found for the user. "
                f"Please choose a doctor from the following list: {', '.join(all_doctors)}"
            )
        }

    if len(matches) > 1:
        return {
            "ok": False,
            "ambiguous_doctor": True,
            "matches": matches,
            "message": (
                "I found multiple doctors that match your query. "
                f"Please choose one from the following list: {', '.join(matches)}."
            ),
        }

    # exactly one match
    appointment.provider = matches[0]

    # 3) Parse date
    try:
        appointment.date = datetime.strptime(
            appointment.date, "%Y-%m-%d"
        ).strftime("%Y-%m-%d")
    except ValueError:
        return {
            "ok": False,
            "error": "Invalid date format. Please use the format YYYY-MM-DD."
        }

    # 4) Check for conflict without writing
    try:
        # Optional: if you have a dry-run or "can_add" check, call it here instead
        appointment_service.check_conflict(appointment)  # pseudo-method
    except AppointmentConflictError:
        available_times = appointment_service.get_doctor_available_times_for_day(
            appointment.provider, appointment.date
        )
        if not available_times:
            return {
                "ok": False,
                "error": (
                    "No available times found for the doctor on the given date. "
                    "Please choose a different date."
                ),
            }
        else:
            return {
                "ok": False,
                "error": "New appointment falls in existing doctor's term.",
                "available_times": available_times,
                "message": (
                    "The doctor is available at the following times: "
                    f"{', '.join(available_times)}. Please choose one."
                ),
            }

    # If we reach here, we have a concrete, conflict-free appointment candidate
    summary = (
        f"Appointment on {appointment.date} at {appointment.time} "
        f"with {appointment.provider} at {appointment.location}"
    )

    return {
        "ok": True,
        "appointment": appointment.model_dump(),
        "message": (
            f"I can schedule the following appointment: {summary}. "
            "Would you like me to confirm this? (yes/no)"
        ),
    }

@tool
def commit_appointment(user: Annotated[User, InjectedState("user")], appointment: Appointment) -> Appointment:
    """
    Commit an appointment for the user.
    Args:
    - user: The user to add the appointment for
    - appointment: The appointment to commit
    Returns: 
    - The appointment that was committed
    """
    if not user or not user.id:
        return {"error": "User not found"}

    try:
        added = appointment_service.add_appointment(appointment)
    except AppointmentConflictError as e:
        # In practice, this should be rare if check_appointment runs first,
        # but we still handle it defensively.
        available_times = appointment_service.get_doctor_available_times_for_day(
            appointment.provider, appointment.date
        )
        if not available_times:
            return {
                "error": (
                    "No available times found for the doctor on the given date. "
                    "Please choose a different date."
                )
            }
        else:
            return {
                "error": "New appointment falls in existing doctor's term.",
                "available_times": available_times,
                "message": (
                    "The doctor is available at the following times: "
                    f"{', '.join(available_times)}. Please choose one."
                ),
            }
    return added.model_dump()

@tool
def cancel_appointment(user: Annotated[User, InjectedState("user")], appointment: Appointment) -> dict:
    """
    Cancel an appointment for the user.
    Args:
    - user: The user to cancel the appointment for
    - appointment: The appointment to cancel
    Returns: 
    - The appointment that was cancelled
    """
    if not user or not user.id or not appointment:
        return {"error": "User not found or appointment id not found"}
    
    try:
        found_appointments = appointment_service.find_appointments_for_user(appointment)
        if len(found_appointments) == 0:
            return {"error": "You don't have any appointments on that date."}
        if len(found_appointments) > 1:
            return {"error": f"Multiple appointments found for the same date. Please choose one from the following list: {', '.join(found_appointments)}"}
        if len(found_appointments) == 1:
            cancelled = appointment_service.cancel_appointment_by_id(found_appointments[0].id)
    except AppointmentNotFoundError as e:
        return {"error": "Appointment not found on that date. Try again with a different date or ask me to list your appointments."}
        
    return cancelled.model_dump()