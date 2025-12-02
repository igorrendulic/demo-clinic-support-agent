import pytest
import asyncio
from helpers import print_messages, run_graph_turn, BLUE, GREEN
import os

@pytest.mark.anyio
async def test_change_mind():
    thread_id = "3"

    conversation = [
        "Here is my information. Just log me in. John Doe, 01-01-1960, 1111",
        "book an appointment for tomorrow at 11:00 AM with Dr. Igor Doe",
        "nevermind i think I'll do this later",
        "book an appointment for tomorrow at 11:00 AM with Dr. Igor Doe",
        "nevermind i think I'll do this later",
        "show me my upcoming appointments",
    ]
    for message in conversation:
        print_messages(f"🧑 user message: {message}", BLUE)
        reply, tid = await run_graph_turn(message, thread_id)
        print_messages(f"🤖 assistant message: {reply}", GREEN)

if __name__ == "__main__":
    asyncio.run(test_change_mind())