import pytest
import asyncio
from helpers import print_messages, run_graph_turn, BLUE, GREEN
from services.appointment_service import appointment_service
import os

@pytest.mark.anyio
async def test_book_appointment():
    thread_id = "2"

    conversation = [
        "book an appointment. John Doe, 01-01-1960, 1111",
        "book an appointment for tomorrow at 11:00 AM with Dr. Igor Doe",
        "yes. Lang Smith is ok",
        "4pm please",
        "yes",
        "Show all my appointments",
    ]
    for message in conversation:
        print_messages(f"🧑 user message: {message}", BLUE)
        reply, tid = await run_graph_turn(message, thread_id)
        print_messages(f"🤖 assistant message: {reply}", GREEN)

    # list appointments
    appointments = appointment_service.list_all_appointments()
    for appointment in appointments:
        print_messages(f"💬 appointment: {appointment.model_dump()}", GREEN)

if __name__ == "__main__":
    asyncio.run(test_book_appointment())
