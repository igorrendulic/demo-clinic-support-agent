import pytest
import asyncio
from helpers import print_messages, run_graph_turn, BLUE, GREEN
import os

@pytest.mark.anyio
async def test_identity_guessing():
    thread_id = "6"

    conversation = [
        "hi. I'm John Doe. My date of birth is 01-01-1960.",
        "my last 4 digits of my SSN are 1112.",
        "no. i made a mistake.",
        "my last 4 digits of my SSN are 1114.",
        "my last 4 digits of my SSN are 1115.",
        "my last 4 digits of my SSN are 1116.",
        "my last 4 digits of my SSN are 1117.",
    ]
    for message in conversation:
        print_messages(f"🧑 user message: {message}", BLUE)
        reply, tid = await run_graph_turn(message, thread_id)
        print_messages(f"🤖 assistant message: {reply}", GREEN)

if __name__ == "__main__":
    asyncio.run(test_identity_guessing())