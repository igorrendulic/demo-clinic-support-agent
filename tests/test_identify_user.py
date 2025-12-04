import pytest
import asyncio
from helpers import print_messages, run_graph_turn, BLUE, GREEN
import os

@pytest.mark.anyio
async def test_identify_user():
    thread_id = "5"

    conversation = [
        "hi. I'm John Doe. My date of birth is 01-01-1960.",
        "my last 4 digits of my SSN are 1111.",
    ]
    for message in conversation:
        print_messages(f"🧑 user message: {message}", BLUE)
        reply, tid = await run_graph_turn(message, thread_id)
        print_messages(f"🤖 assistant message: {reply}", GREEN)

async def test_identify_user_new_patient():
    thread_id = "7"

    conversation = [
        "hi. I'm not feeling well. I have a fever and a headache. I need to see a doctor.",
        "My name is John Doe.",
        "My date of birth is 01-01-1960.",
        "my last 4 digits of my SSN are 1111.",
    ]
    for message in conversation:
        print_messages(f"🧑 user message: {message}", BLUE)
        reply, tid = await run_graph_turn(message, thread_id)
        print_messages(f"🤖 assistant message: {reply}", GREEN)

if __name__ == "__main__":
    # asyncio.run(test_identify_user())
    asyncio.run(test_identify_user_new_patient())