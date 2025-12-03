import pytest
import asyncio
from helpers import print_messages, run_graph_turn, BLUE, GREEN
from datetime import datetime, timedelta

@pytest.mark.anyio
async def test_reschedule_appointment():
    thread_id = "4"

    in_four_weeks = datetime.now() + timedelta(weeks=4)

    conversation = [
        "My identity is John Doe, 01-01-1960, 1111",
        "I can't make it to my appoinment tomorrow. I need to reschedule it.",
        f"to {in_four_weeks.strftime('%B %d, %Y')} at 3pm",
        "yes. Please reschedule it",
        "show me my upcoming appointments",
    ]

    for message in conversation:
        print_messages(f"🧑 user message: {message}", BLUE)
        reply, tid = await run_graph_turn(message, thread_id)
        print_messages(f"🤖 assistant message: {reply}", GREEN)

    

if __name__ == "__main__":
    asyncio.run(test_reschedule_appointment())
