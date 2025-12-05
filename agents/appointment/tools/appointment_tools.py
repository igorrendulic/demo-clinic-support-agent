from langchain_core.tools import tool
from typing import Annotated
from agents.models.user import User
from langgraph.prebuilt import InjectedState
from services.appointment_service import Appointment, AppointmentConflictError, AppointmentNotFoundError
import re
from datetime import datetime
from logging_config import logger
from services.appointment_service import appointment_service
from pydantic import BaseModel, Field
from langgraph.store.memory import InMemoryStore

doctor_preference_store = InMemoryStore()
namespace = ("doctor_preferences", "user_id")

def normalize(s: str) -> str:
    s = s.lower() # lowercase
    s = re.sub(r"[^\w\s]", "", s) # remove all non-alphanumeric characters
    return re.sub(r"\s+", " ", s).strip() # replace multiple spaces with a single space

class PrepareRescheduleAppointmentInput(BaseModel):
    appointment_id: str = Field(description="The id of the appointment to reschedule")
    new_date: str = Field(  # normalize to YYYY-MM-DD
        description="The requested new date",
        examples=[
            "december 4th, 2025",
            "2025-12-04",
            "Jan 4, 2026",
        ]
    )
    new_time: str = Field(
        description="The requested new time",
        examples=[
            "10:00 AM",
            "10:00",
            "10:00 PM",
            "14:00",
            "2pm",
            "5 afternoon"
        ]
    )

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
    if len(appointments) > 0:
        # sort by date and time ascending
        appointments.sort(
            key=lambda x: datetime.strptime(f"{x.date} {x.time}", "%Y-%m-%d %H:%M")
        )
    
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
        # check if this is a preference or the usual doctor
        preference = doctor_preference_store.get(namespace, user.id)
        if preference:
            appointment.provider = preference.value.get("doctor_name", "")
        else:
            # collect doctor names
            all_user_doctors = appointment_service.list_all_doctors_for_user(user.id)
            all_open_doctors = appointment_service.list_open_doctors()
            return {
                "ok": False,
                "error": f"Please provide the doctor's name. These are the doctors you've seen before: {', '.join(all_user_doctors)}. If you'd like to see a different doctor, please choose one from the following list: {', '.join(all_open_doctors)}"
            }

    if missing:
        return {
            "ok": False,
            "error": f"Please provide all of the missing information: {', '.join(missing)}."
        }

    # 2) Validate / normalize doctor
    all_user_doctors = appointment_service.list_all_doctors_for_user(user.id)
    all_open_doctors = appointment_service.list_open_doctors()
    all_doctors = all_user_doctors + all_open_doctors
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

    # check if this is a preference or the usual doctor
    is_new_preference = True
    for d in all_user_doctors:
        if d == appointment.provider:
            is_new_preference = False
            break
    
    # if the doctor is one that user hasn't seen before add it as new preference 
    # next time, the preferred doctor will be seen instead of the usual one
    if is_new_preference:
        doctor_preference_store.put(namespace, user.id, {
            "doctor_name": appointment.provider,
            "reason": "",
        })
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
        appointment.user_id = user.id # add user id to appointment
        appointment.status = "Confirmed" # add status to appointment
        provider = appointment.provider 
        if provider: # assign location based on the doctor
            location = appointment_service.get_doctor_location(provider)
            if location is not None:
                appointment.location = location
        
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
def find_appointment_tool(user: Annotated[User, InjectedState("user")], appointment: Appointment) -> dict:
    """
    Find an appointment for the user.
    Args:
    - user: The user to find the appointment for
    - appointment: The appointment to find
    Returns: 
    - {"ok": True, "appointment": {...}, "message": "..."} when appointment found
    - {"ok": False, "error": "..."} on validation/format errors
    """
    if not user or not user.id:
        return {"ok": False, "error": "User not found"}
    if not appointment.date:
        return {"ok": False, "error": "Missing information. Appointment date is required."}
    
    appointment.user_id = user.id
    
    found_appointments = appointment_service.find_appointments_for_user(appointment)
    if len(found_appointments) == 0:
        return {"ok": False, "error": "Appointment not found on that date. Try again with a different date or ask me to list your appointments."}
    if len(found_appointments) > 1:
        return {"ok": False, "error": "Multiple appointments found for the same date. Please choose one from the following list: {', '.join([a.model_dump() for a in found_appointments])}"}
    return {"ok": True, "appointment": found_appointments[0].model_dump(), "message": (
        f"I found this appointment: {found_appointments[0].date} at {found_appointments[0].time} with {found_appointments[0].provider} at {found_appointments[0].location}. "
        "Would you like me to cancel this appointment? (yes/no)"
    )}

