from langchain_core.tools import tool
from typing import Annotated
from agents.models.user import User
from langgraph.prebuilt import InjectedState
from services.appointment_service import AppointmentService, Appointment, AppointmentConflictError
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
def get_appointment_details(user: Annotated[User, InjectedState("user")], appointment_id: Annotated[str, InjectedState("appointment_id")]) -> dict:
    """
    Get the details of the user's appointment by appointment id.
    Returns: 
    - A dictionary of the user's appointment details by appointment id
    """
    if not user or not user.id or not appointment_id:
        return {"error": "User not found or appointment id not found"}

    appointment = appointment_service.get_appointment(user.id, appointment_id)
    if not appointment:
        return {"error": "Appointment not found by appointment id"}
    return appointment.model_dump()

@tool
def add_appointment(user: Annotated[User, InjectedState("user")], appointment: Appointment) -> Appointment:
    """
    Add an appointment for the user.
    Args:
    - user: The user to add the appointment for
    - appointment: The appointment to add
    Returns: 
    - The appointment that was added
    """
    if not user or not user.id:
        return {"error": "User not found"}

    # 1) Validate required fields
    missing = []
    if not appointment.date:
        missing.append("date")
    if not appointment.provider:
        missing.append("provider")
    else:
        all_doctors = appointment_service.list_all_doctors_for_user(user.id)
        if not all_doctors:
            return {"error": "No doctors found for the user"}
        # check if doctor in the list of users doctors
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
        
        if len(matches) == 1:
            appointment.provider = matches[0]
        
        if len(matches) == 0:
            return {"error": f"Doctor {appointment.provider} not found for the user. Please choose a doctor from the following list: {', '.join(all_doctors)}"}

        if len(matches) > 1:
            return {
                "ambiguous_doctor": True,
                "matches": matches,
                "message": f"I found multiple doctors that match your query. Please choose one from the following list: {', '.join(matches)}."
            }

    # try parsing date
    try:
        appointment.date = datetime.strptime(appointment.date, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        return {"error": "Invalid date format. Please use the format YYYY-MM-DD."}

    if len(missing) > 0:
        return {"error": f"Please provide all of the missing information: {', '.join(missing)}."}

    try:
        added = appointment_service.add_appointment(appointment) 
    except AppointmentConflictError:
        available_times = appointment_service.get_doctor_available_times_for_day(appointment.provider, appointment.date)
        if not available_times:
            return {"error": "No available times found for the doctor on the given date. Please choose a different date."}
        else:
            return {
                "error": "New appointment falls in exsting doctors term. Please choose a different time or provider.",
                "available_times": available_times,
                "message": f"The doctor is available at the following times: {', '.join(available_times)}. Please choose one from the following list."
            }   

    return added.model_dump()