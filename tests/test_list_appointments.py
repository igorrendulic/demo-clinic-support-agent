import pytest
import asyncio
from helpers import print_messages, run_graph_turn
import os

@pytest.mark.anyio
async def test_list_appointments():
    thread_id = "1"

    # Turn 1 – user books an appointment
    message1 = "book an appointment. John Doe, 01-01-1960, 1111"
    reply1, tid1 = await run_graph_turn(message1, thread_id)
    print_messages(f"reply1: {reply1}")

    message2 = "show me my upcoming appointments"
    reply2, tid2 = await run_graph_turn(message2, thread_id)
    print_messages(f"reply2: {reply2}")

    message2 = "show me my upcoming appointments"
    reply2, tid2 = await run_graph_turn(message2, thread_id)
    print_messages(f"reply3: {reply2}")

if __name__ == "__main__":
    asyncio.run(test_list_appointments())