@tool
def commit_cancel_appointment(user: Annotated[User, InjectedState("user")], appointment: Appointment) -> Appointment:
    """
    Commit the cancellation of an appointment for the user.
    Args:
    - user: The user to cancel the appointment for
    - appointment: The appointment to cancel
    Returns: 
    - The appointment that was cancelled
    """
    if not user or not user.id:
        return {"ok": False, "error": "User not found"}

    appointment.user_id = user.id
    
    # sanity check if appointment still exists
    appointments = appointment_service.find_appointments_for_user(appointment)
    if len(appointments) == 0:
        return {"ok": False, "error": "Appointment not found on that date. Try again with a different date or ask me to list your appointments."}
    if len(appointments) > 1:
        return {"ok": False, "error": f"Multiple appointments found for the same date. Please choose one from the following list: {', '.join([a.model_dump() for a in appointment])}"}    
    
    # exactly 1 appointment 
    try:
        app = appointments[0]
        cancelled = appointment_service.cancel_appointment_by_id(app.id)
        if not cancelled:
            return {"ok": False, "error": "Appointment not found. Try again with a different date or ask me to list your appointments."}
        return {"ok": True, "appointment": cancelled.model_dump(), "message": (
            f"I successfully cancelled the following appointment: {cancelled.date} at {cancelled.time} with {cancelled.provider} at {cancelled.location}."
        )}
    except Exception as e:
        return {"ok": False, "error": f"Failed to cancel appointment due to internal system issue. Please try again later."}

@tool
def prepare_reschedule_appointment(user: Annotated[User, InjectedState("user")], data: PrepareRescheduleAppointmentInput) -> Appointment:
    """
    Prepare the rescheduling of an appointment for the user.
    Args:
    - user: The user to reschedule the appointment for
    - data: The data to prepare the rescheduling of an appointment for the user
    Returns: 
    - {"ok": True, "appointment": {...}, "message": "..."} when appointment rescheduled
    - {"ok": False, "error": "..."} on validation/format errors
    """
    
    if not user or not user.id:
        return {"ok": False, "error": "User not found"}
    if not data.appointment_id:
        return {"ok": False, "error": "Missing information. Current appointment is required."}
    if not data.new_date:
        return {"ok": False, "error": "Missing information. New date is required."}
    if not data.new_time:
        return {"ok": False, "error": "Missing information. New time is required."}
    
    current_appointment = next(
        (a for a in appointment_service.appointments
         if a.id == data.appointment_id),
        None,
    )
    if not current_appointment:
        return {
            "ok": False,
            "error": f"Appointment with id {data.appointment_id} was not found.",
        }
    try:
        normalized_date = datetime.strptime(data.new_date, "%Y-%m-%d").strftime("%Y-%m-%d")
        normalized_time = datetime.strptime(data.new_time, "%H:%M").strftime("%H:%M")
    except ValueError:
        return {
            "ok": False,
            "error": "Invalid date or time format. Please use YYYY-MM-DD and HH:MM.",
        }

    updated = current_appointment.model_copy(update={
        "date": normalized_date,
        "time": normalized_time,
    })
    try:
        appointment_service.check_conflict(updated)
    except AppointmentConflictError as e:
        available_times = appointment_service.get_doctor_available_times_for_day(
            updated.provider, updated.date
        )
        if not available_times:
            return {
                "ok": False,
                "error": "No available times found for the doctor on the given date. Please choose a different date.",
            }
    
    # Everything looks good
    return {
        "ok": True,
        "appointment_id": current_appointment.id,
        "new_date": normalized_date,
        "new_time": normalized_time,
        "message": (
            f"I can reschedule the following appointment: {updated.date} at {updated.time} with {updated.provider} at {updated.location}. "
            "Would you like me to confirm this? (yes/no)"
        ),
    }

@tool
def commit_reschedule_appointment(user: Annotated[User, InjectedState("user")], current_appointment: Appointment, new_date: str, new_time: str) -> Appointment:
    """
    Commit the rescheduling of an appointment for the user.
    Args:
    - user: The user to reschedule the appointment for
    - current_appointment: The current appointment to reschedule
    - new_date: The new date to reschedule the appointment to
    - new_time: The new time to reschedule the appointment to
    Returns: 
    - {"ok": True, "appointment": {...}, "message": "..."} when appointment rescheduled
    - {"ok": False, "error": "..."} on validation/format errors
    """
    if not user or not user.id:
        return {"error": "User not found"}
    
    # sanity check if appointment still exists
    appointments = appointment_service.find_appointments_for_user(current_appointment)
    if len(appointments) == 0:
        return {"ok": False, "error": "Appointment not found on that date. Try again with a different date or ask me to list your appointments."}
    if len(appointments) > 1:
        return {"ok": False, "error": f"Multiple appointments found for the same date. Please choose one from the following list: {', '.join([a.model_dump() for a in appointment])}"}    
    
    current_appointment = appointments[0]
    new_date = datetime.strptime(new_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    new_time = datetime.strptime(new_time, "%H:%M").strftime("%H:%M")
    try:
        rescheduled = appointment_service.reschedule_appointment(current_appointment.id, new_date, new_time)
        return {"ok": True, "appointment": rescheduled.model_dump(), "message": (
            f"I rescheduled the following appointment: {current_appointment.date} at {current_appointment.time} with {current_appointment.provider} at {current_appointment.location}. "
            "Would you like me to confirm this? (yes/no)"
        )}
    except AppointmentNotFoundError as e:
        return {"ok": False, "error": "Appointment not found. Try again with a different date or ask me to list your appointments."}
    except AppointmentConflictError as e:
        return {"ok": False, "error": "New appointment falls in existing doctor's term. Please choose a different time or provider."}
    except Exception as e:
        return {"ok": False, "error": f"Failed to reschedule appointment due to internal system issue. Please try again later."}