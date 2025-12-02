import pytest
import asyncio
from helpers import print_messages, run_graph_turn, BLUE, GREEN
import os

@pytest.mark.anyio
async def test_list_appointments():
    thread_id = "1"

    conversation = [
        "book an appointment. John Doe, 01-01-1960, 1111",
        "show me my upcoming appointments",
    ]

    for message in conversation:
        print_messages(f"🧑 user message: {message}", BLUE)
        reply, tid = await run_graph_turn(message, thread_id)
        print_messages(f"🤖 assistant message: {reply}", GREEN)

if __name__ == "__main__":
    asyncio.run(test_list_appointments())
