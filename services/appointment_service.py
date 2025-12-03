from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, timedelta
from datetime import datetime, time

class Appointment(BaseModel):
    id: Optional[str] = Field(default=None, description="The appointment's unique identifier")
    user_id: Optional[str] = Field(default=None, description="The user's unique identifier")
    date: Optional[str] = Field(default=None, description="The appointment's date")
    time: Optional[str] = Field(default=None, description="The appointment's time")
    location: Optional[str] = Field(default=None, description="The appointment's location")
    provider: Optional[str] = Field(default=None, description="The appointment's provider")
    reason: Optional[str] = Field(default=None, description="The appointment's reason")
    status: Optional[str] = Field(default=None, description="The appointment's status")

class AppointmentConflictError(Exception):
    def __init__(self, message="New appointment already falls in exsting doctors term. Please choose a different time or provider."):
        super().__init__(message)

class AppointmentNotFoundError(Exception):
    def __init__(self, message="Appointment not found"):
        super().__init__(message)

class MultipleAppointmentsFoundError(Exception):
    def __init__(self, message="Multiple appointments found for the same date. Please choose one from the following list."):
        super().__init__(message)

class AppointmentService:
    def __init__(self):
        self.appointments: list[Appointment] = []
        today = date.today()
        tomorrow = today + timedelta(days=1)
        next_week = today + timedelta(days=7)
        in_two_weeks = today + timedelta(days=14)
        self.appointments = [
            Appointment(id="1", user_id="1", date=today.strftime("%Y-%m-%d"), time="10:00", location="123 Main St, Anytown, USA", provider="Dr. Lang Smith", reason="Annual physical", status="Confirmed"),
            Appointment(id="2", user_id="1", date=tomorrow.strftime("%Y-%m-%d"), time="11:00", location="456 Main St, Anytown, USA", provider="Dr. Lang Smith", reason="Follow-up", status="Confirmed"),
            Appointment(id="3", user_id="1", date=in_two_weeks.strftime("%Y-%m-%d"), time="12:00", location="456 Main St, Anytown, USA", provider="Dr. Lang Smith", reason="Check up", status="Confirmed"),
            Appointment(id="4", user_id="2", date=today.strftime("%Y-%m-%d"), time="12:00", location="789 Main St, Anytown, USA", provider="Dr. Jim Beam", reason="Annual physical", status="Confirmed"),
            Appointment(id="5", user_id="2", date=tomorrow.strftime("%Y-%m-%d"), time="13:00", location="101 Main St, Anytown, USA", provider="Dr. Jill Johnson", reason="Follow-up", status="Confirmed"),
            Appointment(id="6", user_id="3", date=next_week.strftime("%Y-%m-%d"), time="14:00", location="123 Main St, Anytown, USA", provider="Dr. Jack Daniels", reason="Annual physical", status="Confirmed"),
            Appointment(id="7", user_id="3", date=in_two_weeks.strftime("%Y-%m-%d"), time="15:00", location="456 Main St, Anytown, USA", provider="Dr. Jim Beam", reason="Follow-up", status="Confirmed"),
        ]

    def get_appointments(self, user_id: str) -> list[Appointment]:
        return [appointment for appointment in self.appointments if appointment.user_id == user_id]

    def list_all_appointments(self) -> list[Appointment]:
        return self.appointments

    def add_appointment(self, appointment: Appointment) -> Appointment:
        if appointment.id is None:
            appointment.id = str(len(self.appointments) + 1)
        
        if not appointment.provider:
            raise AppointmentConflictError("Provider does not exist")

        # check if new appointment already falls in exsting doctors term
        for a in self.appointments:
            if a.provider == appointment.provider and a.date == appointment.date and a.time == appointment.time:
                raise AppointmentConflictError("New appointment falls in exsting doctors term. Please choose a different time or provider.")
        
        self.appointments.append(appointment)
        return appointment

    def check_conflict(self, appointment: Appointment) -> None:
        for a in self.appointments:
            if a.provider == appointment.provider and a.date == appointment.date and a.time == appointment.time:
                raise AppointmentConflictError("New appointment falls in exsting doctors term. Please choose a different time or provider.")

    def update_appointment(self, appointment: Appointment) -> Appointment:
        for i, a in enumerate(self.appointments):
            if a.id == appointment.id and a.user_id == appointment.user_id:
                self.appointments[i] = appointment
                return appointment
        return None

    def delete_appointment(self, appointment: Appointment) -> bool:
        self.appointments = [
           a for a in self.appointments
           if not (a.id == appointment.id and a.user_id == appointment.user_id)
        ]
        return True

    def list_all_doctors(self) -> list[str]:
        """
        List all unique doctors in the appointments.
        Returns:
        - A list of all unique doctors
        """
        all_doctors = list(set([a.provider for a in self.appointments]))
        unique = set(all_doctors)
        return list(unique)

    def list_all_doctors_for_user(self, user_id: str) -> list[str]:
        """
        List all unique doctors for a user.
        Returns:
        - A list of all unique doctors for the user
        """
        all_doctors = list(set([a.provider for a in self.appointments if a.user_id == user_id]))
        unique = set(all_doctors)
        return list(unique)

    def get_doctor_available_times_for_day(self, 
        provider: str,
        date: str,
        start_hour: int = 9,
        end_hour: int = 17,
        slot_minutes: int = 60) -> list[str]:
        """
        Suggest available appointment times for a doctor on a specific date.
        
        - provider: full provider name (e.g. "Dr. Lang Smith")
        - date: "YYYY-MM-DD"
        - start_hour: doctor's workday start (default 9)
        - end_hour: doctor's workday end (default 17)
        - slot_minutes: appointment length (default 60)
        """
        booked = {
            a.time
            for a in self.appointments
            if a.provider == provider and a.date == date
        }
        day = datetime.strptime(date, "%Y-%m-%d")
        t = datetime.combine(day, time(hour=start_hour, minute=0)) # start of workday
        end_time = datetime.combine(day, time(hour=end_hour, minute=0)) # end of workday

        all_slots = []
        while t < end_time:
            all_slots.append(t.strftime("%H:%M"))
            t += timedelta(minutes=slot_minutes)

        # Remove booked slots → available slots
        available = [s for s in all_slots if s not in booked]

        return available

    def find_appointments_for_user(self, appointment: Appointment) -> list[Appointment]:
        """
        Find appointments for a user for a specific date.
        Args:
        - appointment: The appointment to find
        Returns:
        - A list of appointments for the user on the given date
        - If time is provided, return the appointment at that time
        Raises:
        - AppointmentNotFoundError: If the appointment is not found
        - MultipleAppointmentsFoundError: If multiple appointments are found for the same date
        """
        if not appointment.user_id or not appointment.date:
            raise AppointmentNotFoundError("User id or date not found")
        
        found_appointments = []
        for i, a in enumerate(self.appointments):
            if a.user_id == appointment.user_id and a.date == appointment.date:
                found_appointments.append(a)
        if len(found_appointments) == 0:
            raise AppointmentNotFoundError("Appointment not found")
        if len(found_appointments) > 1:
            if appointment.time:
                found_appointments = [a for a in found_appointments if a.time == appointment.time]
            
        return found_appointments

    def cancel_appointment_by_id(self, appointment_id: str) -> Appointment:
        """
        Cancel an appointment by id.
        Args:
        - appointment_id: The id of the appointment to cancel
        Returns:
        - The appointment that was cancelled
        - raises AppointmentNotFoundError if appointment not found
        """
        if not appointment_id:
            raise AppointmentNotFoundError("Appointment id not found")
        
        for i, a in enumerate(self.appointments):
            if a.id == appointment_id:
                removed = self.appointments.pop(i)
                return removed

        raise AppointmentNotFoundError("Appointment not found")

    def get_doctor_location(self, provider: str) -> str:
        """
        Get the location of a doctor.
        Args:
        - provider: The provider to get the location for
        Returns:
        - The location of the doctor
        """
        for a in self.appointments:
            if a.provider == provider:
                return a.location
        return None

    def reschedule_appointment(self, appointment_id: str, new_date: str, new_time: str) -> Appointment:
        """
        Reschedule an appointment by id.
        Args:
        - appointment_id: The id of the appointment to reschedule
        - new_date: The new date to reschedule the appointment to
        - new_time: The new time to reschedule the appointment to
        Returns:
        - The appointment that was rescheduled
        - raises AppointmentNotFoundError if appointment not found
        - raises AppointmentConflictError if there is conflicts in new_date and new_time with existing appointments
        """
        # get appointment by id: 
        for a in self.appointments:
            if a.id == appointment_id:
                appointment = a
                break
            
        if not appointment:
            raise AppointmentNotFoundError("Appointment not found")
        
        # check if there is conflicts in new_date and new_time with existing appointments
        for a in self.appointments:
            if a.provider == appointment.provider and a.date == new_date and a.time == new_time:
                raise AppointmentConflictError("New appointment falls in exsting doctors term. Please choose a different time or provider.")
        
        # update the appointment
        for i, a in enumerate(self.appointments):
            if a.id == appointment.id:
                self.appointments[i].date = new_date
                self.appointments[i].time = new_time
                return a

        raise AppointmentNotFoundError("Appointment not found")


appointment_service = AppointmentService()