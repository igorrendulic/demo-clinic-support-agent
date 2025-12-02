import pytest
import asyncio
from helpers import print_messages, run_graph_turn
import os

@pytest.mark.anyio
async def test_book_appointment():
    thread_id = "2"

    # Turn 1 – user books an appointment
    message1 = "book an appointment. John Doe, 01-01-1960, 1111"
    reply1, tid1 = await run_graph_turn(message1, thread_id)
    print_messages(f"reply1: {reply1}")

    message3 = "book an appointment for tomorrow at 11:00 AM with Dr. Igor Doe"
    reply3, tid3 = await run_graph_turn(message3, thread_id)
    print_messages(f"reply3: {reply3}")

    message4 = "yes. Lang Smith is ok"
    reply4, tid4 = await run_graph_turn(message4, thread_id)
    print_messages(f"reply4: {reply4}")

    message5 = "4pm please"
    reply5, tid5 = await run_graph_turn(message5, thread_id)
    print_messages(f"reply5: {reply5}")

if __name__ == "__main__":
    asyncio.run(test_book_appointment())
